"""离线验证 Day 6 的本地检索与一次生成，不读取真实密钥或发送请求。"""

from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from openai import APIConnectionError, APIStatusError
from openai.types.chat import ChatCompletionMessage

from app import local_rag


def sample_chunks():
    return [
        {
            "source": "rag_basics.md",
            "chunk_id": 2,
            "text": "分块把文档拆成较小的片段，片段保留来源和编号。",
        },
        {
            "source": "demo_rules.md",
            "chunk_id": 1,
            "text": "教学演示约定：每次最多向模型提供 2 个检索片段。",
        },
        {
            "source": "rag_basics.md",
            "chunk_id": 1,
            "text": "RAG 会先查找材料，再根据材料生成回答。",
        },
    ]


def sample_results():
    chunks = sample_chunks()
    return [
        {"score": 2, "chunk": chunks[1]},
        {"score": 1, "chunk": chunks[0]},
    ]


def response_with(content=None, finish_reason="stop"):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=ChatCompletionMessage(role="assistant", content=content),
                finish_reason=finish_reason,
            )
        ]
    )


class DocumentTests(unittest.TestCase):
    def test_split_strips_paragraphs_skips_blanks_and_preserves_source(self):
        chunks = local_rag.split_document(" 第一段。 \n\n \n\n 第二段。 \n\n ", "笔记.md")

        self.assertEqual(
            chunks,
            [
                {"source": "笔记.md", "chunk_id": 1, "text": "第一段。"},
                {"source": "笔记.md", "chunk_id": 3, "text": "第二段。"},
            ],
        )
        self.assertEqual(local_rag.split_document(" \n\n\t ", "empty.md"), [])

    def test_load_reads_sorted_direct_markdown_files_as_utf8(self):
        with TemporaryDirectory(prefix="researchflow-rag-docs-") as directory:
            folder = Path(directory)
            (folder / "b.md").write_text("乙文档。", encoding="utf-8")
            (folder / "a.md").write_text("甲第一段。\n\n甲第二段。", encoding="utf-8")
            (folder / "ignored.txt").write_text("不应读取。", encoding="utf-8")
            (folder / "nested").mkdir()
            (folder / "nested" / "hidden.md").write_text("不应递归读取。", encoding="utf-8")
            (folder / "directory.md").mkdir()

            chunks = local_rag.load_documents(folder)

        self.assertEqual(
            chunks,
            [
                {"source": "a.md", "chunk_id": 1, "text": "甲第一段。"},
                {"source": "a.md", "chunk_id": 2, "text": "甲第二段。"},
                {"source": "b.md", "chunk_id": 1, "text": "乙文档。"},
            ],
        )

    def test_load_rejects_missing_directory_and_file_path(self):
        with TemporaryDirectory(prefix="researchflow-rag-path-") as directory:
            folder = Path(directory)
            file_path = folder / "notes.md"
            file_path.write_text("正文。", encoding="utf-8")
            for invalid_path in (folder / "missing", file_path):
                with self.subTest(path=invalid_path), self.assertRaises(ValueError):
                    local_rag.load_documents(invalid_path)


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.chunks = sample_chunks()

    def test_score_counts_matching_keywords_not_text_occurrences(self):
        self.assertEqual(local_rag.score_chunk(self.chunks[0], ["片段", "最多"]), 1)
        self.assertEqual(local_rag.score_chunk(self.chunks[1], ["片段", "最多"]), 2)
        self.assertEqual(local_rag.score_chunk(self.chunks[1], ["显卡"]), 0)

    def test_retrieve_matches_body_and_keeps_complete_chunks(self):
        self.assertEqual(local_rag.retrieve(self.chunks, "最多"), [self.chunks[1]])
        self.assertEqual(local_rag.retrieve(self.chunks, "source"), [])
        self.assertEqual(local_rag.retrieve(self.chunks, "显卡"), [])

    def test_ranked_results_sort_limit_and_preserve_sources_without_mutating_input(self):
        original = deepcopy(self.chunks)
        results = local_rag.retrieve_ranked(self.chunks, ["最多", "片段"], top_k=2)

        self.assertEqual(
            results,
            [
                {"score": 2, "chunk": self.chunks[1]},
                {"score": 1, "chunk": self.chunks[0]},
            ],
        )
        self.assertEqual(
            local_rag.retrieve_ranked(self.chunks, ["最多", "片段"], top_k=1),
            results[:1],
        )
        self.assertEqual(self.chunks, original)

    def test_ranked_results_filter_zero_scores_and_return_empty_for_no_match(self):
        results = local_rag.retrieve_ranked(self.chunks, ["最多"], top_k=5)

        self.assertEqual(results, [{"score": 1, "chunk": self.chunks[1]}])
        self.assertEqual(local_rag.retrieve_ranked(self.chunks, ["显卡"]), [])
        self.assertEqual(local_rag.retrieve_ranked([], ["片段"]), [])

    def test_ranked_rejects_invalid_top_k_including_booleans(self):
        for top_k in (0, -1, True, False, 1.5, "2", None):
            with self.subTest(top_k=top_k), self.assertRaises(ValueError):
                local_rag.retrieve_ranked(self.chunks, ["片段"], top_k=top_k)

    def test_ranked_rejects_missing_blank_or_non_string_keywords(self):
        for keywords in (None, "片段", [], (), [""], ["  "], ["片段", None], ["片段", 2]):
            with self.subTest(keywords=keywords), self.assertRaises(ValueError):
                local_rag.retrieve_ranked(self.chunks, keywords)

    def test_ranked_accepts_nonempty_tuple_of_keywords(self):
        self.assertEqual(
            local_rag.retrieve_ranked(self.chunks, ("最多", "片段")),
            sample_results(),
        )


class MessageTests(unittest.TestCase):
    def test_messages_keep_ranked_source_order_and_only_selected_text(self):
        question = "每次最多提供几个检索片段？"
        results = sample_results()
        messages = local_rag.build_messages(question, results)

        self.assertEqual([message["role"] for message in messages], ["system", "user"])
        self.assertEqual(messages[0]["content"], local_rag.RAG_SYSTEM_PROMPT)
        user_content = messages[1]["content"]
        self.assertIn(question, user_content)
        self.assertLess(user_content.index("[demo_rules.md#1]"), user_content.index("[rag_basics.md#2]"))
        for result in results:
            self.assertIn(result["chunk"]["text"], user_content)
        self.assertNotIn("[rag_basics.md#1]", user_content)
        self.assertNotIn(sample_chunks()[2]["text"], user_content)

    def test_empty_messages_identify_missing_material(self):
        messages = local_rag.build_messages("显卡型号是什么？", [])

        self.assertEqual([message["role"] for message in messages], ["system", "user"])
        self.assertIn("显卡型号是什么？", messages[1]["content"])
        self.assertIn("未检索到相关材料", messages[1]["content"])


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.question = "每次最多提供几个检索片段？"
        self.results = sample_results()

    def test_generation_uses_exactly_one_request_with_only_built_messages(self):
        answer = "最多 2 个检索片段。[demo_rules.md#1]"
        self.client.chat.completions.create.return_value = response_with(f"  {answer}\n")

        actual = local_rag.generate_answer(self.client, self.question, self.results)

        self.assertEqual(actual, answer)
        self.client.chat.completions.create.assert_called_once_with(
            model=local_rag.MODEL,
            messages=local_rag.build_messages(self.question, self.results),
            max_tokens=500,
            extra_body={"thinking": {"type": "disabled"}},
        )

    def test_no_results_return_fixed_answer_without_request(self):
        answer = local_rag.generate_answer(self.client, self.question, [])

        self.assertEqual(answer, local_rag.INSUFFICIENT_ANSWER)
        self.client.chat.completions.create.assert_not_called()

    def test_empty_or_truncated_responses_are_rejected_without_retry(self):
        responses = [SimpleNamespace(choices=[]), response_with("部分答案", finish_reason="length")]
        responses.extend(response_with(content) for content in (None, "", " \n\t "))
        for response in responses:
            with self.subTest(response=response):
                self.client.reset_mock()
                self.client.chat.completions.create.return_value = response
                with self.assertRaises(ValueError):
                    local_rag.generate_answer(self.client, self.question, self.results)
                self.client.chat.completions.create.assert_called_once()


class LocalRagMainTests(unittest.TestCase):
    def setUp(self):
        load_patch = patch.object(local_rag, "load_documents", return_value=sample_chunks())
        self.load_documents = load_patch.start()
        self.addCleanup(load_patch.stop)
        config_patch = patch.object(
            local_rag, "dotenv_values", return_value={"OPENAI_API_KEY": "test-api-key"}
        )
        self.read_config = config_patch.start()
        self.addCleanup(config_patch.stop)
        client_patch = patch.object(local_rag, "OpenAI")
        self.openai = client_patch.start()
        self.addCleanup(client_patch.stop)
        generate_patch = patch.object(
            local_rag, "generate_answer", return_value="最多 2 个。[demo_rules.md#1]"
        )
        self.generate_answer = generate_patch.start()
        self.addCleanup(generate_patch.stop)

    def test_no_match_skips_credentials_client_and_generation(self):
        with redirect_stdout(StringIO()) as output:
            local_rag.main(question="显卡型号是什么？", keywords=["显卡"])

        self.load_documents.assert_called_once_with(local_rag.SAMPLE_DOCS_DIR)
        self.read_config.assert_not_called()
        self.openai.assert_not_called()
        self.generate_answer.assert_not_called()
        self.assertIn(local_rag.INSUFFICIENT_ANSWER, output.getvalue())
        self.assertRegex(output.getvalue(), r"模型请求[^\n]*0")

    def test_matching_main_uses_existing_configuration_and_prints_sources_and_answer(self):
        with redirect_stdout(StringIO()) as output:
            local_rag.main()

        self.read_config.assert_called_once_with(local_rag.ENV_PATH)
        self.openai.assert_called_once_with(
            api_key="test-api-key",
            base_url=local_rag.BASE_URL,
            timeout=30.0,
            max_retries=0,
        )
        self.generate_answer.assert_called_once_with(
            self.openai.return_value, local_rag.DEFAULT_QUESTION, sample_results()
        )
        for expected in ("demo_rules.md#1", "rag_basics.md#2", "最多 2 个。"):
            self.assertIn(expected, output.getvalue())
        self.assertNotIn("test-api-key", output.getvalue())

    def test_missing_blank_and_placeholder_keys_prevent_client_creation(self):
        for config in (
            {},
            {"OPENAI_API_KEY": None},
            {"OPENAI_API_KEY": " \t "},
            {"OPENAI_API_KEY": "your_openai_api_key_here"},
            {"OPENAI_API_KEY": "your_deepseek_api_key_here"},
        ):
            with self.subTest(config=config):
                self.read_config.return_value = config
                with redirect_stdout(StringIO()), self.assertRaises(SystemExit) as error:
                    local_rag.main()
                self.assertIn("OPENAI_API_KEY", str(error.exception))
                self.openai.assert_not_called()
                self.generate_answer.assert_not_called()

    def test_api_failures_hide_sensitive_details_and_do_not_print_success(self):
        errors = (
            APIConnectionError(message="test-api-key", request=MagicMock()),
            APIStatusError(
                "test-api-key",
                response=MagicMock(status_code=429, headers={}),
                body={"message": "test-api-key"},
            ),
        )
        for api_error in errors:
            with self.subTest(error_type=type(api_error).__name__):
                self.generate_answer.side_effect = api_error
                with redirect_stdout(StringIO()) as output, self.assertRaises(SystemExit) as error:
                    local_rag.main()
                self.assertNotIn("test-api-key", output.getvalue() + str(error.exception))
                self.assertNotIn("最多 2 个。", output.getvalue())
                if isinstance(api_error, APIStatusError):
                    self.assertIn("HTTP 429", str(error.exception))

    def test_response_failure_stops_main_without_a_success_answer(self):
        self.generate_answer.side_effect = ValueError("模型输出被截断")

        with redirect_stdout(StringIO()) as output, self.assertRaises(SystemExit) as error:
            local_rag.main()

        self.assertIn("截断", str(error.exception))
        self.assertNotIn("最多 2 个。", output.getvalue())
        self.assertEqual(self.generate_answer.call_count, 1)


if __name__ == "__main__":
    unittest.main()

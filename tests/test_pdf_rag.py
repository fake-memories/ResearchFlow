"""离线验证 PDF 来源定位、关键词检索和模型请求边界。"""

from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from openai.types.chat import ChatCompletionMessage

from app import pdf_rag


def sample_chunks():
    return [
        {"source": "demo.pdf", "page": 1, "chunk_id": 1, "text": "每次最多提供 2 个片段。"},
        {"source": "demo.pdf", "page": 2, "chunk_id": 1, "text": "来源包括文件名、页码和编号。"},
    ]


class PdfLoadingTests(unittest.TestCase):
    def test_sample_pdf_keeps_all_three_pages_and_supports_both_fact_questions(self):
        chunks = pdf_rag.load_pdf(pdf_rag.SAMPLE_PDF_PATH)

        self.assertEqual([chunk["page"] for chunk in chunks], [1, 2, 3])
        self.assertTrue(all(chunk["source"] == "demo.pdf" for chunk in chunks))
        self.assertTrue(all(chunk["chunk_id"] == 1 for chunk in chunks))
        first = pdf_rag.retrieve_ranked(chunks, ["最多"], top_k=1)
        second = pdf_rag.retrieve_ranked(chunks, ["来源", "编号"], top_k=1)
        self.assertEqual(first[0]["chunk"]["page"], 1)
        self.assertIn("2 个检索片段", first[0]["chunk"]["text"])
        self.assertEqual(second[0]["chunk"]["page"], 2)
        self.assertIn("文件名、PDF 页码、页内片段编号和正文", second[0]["chunk"]["text"])
        self.assertEqual(pdf_rag.retrieve_ranked(chunks, ["显卡"]), [])

    def test_skipping_blank_pages_preserves_physical_pages_and_argument_filename(self):
        pages = [
            SimpleNamespace(extract_text=lambda: " 第一页。\n "),
            SimpleNamespace(extract_text=lambda: None),
            SimpleNamespace(extract_text=lambda: " \n\t "),
            SimpleNamespace(extract_text=lambda: " 第四页。 "),
        ]
        with patch.object(pdf_rag, "PdfReader", return_value=SimpleNamespace(pages=pages)):
            chunks = pdf_rag.load_pdf("another.pdf")

        self.assertEqual(
            chunks,
            [
                {"source": "another.pdf", "page": 1, "chunk_id": 1, "text": "第一页。"},
                {"source": "another.pdf", "page": 4, "chunk_id": 1, "text": "第四页。"},
            ],
        )


class PdfMainTests(unittest.TestCase):
    def setUp(self):
        load_patch = patch.object(pdf_rag, "load_pdf", return_value=sample_chunks())
        self.load_pdf = load_patch.start()
        self.addCleanup(load_patch.stop)
        config_patch = patch.object(
            pdf_rag, "dotenv_values", return_value={"OPENAI_API_KEY": "test-api-key"}
        )
        self.read_config = config_patch.start()
        self.addCleanup(config_patch.stop)
        client_patch = patch.object(pdf_rag, "OpenAI")
        self.openai = client_patch.start()
        self.addCleanup(client_patch.stop)

    def test_default_preview_keeps_page_tag_without_reading_credentials_or_requesting(self):
        with redirect_stdout(StringIO()) as output:
            pdf_rag.main()

        self.read_config.assert_not_called()
        self.openai.assert_not_called()
        self.assertIn("[demo.pdf#p1-c1]", output.getvalue())
        self.assertIn("模型请求 0 次", output.getvalue())
        self.assertIn("[system]", output.getvalue())
        self.assertIn("[user]", output.getvalue())

    def test_no_match_returns_before_credentials_or_client_even_with_ask(self):
        with redirect_stdout(StringIO()) as output:
            pdf_rag.main(question="演示系统使用什么显卡？", keywords=["显卡"], ask=True)

        self.read_config.assert_not_called()
        self.openai.assert_not_called()
        self.assertIn(pdf_rag.INSUFFICIENT_ANSWER, output.getvalue())
        self.assertIn("模型请求 0 次", output.getvalue())

    def test_ask_uses_one_request_with_the_selected_page_and_question(self):
        client = self.openai.return_value
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=ChatCompletionMessage(role="assistant", content="最多 2 个。[demo.pdf#p1-c1]"),
                    finish_reason="stop",
                )
            ]
        )
        with redirect_stdout(StringIO()) as output:
            pdf_rag.main(ask=True)

        self.read_config.assert_called_once_with(pdf_rag.ENV_PATH)
        self.openai.assert_called_once_with(
            api_key="test-api-key", base_url=pdf_rag.BASE_URL, timeout=30.0, max_retries=0
        )
        client.chat.completions.create.assert_called_once()
        content = client.chat.completions.create.call_args.kwargs["messages"][1]["content"]
        self.assertIn(pdf_rag.DEFAULT_QUESTION, content)
        self.assertIn("[demo.pdf#p1-c1]", content)
        self.assertNotIn("[demo.pdf#p2-c1]", content)
        self.assertIn("模型请求完成：1 次", output.getvalue())
        self.assertNotIn("test-api-key", output.getvalue())

    def test_empty_pdf_reports_extraction_failure_before_credentials(self):
        self.load_pdf.return_value = []
        with self.assertRaisesRegex(SystemExit, "未提取到非空文字"):
            pdf_rag.main(ask=True)
        self.read_config.assert_not_called()
        self.openai.assert_not_called()

    def test_invalid_question_or_top_k_is_rejected_before_credentials(self):
        for arguments in ({"question": " "}, {"top_k": 0}):
            with self.subTest(arguments=arguments):
                with self.assertRaisesRegex(SystemExit, "PDF 检索失败"):
                    pdf_rag.main(ask=True, **arguments)
        self.read_config.assert_not_called()
        self.openai.assert_not_called()

    def test_missing_key_prevents_client_creation(self):
        self.read_config.return_value = {}
        with redirect_stdout(StringIO()):
            with self.assertRaisesRegex(SystemExit, "OPENAI_API_KEY"):
                pdf_rag.main(ask=True)
        self.openai.assert_not_called()


if __name__ == "__main__":
    unittest.main()

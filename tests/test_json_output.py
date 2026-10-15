"""离线验证模型 JSON 输出、搜索参数校验和安全的命令行错误提示。"""

from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from openai import APIConnectionError, APIStatusError, APITimeoutError

from app import json_output


def response_with(content, finish_reason="stop"):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content), finish_reason=finish_reason
            )
        ]
    )


class GenerateSearchParamsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = MagicMock()
        self.answer = '{"query": "  retrieval augmented generation  ", "max_results": 2}'
        self.client.chat.completions.create.return_value = response_with(self.answer)

    def test_json_mode_passes_user_request_and_returns_validated_parameters(self):
        request = "帮我找两篇关于 RAG 的论文。"
        output = StringIO()
        with redirect_stdout(output):
            params = json_output.generate_search_params(self.client, request)

        self.assertEqual(
            params, {"query": "retrieval augmented generation", "max_results": 2}
        )
        self.client.chat.completions.create.assert_called_once_with(
            model=json_output.MODEL,
            messages=[
                {"role": "system", "content": json_output.SYSTEM_PROMPT},
                {"role": "user", "content": request},
            ],
            response_format={"type": "json_object"},
            max_tokens=200,
            extra_body={"thinking": {"type": "disabled"}},
        )
        self.assertIn(f"模型原始 JSON：\n{self.answer}", output.getvalue())

    def test_empty_model_responses_are_rejected(self):
        responses = [SimpleNamespace(choices=[])]
        responses.extend(response_with(content) for content in (None, "", " \n\t "))
        for response in responses:
            with self.subTest(response=response):
                self.client.chat.completions.create.return_value = response
                with self.assertRaises(ValueError) as error:
                    json_output.generate_search_params(self.client, "搜索论文")
                self.assertEqual(str(error.exception), "模型未返回 JSON 内容")

    def test_incomplete_or_abnormal_completion_rejected_even_with_valid_json(self):
        for finish_reason, message in (
            ("length", "模型输出被截断，请增大 max_tokens 后重试"),
            ("content_filter", "模型未正常完成 JSON 输出，请稍后重试"),
            ("tool_calls", "模型未正常完成 JSON 输出，请稍后重试"),
            (None, "模型未正常完成 JSON 输出，请稍后重试"),
        ):
            with self.subTest(finish_reason=finish_reason):
                self.client.chat.completions.create.return_value = response_with(
                    self.answer, finish_reason
                )
                with self.assertRaises(ValueError) as error:
                    json_output.generate_search_params(self.client, "搜索论文")
                self.assertEqual(str(error.exception), message)

    def test_model_content_must_pass_existing_parser_and_field_checks(self):
        for answer, message in (
            ('{"query": "RAG", "max_results": "2"}', "max_results 必须是整数"),
            ('{"query": "RAG", "max_results": 0}', "max_results 必须在 1–5 之间"),
            ('{"max_results": 2}', "缺少 query 字段"),
            ('{"query": "RAG",', "JSON 格式错误，请检查双引号、逗号和括号"),
        ):
            with self.subTest(answer=answer):
                self.client.chat.completions.create.return_value = response_with(answer)
                with redirect_stdout(StringIO()), self.assertRaises(ValueError) as error:
                    json_output.generate_search_params(self.client, "搜索论文")
                self.assertEqual(str(error.exception), message)


class JsonOutputMainTests(unittest.TestCase):
    def setUp(self) -> None:
        config_patch = patch.object(
            json_output, "dotenv_values", return_value={"OPENAI_API_KEY": "test-api-key"}
        )
        self.read_config = config_patch.start()
        self.addCleanup(config_patch.stop)
        client_patch = patch.object(json_output, "OpenAI")
        self.openai = client_patch.start()
        self.addCleanup(client_patch.stop)
        self.client = self.openai.return_value
        self.client.chat.completions.create.return_value = response_with(
            '{"query": "retrieval augmented generation", "max_results": 2}'
        )
        search_patch = patch.object(json_output, "search_paper")
        self.search_paper = search_patch.start()
        self.addCleanup(search_patch.stop)
        print_patch = patch.object(json_output, "print_papers")
        self.print_papers = print_patch.start()
        self.addCleanup(print_patch.stop)

    def test_main_uses_project_configuration_and_prints_success(self):
        output = StringIO()
        with redirect_stdout(output):
            json_output.main()

        self.read_config.assert_called_once_with(json_output.ENV_PATH)
        self.openai.assert_called_once_with(
            api_key="test-api-key",
            base_url=json_output.BASE_URL,
            timeout=30.0,
            max_retries=0,
        )
        self.assertIn(json_output.REQUEST, output.getvalue())
        self.assertIn("校验通过", output.getvalue())
        self.assertIn("retrieval augmented generation", output.getvalue())
        self.assertNotIn("test-api-key", output.getvalue())
        self.search_paper.assert_not_called()
        self.print_papers.assert_not_called()

    def test_search_uses_validated_parameters_and_prints_tool_results(self):
        self.client.chat.completions.create.return_value = response_with(
            '{"query": "  retrieval augmented generation  ", "max_results": 2}'
        )
        papers = [
            {"title": "A RAG paper", "year": 2020, "url": "https://arxiv.org/abs/2005.11401"}
        ]
        self.search_paper.return_value = papers

        with redirect_stdout(StringIO()):
            json_output.main(search=True)

        self.search_paper.assert_called_once_with("retrieval augmented generation", 2)
        self.print_papers.assert_called_once_with(papers)

    def test_invalid_parameters_prevent_search_and_result_printing(self):
        self.client.chat.completions.create.return_value = response_with(
            '{"query": "RAG", "max_results": "2"}'
        )
        with redirect_stdout(StringIO()), self.assertRaises(SystemExit) as error:
            json_output.main(search=True)

        self.assertEqual(
            str(error.exception), "搜索参数生成失败：max_results 必须是整数"
        )
        self.search_paper.assert_not_called()
        self.print_papers.assert_not_called()

    def test_search_error_stops_with_short_message_without_printing_results(self):
        tool_error = RuntimeError("论文搜索请求失败，请稍后重试。")
        tool_error.__cause__ = ConnectionError("Sensitive request detail: test-api-key")
        self.search_paper.side_effect = tool_error

        output = StringIO()
        with redirect_stdout(output), self.assertRaises(SystemExit) as error:
            json_output.main(search=True)

        self.assertEqual(str(error.exception), "论文搜索请求失败，请稍后重试。")
        self.assertNotIn("test-api-key", output.getvalue() + str(error.exception))
        self.print_papers.assert_not_called()

    def test_missing_blank_or_placeholder_keys_stop_before_client_creation(self):
        for config in (
            {},
            {"OPENAI_API_KEY": None},
            {"OPENAI_API_KEY": ""},
            {"OPENAI_API_KEY": " \t "},
            {"OPENAI_API_KEY": "your_openai_api_key_here"},
            {"OPENAI_API_KEY": "your_deepseek_api_key_here"},
        ):
            with self.subTest(config=config):
                self.read_config.return_value = config
                with self.assertRaises(SystemExit) as error:
                    json_output.main()
                self.assertEqual(
                    str(error.exception),
                    "请在项目 .env 中为 OPENAI_API_KEY 填写 DeepSeek API 密钥。",
                )
                self.openai.assert_not_called()

    def test_connection_errors_and_timeouts_hide_exception_details(self):
        for api_error in (
            APIConnectionError(
                message="Sensitive request detail: test-api-key", request=MagicMock()
            ),
            APITimeoutError(request=MagicMock()),
        ):
            with self.subTest(error_type=type(api_error).__name__):
                self.client.chat.completions.create.side_effect = api_error
                with redirect_stdout(StringIO()), self.assertRaises(SystemExit) as error:
                    json_output.main()
                self.assertEqual(
                    str(error.exception),
                    "连接 DeepSeek API 失败或超时，请检查网络后重试。",
                )

    def test_http_errors_include_status_without_sensitive_details(self):
        for status in (401, 429):
            with self.subTest(status=status):
                response = MagicMock()
                response.status_code = status
                response.headers = {}
                self.client.chat.completions.create.side_effect = APIStatusError(
                    "Sensitive server detail: test-api-key",
                    response=response,
                    body={"message": "test-api-key"},
                )
                with redirect_stdout(StringIO()), self.assertRaises(SystemExit) as error:
                    json_output.main()
                self.assertEqual(
                    str(error.exception),
                    f"LLM 请求失败（HTTP {status}），请检查服务状态、密钥和账户额度。",
                )
                self.assertNotIn("test-api-key", str(error.exception))

    def test_main_reports_parameter_validation_failure(self):
        self.client.chat.completions.create.return_value = response_with(
            '{"query": "RAG", "max_results": "2"}'
        )
        with redirect_stdout(StringIO()), self.assertRaises(SystemExit) as error:
            json_output.main()
        self.assertEqual(
            str(error.exception), "搜索参数生成失败：max_results 必须是整数"
        )


if __name__ == "__main__":
    unittest.main()

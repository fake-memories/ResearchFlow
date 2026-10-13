"""使用临时配置和 SDK mock 验证问答程序，不发送网络请求。"""

from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from openai import APIConnectionError, APIStatusError, APITimeoutError

from app import main as main_module


class MainTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = TemporaryDirectory(prefix="researchflow-test-")
        self.addCleanup(temporary_directory.cleanup)
        self.env_path = Path(temporary_directory.name) / ".env"
        self.env_path.write_text("OPENAI_API_KEY=test-api-key\n", encoding="utf-8")

        environment_patch = patch.object(main_module, "ENV_PATH", self.env_path)
        environment_patch.start()
        self.addCleanup(environment_patch.stop)
        client_patch = patch.object(main_module, "OpenAI")
        self.openai = client_patch.start()
        self.addCleanup(client_patch.stop)
        self.client = self.openai.return_value
        self.answer = "大语言模型是通过大量文本训练、能够理解和生成语言的模型。"
        self.client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.answer))]
        )

    def test_success_reads_file_and_prints_answer(self) -> None:
        output = StringIO()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "unused-process-key"}):
            with redirect_stdout(output):
                main_module.main()

        self.openai.assert_called_once_with(
            api_key="test-api-key",
            base_url="https://api.deepseek.com",
            timeout=30.0,
            max_retries=0,
        )
        self.client.chat.completions.create.assert_called_once_with(
            model="deepseek-flash",
            messages=[{"role": "user", "content": main_module.QUESTION}],
            max_tokens=200,
            extra_body={"thinking": {"type": "disabled"}},
        )
        self.assertIn(main_module.QUESTION, output.getvalue())
        self.assertIn(self.answer, output.getvalue())
        self.assertNotIn("test-api-key", output.getvalue())

    def test_config_is_independent_of_working_directory(self) -> None:
        original_directory = Path.cwd()
        with TemporaryDirectory(prefix="researchflow-cwd-") as other_directory:
            try:
                os.chdir(other_directory)
                with redirect_stdout(StringIO()):
                    main_module.main()
            finally:
                os.chdir(original_directory)
        self.assertEqual(self.openai.call_args.kwargs["api_key"], "test-api-key")

    def test_missing_empty_and_placeholder_keys_do_not_send_requests(self) -> None:
        configurations = [
            "",
            "OPENAI_API_KEY=\n",
            "OPENAI_API_KEY='   '\n",
            "OPENAI_API_KEY=your_openai_api_key_here\n",
            "OPENAI_API_KEY=your_deepseek_api_key_here\n",
        ]
        for configuration in configurations:
            with self.subTest(configuration=configuration):
                self.env_path.write_text(configuration, encoding="utf-8")
                with self.assertRaises(SystemExit) as error:
                    main_module.main()
                self.assertIn("OPENAI_API_KEY", str(error.exception))
                self.openai.assert_not_called()

    def test_connection_error_does_not_expose_exception_text(self) -> None:
        self.client.chat.completions.create.side_effect = APIConnectionError(
            message="A request containing test-api-key failed.", request=MagicMock()
        )
        with self.assertRaises(SystemExit) as error:
            main_module.main()
        self.assertIn("连接", str(error.exception))
        self.assertNotIn("test-api-key", str(error.exception))

    def test_timeout_has_a_short_error_message(self) -> None:
        self.client.chat.completions.create.side_effect = APITimeoutError(
            request=MagicMock()
        )
        with self.assertRaises(SystemExit) as error:
            main_module.main()
        self.assertIn("超时", str(error.exception))

    def test_http_errors_report_status_without_sensitive_details(self) -> None:
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
                with self.assertRaises(SystemExit) as error:
                    main_module.main()
                self.assertIn(f"HTTP {status}", str(error.exception))
                self.assertNotIn("test-api-key", str(error.exception))

    def test_empty_answers_are_not_reported_as_success(self) -> None:
        responses = [SimpleNamespace(choices=[])]
        responses.extend(
            SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
            )
            for content in (None, "", "   ")
        )
        for response in responses:
            with self.subTest(response=response):
                self.client.chat.completions.create.return_value = response
                with self.assertRaises(SystemExit) as error:
                    main_module.main()
                self.assertIn("模型未返回答案", str(error.exception))


if __name__ == "__main__":
    unittest.main()

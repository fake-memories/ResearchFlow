"""用离线响应验证 Day 4 工具调用闭环，不访问模型 API 或 arXiv。"""

from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from openai import APIConnectionError, APIStatusError, APITimeoutError
from openai.types.chat import ChatCompletionMessage

from app import tool_calling


def tool_call_with(
    name="search_paper",
    arguments='{"query": "  RAG  ", "max_results": 2}',
    call_id="call_001",
):
    # 使用 SDK 消息模型，使测试同时覆盖真实响应的序列化方式。
    return ChatCompletionMessage(
        role="assistant",
        content=None,
        tool_calls=[
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": arguments},
            }
        ],
    ).tool_calls[0]


def response_with(content=None, tool_calls=None, finish_reason="stop"):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=ChatCompletionMessage(
                    role="assistant", content=content, tool_calls=tool_calls
                ),
                finish_reason=finish_reason,
            )
        ]
    )


class ExecuteToolCallTests(unittest.TestCase):
    def setUp(self):
        search_patch = patch.object(tool_calling, "search_paper")
        self.search_paper = search_patch.start()
        self.addCleanup(search_patch.stop)
        self.papers = [
            {
                "title": "检索增强生成论文",
                "year": 2020,
                "url": "https://arxiv.org/abs/2005.11401",
            }
        ]
        self.search_paper.return_value = self.papers

    def test_validated_parameters_reach_search_and_result_preserves_call_id(self):
        with redirect_stdout(StringIO()):
            result = tool_calling.execute_tool_call(tool_call_with())

        self.search_paper.assert_called_once_with("RAG", 2)
        self.assertEqual(result["role"], "tool")
        self.assertEqual(result["tool_call_id"], "call_001")
        self.assertIsInstance(result["content"], str)
        self.assertEqual(json.loads(result["content"]), self.papers)

    def test_unknown_tool_is_rejected_before_search(self):
        with redirect_stdout(StringIO()), self.assertRaises(ValueError):
            tool_calling.execute_tool_call(tool_call_with(name="search_papers"))
        self.search_paper.assert_not_called()

    def test_invalid_arguments_are_rejected_before_search(self):
        for arguments in (
            '{"query": "RAG", "max_results": "2"}',
            '{"query": "RAG", "max_results": true}',
            '{"query": "RAG", "max_results": 0}',
            '{"query": "RAG", "max_results": 6}',
            '{"query": "  ", "max_results": 2}',
            '{"max_results": 2}',
            '{"query": "RAG",',
            "[]",
        ):
            with self.subTest(arguments=arguments):
                with redirect_stdout(StringIO()), self.assertRaises(ValueError):
                    tool_calling.execute_tool_call(tool_call_with(arguments=arguments))
                self.search_paper.assert_not_called()

    def test_non_function_or_missing_call_id_is_rejected(self):
        for call_type, call_id in (
            ("custom", "call_001"),
            ("function", ""),
            ("function", "  "),
            ("function", None),
        ):
            with self.subTest(call_type=call_type, call_id=call_id):
                tool_call = SimpleNamespace(
                    type=call_type,
                    id=call_id,
                    function=SimpleNamespace(
                        name="search_paper",
                        arguments='{"query": "RAG", "max_results": 2}',
                    ),
                )
                with redirect_stdout(StringIO()), self.assertRaises(ValueError):
                    tool_calling.execute_tool_call(tool_call)
                self.search_paper.assert_not_called()


class RunToolCallingTests(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.requests = []
        self.call = tool_call_with()
        self.first_response = response_with(
            content="先检索论文。", tool_calls=[self.call], finish_reason="tool_calls"
        )
        self.answer = "根据检索结果，下面是一篇相关论文。"
        search_patch = patch.object(tool_calling, "search_paper")
        self.search_paper = search_patch.start()
        self.addCleanup(search_patch.stop)
        self.papers = [
            {
                "title": "A RAG paper",
                "year": 2020,
                "url": "https://arxiv.org/abs/2005.11401",
            }
        ]
        self.search_paper.return_value = self.papers

    def set_responses(self, *responses):
        iterator = iter(responses)

        def reply(**kwargs):
            # 在调用时保存快照，后续 append 不能改变第一轮的历史证据。
            self.requests.append(deepcopy(kwargs))
            return next(iterator)

        self.client.chat.completions.create.side_effect = reply

    def run_request(self, request="帮我找两篇 RAG 论文。"):
        with redirect_stdout(StringIO()) as output:
            answer = tool_calling.run_tool_calling(self.client, request)
        return answer, output.getvalue()

    def test_two_requests_preserve_full_assistant_call_and_actual_tool_result(self):
        request = "帮我找两篇 RAG 论文。"
        self.set_responses(self.first_response, response_with(f"  {self.answer}\n"))
        answer, output = self.run_request(request)

        self.assertEqual(answer, self.answer)
        self.search_paper.assert_called_once_with("RAG", 2)
        self.assertEqual(len(self.requests), 2)
        first, second = self.requests
        self.assertEqual(first["model"], tool_calling.MODEL)
        self.assertEqual(first["tools"], tool_calling.TOOLS)
        self.assertEqual(
            first["messages"],
            [
                {"role": "system", "content": tool_calling.SYSTEM_PROMPT},
                {"role": "user", "content": request},
            ],
        )
        self.assertNotIn("tools", second)
        self.assertEqual(second["model"], tool_calling.MODEL)
        self.assertEqual(len(second["messages"]), 4)
        self.assertEqual(second["messages"][:2], first["messages"])
        self.assertEqual(
            second["messages"][2],
            self.first_response.choices[0].message.model_dump(exclude_none=True),
        )
        tool_result = second["messages"][3]
        self.assertEqual(tool_result["role"], "tool")
        self.assertEqual(tool_result["tool_call_id"], self.call.id)
        self.assertEqual(json.loads(tool_result["content"]), self.papers)
        for expected in ("call_001", "search_paper", "RAG", "A RAG paper"):
            self.assertIn(expected, output)

    def test_direct_answer_needs_one_model_request_and_no_search(self):
        self.set_responses(response_with(f"  {self.answer}\n"))
        answer, _ = self.run_request("什么是 RAG？")

        self.assertEqual(answer, self.answer)
        self.assertEqual(len(self.requests), 1)
        self.search_paper.assert_not_called()

    def test_empty_search_result_is_forwarded_to_model_as_successful_empty_list(self):
        self.search_paper.return_value = []
        self.set_responses(self.first_response, response_with("本次未找到匹配结果。"))
        answer, _ = self.run_request()

        self.assertEqual(answer, "本次未找到匹配结果。")
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(json.loads(self.requests[1]["messages"][-1]["content"]), [])

    def test_search_failure_prevents_second_request(self):
        self.search_paper.side_effect = RuntimeError("论文搜索请求失败，请稍后重试。")
        self.set_responses(self.first_response)

        with self.assertRaises(RuntimeError):
            self.run_request()
        self.search_paper.assert_called_once_with("RAG", 2)
        self.assertEqual(len(self.requests), 1)

    def test_bad_tool_name_or_arguments_prevent_search_and_second_request(self):
        for call in (
            tool_call_with(name="unknown_tool"),
            tool_call_with(arguments='{"query": "RAG", "max_results": "2"}'),
        ):
            with self.subTest(call=call):
                self.requests.clear()
                self.set_responses(response_with(tool_calls=[call], finish_reason="tool_calls"))
                with self.assertRaises(ValueError):
                    self.run_request()
                self.search_paper.assert_not_called()
                self.assertEqual(len(self.requests), 1)

    def test_multiple_tool_calls_are_rejected_before_any_search(self):
        self.set_responses(
            response_with(
                tool_calls=[self.call, tool_call_with(call_id="call_002")],
                finish_reason="tool_calls",
            )
        )
        with self.assertRaises(ValueError):
            self.run_request()
        self.search_paper.assert_not_called()
        self.assertEqual(len(self.requests), 1)

    def test_empty_choices_are_rejected_on_either_model_request(self):
        for second_request in (False, True):
            with self.subTest(second_request=second_request):
                self.requests.clear()
                self.search_paper.reset_mock()
                responses = [SimpleNamespace(choices=[])]
                if second_request:
                    responses.insert(0, self.first_response)
                self.set_responses(*responses)
                with self.assertRaises(ValueError):
                    self.run_request()
                self.assertEqual(len(self.requests), 2 if second_request else 1)
                self.assertEqual(self.search_paper.call_count, 1 if second_request else 0)

    def test_abnormal_finish_reason_never_uses_partial_content(self):
        for finish_reason in ("length", "content_filter", None):
            for second_request in (False, True):
                with self.subTest(finish_reason=finish_reason, second_request=second_request):
                    self.requests.clear()
                    self.search_paper.reset_mock()
                    responses = [response_with("看起来完整的内容", finish_reason=finish_reason)]
                    if second_request:
                        responses.insert(0, self.first_response)
                    self.set_responses(*responses)
                    with self.assertRaises(ValueError):
                        self.run_request()
                    self.assertEqual(len(self.requests), 2 if second_request else 1)
                    self.assertEqual(self.search_paper.call_count, 1 if second_request else 0)

    def test_first_response_finish_reason_must_match_presence_of_tool_calls(self):
        for response in (
            response_with(tool_calls=[self.call], finish_reason="stop"),
            response_with("回答", finish_reason="tool_calls"),
        ):
            with self.subTest(response=response):
                self.requests.clear()
                self.set_responses(response)
                with self.assertRaises(ValueError):
                    self.run_request()
                self.search_paper.assert_not_called()
                self.assertEqual(len(self.requests), 1)

    def test_blank_answers_are_rejected_on_either_model_request(self):
        for content in (None, "", " \n\t "):
            for second_request in (False, True):
                with self.subTest(content=content, second_request=second_request):
                    self.requests.clear()
                    self.search_paper.reset_mock()
                    responses = [response_with(content)]
                    if second_request:
                        responses.insert(0, self.first_response)
                    self.set_responses(*responses)
                    with self.assertRaises(ValueError):
                        self.run_request()
                    self.assertEqual(len(self.requests), 2 if second_request else 1)

    def test_second_tool_request_is_rejected_without_searching_again(self):
        for finish_reason in ("tool_calls", "stop"):
            with self.subTest(finish_reason=finish_reason):
                self.requests.clear()
                self.search_paper.reset_mock()
                self.set_responses(
                    self.first_response,
                    response_with("继续搜索", tool_calls=[self.call], finish_reason=finish_reason),
                )
                with self.assertRaises(ValueError):
                    self.run_request()
                self.assertEqual(len(self.requests), 2)
                self.search_paper.assert_called_once_with("RAG", 2)


class ToolCallingMainTests(unittest.TestCase):
    def setUp(self):
        config_patch = patch.object(
            tool_calling, "dotenv_values", return_value={"OPENAI_API_KEY": "test-api-key"}
        )
        self.read_config = config_patch.start()
        self.addCleanup(config_patch.stop)
        client_patch = patch.object(tool_calling, "OpenAI")
        self.openai = client_patch.start()
        self.addCleanup(client_patch.stop)
        run_patch = patch.object(tool_calling, "run_tool_calling", return_value="最终回答")
        self.run_tool_calling = run_patch.start()
        self.addCleanup(run_patch.stop)

    def test_main_uses_project_configuration_and_prints_request_and_answer(self):
        with redirect_stdout(StringIO()) as output:
            tool_calling.main()

        self.read_config.assert_called_once_with(tool_calling.ENV_PATH)
        self.openai.assert_called_once_with(
            api_key="test-api-key",
            base_url=tool_calling.BASE_URL,
            timeout=30.0,
            max_retries=0,
        )
        self.run_tool_calling.assert_called_once_with(
            self.openai.return_value, tool_calling.REQUEST
        )
        self.assertIn(tool_calling.REQUEST, output.getvalue())
        self.assertIn("最终回答", output.getvalue())
        self.assertNotIn("test-api-key", output.getvalue())

    def test_missing_blank_or_placeholder_key_prevents_client_creation(self):
        for config in (
            {},
            {"OPENAI_API_KEY": None},
            {"OPENAI_API_KEY": " \t "},
            {"OPENAI_API_KEY": "your_openai_api_key_here"},
            {"OPENAI_API_KEY": "your_deepseek_api_key_here"},
        ):
            with self.subTest(config=config):
                self.read_config.return_value = config
                with self.assertRaises(SystemExit) as error:
                    tool_calling.main()
                self.assertIn("OPENAI_API_KEY", str(error.exception))
                self.openai.assert_not_called()
                self.run_tool_calling.assert_not_called()

    def test_api_errors_hide_sensitive_details_and_report_http_status(self):
        response = MagicMock(status_code=429, headers={})
        errors = (
            APIConnectionError(message="test-api-key", request=MagicMock()),
            APITimeoutError(request=MagicMock()),
            APIStatusError("test-api-key", response=response, body={"message": "test-api-key"}),
        )
        for api_error in errors:
            with self.subTest(error_type=type(api_error).__name__):
                self.run_tool_calling.side_effect = api_error
                with redirect_stdout(StringIO()) as output, self.assertRaises(SystemExit) as error:
                    tool_calling.main()
                self.assertNotIn("test-api-key", output.getvalue() + str(error.exception))
                if isinstance(api_error, APIStatusError):
                    self.assertIn("HTTP 429", str(error.exception))

    def test_tool_failures_stop_main_without_success_answer_or_traceback_details(self):
        for tool_error in (ValueError("max_results 必须是整数"), RuntimeError("论文搜索请求失败，请稍后重试。")):
            with self.subTest(error_type=type(tool_error).__name__):
                tool_error.__cause__ = ConnectionError("test-api-key")
                self.run_tool_calling.side_effect = tool_error
                with redirect_stdout(StringIO()) as output, self.assertRaises(SystemExit) as error:
                    tool_calling.main()
                self.assertNotIn("最终回答", output.getvalue())
                self.assertNotIn("test-api-key", output.getvalue() + str(error.exception))


if __name__ == "__main__":
    unittest.main()

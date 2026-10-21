"""离线验证 Day 5 的工具循环、消息历史、搜索间隔和停止行为。"""

from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from openai import APIConnectionError
from openai.types.chat import ChatCompletionMessage

from app import tool_agent, tool_calling


def tool_call_with(
    call_id="call_001",
    query="RAG",
    name="search_paper",
    arguments=None,
):
    if arguments is None:
        arguments = json.dumps({"query": query, "max_results": 2})
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


def response_with(content=None, tool_calls=None, finish_reason=None):
    if finish_reason is None:
        finish_reason = "tool_calls" if tool_calls else "stop"
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


class RunToolAgentTests(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.requests = []
        self.papers = [
            {
                "title": "A RAG paper",
                "year": 2020,
                "url": "https://arxiv.org/abs/2005.11401",
            }
        ]
        search_patch = patch.object(
            tool_calling, "search_paper", return_value=self.papers
        )
        self.search_paper = search_patch.start()
        self.addCleanup(search_patch.stop)
        sleep_patch = patch.object(tool_agent.time, "sleep")
        self.sleep = sleep_patch.start()
        self.addCleanup(sleep_patch.stop)

    def set_responses(self, *responses):
        iterator = iter(responses)

        def reply(**kwargs):
            # 保存请求当时的历史，后续 append 不应改变前一轮证据。
            self.requests.append(deepcopy(kwargs))
            return next(iterator)

        self.client.chat.completions.create.side_effect = reply

    def run_request(self, request="帮我找两篇 RAG 论文。"):
        with redirect_stdout(StringIO()) as output:
            answer = tool_agent.run_tool_agent(self.client, request)
        return answer, output.getvalue()

    def test_direct_answer_uses_one_request_without_search_or_wait(self):
        self.set_responses(response_with("  RAG 是检索增强生成。\n"))

        answer, _ = self.run_request("什么是 RAG？")

        self.assertEqual(answer, "RAG 是检索增强生成。")
        self.assertEqual(len(self.requests), 1)
        self.search_paper.assert_not_called()
        self.sleep.assert_not_called()

    def test_one_search_preserves_full_call_and_result_for_next_request(self):
        call = tool_call_with()
        first_response = response_with(tool_calls=[call])
        self.set_responses(first_response, response_with("根据检索结果回答。"))

        answer, output = self.run_request()

        self.assertEqual(answer, "根据检索结果回答。")
        self.assertEqual(len(self.requests), 2)
        self.search_paper.assert_called_once_with("RAG", 2)
        self.sleep.assert_not_called()
        first_history = self.requests[0]["messages"]
        second_history = self.requests[1]["messages"]
        self.assertEqual(len(first_history), 2)
        self.assertEqual(second_history[:2], first_history)
        self.assertEqual(
            [message["role"] for message in second_history],
            ["system", "user", "assistant", "tool"],
        )
        self.assertEqual(
            second_history[2],
            first_response.choices[0].message.model_dump(exclude_none=True),
        )
        self.assertEqual(second_history[3]["tool_call_id"], call.id)
        self.assertEqual(json.loads(second_history[3]["content"]), self.papers)
        self.assertIn(call.id, output)
        self.assertIn("A RAG paper", output)

    def test_two_searches_allow_final_answer_on_last_request(self):
        first_call = tool_call_with()
        second_call = tool_call_with(call_id="call_002", query="agent retrieval")
        second_papers = [
            {"title": "Agent retrieval", "year": 2025, "url": "https://example.org/paper"}
        ]
        self.search_paper.side_effect = [self.papers, second_papers]
        self.set_responses(
            response_with(tool_calls=[first_call]),
            response_with(tool_calls=[second_call]),
            response_with("两次检索已经完成。"),
        )

        answer, _ = self.run_request()

        self.assertEqual(answer, "两次检索已经完成。")
        self.assertEqual(len(self.requests), 3)
        self.assertEqual(self.search_paper.call_count, 2)
        self.sleep.assert_called_once_with(tool_agent.SEARCH_DELAY_SECONDS)
        self.assertEqual([len(r["messages"]) for r in self.requests], [2, 4, 6])
        final_history = self.requests[2]["messages"]
        self.assertEqual(
            [message["role"] for message in final_history],
            ["system", "user", "assistant", "tool", "assistant", "tool"],
        )
        self.assertEqual(final_history[3]["tool_call_id"], first_call.id)
        self.assertEqual(final_history[5]["tool_call_id"], second_call.id)
        self.assertEqual(json.loads(final_history[3]["content"]), self.papers)
        self.assertEqual(json.loads(final_history[5]["content"]), second_papers)
        for request in self.requests:
            self.assertEqual(request["tools"], tool_agent.TOOLS)

    def test_third_tool_request_stops_before_third_search_or_fourth_request(self):
        self.set_responses(
            response_with(tool_calls=[tool_call_with(call_id="call_001")]),
            response_with(tool_calls=[tool_call_with(call_id="call_002")]),
            response_with(tool_calls=[tool_call_with(call_id="call_003")]),
        )

        with self.assertRaisesRegex(RuntimeError, "达到模型请求上限"):
            self.run_request()

        self.assertEqual(len(self.requests), 3)
        self.assertEqual(self.search_paper.call_count, 2)
        self.sleep.assert_called_once_with(tool_agent.SEARCH_DELAY_SECONDS)

    def test_reducing_request_limit_to_two_allows_at_most_one_search(self):
        self.set_responses(
            response_with(tool_calls=[tool_call_with(call_id="call_001")]),
            response_with(tool_calls=[tool_call_with(call_id="call_002")]),
        )

        with patch.object(tool_agent, "MAX_REQUESTS", 2):
            with self.assertRaisesRegex(RuntimeError, "达到模型请求上限"):
                self.run_request()

        self.assertEqual(len(self.requests), 2)
        self.search_paper.assert_called_once_with("RAG", 2)
        self.sleep.assert_not_called()

    def test_one_request_limit_still_accepts_direct_answer(self):
        self.set_responses(response_with("直接回答。"))

        with patch.object(tool_agent, "MAX_REQUESTS", 1):
            answer, _ = self.run_request()

        self.assertEqual(answer, "直接回答。")
        self.assertEqual(len(self.requests), 1)
        self.search_paper.assert_not_called()

    def test_invalid_request_limit_prevents_model_and_search_calls(self):
        for limit in (0, -1, True, 1.5, "3"):
            with self.subTest(limit=limit), patch.object(tool_agent, "MAX_REQUESTS", limit):
                with self.assertRaisesRegex(ValueError, "MAX_REQUESTS"):
                    self.run_request()

                self.client.chat.completions.create.assert_not_called()
                self.search_paper.assert_not_called()
                self.sleep.assert_not_called()

    def test_multiple_calls_are_rejected_before_any_search(self):
        self.set_responses(
            response_with(
                tool_calls=[tool_call_with(), tool_call_with(call_id="call_002")]
            )
        )

        with self.assertRaises(ValueError):
            self.run_request()

        self.assertEqual(len(self.requests), 1)
        self.search_paper.assert_not_called()
        self.sleep.assert_not_called()

    def test_unknown_tool_or_invalid_parameters_stop_before_search(self):
        for call in (
            tool_call_with(name="unknown_tool"),
            tool_call_with(arguments='{"query": "RAG", "max_results": "2"}'),
        ):
            with self.subTest(call=call):
                self.requests.clear()
                self.set_responses(response_with(tool_calls=[call]))

                with self.assertRaises(ValueError):
                    self.run_request()

                self.assertEqual(len(self.requests), 1)
                self.search_paper.assert_not_called()
                self.sleep.assert_not_called()

    def test_failed_first_search_does_not_continue_or_return_success(self):
        self.search_paper.side_effect = RuntimeError("搜索超时。")
        self.set_responses(response_with(tool_calls=[tool_call_with()]))

        with self.assertRaisesRegex(RuntimeError, "搜索超时"):
            self.run_request()

        self.assertEqual(len(self.requests), 1)
        self.search_paper.assert_called_once_with("RAG", 2)
        self.sleep.assert_not_called()

    def test_failed_second_search_prevents_third_model_request(self):
        self.search_paper.side_effect = [self.papers, RuntimeError("第二次搜索超时。")]
        self.set_responses(
            response_with(tool_calls=[tool_call_with()]),
            response_with(tool_calls=[tool_call_with(call_id="call_002")]),
        )

        with self.assertRaisesRegex(RuntimeError, "第二次搜索超时"):
            self.run_request()

        self.assertEqual(len(self.requests), 2)
        self.assertEqual(self.search_paper.call_count, 2)
        self.sleep.assert_called_once_with(tool_agent.SEARCH_DELAY_SECONDS)

    def test_empty_search_result_is_forwarded_as_successful_empty_list(self):
        self.search_paper.return_value = []
        self.set_responses(
            response_with(tool_calls=[tool_call_with()]),
            response_with("本次未找到匹配论文。"),
        )

        answer, _ = self.run_request()

        self.assertEqual(answer, "本次未找到匹配论文。")
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(json.loads(self.requests[1]["messages"][-1]["content"]), [])

    def test_wait_occurs_after_first_search_and_before_second_search(self):
        events = []

        def search(query, max_results):
            events.append(("search", query))
            return self.papers

        self.search_paper.side_effect = search
        self.sleep.side_effect = lambda seconds: events.append(("wait", seconds))
        self.set_responses(
            response_with(tool_calls=[tool_call_with(query="first query")]),
            response_with(tool_calls=[tool_call_with(call_id="call_002", query="second query")]),
            response_with("完成。"),
        )

        self.run_request()

        self.assertEqual(
            events,
            [
                ("search", "first query"),
                ("wait", tool_agent.SEARCH_DELAY_SECONDS),
                ("search", "second query"),
            ],
        )

    def test_blank_final_answer_is_rejected_after_search(self):
        self.set_responses(
            response_with(tool_calls=[tool_call_with()]),
            response_with(" \n\t "),
        )

        with self.assertRaises(ValueError):
            self.run_request()

        self.assertEqual(len(self.requests), 2)
        self.search_paper.assert_called_once_with("RAG", 2)

    def test_truncated_response_is_rejected_before_tool_execution(self):
        self.set_responses(
            response_with(tool_calls=[tool_call_with()], finish_reason="length")
        )

        with self.assertRaises(ValueError):
            self.run_request()

        self.assertEqual(len(self.requests), 1)
        self.search_paper.assert_not_called()


class ToolAgentMainTests(unittest.TestCase):
    def setUp(self):
        config_patch = patch.object(
            tool_agent, "dotenv_values", return_value={"OPENAI_API_KEY": "test-api-key"}
        )
        self.read_config = config_patch.start()
        self.addCleanup(config_patch.stop)
        client_patch = patch.object(tool_agent, "OpenAI")
        self.openai = client_patch.start()
        self.addCleanup(client_patch.stop)
        run_patch = patch.object(tool_agent, "run_tool_agent", return_value="最终回答")
        self.run_tool_agent = run_patch.start()
        self.addCleanup(run_patch.stop)

    def test_main_uses_existing_configuration_and_prints_final_answer(self):
        with redirect_stdout(StringIO()) as output:
            tool_agent.main()

        self.read_config.assert_called_once_with(tool_agent.ENV_PATH)
        self.openai.assert_called_once_with(
            api_key="test-api-key",
            base_url=tool_agent.BASE_URL,
            timeout=30.0,
            max_retries=0,
        )
        self.run_tool_agent.assert_called_once_with(
            self.openai.return_value, tool_agent.REQUEST
        )
        self.assertIn("最终回答", output.getvalue())
        self.assertNotIn("test-api-key", output.getvalue())

    def test_missing_key_prevents_client_creation(self):
        self.read_config.return_value = {}

        with self.assertRaises(SystemExit):
            tool_agent.main()

        self.openai.assert_not_called()
        self.run_tool_agent.assert_not_called()

    def test_tool_error_reports_failure_without_success_answer(self):
        self.run_tool_agent.side_effect = RuntimeError("达到模型请求上限，任务尚未完成")

        with redirect_stdout(StringIO()) as output, self.assertRaises(SystemExit) as error:
            tool_agent.main()

        self.assertIn("达到模型请求上限", str(error.exception))
        self.assertNotIn("最终回答", output.getvalue())

    def test_connection_error_hides_internal_error_details(self):
        self.run_tool_agent.side_effect = APIConnectionError(
            message="test-api-key", request=MagicMock()
        )

        with redirect_stdout(StringIO()) as output, self.assertRaises(SystemExit) as error:
            tool_agent.main()

        self.assertNotIn("test-api-key", output.getvalue() + str(error.exception))
        self.assertNotIn("最终回答", output.getvalue())


if __name__ == "__main__":
    unittest.main()

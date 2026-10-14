"""模拟回复，验证循环退出和每轮请求中的消息历史。"""

from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from openai import APIConnectionError, APIStatusError, APITimeoutError

from app import agent_loop


class AgentLoopTests(unittest.TestCase):
    def run_with_answers(self, answers):
        client = MagicMock()
        requests = []
        answer_iterator = iter(answers)

        def reply(**kwargs):
            # 请求时复制历史，避免后续 append 改变已记录的请求。
            requests.append(deepcopy(kwargs["messages"]))
            answer = next(answer_iterator)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=answer))]
            )

        client.chat.completions.create.side_effect = reply
        output = StringIO()
        with redirect_stdout(output):
            agent_loop.run_loop(client)
        return requests, output.getvalue()

    def test_done_stops_and_next_request_contains_previous_answer(self):
        first = "第一项学习任务。\nSTATUS: CONTINUE"
        second = "本轮任务正文。\nSTATUS: DONE"
        requests, output = self.run_with_answers([first, second])

        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0], [{"role": "user", "content": agent_loop.TASK}])
        self.assertEqual(
            requests[1],
            [
                {"role": "user", "content": agent_loop.TASK},
                {"role": "assistant", "content": first},
                {"role": "user", "content": "请继续，补充下一项任务。"},
            ],
        )
        self.assertIn("模型声明任务完成", output)
        self.assertNotIn("达到最大步数", output)

    def test_continue_never_exceeds_limit_and_done_in_body_is_ignored(self):
        answers = ["正文提到 DONE，但还需继续。\nSTATUS: CONTINUE"] * agent_loop.MAX_STEPS
        requests, output = self.run_with_answers(answers)

        self.assertEqual(len(requests), agent_loop.MAX_STEPS)
        self.assertEqual([len(messages) for messages in requests], [1, 3, 5])
        self.assertIn("达到最大步数（3），任务尚未完成", output)
        self.assertNotIn("模型声明任务完成", output)

    def test_done_on_last_step_is_completion(self):
        requests, output = self.run_with_answers(
            [
                "第一项任务。\nSTATUS: CONTINUE",
                "第二项任务。\nSTATUS: CONTINUE",
                "第三项任务。\nSTATUS: DONE",
            ]
        )

        self.assertEqual(len(requests), 3)
        self.assertIn("模型声明任务完成", output)
        self.assertNotIn("达到最大步数", output)

    def test_invalid_or_empty_reply_stops_after_one_call(self):
        for answer in (
            None,
            "   ",
            "没有状态的正文。",
            "任务正文。\nSTATUS: NOT_DONE",
            "任务正文。\nSTATUS: DONE extra",
            "STATUS: DONE",
            "STATUS: CONTINUE\nSTATUS: DONE",
            "任务正文。\nSTATUS: DONE\n继续写了其他内容。",
        ):
            with self.subTest(answer=answer):
                client = MagicMock()
                client.chat.completions.create.return_value = SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content=answer))]
                )
                with redirect_stdout(StringIO()), self.assertRaises(SystemExit):
                    agent_loop.run_loop(client)
                client.chat.completions.create.assert_called_once()

    def test_empty_choices_stops_after_one_call(self):
        client = MagicMock()
        client.chat.completions.create.return_value = SimpleNamespace(choices=[])

        with redirect_stdout(StringIO()), self.assertRaises(SystemExit) as error:
            agent_loop.run_loop(client)
        self.assertIn("模型未返回答案", str(error.exception))
        client.chat.completions.create.assert_called_once()

    def test_missing_key_does_not_create_client(self):
        for configuration in (
            {},
            {"OPENAI_API_KEY": "   "},
            {"OPENAI_API_KEY": "your_deepseek_api_key_here"},
            {"OPENAI_API_KEY": "your_openai_api_key_here"},
        ):
            with self.subTest(configuration=configuration):
                with patch.object(agent_loop, "dotenv_values", return_value=configuration):
                    with patch.object(agent_loop, "OpenAI") as openai:
                        with self.assertRaises(SystemExit):
                            agent_loop.main()
                        openai.assert_not_called()

    def test_api_errors_stop_and_hide_sensitive_details(self):
        secret = "test-api-key"
        response = MagicMock()
        response.status_code = 429
        errors = [
            APIConnectionError(message=secret, request=MagicMock()),
            APITimeoutError(request=MagicMock()),
            APIStatusError(secret, response=response, body={"message": secret}),
        ]
        for error in errors:
            with self.subTest(error_type=type(error).__name__):
                with patch.object(
                    agent_loop, "dotenv_values", return_value={"OPENAI_API_KEY": secret}
                ):
                    with patch.object(agent_loop, "OpenAI") as openai:
                        client = openai.return_value
                        client.chat.completions.create.side_effect = error
                        output = StringIO()
                        with redirect_stdout(output), self.assertRaises(SystemExit) as caught:
                            agent_loop.main()

                        client.chat.completions.create.assert_called_once()
                        self.assertIn("循环已停止", str(caught.exception))
                        self.assertNotIn(secret, str(caught.exception))
                        self.assertNotIn(secret, output.getvalue())
                        self.assertNotIn("模型声明任务完成", output.getvalue())
                        self.assertNotIn("达到最大步数", output.getvalue())


if __name__ == "__main__":
    unittest.main()

"""离线验证搜索参数的 JSON 解析、字段校验与边界。"""

import json
import unittest

from app.structured_output import parse_search_params


class SearchParamsTests(unittest.TestCase):
    def assert_invalid(self, answer, expected_message):
        with self.assertRaises(ValueError) as caught:
            parse_search_params(answer)
        self.assertEqual(str(caught.exception), expected_message)

    def test_valid_params_trim_query_and_accept_result_count_boundaries(self):
        for query, max_results in (
            ("  AI agents  ", 1),
            ("论文检索", 3),
            ("\nretrieval augmented generation\t", 5),
        ):
            with self.subTest(query=query, max_results=max_results):
                answer = json.dumps({"query": query, "max_results": max_results})
                self.assertEqual(
                    parse_search_params(answer),
                    {"query": query.strip(), "max_results": max_results},
                )

    def test_rejects_non_string_and_blank_input(self):
        for answer in (None, 3, True, {}, [], b"{}", "", " \n\t "):
            with self.subTest(answer=answer):
                self.assert_invalid(answer, "输入必须是非空 JSON 字符串")

    def test_rejects_invalid_json(self):
        for answer in (
            "{'query': 'AI agents', 'max_results': 3}",
            '{"query": "AI agents", "max_results": 3,}',
            '{"query": "AI agents", "max_results": 3',
            '```json\n{"query": "AI agents", "max_results": 3}\n```',
            '搜索参数：{"query": "AI agents", "max_results": 3}',
        ):
            with self.subTest(answer=answer):
                self.assert_invalid(answer, "JSON 格式错误，请检查双引号、逗号和括号")

    def test_rejects_json_values_that_are_not_objects(self):
        for value in ([], None, True, 3, "AI agents"):
            with self.subTest(value=value):
                self.assert_invalid(json.dumps(value), "JSON 顶层必须是对象")

    def test_rejects_missing_required_fields(self):
        for value, message in (
            ({"max_results": 3}, "缺少 query 字段"),
            ({"query": "AI agents"}, "缺少 max_results 字段"),
        ):
            with self.subTest(value=value):
                self.assert_invalid(json.dumps(value), message)

    def test_rejects_query_with_wrong_type(self):
        for query in (None, True, 3, [], {}):
            with self.subTest(query=query):
                answer = json.dumps({"query": query, "max_results": 3})
                self.assert_invalid(answer, "query 必须是字符串")

    def test_rejects_empty_or_whitespace_query(self):
        for query in ("", "   ", "\n\t"):
            with self.subTest(query=query):
                answer = json.dumps({"query": query, "max_results": 3})
                self.assert_invalid(answer, "query 不能为空")

    def test_rejects_result_count_that_is_not_strictly_integer(self):
        for max_results in (True, False, 2.0, "3", None, [], {}):
            with self.subTest(max_results=max_results):
                answer = json.dumps({"query": "AI agents", "max_results": max_results})
                self.assert_invalid(answer, "max_results 必须是整数")

    def test_rejects_result_count_outside_allowed_range(self):
        for max_results in (-1, 0, 6):
            with self.subTest(max_results=max_results):
                answer = json.dumps({"query": "AI agents", "max_results": max_results})
                self.assert_invalid(answer, "max_results 必须在 1–5 之间")


if __name__ == "__main__":
    unittest.main()

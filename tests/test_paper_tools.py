"""使用固定 Atom 数据离线验证论文搜索，不请求 arXiv。"""

from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import MagicMock, patch
from xml.sax.saxutils import escape

import requests

from app import paper_tools


def atom_entry(
    title="A RAG Paper",
    url="https://arxiv.org/abs/2401.00001v1",
    published="2024-01-02T03:04:05Z",
):
    fields = []
    for name, value in (("title", title), ("id", url), ("published", published)):
        if value is not None:
            fields.append(f"<{name}>{escape(value)}</{name}>")
    return "<entry>" + "".join(fields) + "</entry>"


def atom_feed(*entries):
    xml = '<feed xmlns="http://www.w3.org/2005/Atom">' + "".join(entries) + "</feed>"
    return xml.encode("utf-8")


class PaperSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        request_patch = patch.object(paper_tools.requests, "get")
        self.get = request_patch.start()
        self.addCleanup(request_patch.stop)
        self.response = MagicMock()
        self.response.content = atom_feed(atom_entry())
        self.get.return_value = self.response

    def assert_invalid(self, query, max_results, message):
        with self.assertRaises(ValueError) as caught:
            paper_tools.search_paper(query, max_results)
        self.assertEqual(str(caught.exception), message)
        self.get.assert_not_called()

    def test_returns_source_records_and_trims_title_without_printing(self):
        self.response.content = atom_feed(
            atom_entry(title="  Retrieval-Augmented\n Generation   for QA  "),
            atom_entry(
                title="A second paper",
                url="  https://arxiv.org/abs/2502.00002v2  ",
                published="2025-02-03T00:00:00Z",
            ),
        )
        output = StringIO()
        with redirect_stdout(output):
            papers = paper_tools.search_paper("  retrieval-augmented generation  ", 2)

        self.assertEqual(
            papers,
            [
                {
                    "title": "Retrieval-Augmented Generation for QA",
                    "url": "https://arxiv.org/abs/2401.00001v1",
                    "year": 2024,
                },
                {
                    "title": "A second paper",
                    "url": "https://arxiv.org/abs/2502.00002v2",
                    "year": 2025,
                },
            ],
        )
        self.assertEqual(output.getvalue(), "")
        self.get.assert_called_once()
        args, kwargs = self.get.call_args
        self.assertEqual(args[0], "https://export.arxiv.org/api/query")
        self.assertEqual(
            kwargs["params"]["search_query"], 'all:"retrieval-augmented generation"'
        )
        self.assertEqual(kwargs["params"]["max_results"], 2)
        self.assertEqual(kwargs["params"]["sortBy"], "relevance")
        self.assertGreater(kwargs["timeout"], 0)

    def test_default_and_boundary_counts_limit_returned_entries(self):
        self.response.content = atom_feed(
            *(atom_entry(title=f"Paper {i}") for i in range(6))
        )
        for count in (None, 1, 5):
            with self.subTest(max_results=count):
                if count is None:
                    papers = paper_tools.search_paper("RAG")
                else:
                    papers = paper_tools.search_paper("RAG", count)
                expected = 3 if count is None else count
                self.assertEqual(len(papers), expected)
                self.assertEqual(
                    self.get.call_args.kwargs["params"]["max_results"], expected
                )

    def test_invalid_arguments_stop_before_any_request(self):
        invalid = [
            (query, 2, "query 必须是字符串")
            for query in (None, True, 3, [], {})
        ]
        invalid.extend((query, 2, "query 不能为空") for query in ("", " \n\t "))
        invalid.extend(
            ("RAG", count, "max_results 必须是整数")
            for count in (True, False, "2", 2.0, None)
        )
        invalid.extend(
            ("RAG", count, "max_results 必须在 1–5 之间")
            for count in (-1, 0, 6)
        )
        for query, count, message in invalid:
            with self.subTest(query=query, max_results=count):
                self.assert_invalid(query, count, message)

    def test_empty_atom_feed_returns_empty_list(self):
        self.response.content = atom_feed()
        self.assertEqual(paper_tools.search_paper("a query with no matches", 2), [])

    def test_http_failures_report_status_without_server_details(self):
        for status in (429, 503):
            with self.subTest(status=status):
                self.response.status_code = status
                self.response.raise_for_status.side_effect = requests.HTTPError(
                    "server diagnostic details", response=self.response
                )
                with self.assertRaises(RuntimeError) as caught:
                    paper_tools.search_paper("RAG", 2)
                self.assertEqual(
                    str(caught.exception),
                    f"论文检索失败（HTTP {status}），请稍后重试。",
                )

    def test_network_failures_and_timeouts_have_actionable_message(self):
        for error in (
            requests.ConnectionError("connection details"),
            requests.Timeout("timeout details"),
        ):
            with self.subTest(error_type=type(error).__name__):
                self.get.side_effect = error
                with self.assertRaises(RuntimeError) as caught:
                    paper_tools.search_paper("RAG", 2)
                self.assertEqual(
                    str(caught.exception), "连接 arXiv 失败或超时，请检查网络后重试。"
                )

    def test_malformed_xml_or_non_atom_feed_is_a_failure_not_no_results(self):
        for content in (
            b"<feed",
            b"<html><body>Unavailable</body></html>",
            b"<feed/>",
            b"",
        ):
            with self.subTest(content=content):
                self.response.content = content
                with self.assertRaises(RuntimeError) as caught:
                    paper_tools.search_paper("RAG", 2)
                self.assertEqual(
                    str(caught.exception),
                    "arXiv 返回的不是有效论文数据，请稍后重试。",
                )

    def test_arxiv_error_entry_is_not_returned_as_a_paper(self):
        for error_url in (
            "http://arxiv.org/api/errors#incorrect_query",
            "https://arxiv.org/api/errors#incorrect_query",
        ):
            with self.subTest(url=error_url):
                self.response.content = atom_feed(
                    atom_entry(title="Error", url=error_url)
                )
                with self.assertRaises(RuntimeError) as caught:
                    paper_tools.search_paper("RAG", 2)
                self.assertEqual(
                    str(caught.exception), "arXiv 返回了查询错误，请检查搜索关键词。"
                )

    def test_missing_or_blank_title_or_source_is_rejected(self):
        for title, url in (
            (None, "https://arxiv.org/abs/2401.00001"),
            (" \n ", "https://arxiv.org/abs/2401.00001"),
            ("A paper", None),
            ("A paper", "  "),
        ):
            with self.subTest(title=title, url=url):
                self.response.content = atom_feed(atom_entry(title=title, url=url))
                with self.assertRaises(RuntimeError) as caught:
                    paper_tools.search_paper("RAG", 2)
                self.assertEqual(
                    str(caught.exception), "arXiv 返回的论文缺少标题或来源链接。"
                )

    def test_missing_or_invalid_publication_date_keeps_year_unknown(self):
        for published in (None, "", "not a date", "2024-99-99T00:00:00Z"):
            with self.subTest(published=published):
                self.response.content = atom_feed(
                    atom_entry(title="A paper mentioning 2023", published=published)
                )
                papers = paper_tools.search_paper("RAG", 2)
                self.assertIsNone(papers[0]["year"])


if __name__ == "__main__":
    unittest.main()

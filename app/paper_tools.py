"""Day 3：通过 arXiv API 检索论文，由 Python 直接调用。"""

from datetime import datetime
from xml.etree import ElementTree as ET

import requests


ARXIV_API_URL = "https://export.arxiv.org/api/query"
ATOM_NAMESPACE = {"atom": "http://www.w3.org/2005/Atom"}


def search_paper(query: str, max_results: int = 3) -> list[dict[str, str | int | None]]:
    """按关键词短语检索，返回标题、来源链接与首次提交年份；无结果时返回空列表。"""
    # 工具也能被直接调用，因此不能只依赖模型输出阶段的校验。
    if not isinstance(query, str):
        raise ValueError("query 必须是字符串")
    query = query.strip()
    if not query:
        raise ValueError("query 不能为空")
    if type(max_results) is not int:
        raise ValueError("max_results 必须是整数")
    if not 1 <= max_results <= 5:
        raise ValueError("max_results 必须在 1–5 之间")

    try:
        response = requests.get(
            ARXIV_API_URL,
            params={
                "search_query": f'all:"{query}"',
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending",
            },
            timeout=30.0,
            headers={
                "User-Agent": "ResearchFlow/0.1 (learning project; single-request paper search)"
            },
        )
        response.raise_for_status()
    except requests.HTTPError as error:
        status = error.response.status_code if error.response is not None else "未知"
        raise RuntimeError(f"论文检索失败（HTTP {status}），请稍后重试。") from None
    except requests.RequestException:
        raise RuntimeError("连接 arXiv 失败或超时，请检查网络后重试。") from None

    try:
        feed = ET.fromstring(response.content)
    except ET.ParseError:
        raise RuntimeError("arXiv 返回的不是有效论文数据，请稍后重试。") from None
    if feed.tag != "{http://www.w3.org/2005/Atom}feed":
        raise RuntimeError("arXiv 返回的不是有效论文数据，请稍后重试。")

    papers = []
    for entry in feed.findall("atom:entry", ATOM_NAMESPACE)[:max_results]:
        url = (entry.findtext("atom:id", "", ATOM_NAMESPACE) or "").strip()
        if url.startswith(("http://arxiv.org/api/errors", "https://arxiv.org/api/errors")):
            raise RuntimeError("arXiv 返回了查询错误，请检查搜索关键词。")

        title = " ".join((entry.findtext("atom:title", "", ATOM_NAMESPACE) or "").split())
        if not title or not url:
            raise RuntimeError("arXiv 返回的论文缺少标题或来源链接。")

        published = (entry.findtext("atom:published", "", ATOM_NAMESPACE) or "").strip()
        try:
            year = datetime.fromisoformat(published).year
        except ValueError:
            year = None

        papers.append({"title": title, "url": url, "year": year})

    return papers


def print_papers(papers: list[dict[str, str | int | None]]) -> None:
    """统一显示直接调用和模型参数检索的结果。"""
    if not papers:
        print("未找到匹配论文，请尝试调整搜索关键词。")
        return

    print(f"检索到 {len(papers)} 篇论文（来源：arXiv）：")
    for index, paper in enumerate(papers, start=1):
        year = paper["year"] if paper["year"] is not None else "年份未知"
        print(f"\n{index}. {paper['title']}\n年份：{year}\n来源：{paper['url']}")


def main() -> None:
    """先用固定参数直接调用真实工具，不请求模型。"""
    query = "retrieval-augmented generation"
    print(f"搜索关键词：{query}")
    try:
        papers = search_paper(query, max_results=2)
    except (ValueError, RuntimeError) as error:
        raise SystemExit(str(error)) from None
    print_papers(papers)


if __name__ == "__main__":
    main()

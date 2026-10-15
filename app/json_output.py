"""Day 3：请求模型生成 JSON 搜索参数，再交给 Python 校验。"""

import argparse
from pathlib import Path

from dotenv import dotenv_values
from openai import APIConnectionError, APIStatusError, OpenAI

from app.structured_output import parse_search_params
from app.paper_tools import print_papers, search_paper


ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-flash"
REQUEST = "帮我找两篇关于 RAG（检索增强生成）的论文。"
SYSTEM_PROMPT = """你是论文搜索参数整理助手。
根据用户需求，提取搜索关键词 query 和返回数量 max_results。
这些参数将交给 Python 搜索函数使用；当前只整理参数，不生成论文列表。

要求：
- query 是非空字符串，使用表达主题的英文搜索关键词，缩写优先展开为全称。
- max_results 是 1–5 的整数，用户未指定时默认为 3。
- 只输出包含 query 和 max_results 两个字段的合法 JSON，不附加解释或 Markdown 代码块。

示例 JSON：
{"query": "AI agents", "max_results": 3}
"""


def generate_search_params(client: OpenAI, request: str) -> dict[str, str | int]:
    """发起一次 JSON 模式请求，打印原始文本并返回通过校验的搜索参数。"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": request},
        ],
        response_format={"type": "json_object"},
        max_tokens=200,
        extra_body={"thinking": {"type": "disabled"}},
    )

    if not response.choices:
        raise ValueError("模型未返回 JSON 内容")

    choice = response.choices[0]
    # 即使截断的文本碰巧能解析，也不把未正常完成的回复当成成功。
    if choice.finish_reason == "length":
        raise ValueError("模型输出被截断，请增大 max_tokens 后重试")
    if choice.finish_reason != "stop":
        raise ValueError("模型未正常完成 JSON 输出，请稍后重试")

    answer = (choice.message.content or "").strip()
    if not answer:
        raise ValueError("模型未返回 JSON 内容")

    print(f"模型原始 JSON：\n{answer}")
    # JSON 模式约束输出格式，字段的类型、范围仍由 Python 检查。
    return parse_search_params(answer)


def main(search: bool = False) -> None:
    """生成并显示搜索参数，按需继续调用论文工具。"""
    config = dotenv_values(ENV_PATH)
    api_key = (config.get("OPENAI_API_KEY") or "").strip()
    if not api_key or api_key in {
        "your_openai_api_key_here",
        "your_deepseek_api_key_here",
    }:
        raise SystemExit("请在项目 .env 中为 OPENAI_API_KEY 填写 DeepSeek API 密钥。")

    client = OpenAI(
        api_key=api_key,
        base_url=BASE_URL,
        timeout=30.0,
        max_retries=0,
    )
    print(f"用户需求：{REQUEST}")
    try:
        params = generate_search_params(client, REQUEST)
    except APIConnectionError:
        raise SystemExit("连接 DeepSeek API 失败或超时，请检查网络后重试。") from None
    except APIStatusError as error:
        raise SystemExit(
            f"LLM 请求失败（HTTP {error.status_code}），请检查服务状态、密钥和账户额度。"
        ) from None
    except ValueError as error:
        raise SystemExit(f"搜索参数生成失败：{error}") from None

    print(f"校验通过的搜索参数：{params}")

    if search:
        try:
            papers = search_paper(params["query"], params["max_results"])
        except RuntimeError as error:
            raise SystemExit(str(error)) from None
        print_papers(papers)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成 JSON 搜索参数，可选执行论文检索。")
    parser.add_argument("--search", action="store_true", help="校验通过后调用 arXiv 搜索工具")
    main(search=parser.parse_args().search)

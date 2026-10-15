"""Day 3：先用固定 JSON 文本练习搜索参数的解析与校验。"""

import json


def parse_search_params(answer: str) -> dict[str, str | int]:
    """解析 JSON 对象，校验并返回 query 和 max_results；失败时抛出 ValueError。"""
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("输入必须是非空 JSON 字符串")

    try:
        params = json.loads(answer)
    except json.JSONDecodeError:
        raise ValueError("JSON 格式错误，请检查双引号、逗号和括号") from None

    # 合法 JSON 也可能是列表、数字等，需要先确认可以按字段取值。
    if not isinstance(params, dict):
        raise ValueError("JSON 顶层必须是对象")

    if "query" not in params:
        raise ValueError("缺少 query 字段")
    if "max_results" not in params:
        raise ValueError("缺少 max_results 字段")

    query = params["query"]
    if not isinstance(query, str):
        raise ValueError("query 必须是字符串")
    query = query.strip()
    if not query:
        raise ValueError("query 不能为空")

    max_results = params["max_results"]
    # bool 在 Python 中是 int 的子类；严格检查可以排除 true 和 false。
    if type(max_results) is not int:
        raise ValueError("max_results 必须是整数")
    if not 1 <= max_results <= 5:
        raise ValueError("max_results 必须在 1–5 之间")

    return {"query": query, "max_results": max_results}


def main() -> None:
    """展示正常输入和常见错误；逐例捕获错误，以便比较不同检查的作用。"""
    examples = [
        ("正常参数", '{"query": " RAG ", "max_results": 2}'),
        ("数量是字符串", '{"query": "RAG", "max_results": "2"}'),
        ("数量超出范围", '{"query": "RAG", "max_results": 0}'),
        ("缺少字段", '{"max_results": 2}'),
        ("关键词类型错误", '{"query": 123, "max_results": 2}'),
        ("关键词只有空白", '{"query": "   ", "max_results": 2}'),
        ("JSON 格式错误", '{"query": "RAG", "max_results": 2'),
        ("JSON 顶层是列表", '[]'),
    ]

    for label, answer in examples:
        print(f"\n{label}\nJSON 文本：{answer}")
        try:
            params = parse_search_params(answer)
        except ValueError as error:
            print(f"校验失败：{error}")
        else:
            print(f"校验通过：{params}")


if __name__ == "__main__":
    main()

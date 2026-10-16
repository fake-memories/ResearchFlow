"""Day 4：原生 Tool Calling，执行一次论文搜索并把结果交回模型。"""

import argparse
import json
from pathlib import Path

from dotenv import dotenv_values
from openai import APIConnectionError, APIStatusError, OpenAI

from app.paper_tools import search_paper
from app.structured_output import parse_search_params


ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-flash"
REQUEST = "帮我找两篇关于 RAG（检索增强生成）的论文。"
SYSTEM_PROMPT = """你是论文检索助手。
用户需要查找论文时使用 search_paper；一般概念问题可以直接回答。
搜索关键词使用表达主题的英文短语，缩写优先展开为全称。
用户未指定数量时使用 3；返回数量必须是 1–5 的整数。
收到工具结果后，根据其中的标题、首次提交年份和来源链接回答，不编造论文。
工具只提供检索元数据，不代表已经阅读全文；空列表表示本次检索未找到匹配结果。
"""
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_paper",
            "description": "按关键词搜索 arXiv 论文，返回标题、来源链接和首次提交年份。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "非空的英文论文搜索关键词或短语",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "返回数量，用户未指定时使用 3",
                        "minimum": 1,
                        "maximum": 5,
                    },
                },
                "required": ["query", "max_results"],
                "additionalProperties": False,
            },
        },
    }
]


def execute_tool_call(tool_call) -> dict[str, str]:
    """检查调用请求，执行已允许的工具，并返回一条 tool 结果消息。"""
    if tool_call.type != "function":
        raise ValueError("只支持 function 类型的工具调用")
    if not isinstance(tool_call.id, str) or not tool_call.id.strip():
        raise ValueError("工具调用缺少有效 ID")
    if tool_call.function.name != "search_paper":
        raise ValueError("未知工具:" + tool_call.function.name)

    params = parse_search_params(tool_call.function.arguments)
    papers = search_paper(params["query"], params["max_results"])

    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(papers, ensure_ascii=False),
    }


def read_message(response):
    """检查生成结束原因，再读取本轮消息；工具调用可以没有正文。"""
    if not response.choices:
        raise ValueError("模型未返回候选结果")

    choice = response.choices[0]
    if choice.finish_reason == "length":
        raise ValueError("模型输出被截断，请增大 max_tokens 后重试")

    message = choice.message
    expected_reason = "tool_calls" if message.tool_calls else "stop"
    if choice.finish_reason != expected_reason:
        raise ValueError("模型未正常完成回答或工具调用")
    return message


def read_answer(message) -> str:
    """读取直接回答或最终回答；本日示例不继续新的工具调用。"""
    if message.tool_calls:
        raise ValueError("本示例在回传结果后不继续新的工具调用")
    answer = (message.content or "").strip()
    if not answer:
        raise ValueError("模型未返回回答文本")
    return answer


def run_tool_calling(client: OpenAI, request: str) -> str:
    """最多请求模型两次，完成直接回答或一次工具调用闭环。"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request},
    ]
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
        max_tokens=800,
        extra_body={"thinking": {"type": "disabled"}},
    )
    message = read_message(response)

    if not message.tool_calls:
        return read_answer(message)
    if len(message.tool_calls) != 1:
        raise ValueError("本示例只处理一条工具调用")

    tool_call = message.tool_calls[0]
    # 转为字典时仍保留完整 tool_calls，不能只保存 content。
    messages.append(message.model_dump(exclude_none=True))
    tool_message = execute_tool_call(tool_call)
    messages.append(tool_message)

    print(f"工具调用 ID：{tool_call.id}")
    print(f"模型选择工具：{tool_call.function.name}")
    print(f"模型原始参数：{tool_call.function.arguments}")
    print(f"工具返回结果：\n{tool_message['content']}")

    # 第二次只根据已有历史回答，不再提供新的工具。
    final_response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=800,
        extra_body={"thinking": {"type": "disabled"}},
    )
    return read_answer(read_message(final_response))


def main(request: str = REQUEST) -> None:
    """沿用项目配置运行示例，并显示简短的成功结果或失败原因。"""
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
    print(f"用户需求：{request}")
    try:
        answer = run_tool_calling(client, request)
    except APIConnectionError:
        raise SystemExit("连接 DeepSeek API 失败或超时，请检查网络后重试。") from None
    except APIStatusError as error:
        raise SystemExit(
            f"LLM 请求失败（HTTP {error.status_code}），请检查服务状态、密钥和账户额度。"
        ) from None
    except (ValueError, RuntimeError) as error:
        raise SystemExit(f"工具调用流程失败：{error}") from None

    print(f"最终回答：\n{answer}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 4：论文搜索 Tool Calling 示例。")
    parser.add_argument("--request", default=REQUEST, help="本次要交给模型的自然语言需求")
    main(request=parser.parse_args().request)

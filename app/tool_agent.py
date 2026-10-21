"""Day 5：保留消息历史、限制请求次数的最小论文工具 Agent。"""

import argparse
import time

from dotenv import dotenv_values
from openai import APIConnectionError, APIStatusError, OpenAI

from app.tool_calling import (
    BASE_URL,
    ENV_PATH,
    MODEL,
    REQUEST,
    SYSTEM_PROMPT,
    TOOLS,
    execute_tool_call,
    read_answer,
    read_message,
)


MAX_REQUESTS = 3
SEARCH_DELAY_SECONDS = 3


def run_tool_agent(client: OpenAI, request: str) -> str:
    """每轮请求模型一次；有下一轮时才执行工具，否则回答或明确停止。"""
    if type(MAX_REQUESTS) is not int or MAX_REQUESTS < 1:
        raise ValueError("MAX_REQUESTS 必须是大于等于 1 的整数")

    # 只初始化一次，后续每轮都保留前面的调用请求和真实工具结果。
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request},
    ]
    search_count = 0

    for step in range(1, MAX_REQUESTS + 1):
        print(f"\n第 {step}/{MAX_REQUESTS} 次模型请求，已成功搜索 {search_count} 次。")
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            max_tokens=800,
            extra_body={"thinking": {"type": "disabled"}},
        )
        message = read_message(response)

        # 先接受有效答案：最后一次模型请求也可以正常结束。
        if not message.tool_calls:
            answer = read_answer(message)
            print(f"模型给出答案，结束循环。模型请求 {step} 次，成功搜索 {search_count} 次。")
            return answer

        # 最后一轮仍要求工具时，不执行无法交回模型的新搜索。
        if step == MAX_REQUESTS:
            print(f"本轮工具请求未执行。模型请求 {step} 次，成功搜索 {search_count} 次。")
            raise RuntimeError("达到模型请求上限，任务尚未完成")

        if len(message.tool_calls) != 1:
            raise ValueError("每轮只支持一条工具调用")

        tool_call = message.tool_calls[0]
        messages.append(message.model_dump(exclude_none=True))
        print(f"工具调用 ID：{tool_call.id}")
        print(f"模型选择工具：{tool_call.function.name}")
        print(f"模型原始参数：{tool_call.function.arguments}")

        # 简单限速：第一次不等；后续每次搜索前额外等待三秒。
        if search_count > 0:
            print(f"再次搜索前等待 {SEARCH_DELAY_SECONDS} 秒。")
            time.sleep(SEARCH_DELAY_SECONDS)

        tool_message = execute_tool_call(tool_call)
        # 执行失败会抛出异常；只有成功返回才计数、保存结果并继续。
        search_count += 1
        messages.append(tool_message)
        print(f"第 {search_count} 次搜索成功，工具返回结果：\n{tool_message['content']}")


def main(request: str = REQUEST) -> None:
    """沿用 Day 4 的客户端配置，显示执行记录、答案或简短错误。"""
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
        answer = run_tool_agent(client, request)
    except APIConnectionError:
        raise SystemExit("连接 DeepSeek API 失败或超时，请检查网络后重试。") from None
    except APIStatusError as error:
        raise SystemExit(
            f"LLM 请求失败（HTTP {error.status_code}），请检查服务状态、密钥和账户额度。"
        ) from None
    except (ValueError, RuntimeError) as error:
        raise SystemExit(f"工具 Agent 流程失败：{error}") from None

    print(f"最终回答：\n{answer}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 5：有次数上限的论文工具 Agent。")
    parser.add_argument("--request", default=REQUEST, help="本次要交给模型的自然语言需求")
    main(request=parser.parse_args().request)

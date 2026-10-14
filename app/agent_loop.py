"""Day 2：带消息历史和停止条件的最小 LLM 循环。"""

from pathlib import Path

from dotenv import dotenv_values
from openai import APIConnectionError, APIStatusError, OpenAI


ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-flash"
MAX_STEPS = 3
TASK = (
    "为 Python 初学者制定一份包含三项任务的 AI Agent 入门学习计划。"
    "每轮只补充一项任务，包含学习目标和一个可执行练习，不重复已有任务。"
    "每轮正文不超过 100 字。"
    "尚未凑齐三项任务时，最后一行必须是 STATUS: CONTINUE；"
    "凑齐三项任务时，最后一行必须是 STATUS: DONE。"
    "状态行必须独占一行，前面必须有本轮任务正文。"
)


def run_loop(client: OpenAI) -> None:
    """保存本次运行的消息，收到完成信号或达到上限时退出。"""
    messages = [{"role": "user", "content": TASK}]

    for step in range(1, MAX_STEPS + 1):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=200,
            extra_body={"thinking": {"type": "disabled"}},
        )

        if not response.choices:
            raise SystemExit("模型未返回答案，循环已停止。")
        answer = (response.choices[0].message.content or "").strip()
        if not answer:
            raise SystemExit("模型未返回答案，循环已停止。")

        # 检查最后一行的完整状态，正文中的 DONE 不会触发结束。
        lines = answer.splitlines()
        status = lines[-1].strip()
        body = "\n".join(lines[:-1]).strip()
        valid_statuses = {"STATUS: CONTINUE", "STATUS: DONE"}
        extra_status = any(line.strip() in valid_statuses for line in lines[:-1])
        if not body or status not in valid_statuses or extra_status:
            raise SystemExit("回复格式错误：需要正文及独立的状态行，循环已停止。")

        print(f"\n第 {step} 轮：\n{answer}")
        messages.append({"role": "assistant", "content": answer})

        if status == "STATUS: DONE":
            # 这是模型的结束信号，计划内容是否合格仍需人工检查。
            print("模型声明任务完成，结束循环。")
            break

        if step < MAX_STEPS:
            messages.append({"role": "user", "content": "请继续，补充下一项任务。"})
    else:
        # for 的 else 只在循环没有被 break 中断时执行。
        print(f"达到最大步数（{MAX_STEPS}），任务尚未完成。")


def main() -> None:
    """沿用 Day 1 的密钥读取与客户端配置，运行多轮示例。"""
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
    print(f"任务：{TASK}")
    try:
        run_loop(client)
    except APIConnectionError:
        raise SystemExit("连接 DeepSeek API 失败或超时，循环已停止，请检查网络。") from None
    except APIStatusError as error:
        raise SystemExit(
            f"LLM 请求失败（HTTP {error.status_code}），循环已停止，请检查服务状态、密钥和账户额度。"
        ) from None


if __name__ == "__main__":
    main()

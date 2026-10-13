"""Day 1：通过 OpenAI 兼容 SDK 向 DeepSeek 提问一次。"""

from pathlib import Path

from dotenv import dotenv_values
from openai import APIConnectionError, APIStatusError, OpenAI


ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-flash"
QUESTION = "请用一句话解释什么是大语言模型。"


def main() -> None:
    """读取密钥、发送一个问题，并打印模型回答。"""
    # 按脚本位置读取项目配置，不依赖终端当前目录。
    config = dotenv_values(ENV_PATH)
    api_key = (config.get("OPENAI_API_KEY") or "").strip()
    if not api_key or api_key in {
        "your_openai_api_key_here",
        "your_deepseek_api_key_here",
    }:
        raise SystemExit("请在项目 .env 中为 OPENAI_API_KEY 填写 DeepSeek API 密钥。")

    # SDK 名称是 OpenAI；base_url 决定请求实际发送到 DeepSeek。
    client = OpenAI(
        api_key=api_key,
        base_url=BASE_URL,
        timeout=30.0,
        max_retries=0,
    )
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": QUESTION}],
            max_tokens=200,
            # 第一次只学习简单问答，关闭模型的思考模式。
            extra_body={"thinking": {"type": "disabled"}},
        )
    except APIConnectionError:
        raise SystemExit("连接 DeepSeek API 失败或超时，请检查网络后重试。") from None
    except APIStatusError as error:
        raise SystemExit(
            f"LLM 请求失败（HTTP {error.status_code}），请检查服务状态、密钥和账户额度。"
        ) from None

    # choices 中保存模型回复，message.content 是最终答案文本。
    if not response.choices:
        raise SystemExit("模型未返回答案，请稍后重试。")
    answer = (response.choices[0].message.content or "").strip()
    if not answer:
        raise SystemExit("模型未返回答案，请稍后重试。")

    print(f"问题：{QUESTION}")
    print(f"回答：{answer}")


if __name__ == "__main__":
    main()

"""Day 7：读取短文本 PDF，检索并生成带页码来源的回答。"""

import argparse
from pathlib import Path

from dotenv import dotenv_values
from openai import APIConnectionError, APIStatusError, OpenAI
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.local_rag import (
    INSUFFICIENT_ANSWER,
    build_messages,
    generate_answer,
    retrieve_ranked,
)
from app.tool_calling import BASE_URL, ENV_PATH


SAMPLE_PDF_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_pdfs" / "demo.pdf"
DEFAULT_QUESTION = "根据教学演示约定，每次最多向模型提供几个检索片段？"


def load_pdf(file_path):
    """暂按一页一个片段读取，跳过空白页，保留原始 PDF 页码。"""
    file_path = Path(file_path)
    reader = PdfReader(file_path)
    chunks = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()

        if not text:
            continue

        chunk = {
            "source": file_path.name,
            "page": page_number,
            "chunk_id": 1,
            "text": text,
        }
        chunks.append(chunk)

    return chunks


def main(pdf_path=SAMPLE_PDF_PATH, question=DEFAULT_QUESTION, keywords=None, top_k=1, ask=False):
    """先读取和检索；默认打印消息，ask=True 时请求模型生成回答。"""
    if keywords is None:
        keywords = ["最多"]

    try:
        if not isinstance(question, str) or not question.strip():
            raise ValueError("问题不能为空")
        chunks = load_pdf(pdf_path)
        if not chunks:
            raise ValueError("PDF 未提取到非空文字，请检查是否为扫描件或空白文档")
        results = retrieve_ranked(chunks, keywords, top_k=top_k)
    except (OSError, ValueError, PdfReadError) as error:
        raise SystemExit(f"PDF 检索失败：{error}") from None

    print(f"问题：{question}")
    print(f"检索关键词：{keywords}，top_k={top_k}")
    print(f"PDF 片段数量：{len(chunks)}")
    print(f"选中片段数量：{len(results)}")
    for result in results:
        chunk = result["chunk"]
        source_tag = f"[{chunk['source']}#p{chunk['page']}-c{chunk['chunk_id']}]"
        print(f"\n得分：{result['score']}，来源：{source_tag}\n{chunk['text']}")

    if not results:
        print("未检索到相关片段，模型请求 0 次。")
        print(f"最终回答：\n{INSUFFICIENT_ANSWER}")
        return

    if not ask:
        messages = build_messages(question, results)
        print("\n准备交给模型的消息（本次仅打印，模型请求 0 次）：")
        for message in messages:
            print(f"\n[{message['role']}]\n{message['content']}")
        return

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
    print("开始请求模型（最多 1 次，无自动重试）。")
    try:
        answer = generate_answer(client, question, results)
    except APIConnectionError:
        raise SystemExit("连接 DeepSeek API 失败或超时，请检查网络后重试。") from None
    except APIStatusError as error:
        raise SystemExit(
            f"LLM 请求失败（HTTP {error.status_code}），请检查服务状态、密钥和账户额度。"
        ) from None
    except (ValueError, RuntimeError) as error:
        raise SystemExit(f"PDF 回答失败：{error}") from None

    print("模型请求完成：1 次。")
    print(f"最终回答：\n{answer}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 7：带页码来源的 PDF RAG 示例。")
    parser.add_argument("--pdf", type=Path, default=SAMPLE_PDF_PATH, help="要读取的文本 PDF 路径")
    parser.add_argument("--ask", action="store_true", help="检索后请求真实模型生成回答")
    parser.add_argument("--question", default=DEFAULT_QUESTION, help="要根据 PDF 回答的问题")
    parser.add_argument("--keywords", nargs="+", default=["最多"], help="手动指定的检索关键词")
    parser.add_argument("--top-k", type=int, default=1, help="最多提供给模型的片段数")
    args = parser.parse_args()
    main(
        pdf_path=args.pdf,
        question=args.question,
        keywords=args.keywords,
        top_k=args.top_k,
        ask=args.ask,
    )

"""Day 7：逐页查看教学 PDF 的文本，暂不分块或请求模型。"""

from pathlib import Path

from pypdf import PdfReader


PDF_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_pdfs" / "demo.pdf"


def main():
    reader = PdfReader(PDF_PATH)
    print("总页数：", len(reader.pages))

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        print(f"\n--- 第 {page_number} 页 ---")
        print(text)


if __name__ == "__main__":
    main()

from parsers.docx import DocxParser
from parsers.pdf import PDFParser
from parsers.text import TextParser


def get_parser(content_type: str):
    if content_type in ("text/plain", "text/markdown"):
        return TextParser()
    if content_type == "application/pdf":
        return PDFParser()
    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return DocxParser()
    raise ValueError(f"Unsupported content type: {content_type}")

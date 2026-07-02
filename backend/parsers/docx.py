from pathlib import Path

from docx import Document

from parsers.base import Parser


class DocxParser(Parser):
    def parse(self, file_path: Path) -> str:
        document = Document(file_path)
        return "\n".join(p.text for p in document.paragraphs).strip()

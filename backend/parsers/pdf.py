from pathlib import Path

from pypdf import PdfReader

from parsers.base import Parser


class PDFParser(Parser):
    def parse(self, file_path: Path) -> str:
        reader = PdfReader(str(file_path))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()

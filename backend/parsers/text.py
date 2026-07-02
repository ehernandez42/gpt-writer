from pathlib import Path

from parsers.base import Parser


class TextParser(Parser):
    def parse(self, file_path: Path) -> str:
        return file_path.read_text(encoding="utf-8")

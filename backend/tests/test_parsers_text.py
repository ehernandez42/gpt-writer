from pathlib import Path

from parsers.factory import get_parser


def test_text_parser_reads_utf8_file(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello world", encoding="utf-8")

    parser = get_parser("text/plain")

    assert parser.parse(file_path) == "hello world"

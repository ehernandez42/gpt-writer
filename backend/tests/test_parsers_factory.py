import pytest

from parsers.factory import get_parser
from parsers.docx import DocxParser
from parsers.pdf import PDFParser
from parsers.text import TextParser


def test_factory_returns_expected_parser_types():
    assert isinstance(get_parser("text/plain"), TextParser)
    assert isinstance(get_parser("text/markdown"), TextParser)
    assert isinstance(get_parser("application/pdf"), PDFParser)
    assert isinstance(
        get_parser("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        DocxParser,
    )


def test_factory_rejects_unsupported_types():
    with pytest.raises(ValueError):
        get_parser("image/png")

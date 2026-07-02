from services.export import export_text


def test_export_docx_returns_bytes_and_content_type():
    payload = export_text("hello world", "docx")

    assert payload["filename"] == "generated.docx"
    assert payload["content_type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert isinstance(payload["content"], bytes)

from services.export import export_document


def test_pdf_export_supports_rich_html_without_truncation():
    html = (
        '<h1>Heading</h1>'
        + ('<p><strong>Bold</strong> paragraph with enough text to require wrapping. ' * 20)
        + '</p>'
        + '<ul><li>First item</li><li>Second item</li></ul>'
    )

    result = export_document(html, 'pdf', 'html')

    assert result['filename'] == 'generated.pdf'
    assert result['content_type'] == 'application/pdf'
    assert len(result['content']) > 1000

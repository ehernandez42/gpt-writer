from services.export import parse_html_document


def test_parse_html_document_preserves_supported_blocks_and_marks():
    document = parse_html_document(
        '<h1 style="text-align:center">Title</h1>'
        '<p><strong>Bold</strong> and <em>italic</em> text.</p>'
        '<ul><li>One</li><li>Two</li></ul>'
        '<blockquote><u>Quoted</u></blockquote>'
        '<hr>'
    )

    assert document[0].type == 'heading'
    assert document[0].level == 1
    assert document[0].align == 'center'
    assert any(run.bold for run in document[1].inlines)
    assert any(run.italic for run in document[1].inlines)
    assert document[2].ordered is False
    assert document[3].type == 'blockquote'
    assert any(run.underline for run in document[3].inlines)
    assert document[4].type == 'horizontal_rule'

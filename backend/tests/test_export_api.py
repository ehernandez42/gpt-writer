from fastapi.testclient import TestClient
import main


client = TestClient(main.app)


def test_export_accepts_html_content_payload(monkeypatch):
    monkeypatch.setattr(
        'routers.export.export_document',
        lambda content, format, content_type: {
            'filename': 'generated.pdf',
            'content_type': 'application/pdf',
            'content': b'pdf-bytes',
        },
    )

    response = client.post('/export', json={
        'content': '<p>Hello</p>',
        'format': 'pdf',
        'content_type': 'html',
    })

    assert response.status_code == 200
    assert response.headers['content-type'].startswith('application/pdf')


def test_export_rejects_unsupported_content_type():
    response = client.post('/export', json={
        'content': 'plain text',
        'format': 'pdf',
        'content_type': 'text',
    })

    assert response.status_code == 400
    assert 'Unsupported content type' in response.text

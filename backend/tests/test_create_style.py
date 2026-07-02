from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_create_style_from_uploaded_text_file(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BASE_DIR", str(tmp_path / "storage"))
    response = client.post(
        "/styles",
        data={"name": "Formal Memo"},
        files=[("files", ("sample.txt", b"Line one", "text/plain"))],
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Formal Memo"
    assert body["docs_count"] == 1
    assert body["style_id"]

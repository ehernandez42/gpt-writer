from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_and_style_creation_happy_path(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BASE_DIR", str(tmp_path / "storage"))

    health = client.get("/health")
    create = client.post(
        "/styles",
        data={"name": "Policy Style"},
        files=[("files", ("sample.txt", b"clear short declarative writing", "text/plain"))],
    )
    styles = client.get("/styles")

    assert health.status_code == 200
    assert create.status_code == 201
    assert styles.status_code == 200
    assert styles.json()[0]["name"] == "Policy Style"

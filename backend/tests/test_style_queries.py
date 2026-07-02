from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_style_can_be_listed_read_and_deleted(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BASE_DIR", str(tmp_path / "storage"))
    created = client.post(
        "/styles",
        data={"name": "Board Report"},
        files=[("files", ("sample.txt", b"alpha beta", "text/plain"))],
    ).json()
    style_id = created["style_id"]

    list_response = client.get("/styles")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == style_id

    detail_response = client.get(f"/styles/{style_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["name"] == "Board Report"
    assert "alpha beta" in detail_response.json()["combined_text"]

    delete_response = client.delete(f"/styles/{style_id}")
    assert delete_response.status_code == 204

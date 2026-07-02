import pytest

from providers.ollama import OllamaProvider


class DummyResponse:
    def __init__(self, *, is_success=True, json_data=None):
        self.is_success = is_success
        self._json_data = json_data or {}

    def json(self):
        return self._json_data

    def raise_for_status(self):
        return None


class DummyAsyncClient:
    last_get = None
    last_post = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def get(self, url, headers=None):
        type(self).last_get = {"url": url, "headers": headers}
        return DummyResponse(is_success=True)

    async def post(self, url, headers=None, json=None):
        type(self).last_post = {"url": url, "headers": headers, "json": json}
        return DummyResponse(
            json_data={
                "message": {"content": "generated text"},
            }
        )


@pytest.mark.asyncio
async def test_ollama_provider_uses_cloud_api_endpoints(monkeypatch):
    monkeypatch.setenv("OLLAMA_API_KEY", "test-key")
    monkeypatch.setattr("providers.ollama.httpx.AsyncClient", DummyAsyncClient)

    provider = OllamaProvider()

    available = await provider.is_available()
    text = await provider.generate([{"role": "user", "content": "hello"}])

    assert available is True
    assert text == "generated text"
    assert DummyAsyncClient.last_get["url"] == "https://ollama.com/api/tags"
    assert DummyAsyncClient.last_post["url"] == "https://ollama.com/api/chat"
    assert DummyAsyncClient.last_post["json"] == {
        "model": provider.model,
        "messages": [{"role": "user", "content": "hello"}],
        "stream": False,
    }

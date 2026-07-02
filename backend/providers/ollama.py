import os

import httpx

from providers.base import LLMProvider


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self):
        self.base_url = "https://ollama.com"
        self.model = os.getenv("OLLAMA_MODEL", "llama3.1")
        self.api_key = os.getenv("OLLAMA_API_KEY")

    async def generate(self, messages: list[dict], **kwargs) -> str:
        endpoint = f"{self.base_url}/api/chat"
        payload = {"model": self.model, "messages": messages, "stream": False, **kwargs}
        print(f"[ollama] POST {endpoint} model={self.model} api_key_set={bool(self.api_key)}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            return response.json()["message"]["content"]

    async def is_available(self) -> bool:
        if not self.api_key:
            print("[ollama] skipping availability check: api_key_set=False")
            return False
        endpoint = f"{self.base_url}/api/tags"
        print(f"[ollama] GET {endpoint} model={self.model} api_key_set={bool(self.api_key)}")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return response.is_success
        except Exception as exc:
            print(f"[ollama] availability check failed: {exc}")
            return False

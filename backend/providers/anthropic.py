import os

from anthropic import AsyncAnthropic

from providers.base import LLMProvider


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        self.client = AsyncAnthropic(api_key=self.api_key) if self.api_key else None

    async def generate(self, messages: list[dict], **kwargs) -> str:
        system_messages = [m["content"] for m in messages if m["role"] == "system"]
        user_messages = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1000),
            system="\n\n".join(system_messages),
            messages=user_messages,
        )
        return "".join(block.text for block in response.content if block.type == "text")

    async def is_available(self) -> bool:
        return self.client is not None

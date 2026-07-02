from abc import ABC, abstractmethod


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, messages: list[dict], **kwargs) -> str: ...

    @abstractmethod
    async def is_available(self) -> bool: ...

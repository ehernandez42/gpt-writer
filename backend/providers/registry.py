from providers.anthropic import AnthropicProvider
from providers.ollama import OllamaProvider


def get_provider_chain():
    return [OllamaProvider(), AnthropicProvider()]

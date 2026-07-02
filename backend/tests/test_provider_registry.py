from providers.registry import get_provider_chain


def test_provider_chain_prefers_ollama_then_anthropic():
    chain = get_provider_chain()

    assert [provider.name for provider in chain] == ["ollama", "anthropic"]

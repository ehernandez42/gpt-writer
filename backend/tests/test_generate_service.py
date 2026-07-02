from services.generate import build_messages


def test_build_messages_embeds_style_reference_and_prompt():
    messages = build_messages("formal style sample", "Write an update")

    assert messages[0]["role"] == "system"
    assert "formal style sample" in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "Write an update"}

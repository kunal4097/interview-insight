"""
The one function that actually calls a model provider. call_llm() dispatches to the Claude
(Anthropic) or OpenAI SDK depending on `provider` and normalizes both providers' responses to
the same (text, truncated) shape, so callers never branch on provider again after this point.
"""
from anthropic import Anthropic
from openai import OpenAI


def call_llm(provider: str, api_key: str, model: str, system: str, user_content: str) -> tuple[str, bool]:
    """Returns (response_text, truncated) - truncated is True when the model hit the token
    limit before finishing, which is the main way a well-formed JSON summary block goes missing."""
    if provider == "OpenAI":
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            max_completion_tokens=16000,
            messages=[
                {"role": "developer", "content": system},
                {"role": "user", "content": user_content},
            ],
        )
        choice = response.choices[0]
        return choice.message.content or "", choice.finish_reason == "length"

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=16000,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return text, response.stop_reason == "max_tokens"

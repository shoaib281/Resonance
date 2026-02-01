"""LLM abstraction — OpenAI gpt-4o-mini for all agent calls."""

from __future__ import annotations
import os
from openai import AsyncOpenAI

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("Set OPENAI_API_KEY environment variable")
        _client = AsyncOpenAI(api_key=key)
    return _client


async def chat(system: str, user: str, max_tokens: int = 1024) -> str:
    client = get_client()
    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content

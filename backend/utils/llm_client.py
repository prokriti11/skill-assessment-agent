# llm_client.py
# Centralized LLM client using Groq (free, fast).
# Model: llama-3.3-70b-versatile
# All agents import call_llm() from here.

import os
from groq import Groq

_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def call_llm(system_prompt: str, user_message: str, max_tokens: int = 4096) -> str:
    """Single-turn LLM call. Returns assistant reply as string."""
    response = _client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content.strip()


def call_llm_with_history(
    system_prompt: str,
    messages: list[dict],
    max_tokens: int = 512,
) -> str:
    """Multi-turn LLM call with full conversation history."""
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    response = _client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=full_messages,
    )
    return response.choices[0].message.content.strip()

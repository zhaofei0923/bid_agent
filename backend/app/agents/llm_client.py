"""LLM Client — DeepSeek API wrapper (OpenAI-compatible).

All LLM calls in the system go through this client.
"""

import json
import logging
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Literal

import httpx
from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class Message:
    """Chat message."""

    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class LLMResponse:
    """Structured response from the LLM."""

    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"


@dataclass
class LLMJsonResult:
    """Parsed JSON result from extract_json, including token usage."""

    data: dict
    tokens_used: int = 0


class LLMClient:
    """DeepSeek API wrapper using OpenAI-compatible interface.

    Usage:
        client = LLMClient()
        response = await client.chat([Message("user", "Hello")])
        print(response.content)
    """

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            http_client=httpx.AsyncClient(timeout=settings.LLM_TIMEOUT),
            max_retries=settings.LLM_MAX_RETRIES,
        )
        self.model = settings.LLM_MODEL
        self.reasoning_model = settings.LLM_REASONING_MODEL

    async def chat(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        model: str | None = None,
        **kwargs: object,
    ) -> LLMResponse:
        """Send a chat completion request."""
        model = model or self.model
        logger.info("LLM chat: model=%s, msgs=%d, max_tokens=%d", model, len(messages), max_tokens)

        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        choice = response.choices[0]
        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage=usage,
            finish_reason=choice.finish_reason or "stop",
        )

    async def chat_stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        model: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream a chat completion, yielding content chunks."""
        model = model or self.model

        stream = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def generate_with_context(
        self,
        question: str,
        context: list[str],
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> LLMResponse:
        """RAG helper — inject retrieved context into the prompt."""
        context_text = "\n\n---\n\n".join(context)
        user_prompt = (
            f"基于以下参考内容回答问题。如果参考内容未涵盖，请明确说明。\n\n"
            f"=== 参考内容 ===\n{context_text}\n\n"
            f"=== 问题 ===\n{question}"
        )

        messages = []
        if system_prompt:
            messages.append(Message("system", system_prompt))
        messages.append(Message("user", user_prompt))

        return await self.chat(
            messages, temperature=temperature, max_tokens=max_tokens
        )

    async def extract_json(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4000,
    ) -> LLMJsonResult:
        """Call LLM and parse the response as JSON.

        Returns LLMJsonResult with parsed data and token usage.
        Automatically strips markdown code fences.
        """
        response = await self.chat(
            messages=[
                Message("system", system_prompt),
                Message("user", prompt),
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        tokens_used = response.usage.get("total_tokens", 0)

        # Strip markdown code fences (```json ... ```)
        content = response.content.strip()
        content = re.sub(r"^```(?:json)?\s*\n?", "", content)
        content = re.sub(r"\n?```\s*$", "", content)

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM JSON response: %s", content[:200])
            data = {"raw_content": response.content, "parse_error": True}

        return LLMJsonResult(data=data, tokens_used=tokens_used)

    async def summarize(
        self, text: str, max_length: int = 500
    ) -> str:
        """Summarize text to the specified length."""
        response = await self.chat(
            messages=[
                Message(
                    "system",
                    f"用中文写一段不超过 {max_length} 字的摘要。仅输出摘要本身。",
                ),
                Message("user", text),
            ],
            temperature=0.3,
            max_tokens=max_length * 2,
        )
        return response.content


# ── Module-level singleton ────────────────────────────

_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get or create the singleton LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

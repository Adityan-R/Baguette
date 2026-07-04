import httpx
import json
from typing import AsyncIterator
from .base import BaseProvider
from ..keystore import get_key

class AnthropicProvider(BaseProvider):
    name = "anthropic"
    requires_key = True

    async def stream_chat(self, model: str, messages: list[dict], tools: list[dict] | None = None, system: str | None = None) -> AsyncIterator[str]:
        anthropic_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m["role"] != "system"
        ]
        system_text = system or next(
            (m["content"] for m in messages if m["role"] == "system"), None
        )
        payload = {
            "model": model,
            "max_tokens": 8096,
            "messages": anthropic_messages,
            "stream": True,
        }
        if system_text:
            payload["system"] = system_text
        if tools:
            payload["tools"] = tools

        headers = {
            "x-api-key": get_key("anthropic"),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", "https://api.anthropic.com/v1/messages", json=payload, headers=headers) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if data.get("type") == "content_block_delta":
                                if chunk := data.get("delta", {}).get("text", ""):
                                    yield chunk
                        except json.JSONDecodeError:
                            pass

    async def list_models(self) -> list[str]:
        return ["claude-3-7-sonnet-latest", "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"]

    def is_available(self) -> bool:
        return get_key("anthropic") is not None

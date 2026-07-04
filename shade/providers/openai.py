import httpx
import json
from typing import AsyncIterator
from .base import BaseProvider
from ..keystore import get_key

class OpenAIProvider(BaseProvider):
    name = "openai"
    requires_key = True
    base_url = "https://api.openai.com/v1"

    async def stream_chat(self, model: str, messages: list[dict], tools: list[dict] | None = None, system: str | None = None) -> AsyncIterator[str]:
        headers = {
            "Authorization": f"Bearer {get_key(self.name)}",
            "Content-Type": "application/json"
        }
        payload = {"model": model, "messages": messages, "stream": True}
        if tools:
            payload["tools"] = tools
            
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{self.base_url}/chat/completions", json=payload, headers=headers) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if line.startswith("data: "):
                        raw = line[6:]
                        if raw == "[DONE]":
                            break
                        try:
                            data = json.loads(raw)
                            if choices := data.get("choices"):
                                if chunk := choices[0].get("delta", {}).get("content", ""):
                                    yield chunk
                        except json.JSONDecodeError:
                            pass

    async def list_models(self) -> list[str]:
        return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o1-mini", "o3-mini"]

    def is_available(self) -> bool:
        return get_key(self.name) is not None

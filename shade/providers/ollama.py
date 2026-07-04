import httpx
import json
from .base import BaseProvider
from ..config import config

class OllamaProvider(BaseProvider):
    name = "ollama"
    requires_key = False

    def __init__(self):
        self.host = config.get("ollama", "host", "http://localhost:11434")

    async def stream_chat(self, model: str, messages: list[dict], tools: list[dict] | None = None, system: str | None = None) -> __import__('typing').AsyncIterator[str]:
        payload = {"model": model, "messages": messages, "stream": True}
        if tools:
            payload["tools"] = tools
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{self.host}/api/chat", json=payload) as r:
                async for line in r.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if chunk := data.get("message", {}).get("content", ""):
                            yield chunk
                        if data.get("done"):
                            break

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{self.host}/api/tags")
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []

    def is_available(self) -> bool:
        try:
            httpx.get(f"{self.host}/api/tags", timeout=2)
            return True
        except Exception:
            return False

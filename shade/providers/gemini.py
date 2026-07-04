import httpx
import json
from typing import AsyncIterator
from .base import BaseProvider
from ..keystore import get_key

class GeminiProvider(BaseProvider):
    name = "gemini"
    requires_key = True

    async def stream_chat(self, model: str, messages: list[dict], tools: list[dict] | None = None, system: str | None = None) -> AsyncIterator[str]:
        # Translating to Gemini format
        # User -> user, Assistant -> model
        gemini_contents = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
                continue
            role = "model" if m["role"] == "assistant" else m["role"]
            gemini_contents.append({
                "role": role,
                "parts": [{"text": m["content"]}]
            })

        payload = {
            "contents": gemini_contents,
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        key = get_key("gemini")
        # Ensure we're using a proper gemini model format
        # Actually Google API paths usually use models/gemini-1.5-flash
        model_path = model if "models/" in model else f"models/{model}"
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:streamGenerateContent?key={key}"

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", url, json=payload) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if candidates := data.get("candidates"):
                                if parts := candidates[0].get("content", {}).get("parts"):
                                    if text := parts[0].get("text"):
                                        yield text
                        except json.JSONDecodeError:
                            pass

    async def list_models(self) -> list[str]:
        return ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"]

    def is_available(self) -> bool:
        return get_key("gemini") is not None

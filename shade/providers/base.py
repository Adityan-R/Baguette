from abc import ABC, abstractmethod
from typing import AsyncIterator

class BaseProvider(ABC):
    name: str          
    requires_key: bool 

    @abstractmethod
    async def stream_chat(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        """Yield text chunks. Must be a real async generator."""
        ...

    @abstractmethod
    async def list_models(self) -> list[str]:
        """Return available model names for this provider."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider can be used right now (key present, server running, etc.)."""
        ...

from .base import BaseProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .gemini import GeminiProvider
from .groq import GroqProvider
from ..config import config

PROVIDERS: dict[str, BaseProvider] = {
    "ollama":    OllamaProvider(),
    "openai":    OpenAIProvider(),
    "anthropic": AnthropicProvider(),
    "gemini":    GeminiProvider(),
    "groq":      GroqProvider(),
}

MODEL_PREFIXES = {
    "gpt-":        "openai",
    "o1-":         "openai",
    "o3-":         "openai",
    "claude-":     "anthropic",
    "gemini-":     "gemini",
    "gemma-":      "gemini",
    "llama-":      "groq",
    "mixtral-":    "groq",
}

def resolve_provider(model_name: str) -> BaseProvider:
    """Infer the right provider from a model name string."""
    for prefix, provider_name in MODEL_PREFIXES.items():
        if model_name.startswith(prefix):
            return PROVIDERS[provider_name]
    # Default fallback
    return PROVIDERS["ollama"]

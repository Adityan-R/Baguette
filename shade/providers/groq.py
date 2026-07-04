from .openai import OpenAIProvider

class GroqProvider(OpenAIProvider):
    name = "groq"
    base_url = "https://api.groq.com/openai/v1"
    
    async def list_models(self) -> list[str]:
        return [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]

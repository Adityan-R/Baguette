import unittest
from shade.providers.registry import resolve_provider, PROVIDERS

class TestProviders(unittest.TestCase):
    def test_provider_registry_contains_all(self):
        self.assertIn("ollama", PROVIDERS)
        self.assertIn("openai", PROVIDERS)
        self.assertIn("anthropic", PROVIDERS)
        self.assertIn("gemini", PROVIDERS)
        self.assertIn("groq", PROVIDERS)

    def test_resolve_provider_by_prefix(self):
        self.assertEqual(resolve_provider("gpt-4o").name, "openai")
        self.assertEqual(resolve_provider("o1-mini").name, "openai")
        self.assertEqual(resolve_provider("claude-3-5-sonnet").name, "anthropic")
        self.assertEqual(resolve_provider("gemini-2.5-flash").name, "gemini")
        self.assertEqual(resolve_provider("llama-3.3-70b-versatile").name, "groq")

    def test_resolve_provider_fallback(self):
        self.assertEqual(resolve_provider("qwen2.5-coder:7b").name, "ollama")
        self.assertEqual(resolve_provider("deepseek-r1").name, "ollama")

if __name__ == "__main__":
    unittest.main()

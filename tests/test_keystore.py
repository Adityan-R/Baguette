import os
import unittest
from unittest.mock import patch
from shade.keystore import get_key, set_key, delete_key, list_stored_keys

class TestKeystore(unittest.TestCase):
    @patch.dict(os.environ, {"OPENAI_API_KEY": "env-sk-test12345"})
    def test_get_key_from_env(self):
        key = get_key("openai")
        self.assertEqual(key, "env-sk-test12345")

    @patch("keyring.get_password", return_value="keyring-sk-test67890")
    @patch.dict(os.environ, {}, clear=True)
    def test_get_key_from_keyring(self, mock_keyring):
        key = get_key("anthropic")
        self.assertEqual(key, "keyring-sk-test67890")
        mock_keyring.assert_called_with("shade", "ANTHROPIC_API_KEY")

    def test_get_key_unknown_provider(self):
        self.assertIsNone(get_key("unknown_provider"))

    @patch("keyring.set_password")
    def test_set_key(self, mock_set):
        set_key("gemini", "gemini-key-123")
        mock_set.assert_called_with("shade", "GEMINI_API_KEY", "gemini-key-123")

    def test_set_key_invalid_provider(self):
        with self.assertRaises(ValueError):
            set_key("invalid_provider", "key")

    @patch("keyring.delete_password")
    def test_delete_key(self, mock_delete):
        delete_key("groq")
        mock_delete.assert_called_with("shade", "GROQ_API_KEY")

if __name__ == "__main__":
    unittest.main()

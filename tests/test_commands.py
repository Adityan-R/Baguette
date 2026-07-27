import unittest
from unittest.mock import MagicMock, patch
from shade.context import ConversationContext
from shade.commands import handle_slash_command

class TestCommands(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ctx = ConversationContext(active_model="qwen2.5-coder:7b")
        self.renderer = MagicMock()

    async def test_clear_command(self):
        self.ctx.add_user("test")
        handled = await handle_slash_command("/clear", self.ctx, self.renderer)
        self.assertTrue(handled)
        self.assertEqual(len(self.ctx.messages), 0)

    @patch("shade.commands.prompt_and_store_key", return_value="dummy-key")
    async def test_model_switch_command(self, mock_prompt):
        handled = await handle_slash_command("/model gpt-4o", self.ctx, self.renderer)
        self.assertTrue(handled)
        self.assertEqual(self.ctx.active_model, "gpt-4o")

    async def test_persona_command(self):
        handled = await handle_slash_command("/persona herta", self.ctx, self.renderer)
        self.assertTrue(handled)
        self.assertIn("elite ai", self.ctx.system_prompt.lower())

    async def test_help_command(self):
        handled = await handle_slash_command("/help", self.ctx, self.renderer)
        self.assertTrue(handled)
        self.renderer.print.assert_called()

if __name__ == "__main__":
    unittest.main()

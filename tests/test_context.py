import unittest
from shade.context import ConversationContext, Message

class TestConversationContext(unittest.TestCase):
    def test_context_initialization(self):
        ctx = ConversationContext()
        self.assertTrue(len(ctx.session_id) > 0)
        self.assertEqual(len(ctx.messages), 0)
        self.assertEqual(ctx.active_model, "")

    def test_add_user_message(self):
        ctx = ConversationContext()
        ctx.add_user("Hello agent")
        self.assertEqual(len(ctx.messages), 1)
        self.assertEqual(ctx.messages[0].role, "user")
        self.assertEqual(ctx.messages[0].content, "Hello agent")

    def test_add_assistant_message(self):
        ctx = ConversationContext(active_model="qwen2.5-coder")
        ctx.add_assistant("Hello user")
        self.assertEqual(len(ctx.messages), 1)
        self.assertEqual(ctx.messages[0].role, "assistant")
        self.assertEqual(ctx.messages[0].content, "Hello user")
        self.assertEqual(ctx.messages[0].model, "qwen2.5-coder")

    def test_add_tool_result(self):
        ctx = ConversationContext()
        ctx.add_tool_result("read_file", "file content")
        self.assertEqual(len(ctx.messages), 1)
        self.assertEqual(ctx.messages[0].role, "tool")
        self.assertEqual(ctx.messages[0].content, "file content")
        self.assertEqual(ctx.messages[0].tool_results, [{"tool": "read_file"}])

    def test_switch_model(self):
        ctx = ConversationContext(active_model="qwen2.5-coder")
        ctx.switch_model("gpt-4o")
        self.assertEqual(ctx.active_model, "gpt-4o")
        self.assertEqual(len(ctx.messages), 1)
        self.assertIn("gpt-4o", ctx.messages[0].content)

    def test_serialization(self):
        ctx = ConversationContext(active_model="qwen2.5-coder", system_prompt="Be concise")
        ctx.add_user("What is 2+2?")
        ctx.add_assistant("4")

        data = ctx.to_dict()
        restored = ConversationContext.from_dict(data)

        self.assertEqual(restored.session_id, ctx.session_id)
        self.assertEqual(restored.active_model, "qwen2.5-coder")
        self.assertEqual(restored.system_prompt, "Be concise")
        self.assertEqual(len(restored.messages), 2)
        self.assertEqual(restored.messages[0].content, "What is 2+2?")
        self.assertEqual(restored.messages[1].content, "4")

if __name__ == "__main__":
    unittest.main()

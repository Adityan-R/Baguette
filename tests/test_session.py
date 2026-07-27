import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from shade.context import ConversationContext
from shade.session import save_session, load_session, list_sessions

class TestSession(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.patcher = patch("shade.session.SESSION_DIR", Path(self.temp_dir.name))
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

    def test_save_and_load_session(self):
        ctx = ConversationContext(session_id="test1234", active_model="qwen2.5-coder")
        ctx.add_user("Test prompt")
        ctx.add_assistant("Test response")

        saved_path = save_session(ctx)
        self.assertTrue(Path(saved_path).exists())

        loaded_ctx = load_session("test1234")
        self.assertIsNotNone(loaded_ctx)
        self.assertEqual(loaded_ctx.session_id, "test1234")
        self.assertEqual(loaded_ctx.active_model, "qwen2.5-coder")
        self.assertEqual(len(loaded_ctx.messages), 2)

    def test_list_sessions(self):
        ctx1 = ConversationContext(session_id="sess_1")
        ctx2 = ConversationContext(session_id="sess_2")
        save_session(ctx1)
        save_session(ctx2)

        sessions = list_sessions()
        self.assertIn("sess_1", sessions)
        self.assertIn("sess_2", sessions)

    def test_load_nonexistent_session(self):
        res = load_session("nonexistent_session_id")
        self.assertIsNone(res)

if __name__ == "__main__":
    unittest.main()

import os
import tempfile
import unittest
from shade.tools.registry import dispatch, get_active_tools, TOOL_REGISTRY
from shade.tools.filesystem import read_file, write_file, list_dir, replace_in_file

class TestTools(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = os.path.join(self.temp_dir.name, "sample.txt")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_active_tools_registry(self):
        tools = get_active_tools()
        tool_names = [t["function"]["name"] for t in tools]
        self.assertIn("read_file", tool_names)
        self.assertIn("write_file", tool_names)
        self.assertIn("list_dir", tool_names)
        self.assertIn("replace_in_file", tool_names)

    def test_write_and_read_file(self):
        res_write = write_file(self.test_file, "Hello Shade CLI")
        self.assertIn("Successfully wrote", res_write)

        res_read = read_file(self.test_file)
        self.assertEqual(res_read, "Hello Shade CLI")

    def test_replace_in_file(self):
        write_file(self.test_file, "foo bar baz")
        res_replace = replace_in_file(self.test_file, "bar", "qux")
        self.assertIn("Successfully replaced", res_replace)

        res_read = read_file(self.test_file)
        self.assertEqual(res_read, "foo qux baz")

    def test_replace_in_file_not_found(self):
        write_file(self.test_file, "foo bar baz")
        res_replace = replace_in_file(self.test_file, "missing", "qux")
        self.assertIn("Error", res_replace)

    def test_list_dir(self):
        write_file(self.test_file, "test")
        files = list_dir(self.temp_dir.name)
        self.assertIn("sample.txt", files)

    def test_dispatch_unknown_tool(self):
        res = dispatch("unknown_tool", {})
        self.assertIn("Error", res)

    def test_dispatch_known_tool(self):
        res = dispatch("write_file", {"path": self.test_file, "content": "dispatched content"})
        self.assertIn("Successfully wrote", res)
        self.assertEqual(read_file(self.test_file), "dispatched content")

if __name__ == "__main__":
    unittest.main()

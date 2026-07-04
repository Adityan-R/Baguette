import os
from pathlib import Path
from .registry import tool

@tool("read_file", "Read file content", {
    "type": "object",
    "properties": {
        "path": {"type": "string"},
    },
    "required": ["path"]
})
def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

@tool("write_file", "Write or overwrite a file", {
    "type": "object",
    "properties": {
        "path": {"type": "string"},
        "content": {"type": "string"}
    },
    "required": ["path", "content"]
})
def write_file(path: str, content: str) -> str:
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error: {e}"

@tool("list_dir", "List files in directory", {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "Defaults to current directory"}
    }
})
def list_dir(path: str = ".") -> str:
    try:
        items = os.listdir(path)
        return "\n".join(items)
    except Exception as e:
        return f"Error: {e}"

@tool("replace_in_file", "Replace specific content in a file without overwriting the whole file. Highly recommended for small edits.", {
    "type": "object",
    "properties": {
        "path": {"type": "string"},
        "old_content": {"type": "string", "description": "The exact string to find and replace. Must match exactly, including whitespace."},
        "new_content": {"type": "string", "description": "The new content to insert."}
    },
    "required": ["path", "old_content", "new_content"]
})
def replace_in_file(path: str, old_content: str, new_content: str) -> str:
    try:
        p = Path(path)
        if not p.exists():
            return f"Error: File {path} does not exist."
        content = p.read_text(encoding="utf-8")
        if old_content not in content:
            return f"Error: old_content not found in {path}. Exact match required."
        new_text = content.replace(old_content, new_content)
        p.write_text(new_text, encoding="utf-8")
        return f"Successfully replaced content in {path}"
    except Exception as e:
        return f"Error: {e}"

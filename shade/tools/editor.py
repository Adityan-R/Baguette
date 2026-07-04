from .registry import tool

@tool("apply_diff", "Apply a simple diff to a file. For now, it just asks the model to rewrite.", {
    "type": "object",
    "properties": {
        "path": {"type": "string"}
    },
    "required": ["path"]
})
def apply_diff(path: str) -> str:
    return "apply_diff not fully implemented, please use write_file instead to rewrite the file."

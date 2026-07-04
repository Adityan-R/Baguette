TOOL_REGISTRY: dict[str, dict] = {}
TOOL_HANDLERS: dict[str, callable] = {}

def tool(name: str, description: str, parameters: dict):
    def decorator(fn):
        TOOL_REGISTRY[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        }
        TOOL_HANDLERS[name] = fn
        return fn
    return decorator

def dispatch(tool_name: str, args: dict) -> str:
    if tool_name not in TOOL_HANDLERS:
        return f"Error: tool '{tool_name}' not found"
    try:
        return str(TOOL_HANDLERS[tool_name](**args))
    except Exception as e:
        return f"Tool error: {e}"

def get_active_tools():
    return list(TOOL_REGISTRY.values())

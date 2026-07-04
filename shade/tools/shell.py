import subprocess
from .registry import tool
from rich.prompt import Confirm
from ..renderer import console

@tool("run_command", "Execute a shell command", {
    "type": "object",
    "properties": {
        "command": {"type": "string"}
    },
    "required": ["command"]
})
def run_command(command: str) -> str:
    console.print(f"\n[warning]The model wants to run a command:[/warning] [bold white]{command}[/bold white]")
    if not Confirm.ask("Allow execution?"):
        return "Error: User denied execution."
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except Exception as e:
        return f"Error executing command: {e}"

import json
import uuid
from pathlib import Path
from .context import ConversationContext
from .renderer import console

SESSION_DIR = Path.home() / ".local" / "share" / "shade" / "sessions"

def save_session(ctx: ConversationContext, name: str = None) -> str:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    if not name:
        name = ctx.session_id
    filepath = SESSION_DIR / f"{name}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(ctx.to_dict(), f, indent=2)
    return str(filepath)

def load_session(name: str) -> ConversationContext | None:
    filepath = SESSION_DIR / f"{name}.json"
    if not filepath.exists():
        console.print(f"[danger]Session {name} not found.[/danger]")
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return ConversationContext.from_dict(data)
    except Exception as e:
        console.print(f"[danger]Error loading session: {e}[/danger]")
        return None

def list_sessions():
    if not SESSION_DIR.exists():
        return []
    return [f.stem for f in SESSION_DIR.glob("*.json")]

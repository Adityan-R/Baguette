import os
import tomllib
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = {
    "ollama": {
        "host": "http://localhost:11434",
        "default_model": "qwen2.5-coder:7b",
        "timeout": 120
    },
    "providers": {
        "openai": {"enabled": True},
        "anthropic": {"enabled": True},
        "gemini": {"enabled": True},
        "groq": {"enabled": True},
        "custom": []
    },
    "agent": {
        "auto_save": True,
        "confirm_shell_commands": True,
        "max_context_messages": 100,
        "working_dir": "."
    },
    "system_prompt": {
        "persona": "professional",
        "default": "You are a helpful AI coding assistant. You have access to tools to read files, run shell commands, and edit code. Always think step by step. When using tools, explain what you're doing before each tool call."
    },
    "tools": {
        "enabled": ["read_file", "write_file", "list_dir", "search_files", "run_command", "apply_diff"],
        "disabled": []
    },
    "ui": {
        "theme": "dark",
        "show_model_in_prompt": True,
        "show_provider_in_prompt": True,
        "show_token_count": True
    }
}

class Config:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "shade"
        self.config_file = self.config_dir / "config.toml"
        self._data: dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if not self.config_file.exists():
            self.save_defaults()
        else:
            try:
                with open(self.config_file, "rb") as f:
                    user_config = tomllib.load(f)
                    self._deep_update(self._data, user_config)
            except Exception as e:
                print(f"Error loading config: {e}")

    def save_defaults(self):
        # We don't necessarily write the defaults back to disk immediately, 
        # but we could create the directory if it doesn't exist.
        self.config_dir.mkdir(parents=True, exist_ok=True)
        # For simplicity, we just keep the defaults in memory if file is missing.

    def _deep_update(self, d: dict, u: dict) -> dict:
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = self._deep_update(d[k], v)
            else:
                d[k] = v
        return d

    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        if key is None:
            return self._data.get(section, default)
        return self._data.get(section, {}).get(key, default)

# Global config instance
config = Config()

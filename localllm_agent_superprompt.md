# Super Prompt: Local LLM Agent CLI (Model-Agnostic, Context-Persistent)

---

## Project Identity

**Name:** `cypher` (working title — pick your own)  
**Type:** Terminal-first AI coding/task agent  
**Model backend:** Local LLMs via Ollama + remote paid APIs (OpenAI, Anthropic, Google Gemini, Groq, and any OpenAI-compatible endpoint)  
**Inspiration:** Claude Code, Gemini CLI, Aider  
**Core differentiator:** Switch between any locally installed model OR any remote paid model (OpenAI, Anthropic, Gemini, Groq…) mid-session without losing conversation context, file context, or agent state. API keys are stored securely in the system keychain — never in plaintext config files.

---

## What You Are Building

A Python CLI agent that:

1. Connects to a local Ollama instance **and/or** remote paid API providers (OpenAI, Anthropic, Gemini, Groq, any OpenAI-compatible endpoint)
2. Maintains a **persistent conversation context** in a structured session format
3. Allows the user to **switch models at any point** using a command — the full conversation history is re-passed to the new model, preserving continuity, even across provider boundaries (e.g. from a local `qwen2.5-coder` to `gpt-4o` to `claude-sonnet-4-5` and back)
4. Manages **API keys securely** via system keychain (`keyring` library) — keys are entered once, never stored in plaintext
5. Has **tool use / function calling** for file reading, shell execution, directory listing, and code editing
6. Has a **streaming output** interface in the terminal (Rich library)
7. Supports **slash commands** (like `/model`, `/keys`, `/providers`, `/clear`, `/save`, `/load`, `/exit`)
8. Has **session persistence** — save and resume sessions from disk as JSON
9. Optionally supports a **system prompt** per-session or per-model

---

## Technical Stack

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| CLI rendering | `rich` (panels, markdown, live streaming) |
| Ollama API | `ollama` Python SDK or raw `httpx` streaming |
| Remote provider APIs | `httpx` with per-provider adapters (OpenAI, Anthropic, Gemini, Groq) |
| **API key storage** | **`keyring`** — OS system keychain (Credential Manager / Keychain / libsecret) |
| Config | `~/.config/cypher/config.toml` via `tomllib` — **never stores API keys** |
| Session storage | `~/.local/share/cypher/sessions/` as JSON files |
| Tools / function calling | Custom JSON schema tool definitions |
| Shell execution | `subprocess` with timeout + sandboxing |
| Package manager | `uv` or `pip` with `pyproject.toml` |

---

## Project Structure

```
cypher/
├── pyproject.toml
├── README.md
├── cypher/
│   ├── __init__.py
│   ├── main.py              # Entry point, CLI arg parsing
│   ├── agent.py             # Core agent loop
│   ├── context.py           # ConversationContext class — model-agnostic
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py          # BaseProvider ABC — common interface all providers implement
│   │   ├── ollama.py        # Ollama local provider
│   │   ├── openai.py        # OpenAI + OpenAI-compatible endpoints
│   │   ├── anthropic.py     # Anthropic Claude API
│   │   ├── gemini.py        # Google Gemini API
│   │   ├── groq.py          # Groq cloud inference API
│   │   └── registry.py      # Provider registry — resolve model name → provider
│   ├── keystore.py          # API key management via `keyring` (get/set/delete/list)
│   ├── models.py            # Unified model catalogue (local + remote)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py      # Tool registration decorator + dispatcher
│   │   ├── filesystem.py    # read_file, write_file, list_dir, search_files
│   │   ├── shell.py         # run_shell_command (with confirm prompt)
│   │   └── editor.py        # apply_diff, replace_in_file
│   ├── session.py           # Save/load sessions to/from disk
│   ├── renderer.py          # Rich-based terminal UI, streaming output
│   ├── config.py            # Load ~/.config/cypher/config.toml
│   └── commands.py          # Slash command handlers (/model, /keys, /providers, etc.)
└── tests/
    ├── test_context.py
    ├── test_tools.py
    ├── test_session.py
    ├── test_keystore.py
    └── test_providers.py
```

---

## Core Architecture: The ConversationContext

This is the heart of the model-switching system. The context must be **completely model-agnostic** — it stores messages in a neutral format and can be serialised and re-injected into any model.

```python
# context.py

from dataclasses import dataclass, field
from typing import Literal
import json, time, uuid

Role = Literal["system", "user", "assistant", "tool"]

@dataclass
class Message:
    role: Role
    content: str
    tool_calls: list[dict] | None = None   # for assistant tool use
    tool_results: list[dict] | None = None  # for tool return values
    timestamp: float = field(default_factory=time.time)
    model: str = ""   # which model generated this message

@dataclass
class ConversationContext:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    messages: list[Message] = field(default_factory=list)
    active_model: str = ""
    system_prompt: str = ""
    working_dir: str = ""
    created_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def add_user(self, content: str):
        self.messages.append(Message(role="user", content=content))

    def add_assistant(self, content: str, model: str = ""):
        self.messages.append(Message(role="assistant", content=content, model=model or self.active_model))

    def add_tool_result(self, tool_name: str, result: str):
        self.messages.append(Message(role="tool", content=result, metadata={"tool": tool_name}))

    def to_ollama_messages(self) -> list[dict]:
        """Convert to Ollama/OpenAI message format for API calls."""
        out = []
        if self.system_prompt:
            out.append({"role": "system", "content": self.system_prompt})
        for m in self.messages:
            out.append({"role": m.role, "content": m.content})
        return out

    def switch_model(self, new_model: str):
        """Switch active model. Context is preserved — next API call re-injects full history."""
        old = self.active_model
        self.active_model = new_model
        self.messages.append(Message(
            role="system",
            content=f"[Model switched from {old} to {new_model}. Conversation history preserved.]"
        ))

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "active_model": self.active_model,
            "system_prompt": self.system_prompt,
            "working_dir": self.working_dir,
            "created_at": self.created_at,
            "metadata": self.metadata,
            "messages": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp, "model": m.model}
                for m in self.messages
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationContext":
        ctx = cls(
            session_id=data["session_id"],
            active_model=data["active_model"],
            system_prompt=data.get("system_prompt", ""),
            working_dir=data.get("working_dir", ""),
            created_at=data.get("created_at", time.time()),
            metadata=data.get("metadata", {}),
        )
        ctx.messages = [
            Message(role=m["role"], content=m["content"], timestamp=m.get("timestamp", 0), model=m.get("model", ""))
            for m in data.get("messages", [])
        ]
        return ctx
```

---

## Provider Abstraction Layer

Every model backend — Ollama, OpenAI, Anthropic, Gemini, Groq — implements the same `BaseProvider` interface. The agent never calls a provider directly; it always goes through the registry. This is what makes cross-provider model switching seamless.

```python
# providers/base.py

from abc import ABC, abstractmethod
from typing import AsyncIterator

class BaseProvider(ABC):
    name: str          # e.g. "ollama", "openai", "anthropic"
    requires_key: bool # False for Ollama, True for everything else

    @abstractmethod
    async def stream_chat(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        """Yield text chunks. Must be a real async generator."""
        ...

    @abstractmethod
    async def list_models(self) -> list[str]:
        """Return available model names for this provider."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider can be used right now (key present, server running, etc.)."""
        ...
```

```python
# providers/registry.py

from .ollama import OllamaProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .gemini import GeminiProvider
from .groq import GroqProvider

PROVIDERS: dict[str, BaseProvider] = {
    "ollama":    OllamaProvider(),
    "openai":    OpenAIProvider(),
    "anthropic": AnthropicProvider(),
    "gemini":    GeminiProvider(),
    "groq":      GroqProvider(),
}

# Model name → provider routing table
MODEL_PREFIXES = {
    "gpt-":        "openai",
    "o1-":         "openai",
    "o3-":         "openai",
    "claude-":     "anthropic",
    "gemini-":     "gemini",
    "gemma-":      "gemini",     # Gemini API also serves Gemma
    "llama-":      "groq",       # Groq's hosted Llama
    "mixtral-":    "groq",
    "moonshotai/": "groq",
}

def resolve_provider(model_name: str) -> BaseProvider:
    """Infer the right provider from a model name string."""
    for prefix, provider_name in MODEL_PREFIXES.items():
        if model_name.startswith(prefix):
            return PROVIDERS[provider_name]
    # Default: assume Ollama local model
    return PROVIDERS["ollama"]
```

### Per-Provider Implementation Notes

**`providers/openai.py`** — use `httpx` to call `https://api.openai.com/v1/chat/completions` with `stream: true`. Also supports custom `base_url` for OpenAI-compatible endpoints (Together, Fireworks, Perplexity, local LM Studio, etc.) configured via `config.toml`.

**`providers/anthropic.py`** — call `https://api.anthropic.com/v1/messages` with `stream: true`. Anthropic's message format differs slightly: system prompt is a top-level field, not a message role. The provider adapter must handle this translation from the neutral `ConversationContext` format.

**`providers/gemini.py`** — call the Gemini REST API (`generativelanguage.googleapis.com`). Message roles use `"model"` instead of `"assistant"` — the adapter translates.

**`providers/groq.py`** — Groq is OpenAI-compatible, so reuse the OpenAI provider with `base_url = "https://api.groq.com/openai/v1"`.

---

## API Key Management (Keystore)

API keys are **never** stored in `config.toml` or session files. They live exclusively in the OS system keychain via the `keyring` library (Windows Credential Manager, macOS Keychain, Linux libsecret/KWallet).

```python
# keystore.py

import keyring
from rich.prompt import Prompt
from rich.console import Console

KEYRING_SERVICE = "cypher"

PROVIDER_KEY_NAMES = {
    "openai":    "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini":    "GEMINI_API_KEY",
    "groq":      "GROQ_API_KEY",
}

console = Console()

def get_key(provider: str) -> str | None:
    """Retrieve a stored API key. Returns None if not set."""
    env_var = PROVIDER_KEY_NAMES.get(provider)
    if not env_var:
        return None
    # Also check environment variables as a fallback
    import os
    return keyring.get_password(KEYRING_SERVICE, env_var) or os.environ.get(env_var)

def set_key(provider: str, key: str) -> None:
    """Store an API key in the system keychain."""
    env_var = PROVIDER_KEY_NAMES.get(provider)
    if not env_var:
        raise ValueError(f"Unknown provider: {provider}")
    keyring.set_password(KEYRING_SERVICE, env_var, key)

def delete_key(provider: str) -> None:
    """Remove an API key from the system keychain."""
    env_var = PROVIDER_KEY_NAMES.get(provider)
    if env_var:
        keyring.delete_password(KEYRING_SERVICE, env_var)

def prompt_and_store_key(provider: str) -> str:
    """
    Interactively prompt the user for an API key, validate it's non-empty,
    store it in keychain, and return it.
    Key input is masked (password field).
    """
    console.print(f"\n[bold]No API key found for [cyan]{provider}[/cyan].[/bold]")
    console.print(f"Get yours at: {PROVIDER_URLS[provider]}")
    key = Prompt.ask(f"Enter your {PROVIDER_KEY_NAMES[provider]}", password=True)
    if not key.strip():
        raise ValueError("API key cannot be empty.")
    set_key(provider, key.strip())
    console.print(f"[green]✓ Key stored in system keychain. You won't be asked again.[/green]\n")
    return key.strip()

def list_stored_keys() -> dict[str, bool]:
    """Return a dict of provider → has_key for display in /keys command."""
    return {
        provider: get_key(provider) is not None
        for provider in PROVIDER_KEY_NAMES
    }

PROVIDER_URLS = {
    "openai":    "https://platform.openai.com/api-keys",
    "anthropic": "https://console.anthropic.com/keys",
    "gemini":    "https://aistudio.google.com/app/apikey",
    "groq":      "https://console.groq.com/keys",
}
```

### Key Resolution Flow (on every API call)

```
1. User types /model gpt-4o  →  registry resolves provider = "openai"
2. Agent calls openai_provider.stream_chat(...)
3. OpenAIProvider checks: keystore.get_key("openai")
4a. Key found → proceed with API call
4b. Key not found → call keystore.prompt_and_store_key("openai")
       → user enters key (masked input)
       → key stored in OS keychain
       → API call proceeds
5. On next session, key is already in keychain — no prompt needed
```

**Environment variable fallback:** If a key is set as an env var (`OPENAI_API_KEY`, etc.), it takes priority over the keychain. This allows CI/server usage without interactive prompts.

**Custom base URL for OpenAI-compatible endpoints:** Support a `custom` provider type in config for self-hosted or third-party OpenAI-compatible endpoints:

```toml
# config.toml
[[providers.custom]]
name = "lmstudio"
base_url = "http://localhost:1234/v1"
api_key_required = false   # LM Studio doesn't need a key

[[providers.custom]]
name = "together"
base_url = "https://api.together.xyz/v1"
api_key_env = "TOGETHER_API_KEY"
```

---

## Model Switching: How It Works

When the user types `/model gpt-4o` mid-session (switching from a local Ollama model to OpenAI):

1. `providers/registry.py` resolves `"gpt-4o"` → `OpenAIProvider`
2. `OpenAIProvider.is_available()` checks the keychain for `OPENAI_API_KEY`
3. If key is missing, `keystore.prompt_and_store_key("openai")` runs — masked input, stored once
4. `ConversationContext.switch_model("gpt-4o")` is called — appends a system note, updates `active_model`
5. On the **next user message**, the full `ctx.to_messages()` history is translated into OpenAI format and sent to GPT-4o
6. GPT-4o responds with complete awareness of the prior conversation, including anything generated by the local model
7. The model name and provider are stored on each `Message` for auditing

The context format translation (e.g. Anthropic uses `"model"` role instead of `"assistant"`, system prompt is top-level not a message) is handled by each provider's adapter — the `ConversationContext` always stays in the neutral format.

**Context window management:** If context gets large, offer a `/summarize` command that uses the current model to summarize older messages, replacing them with a compressed summary block tagged `[SUMMARIZED]`. This keeps the session continuable without hitting token limits.

---

## Slash Commands

| Command | Description |
|---|---|
| `/model [name]` | Switch to any model (local or remote). Lists all available if no name given. |
| `/models` | List all models — local (Ollama) and remote (per provider, if key is set) |
| `/providers` | Show all providers, their status (available / missing key / offline), and key link |
| `/keys` | Show which providers have API keys stored. Never shows the key value itself. |
| `/key set [provider]` | Store or update an API key for a provider (masked input → OS keychain) |
| `/key delete [provider]` | Remove a stored API key from keychain |
| `/key test [provider]` | Send a minimal test request to verify the key works |
| `/tools` | List all available tools and their descriptions |
| `/tool-on [name]` | Enable a specific tool |
| `/tool-off [name]` | Disable a specific tool |
| `/save [name]` | Save current session to disk |
| `/load [name]` | Load a previous session |
| `/sessions` | List all saved sessions |
| `/history` | Show conversation history with model + provider attribution |
| `/clear` | Clear conversation (keep model and system prompt) |
| `/system [prompt]` | Set or view system prompt |
| `/summarize` | Summarize old context to free up token space |
| `/undo` | Remove the last user+assistant exchange |
| `/cd [path]` | Change working directory for file tools |
| `/context` | Show token estimate and message count |
| `/exit` | Exit (auto-saves session) |

---

## Tool System

Tools are defined as JSON schemas (OpenAI function calling format) and dispatched by name. Ollama models that support tool use (e.g., `qwen2.5-coder`, `llama3.1`, `mistral-nemo`) will call them natively. For models that don't support tool use, implement a **ReAct-style fallback parser** that reads `Action:` / `Action Input:` patterns in the model output.

### Tool Registry Pattern

```python
# tools/registry.py

TOOL_REGISTRY: dict[str, dict] = {}
TOOL_HANDLERS: dict[str, callable] = {}

def tool(name: str, description: str, parameters: dict):
    """Decorator to register a tool."""
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
        return TOOL_HANDLERS[tool_name](**args)
    except Exception as e:
        return f"Tool error: {e}"
```

### Core Tools to Implement

```
read_file(path, start_line=None, end_line=None)
  → Read file content, optionally a line range

write_file(path, content)
  → Write or overwrite a file (with confirmation prompt)

apply_diff(path, diff)
  → Apply a unified diff to a file

list_dir(path=".", recursive=False, pattern=None)
  → List files in a directory, with optional glob pattern

search_files(query, path=".", file_pattern="*")
  → Search file contents for a string (grep-style)

run_command(command, timeout=30)
  → Execute a shell command, return stdout+stderr
  → Always show command to user and require Y/n confirmation before running

create_file(path, content)
  → Create a new file

delete_file(path)
  → Delete a file (with confirmation)

get_context(paths: list[str])
  → Read multiple files and return their contents as a combined block
  → Useful for "add these files to context" workflow
```

---

## Agent Loop

```python
# agent.py — simplified pseudocode

async def run_agent(ctx: ConversationContext, renderer: Renderer):
    while True:
        user_input = renderer.prompt(f"[{ctx.active_model}]> ")

        if user_input.startswith("/"):
            await handle_slash_command(user_input, ctx, renderer)
            continue

        ctx.add_user(user_input)

        # Resolve which provider handles the active model
        provider = resolve_provider(ctx.active_model)

        # If provider needs a key and doesn't have one, prompt now
        if provider.requires_key and not provider.is_available():
            key = keystore.prompt_and_store_key(provider.name)
            provider.set_key(key)

        # Build message list from neutral context format
        messages = ctx.to_messages()
        tools = get_active_tools()

        # Stream response through the resolved provider
        full_response = ""
        with renderer.live_panel(label=f"{ctx.active_model} ({provider.name})"):
            async for chunk in provider.stream_chat(ctx.active_model, messages, tools):
                full_response += chunk
                renderer.update(chunk)

        # Check for tool calls in response
        tool_calls = parse_tool_calls(full_response)
        if tool_calls:
            for call in tool_calls:
                result = dispatch_tool(call, renderer)
                ctx.add_tool_result(call["name"], result)
            # Continue loop — model will see tool results in next pass
            continue

        ctx.add_assistant(full_response)
        renderer.finalize()
```

---

## Config File Format

`~/.config/cypher/config.toml`

**Security rule: API keys are NEVER written here.** They live in the OS keychain only. The config file is safe to commit to version control.

```toml
[ollama]
host = "http://localhost:11434"
default_model = "qwen2.5-coder:7b"
timeout = 120

# Built-in remote providers — no config needed beyond having a key stored.
# Keys are stored in OS keychain via: /key set openai
[providers.openai]
enabled = true

[providers.anthropic]
enabled = true

[providers.gemini]
enabled = true

[providers.groq]
enabled = true

# Optional: custom OpenAI-compatible endpoints
[[providers.custom]]
name = "lmstudio"
base_url = "http://localhost:1234/v1"
api_key_required = false

[[providers.custom]]
name = "together"
base_url = "https://api.together.xyz/v1"
# Key stored in keychain under service="cypher", username="TOGETHER_API_KEY"
api_key_env = "TOGETHER_API_KEY"

[agent]
auto_save = true
confirm_shell_commands = true
max_context_messages = 100  # after this, prompt to summarize
working_dir = "."

[system_prompt]
default = """
You are a helpful AI coding assistant. You have access to tools to read files,
run shell commands, and edit code. Always think step by step.
When using tools, explain what you're doing before each tool call.
"""

[tools]
enabled = ["read_file", "write_file", "list_dir", "search_files", "run_command", "apply_diff"]
disabled = []

[ui]
theme = "dark"
show_model_in_prompt = true
show_provider_in_prompt = true   # shows [gpt-4o | openai]> in the prompt
show_token_count = true
```

---

## Provider Implementations

### Ollama (local)

```python
# providers/ollama.py

class OllamaProvider(BaseProvider):
    name = "ollama"
    requires_key = False

    async def stream_chat(self, model, messages, tools=None, system=None):
        payload = {"model": model, "messages": messages, "stream": True}
        if tools:
            payload["tools"] = tools
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{self.host}/api/chat", json=payload) as r:
                async for line in r.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if chunk := data.get("message", {}).get("content", ""):
                            yield chunk
                        if data.get("done"):
                            break

    async def list_models(self):
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.host}/api/tags")
            return [m["name"] for m in r.json().get("models", [])]

    def is_available(self):
        try:
            httpx.get(f"{self.host}/api/tags", timeout=2)
            return True
        except Exception:
            return False
```

### OpenAI (and compatible endpoints)

```python
# providers/openai.py

class OpenAIProvider(BaseProvider):
    name = "openai"
    requires_key = True
    base_url = "https://api.openai.com/v1"

    async def stream_chat(self, model, messages, tools=None, system=None):
        headers = {"Authorization": f"Bearer {keystore.get_key('openai')}",
                   "Content-Type": "application/json"}
        payload = {"model": model, "messages": messages, "stream": True}
        if tools:
            payload["tools"] = tools
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{self.base_url}/chat/completions",
                                     json=payload, headers=headers) as r:
                async for line in r.aiter_lines():
                    if line.startswith("data: "):
                        raw = line[6:]
                        if raw == "[DONE]":
                            break
                        data = json.loads(raw)
                        if chunk := data["choices"][0]["delta"].get("content", ""):
                            yield chunk

    async def list_models(self):
        # Returns curated list — OpenAI's /models endpoint has 100+ entries
        return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o1-mini", "o3-mini"]

    def is_available(self):
        return keystore.get_key("openai") is not None
```

### Anthropic

```python
# providers/anthropic.py

class AnthropicProvider(BaseProvider):
    name = "anthropic"
    requires_key = True

    async def stream_chat(self, model, messages, tools=None, system=None):
        # Anthropic format: system is top-level, role is "user"/"assistant" (not "tool")
        anthropic_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m["role"] != "system"
        ]
        system_text = system or next(
            (m["content"] for m in messages if m["role"] == "system"), None
        )
        payload = {
            "model": model,
            "max_tokens": 8096,
            "messages": anthropic_messages,
            "stream": True,
        }
        if system_text:
            payload["system"] = system_text
        if tools:
            payload["tools"] = tools  # Anthropic tool format is compatible

        headers = {
            "x-api-key": keystore.get_key("anthropic"),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", "https://api.anthropic.com/v1/messages",
                                     json=payload, headers=headers) as r:
                async for line in r.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if data.get("type") == "content_block_delta":
                            if chunk := data.get("delta", {}).get("text", ""):
                                yield chunk

    async def list_models(self):
        return ["claude-opus-4-5", "claude-sonnet-4-5", "claude-haiku-4-5"]

    def is_available(self):
        return keystore.get_key("anthropic") is not None
```

### Gemini and Groq

**Gemini (`providers/gemini.py`):** Call `https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent`. Translate `"assistant"` role → `"model"` in the request. Translate back on response. System instruction goes in a top-level `"system_instruction"` field.

**Groq (`providers/groq.py`):** Groq is OpenAI-compatible. Subclass `OpenAIProvider`, override `base_url = "https://api.groq.com/openai/v1"` and `name = "groq"`. Point keystore to `"groq"`. Groq's `/models` endpoint works so `list_models()` can hit it directly for current offerings.

---

## Model-Switching UX Flow

### Switching between local models (no key needed)
```
[qwen2.5-coder:7b | ollama]> read the main.py file and explain it

[reading main.py...]
[streaming response...]

[qwen2.5-coder:7b | ollama]> /model llama3.2

  ✓ Switched to llama3.2 (ollama)
  ✓ Context preserved — 12 messages, ~3.2k tokens

[llama3.2 | ollama]> now refactor the agent loop to be cleaner
```

### Switching from a local model to a paid API (first time — key prompt)
```
[llama3.2 | ollama]> /model gpt-4o

  Switching to gpt-4o (openai)...
  ✗ No API key found for openai.

  Get your key at: https://platform.openai.com/api-keys
  Enter your OPENAI_API_KEY: ********************************

  ✓ Key stored in system keychain.
  ✓ Context preserved — 12 messages, ~3.2k tokens
  ✓ Switched to gpt-4o (openai)

[gpt-4o | openai]> what do you think of the refactor so far?

[GPT-4o has full context — sees everything the local models said and did]
```

### On subsequent sessions (key already in keychain)
```
[gpt-4o | openai]> /model claude-sonnet-4-5

  ✓ Switched to claude-sonnet-4-5 (anthropic)
  ✓ Context preserved — 18 messages, ~5.1k tokens

[claude-sonnet-4-5 | anthropic]>
```

### /providers output
```
  Providers:
  ● ollama      local       8 models installed   [running]
  ● openai      remote      key stored           [available]
  ● anthropic   remote      key stored           [available]
  ◌ gemini      remote      no key               /key set gemini
  ◌ groq        remote      no key               /key set groq
  ● lmstudio    custom      no key required      [running]
```

### /keys output
```
  API Keys (stored in system keychain — values never shown):
  ✓ openai      OPENAI_API_KEY      stored
  ✓ anthropic   ANTHROPIC_API_KEY   stored
  ✗ gemini      GEMINI_API_KEY      not set   →  /key set gemini
  ✗ groq        GROQ_API_KEY        not set   →  /key set groq
```

---

## Session Save/Load

Sessions are saved as JSON to `~/.local/share/cypher/sessions/<session_id>.json`.

On startup, if a `sessions/` directory has saved sessions, show the user a list:

```
  Recent sessions:
  ① [abc123] qwen2.5-coder:7b · 24 messages · "read the main.py file..."  (2h ago)
  ② [def456] llama3.2 · 8 messages · "help me write a FastAPI..."         (yesterday)
  ③ Start new session
```

Auto-save on exit and on `/save`.

---

## Deliverables

1. **Working CLI** installable via `pip install -e .` or `uv tool install .`
2. **`cypher`** command available globally in terminal
3. **All slash commands** implemented, including `/keys`, `/key set`, `/key delete`, `/key test`, `/providers`
4. **All core tools** implemented with confirmation prompts for destructive operations
5. **Full streaming output** using Rich, prompt shows `[model | provider]>`
6. **Session save/load** working — sessions never contain API keys
7. **Model switching** working with context preservation, including cross-provider switching
8. **All 4 built-in remote providers** implemented: OpenAI, Anthropic, Gemini, Groq
9. **Custom endpoint** support via `config.toml`
10. **Keystore** implemented with `keyring`, env var fallback, masked input, and `/key test` validation
11. **README.md** with install steps, usage guide, provider setup instructions, and supported model list per provider
12. **Tests** for ConversationContext serialisation, model switching, tool dispatch, keystore get/set/delete, and provider resolution

---

## Stretch Goals (implement if time allows)

- **Multi-model mode:** Send the same prompt to two models (local or remote) simultaneously and display side-by-side in Rich columns — useful for comparing local vs. paid model output quality
- **`/diff` command:** Show a rich diff of a file before/after the last `write_file` or `apply_diff` call
- **Token counter:** Show estimated token count of current context in the prompt line, with per-provider context window limit (e.g. warn when nearing GPT-4o's 128k or Gemini's 1M)
- **Cost tracker:** For paid providers, estimate cost of the current session based on input/output tokens and published pricing. Show in `/context` output.
- **Web search tool:** Integrate with a local SearXNG or DuckDuckGo scraper
- **Vision support:** If model supports it (e.g., `llava` locally, `gpt-4o` or `claude-sonnet-4-5` remotely), allow image uploads via `/attach path/to/image.png`
- **Provider auto-fallback:** If the active provider fails (network error, quota exceeded), optionally fall back to a user-configured backup provider without losing context
- **Plugin system:** Allow external Python files in `~/.config/cypher/plugins/` to register new tools via the `@tool` decorator, and new providers via `BaseProvider`
- **API Usage & Rate Limit Warning:** Track model/API usage limits (e.g., tokens per minute or daily requests) and display a proactive warning to the user when they are within 10% of hitting the limit.

---

## Key Constraints & Quality Gates

- **No context loss on model switch** — this is the #1 requirement. Write a test that switches models 3 times across 3 different providers in one session and asserts full message history is intact and correctly formatted for each provider.
- **API keys never touch disk in plaintext** — search the entire codebase. If any key value appears in a log, a session file, a config file, or stdout (outside of masked input), it is a critical bug. The only exception is reading from env vars that the user set themselves.
- **Never truncate silently** — if context is too long, warn the user and offer `/summarize`, never silently drop messages.
- **Streaming must be real** — no fake streaming. All four provider implementations must use their respective streaming APIs.
- **Confirm before destructive actions** — `write_file`, `delete_file`, `run_command` always ask Y/n first.
- **Cross-platform** — must work on Windows, macOS, and Linux. Use `pathlib.Path` everywhere, never raw string paths. `keyring` handles OS differences for the keychain automatically.
- **Graceful degradation** — if Ollama is not running, show a clear error with instructions, don't crash. If a remote provider call fails, show the HTTP status and error message from the API, not a Python traceback.

---

*Generated for: Antigravity AI Agent Build*  
*Stack: Python + Ollama + OpenAI + Anthropic + Gemini + Groq + Rich + httpx + keyring*  
*Primary features: Model-agnostic context-persistent agent · secure API key management · cross-provider model switching*

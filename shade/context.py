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
        self.messages.append(Message(role="tool", content=result, model="tool", tool_results=[{"tool": tool_name}]))

    def to_ollama_messages(self) -> list[dict]:
        """Convert to Ollama/OpenAI message format for API calls."""
        out = []
        if self.system_prompt:
            out.append({"role": "system", "content": self.system_prompt})
        for m in self.messages:
            # We skip tool calls rendering here unless strictly required for simple interactions
            out.append({"role": m.role, "content": m.content})
        return out

    def to_messages(self) -> list[dict]:
        """Alias for to_ollama_messages used widely in providers."""
        return self.to_ollama_messages()

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
                {
                    "role": m.role, 
                    "content": m.content, 
                    "timestamp": m.timestamp, 
                    "model": m.model,
                    "tool_calls": m.tool_calls,
                    "tool_results": m.tool_results
                }
                for m in self.messages
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationContext":
        ctx = cls(
            session_id=data.get("session_id", str(uuid.uuid4())[:8]),
            active_model=data.get("active_model", ""),
            system_prompt=data.get("system_prompt", ""),
            working_dir=data.get("working_dir", ""),
            created_at=data.get("created_at", time.time()),
            metadata=data.get("metadata", {}),
        )
        ctx.messages = [
            Message(
                role=m["role"], 
                content=m["content"], 
                timestamp=m.get("timestamp", 0), 
                model=m.get("model", ""),
                tool_calls=m.get("tool_calls"),
                tool_results=m.get("tool_results")
            )
            for m in data.get("messages", [])
        ]
        return ctx

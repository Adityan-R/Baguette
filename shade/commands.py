from .context import ConversationContext
from .renderer import Renderer
from .providers.registry import PROVIDERS, resolve_provider
from .keystore import list_stored_keys, prompt_and_store_key, delete_key

async def handle_slash_command(user_input: str, ctx: ConversationContext, renderer: Renderer) -> bool:
    """Returns True if the loop should continue (i.e. command was handled)."""
    parts = user_input.strip().split()
    cmd = parts[0].lower()

    if cmd == "/model":
        if len(parts) > 1:
            new_model = parts[1]
            provider = resolve_provider(new_model)
            if provider.requires_key and not provider.is_available():
                prompt_and_store_key(provider.name)
            ctx.switch_model(new_model)
            renderer.print(f"[success]✓ Switched to {new_model} ({provider.name})[/success]")
            renderer.print(f"[success]✓ Context preserved — {len(ctx.messages)} messages[/success]")
        else:
            renderer.print("[info]Usage: /model <name>[/info]")
        return True

    elif cmd == "/models":
        renderer.print("\n[bold]Available Models:[/bold]")
        for name, provider in PROVIDERS.items():
            if provider.is_available():
                # We can't await here directly without refactoring, so we'll just list the provider as active
                renderer.print(f"  ● {name} [success]available[/success]")
            else:
                renderer.print(f"  ◌ {name} [dim]unavailable[/dim]")
        return True

    elif cmd == "/providers":
        renderer.print("\n[bold]Providers:[/bold]")
        keys = list_stored_keys()
        for name, provider in PROVIDERS.items():
            if not provider.requires_key:
                status = "[success]running[/success]" if provider.is_available() else "[danger]offline[/danger]"
                renderer.print(f"  ● {name:10} local      {status}")
            else:
                has_key = keys.get(name, False)
                if has_key:
                    renderer.print(f"  ● {name:10} remote     key stored   [success]available[/success]")
                else:
                    renderer.print(f"  ◌ {name:10} remote     no key       [dim]/key set {name}[/dim]")
        return True

    elif cmd == "/keys":
        renderer.print("\n[bold]API Keys:[/bold]")
        for provider, has_key in list_stored_keys().items():
            if has_key:
                renderer.print(f"  [success]✓ {provider:10} stored[/success]")
            else:
                renderer.print(f"  [danger]✗ {provider:10} not set[/danger]   →  /key set {provider}")
        return True

    elif cmd == "/key":
        if len(parts) > 2 and parts[1] == "set":
            provider = parts[2]
            try:
                prompt_and_store_key(provider)
            except ValueError as e:
                renderer.print(f"[danger]{e}[/danger]")
        elif len(parts) > 2 and parts[1] == "delete":
            provider = parts[2]
            delete_key(provider)
            renderer.print(f"[success]✓ Deleted key for {provider}[/success]")
        else:
            renderer.print("[info]Usage: /key set <provider> | /key delete <provider>[/info]")
        return True

    elif cmd == "/clear":
        ctx.messages.clear()
        renderer.print("[success]✓ Conversation cleared.[/success]")
        return True

    elif cmd == "/history":
        for idx, m in enumerate(ctx.messages):
            role_color = "cyan" if m.role == "user" else "blue"
            renderer.print(f"[{idx}] [{role_color}]{m.role}[/{role_color}] (model: {m.model}): {m.content[:50]}...")
        return True

    elif cmd == "/persona":
        from .personas import PERSONAS
        if len(parts) > 1:
            new_persona = parts[1].lower()
            if new_persona in PERSONAS:
                ctx.system_prompt = PERSONAS[new_persona]
                renderer.print(f"[success]✓ Persona switched to: {new_persona}[/success]")
            else:
                renderer.print(f"[danger]Unknown persona: {new_persona}[/danger]")
                renderer.print(f"[info]Available: {', '.join(PERSONAS.keys())}[/info]")
        else:
            renderer.print(f"[info]Available personas: {', '.join(PERSONAS.keys())}[/info]\n[dim]Usage: /persona <name>[/dim]")
        return True

    elif cmd == "/save":
        from .session import save_session
        session_name = parts[1] if len(parts) > 1 else None
        saved_path = save_session(ctx, session_name)
        renderer.print(f"[success]✓ Session saved to {saved_path}[/success]")
        return True

    elif cmd == "/load":
        from .session import load_session
        if len(parts) > 1:
            session_name = parts[1]
            loaded_ctx = load_session(session_name)
            if loaded_ctx:
                ctx.session_id = loaded_ctx.session_id
                ctx.messages = loaded_ctx.messages
                ctx.active_model = loaded_ctx.active_model
                ctx.system_prompt = loaded_ctx.system_prompt
                ctx.working_dir = loaded_ctx.working_dir
                ctx.metadata = loaded_ctx.metadata
                renderer.print(f"[success]✓ Loaded session '{session_name}' ({len(ctx.messages)} messages)[/success]")
        else:
            renderer.print("[info]Usage: /load <session_name>[/info]")
        return True

    elif cmd == "/sessions":
        from .session import list_sessions
        sessions = list_sessions()
        if sessions:
            renderer.print("\n[bold]Saved Sessions:[/bold]")
            for s in sessions:
                renderer.print(f"  ● {s}")
        else:
            renderer.print("[info]No saved sessions found.[/info]")
        return True

    elif cmd == "/help":
        renderer.print("\n[bold]Available Commands:[/bold]")
        renderer.print("  /model <name>       Switch active AI model")
        renderer.print("  /models             List available models and availability")
        renderer.print("  /providers          View provider status")
        renderer.print("  /keys               View API key status")
        renderer.print("  /key set <provider> Store an API key securely in keychain")
        renderer.print("  /key delete <prov>  Delete a stored API key")
        renderer.print("  /save [name]        Save active session")
        renderer.print("  /load <name>        Load session from disk")
        renderer.print("  /sessions           List saved sessions")
        renderer.print("  /history            View message history")
        renderer.print("  /clear              Clear conversation history")
        renderer.print("  /persona [name]     Switch agent personality")
        renderer.print("  /exit               Exit SHADE")
        return True

    else:
        renderer.print(f"[warning]Unknown command: {cmd}[/warning]")
        return True

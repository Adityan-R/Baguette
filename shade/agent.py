import json
from .context import ConversationContext
from .renderer import Renderer
from .commands import handle_slash_command
from .providers.registry import resolve_provider
from .keystore import prompt_and_store_key
from .tools.registry import get_active_tools, dispatch
from .config import config

async def run_agent(ctx: ConversationContext, renderer: Renderer):
    # Ensure there's an active model
    if not ctx.active_model:
        ctx.switch_model(config.get("ollama", "default_model", "qwen2.5-coder:7b"))

    if not ctx.system_prompt:
        from .personas import PERSONAS
        ctx.system_prompt = PERSONAS.get("professional", "")

    first_turn = True

    while True:
        provider = resolve_provider(ctx.active_model)
        
        user_input = await renderer.prompt(ctx.active_model, provider.name, centered=first_turn)

        if not user_input.strip():
            continue

        if first_turn:
            import os
            os.system('cls' if os.name == 'nt' else 'clear')
            renderer.print_active_header(ctx.session_id)
            first_turn = False

        if user_input.startswith("/"):
            if user_input.strip() == "/exit":
                break
            await handle_slash_command(user_input, ctx, renderer)
            continue

        ctx.add_user(user_input)

        if provider.requires_key and not provider.is_available():
            try:
                prompt_and_store_key(provider.name)
            except ValueError:
                continue
                
        # Inner loop for agent autonomy (Phase 1)
        while True:
            messages = ctx.to_messages()
            tools = [t["function"] for t in get_active_tools()] if config.get("tools", "enabled") else None
    
            full_response = ""
            
            with renderer.streaming_panel(f"{ctx.active_model} ({provider.name})") as stream:
                try:
                    async for chunk in provider.stream_chat(ctx.active_model, messages, tools):
                        full_response += chunk
                        stream.update(chunk)
                except Exception as e:
                    full_response = f"[Error communicating with provider: {e}]"
                    stream.update(full_response)
    
            ctx.add_assistant(full_response, model=ctx.active_model)
    
            tool_executed = False
            # Markdown tool parsing (ReAct fallback for non-native tools)
            import re
            match = re.search(r"Action:\s*([^\n]+)\s*\nAction Input:\s*(\{.*?\})", full_response, re.DOTALL)
            if match:
                action = match.group(1).strip()
                args_str = match.group(2).strip()
                try:
                    args = json.loads(args_str)
                    renderer.print(f"[tool]Running tool: {action}[/tool]")
                    result = dispatch(action, args)
                    ctx.add_tool_result(action, result)
                    renderer.render_message(ctx.messages[-1])
                    tool_executed = True
                except Exception as e:
                    renderer.print(f"[danger]Tool parsing error: {e}[/danger]")
                        
            # If no tool was executed in this turn, break the loop to ask the user for input
            if not tool_executed:
                break

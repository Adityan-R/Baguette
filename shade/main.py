import sys
import asyncio
from .renderer import Renderer
from .context import ConversationContext
from .agent import run_agent

async def main():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')
    
    renderer = Renderer()
    ctx = ConversationContext()
    
    from .config import config
    if not ctx.active_model:
        ctx.switch_model(config.get("ollama", "default_model", "qwen2.5-coder:7b"))
        
    renderer.print_dashboard(ctx.active_model)
    await run_agent(ctx, renderer)
    renderer.print("[dim]Goodbye![/dim]")

def cli():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    cli()

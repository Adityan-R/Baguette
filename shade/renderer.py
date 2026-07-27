import os
import shutil
import time
import asyncio
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.theme import Theme
from rich.text import Text
from rich.padding import Padding
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style as PtStyle
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.completion import Completer, Completion
from pygments.lexers.markup import MarkdownLexer
from prompt_toolkit.formatted_text import FormattedText

from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, FloatContainer, Float, WindowAlign
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.cursor_shapes import CursorShape

custom_theme = Theme({
    "info": "dim white",
    "warning": "magenta",
    "danger": "bold red",
    "success": "bold #4DAAFB",
    "model": "bold white",
    "provider": "dim white",
    "tool": "dim yellow"
})

console = Console(theme=custom_theme)

COMMANDS = [
    ("/model", "Switch models"),
    ("/models", "List available models"),
    ("/providers", "List provider status"),
    ("/keys", "View stored API keys"),
    ("/key set", "Securely store an API key"),
    ("/key delete", "Remove an API key"),
    ("/save", "Save active session"),
    ("/load", "Load session from disk"),
    ("/sessions", "List saved sessions"),
    ("/history", "View conversation history"),
    ("/clear", "Clear session history"),
    ("/persona", "Change agent personality"),
    ("/help", "Show command menu"),
    ("/exit", "Save session and exit")
]

class SlashCommandCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith('/'):
            for cmd, desc in COMMANDS:
                if cmd.startswith(text):
                    yield Completion(
                        cmd, 
                        start_position=-len(text),
                        display=cmd,
                        display_meta=desc
                    )

class PlaceholderProcessor(Processor):
    def apply_transformation(self, ti):
        if not ti.document.text:
            return Transformation([('class:placeholder', 'Ask anything... "Fix broken tests"')])
        return Transformation(ti.fragments)

class Renderer:
    def __init__(self):
        self.console = console
        self.style = PtStyle.from_dict({
            'prompt.left': '#4DAAFB',
            'prompt.input': '#ffffff',
            
            # Premium Unified Box
            'box-bg': 'bg:#141414',
            'box-left': '#4DAAFB bg:#141414',
            
            # Agent States
            'agent-active': '#4DAAFB bg:#141414 bold',
            'agent-inactive': '#555555 bg:#141414',
            
            # Placeholder
            'placeholder': '#555555 italic bg:#141414',
            
            # Typography and accents
            'shortcuts': '#444444',
            'shortcuts.bold': '#666666 bold',
            
            'tip.dot': '#4DAAFB',
            'tip.text': '#444444 bold',
            'tip.main': '#333333',
            
            'corner': '#444444',
            
            # Subtle gradient logo
            'logo.1': '#ffffff',
            'logo.2': '#cccccc',
            'logo.3': '#999999',
            'logo.4': '#666666',
            'logo.5': '#444444',
            
            # Fade animation states
            'fade.0': '#000000',
            'fade.1': '#111111',
            'fade.2': '#333333',
            'fade.3': '#555555',
            
            'completion-menu': 'bg:#1e1e1e #ffffff',
            'completion-menu.completion': 'bg:#1e1e1e #ffffff',
            'completion-menu.completion.current': 'bg:#4DAAFB #000000 bold',
            'completion-menu.meta.completion': 'bg:#1e1e1e #888888',
            'completion-menu.meta.completion.current': 'bg:#4DAAFB #000000',
        })
        self.active_model = "Unknown"
        self.provider = "Unknown"
        self.session = PromptSession(
            lexer=PygmentsLexer(MarkdownLexer),
            completer=SlashCommandCompleter(),
            complete_while_typing=True,
            style=self.style
        )

    def print_dashboard(self, active_model: str):
        pass

    def print_active_header(self, session_id: str):
        header = f"""[dim]~[/dim]"""
        self.console.print(header)

    def print(self, *args, **kwargs):
        self.console.print(*args, **kwargs)

    def print_markdown(self, text: str):
        self.console.print(Markdown(text))

    async def prompt(self, active_model: str, provider: str = "", centered: bool = False) -> str:
        self.active_model = active_model
        self.provider = provider
        
        if not centered:
            prompt_text = [
                ('class:prompt.left', "▌ "),
                ('class:prompt.input', "")
            ]
            try:
                result = await self.session.prompt_async(prompt_text)
                self.console.print("") 
                return result.strip()
            except (KeyboardInterrupt, EOFError):
                return "/exit"

        # -------------------------------------------------------------
        # PERFECT PREMIUM RESPONSIVE DASHBOARD
        # -------------------------------------------------------------
        input_buffer = Buffer(multiline=False, completer=SlashCommandCompleter(), complete_while_typing=True)
        
        kb = KeyBindings()
        @kb.add('enter')
        def _(event):
            event.app.exit(result=input_buffer.text)
            
        @kb.add('c-c')
        def _(event):
            event.app.exit(result='/exit')
            
        @kb.add('c-d')
        def _(event):
            event.app.exit(result='/exit')
            
        # Agent cycling logic
        active_agent_idx = 0
        agents = ["Build", "Big Pickle", "Shade Zen"]
        
        @kb.add('tab')
        def _(event):
            nonlocal active_agent_idx
            active_agent_idx = (active_agent_idx + 1) % len(agents)
            # The subtle selection animation is handled instantly, giving snappy terminal feedback
            event.app.invalidate()

        fade_state = 0

        # 1. Bold, Crisp Pixel Logo
        logo_lines = [
            " ██████  ██   ██  █████  ██████  ███████\n",
            "██       ██   ██ ██   ██ ██   ██ ██     \n",
            "███████  ███████ ███████ ██   ██ █████  \n",
            "     ██  ██   ██ ██   ██ ██   ██ ██     \n",
            "██████   ██   ██ ██   ██ ██████  ███████\n"
        ]
        
        def get_logo_text():
            if fade_state < 4:
                return [ (f'class:fade.{fade_state}', line) for line in logo_lines ]
            return [ (f'class:logo.{i+1}', line) for i, line in enumerate(logo_lines) ]
            
        logo_window = Window(
            content=FormattedTextControl(get_logo_text),
            align=WindowAlign.CENTER,
            height=5,
            dont_extend_height=True
        )

        # 2. Premium Unified Prompt Box Component
        def get_agents_text():
            fragments = []
            for i, agent in enumerate(agents):
                cls = 'class:agent-active' if i == active_agent_idx else 'class:agent-inactive'
                if fade_state < 4:
                    cls = f'class:fade.{fade_state}'
                fragments.append((cls, agent))
                if i < len(agents) - 1:
                    fragments.append(('class:box-bg', "        ")) # Generous spacing
            return fragments

        # The right side of the box containing all inputs and tabs
        box_content = HSplit([
            Window(height=1, style='class:box-bg'), # Top internal padding
            Window(
                content=BufferControl(
                    buffer=input_buffer, 
                    lexer=PygmentsLexer(MarkdownLexer),
                    input_processors=[PlaceholderProcessor()]
                ), 
                style='class:box-bg', 
                height=Dimension(min=1), 
                wrap_lines=True
            ),
            Window(height=1, style='class:box-bg'), # Middle internal padding
            Window(content=FormattedTextControl(get_agents_text), style='class:box-bg', height=1, dont_extend_height=True),
            Window(height=1, style='class:box-bg'), # Bottom internal padding
        ])

        def get_box_left_style():
            if fade_state < 4:
                return f'class:fade.{fade_state}'
            return 'class:box-left'

        # Using char="▌ " guarantees a solid border regardless of dynamic height
        left_border = Window(char="▌ ", width=2, style=get_box_left_style)
        
        unified_box = VSplit([ left_border, box_content ])

        # 3. Shortcuts Component (Moved closer)
        shortcuts = FormattedText([
            ('class:shortcuts.bold', 'ctrl+t'), ('class:shortcuts', ' variants  '),
            ('class:shortcuts.bold', 'tab'), ('class:shortcuts', ' agents  '),
            ('class:shortcuts.bold', 'ctrl+p'), ('class:shortcuts', ' commands')
        ])
        def get_shortcuts_text():
            if fade_state < 4:
                return [ (f'class:fade.{fade_state}', txt) for _, txt in shortcuts ]
            return shortcuts
            
        shortcuts_window = Window(
            content=FormattedTextControl(get_shortcuts_text),
            align=WindowAlign.RIGHT,
            height=1,
            dont_extend_height=True
        )
        
        # 4. Subtle Tip Component
        tip_text = FormattedText([
            ('class:tip.dot', '● '),
            ('class:tip.text', 'Tip '),
            ('class:tip.main', 'Press Tab to cycle between Build and Plan agents')
        ])
        def get_tip_text():
            if fade_state < 4:
                return [ (f'class:fade.{fade_state}', txt) for _, txt in tip_text ]
            return tip_text
            
        tip_window = Window(
            content=FormattedTextControl(get_tip_text),
            align=WindowAlign.CENTER,
            height=1,
            dont_extend_height=True
        )
        
        # 5. Main perfectly proportioned column
        main_column = HSplit([
            Window(height=Dimension(weight=3)), # 30% top padding
            
            logo_window,
            Window(height=2, dont_extend_height=True), # Logo Gap
            
            unified_box,
            
            Window(height=1, dont_extend_height=True), # Tighter Gap (Moved closer)
            shortcuts_window,
            
            Window(height=2, dont_extend_height=True), # Gap
            tip_window,
            
            Window(height=Dimension(weight=7)), # 70% bottom padding
        ], width=80)

        # 6. Global Responsive Layout wrapper
        def get_corner_style():
            if fade_state < 4:
                return f'class:fade.{fade_state}'
            return 'class:corner'
            
        root_container = FloatContainer(
            content=VSplit([
                Window(), 
                main_column,
                Window()  
            ]),
            floats=[
                Float(
                    bottom=0, left=0,
                    content=Window(content=FormattedTextControl(lambda: [(get_corner_style(), '~')]), width=1, height=1)
                ),
                Float(
                    bottom=0, right=0,
                    content=Window(content=FormattedTextControl(lambda: [(get_corner_style(), '1.0.4')]), width=5, height=1)
                )
            ]
        )

        # Focus goes directly to the input field
        layout = Layout(root_container, focused_element=box_content.children[1])
        
        app = Application(
            layout=layout,
            key_bindings=kb,
            style=self.style,
            full_screen=True,
            mouse_support=False,
            cursor=CursorShape.BLOCK
        )
        
        # Fade-in animation task
        async def run_fade_in():
            nonlocal fade_state
            for i in range(5):
                fade_state = i
                app.invalidate()
                await asyncio.sleep(0.04) # 5 steps * 40ms = 200ms total fade in
                
        # Fire and forget the animation
        asyncio.create_task(run_fade_in())
        
        result = await app.run_async()
        
        os.system('cls' if os.name == 'nt' else 'clear')
        self.print_active_header(str(time.time())[-8:])
        
        if result == '/exit' or result is None:
            return '/exit'
        return result.strip()

    def render_message(self, message):
        if message.role == "user":
            lines = message.content.splitlines()
            formatted_lines = [f"[#4DAAFB]▌[/#4DAAFB] {line}" for line in lines]
            self.console.print("\n".join(formatted_lines))
            self.console.print("")
        elif message.role == "assistant":
            self.console.print(Markdown(message.content))
            footer = f"[#4DAAFB]▣[/#4DAAFB] [white]Assistant[/white] [dim]· {self.active_model}[/dim]"
            self.console.print(Padding(footer, (1, 0, 0, 2)))
            self.console.print("")
        elif message.role == "tool":
            content_preview = message.content.strip().splitlines()[0]
            if len(content_preview) > 80:
                content_preview = content_preview[:80] + "..."
            self.console.print(Padding(f"[dim]⚙  {content_preview}[/dim]", (0, 0, 0, 2)))
            self.console.print("")

    def streaming_panel(self, title: str):
        return StreamingPanel(title, self)

class StreamingPanel:
    def __init__(self, title: str, renderer: Renderer):
        self.content = ""
        self.title = title
        self.renderer = renderer
        self.live = Live(
            Markdown("▌"),
            refresh_per_second=15
        )

    def __enter__(self):
        self.live.start()
        return self

    def update(self, chunk: str):
        self.content += chunk
        self.live.update(Markdown(self.content + " ▌"))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.live.stop()
        if self.content:
            self.renderer.console.print(Markdown(self.content))
            footer = f"[#4DAAFB]▣[/#4DAAFB] [white]Assistant[/white] [dim]· {self.renderer.active_model}[/dim]"
            self.renderer.console.print(Padding(footer, (1, 0, 0, 2)))
            self.renderer.console.print("")

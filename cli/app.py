"""Main CLI application."""

from prompt_toolkit import PromptSession
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.theme import Theme

from agents import Runner

from cli.commands import registry, CommandContext
from cli.completer import show_command_menu
from cli_agents.assistant import create_assistant
from mcp_support import MCPManager
from sessions import SessionManager


# Theme
_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green",
    "dim": "dim white",
})

# Prompt style
_prompt_style = Style.from_dict({
    "prompt": "bold #c4a7e7",
})


class App:
    """Main CLI application."""

    def __init__(self):
        self.console = Console(theme=_theme)
        self.session_manager = SessionManager()
        self.mcp_manager = MCPManager()
        self._selected_command: str | None = None
        self._mcp_servers: list = []
        self._mcp_tools: list = []  # Cached MCP tools for /tools command
        self.ctx = CommandContext(self.session_manager, self.console, self._mcp_tools)

        # Key bindings for instant "/" menu
        kb = KeyBindings()

        @kb.add("/", filter=Condition(lambda: True))
        def _(event):
            # Show menu immediately when "/" is pressed on empty input
            if not event.app.current_buffer.text:
                selected = show_command_menu()
                if selected:
                    self._selected_command = selected
                    event.app.current_buffer.text = selected
                    event.app.current_buffer.validate_and_handle()
            else:
                # Normal "/" input if there's already text
                event.app.current_buffer.insert_text("/")

        self.prompt_session = PromptSession(style=_prompt_style, key_bindings=kb)

    def _show_welcome(self) -> None:
        """Display welcome message."""
        session_id = self.session_manager.get_current_session_id()
        self.console.print()
        self.console.print("[bold]Demo CLI Agent[/bold]")
        self.console.print(f"[dim]会话: {session_id} | 输入 / 打开命令菜单[/dim]")

        # Show MCP servers if enabled
        if self._mcp_servers:
            server_names = self.mcp_manager.get_enabled_server_names()
            self.console.print(
                f"[dim]MCP 服务器: {', '.join(server_names)}[/dim]"
            )

    async def _run_agent(self, user_input: str) -> str:
        """Run the agent with user input."""
        agent = create_assistant(mcp_servers=self._mcp_servers if self._mcp_servers else None)
        messages = self.session_manager.get_messages()
        messages.append({"role": "user", "content": user_input})
        result = await Runner.run(agent, messages)
        return result.final_output

    async def _handle_command(self, user_input: str) -> bool:
        """Handle a slash command. Returns True if should exit."""
        cmd = registry.get(user_input)
        if cmd:
            result = cmd.handler(self.ctx)
            return result == "exit"
        else:
            self.console.print(f"[warning]未知命令: {user_input}[/warning]")
            self.console.print("[dim]输入 / 打开命令菜单[/dim]")
            return False

    async def _handle_chat(self, user_input: str) -> None:
        """Handle a chat message."""
        self.session_manager.save_message("user", user_input)

        with self.console.status("[cyan]思考中...[/cyan]", spinner="dots"):
            response = await self._run_agent(user_input)

        self.session_manager.save_message("assistant", response)
        self.console.print()
        self.console.print("[bold]Assistant:[/bold]")
        self.console.print(Markdown(response))

    async def run(self) -> None:
        """Run the main loop."""
        # Load session
        if not self.session_manager.load_latest_session():
            self.session_manager.create_session()

        # Initialize MCP servers
        await self._initialize_mcp_servers()

        self._show_welcome()

        try:
            while True:
                try:
                    self.console.print()
                    user_input = await self.prompt_session.prompt_async(
                        [("class:prompt", "> ")],
                    )
                    user_input = user_input.strip()

                    if not user_input:
                        continue

                    if user_input.startswith("/"):
                        should_exit = await self._handle_command(user_input)
                        if should_exit:
                            break
                    else:
                        await self._handle_chat(user_input)

                except KeyboardInterrupt:
                    self.console.print("\n[dim]再见![/dim]")
                    break
                except EOFError:
                    self.console.print("\n[dim]再见![/dim]")
                    break
                except Exception as e:
                    self.console.print(f"[error]错误: {e}[/error]")
        finally:
            # Cleanup MCP servers on exit
            await self._cleanup_mcp_servers()

    async def _initialize_mcp_servers(self) -> None:
        """Initialize MCP servers from configuration file."""
        if self.mcp_manager.load_config():
            self.console.print("[dim]正在加载 MCP 配置...[/dim]")
            try:
                servers = await self.mcp_manager.initialize_all_servers()
                self._mcp_servers.extend(servers)
                if self._mcp_servers:
                    server_count = len(self._mcp_servers)
                    self.console.print(
                        f"[success]成功加载 {server_count} 个 MCP 服务器[/success]"
                    )
                    # Cache MCP tools for /tools command
                    for server in self._mcp_servers:
                        tools = await server.list_tools()
                        for tool in tools:
                            self._mcp_tools.append(
                                (server.name, tool.name, tool.description)
                            )
            except Exception as e:
                self.console.print(f"[warning]MCP 服务器初始化失败: {e}[/warning]")

    async def _cleanup_mcp_servers(self) -> None:
        """Cleanup MCP servers."""
        if self._mcp_servers:
            await self.mcp_manager.cleanup_servers()
            self._mcp_servers.clear()  # Use clear to keep list reference

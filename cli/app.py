"""Main CLI application."""

from prompt_toolkit import PromptSession
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.theme import Theme

from cli.commands import registry, CommandContext
from cli.completer import show_command_menu
from config import AppConfig
from core import ContextManager, AgentRunner, setup_local_tracing
from core.context_manager import ContextConfig
from extensions.mcp import MCPManager
from tools import registry as tool_registry


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
        self.config = AppConfig.from_env()
        
        # Context management (replaces SessionManager + ContextCompressor)
        self.context_manager = ContextManager(
            config=ContextConfig(
                model=self.config.model_name,
                max_context_tokens=self.config.model_max_context_tokens,
                compression_threshold=self.config.context_compression_threshold,
                keep_last_messages=self.config.context_compression_keep_last_messages,
            )
        )
        
        # Agent runner (handles skills and execution)
        self.agent_runner = AgentRunner(
            context_manager=self.context_manager,
            model=self.config.model_name,
        )
        
        # MCP management
        self.mcp_manager = MCPManager()
        self._mcp_servers: list = []
        self._mcp_tools: list = []  # Cached MCP tools for /tools command
        
        # Command context
        self.ctx = CommandContext(
            self.context_manager._session,  # Pass SessionManager for commands
            self.console, 
            self._mcp_tools
        )
        
        self._selected_command: str | None = None

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
        session_id = self.context_manager.get_session_id()
        self.console.print()
        self.console.print("[bold]Demo CLI Agent[/bold]")
        self.console.print(f"[dim]会话: {session_id} | 输入 / 打开命令菜单[/dim]")

        # Show loaded skills
        available_skills = self.agent_runner.available_skills
        if available_skills:
            skill_names = [s.name for s in available_skills]
            self.console.print(f"[dim]已加载 {len(available_skills)} 个 Skills: {', '.join(skill_names)}[/dim]")

        # Show MCP servers if enabled
        if self._mcp_servers:
            server_names = self.mcp_manager.get_enabled_server_names()
            self.console.print(
                f"[dim]MCP 服务器: {', '.join(server_names)}[/dim]"
            )

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
        self.context_manager.save_message("user", user_input)

        # Show activated skills
        activated_skills = self.agent_runner.get_activated_skills(user_input)
        if activated_skills:
            self.console.print(f"[dim]🔧 激活 Skills: {', '.join(activated_skills)}[/dim]")

        with self.console.status("[cyan]思考中...[/cyan]", spinner="dots"):
            response = await self.agent_runner.run(user_input)

        self.context_manager.save_message("assistant", response.content)
        if response.prompt_tokens is not None:
            self.context_manager.set_last_prompt_tokens(response.prompt_tokens)
        
        self.console.print()
        self.console.print("[bold]Assistant:[/bold]")
        self.console.print(Markdown(response.content))
        
        await self.context_manager.maybe_compress()

    async def run(self) -> None:
        """Run the main loop."""
        # Setup local tracing if enabled
        import os
        if os.getenv("ENABLE_TRACING", "").lower() in ("1", "true", "yes"):
            verbose = os.getenv("TRACING_VERBOSE", "").lower() in ("1", "true", "yes")
            log_to_file = os.getenv("TRACING_LOG_TO_FILE", "").lower() in ("1", "true", "yes")
            setup_local_tracing(
                log_to_console=True,
                log_to_file=log_to_file,
                verbose=verbose,
            )
            self.console.print("[dim]🔍 本地追踪已启用[/dim]")
        
        # Load session
        self.context_manager.load_or_create_session()

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
                    # Update agent runner with MCP servers
                    self.agent_runner.set_mcp_servers(self._mcp_servers)
            except Exception as e:
                self.console.print(f"[warning]MCP 服务器初始化失败: {e}[/warning]")
        tool_registry.register_mcp_tools(self._mcp_tools)

    async def _cleanup_mcp_servers(self) -> None:
        """Cleanup MCP servers."""
        if self._mcp_servers:
            await self.mcp_manager.cleanup_servers()
            self._mcp_servers.clear()  # Use clear to keep list reference

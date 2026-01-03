"""Command registry and built-in commands."""

from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

from rich.console import Console
from tools.file_tools import BUILTIN_TOOL_DESCRIPTIONS

if TYPE_CHECKING:
    from sessions import SessionManager


@dataclass
class CommandContext:
    """Context passed to command handlers."""
    session_manager: "SessionManager"
    console: Console
    mcp_tools: list = None  # Cached MCP tools list [(server_name, tool_name, description), ...]


@dataclass
class Command:
    """A registered command."""
    name: str
    description: str
    handler: Callable[[CommandContext], str | None]


class CommandRegistry:
    """Registry for slash commands."""

    def __init__(self):
        self._commands: dict[str, Command] = {}

    def register(self, name: str, description: str):
        """Decorator to register a command.

        Usage:
            @registry.register("/help", "显示帮助信息")
            def cmd_help(ctx: CommandContext) -> str | None:
                ...
        """
        def decorator(func: Callable[[CommandContext], str | None]):
            self._commands[name] = Command(name, description, func)
            return func
        return decorator

    def get(self, name: str) -> Command | None:
        """Get a command by name."""
        return self._commands.get(name.lower())

    def all(self) -> list[Command]:
        """Get all registered commands."""
        return list(self._commands.values())


# Global registry
registry = CommandRegistry()


# Built-in commands

@registry.register("/help", "显示帮助信息")
def cmd_help(ctx: CommandContext) -> None:
    """Display available commands."""
    ctx.console.print()
    ctx.console.print("[bold]可用命令:[/bold]")
    for cmd in registry.all():
        ctx.console.print(f"  [cyan]{cmd.name:<12}[/cyan] {cmd.description}")
    ctx.console.print()
    ctx.console.print("[dim]直接输入问题与 AI 助手对话，输入 / 可触发命令补全[/dim]")


@registry.register("/tools", "显示可用工具")
def cmd_tools(ctx: CommandContext) -> None:
    """Display available tools."""
    builtin_tools = BUILTIN_TOOL_DESCRIPTIONS
    ctx.console.print()
    ctx.console.print("[bold]内置工具:[/bold]")
    for name, desc in builtin_tools:
        ctx.console.print(f"  [cyan]{name:<20}[/cyan] {desc}")

    # Show MCP tools if available (cached during initialization)
    if ctx.mcp_tools:
        current_server = None
        for server_name, tool_name, description in ctx.mcp_tools:
            if server_name != current_server:
                ctx.console.print()
                ctx.console.print(f"[bold]MCP 工具 ({server_name}):[/bold]")
                current_server = server_name
            desc = description[:40] + "..." if len(description) > 40 else description
            ctx.console.print(f"  [green]{tool_name:<20}[/green] {desc}")

    ctx.console.print()
    ctx.console.print("[dim]所有文件操作限制在当前工作目录内[/dim]")


@registry.register("/clear", "清除上下文，创建新会话")
def cmd_clear(ctx: CommandContext) -> None:
    """Clear session and create a new one."""
    new_session_id = ctx.session_manager.clear_session()
    ctx.console.print(f"[success]已创建新会话: {new_session_id}[/success]")


@registry.register("/session", "显示当前会话 ID")
def cmd_session(ctx: CommandContext) -> None:
    """Display current session ID."""
    session_id = ctx.session_manager.get_current_session_id()
    ctx.console.print(f"[dim]当前会话: {session_id}[/dim]")


@registry.register("/mcp", "查看 MCP 服务器和工具")
def cmd_mcp(ctx: CommandContext) -> None:
    """Show MCP servers and their tools."""
    from simple_term_menu import TerminalMenu

    if not ctx.mcp_tools:
        ctx.console.print("[warning]没有加载任何 MCP 服务器[/warning]")
        ctx.console.print("[dim]请在项目目录下创建 demo.mcp.json 配置文件[/dim]")
        return

    # Group tools by server name
    servers: dict[str, list[tuple[str, str]]] = {}
    for server_name, tool_name, description in ctx.mcp_tools:
        if server_name not in servers:
            servers[server_name] = []
        servers[server_name].append((tool_name, description))

    server_names = list(servers.keys())

    if len(server_names) == 1:
        # Only one server, show tools directly
        selected_server = server_names[0]
    else:
        # Multiple servers, let user choose
        menu = TerminalMenu(
            server_names,
            title="选择 MCP 服务器",
            menu_cursor="› ",
            menu_cursor_style=("fg_purple", "bold"),
            menu_highlight_style=("fg_purple",),
            cycle_cursor=True,
            clear_screen=False,
        )
        choice = menu.show()
        if choice is None:
            return
        selected_server = server_names[choice]

    # Show tools for selected server
    tools = servers[selected_server]
    ctx.console.print()
    ctx.console.print(f"[bold]{selected_server}[/bold] - {len(tools)} 个工具")
    ctx.console.print()

    for tool_name, description in tools:
        ctx.console.print(f"  [green]{tool_name}[/green]")
        # Wrap description nicely
        desc_lines = description.split('\n')
        for line in desc_lines[:3]:  # Show first 3 lines
            if line.strip():
                ctx.console.print(f"    [dim]{line.strip()}[/dim]")
        if len(desc_lines) > 3:
            ctx.console.print(f"    [dim]...[/dim]")
        ctx.console.print()


@registry.register("/exit", "退出程序")
def cmd_exit(ctx: CommandContext) -> str:
    """Exit the program."""
    ctx.console.print("[dim]再见![/dim]")
    return "exit"

"""Command registry and built-in commands."""

from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from sessions import SessionManager


@dataclass
class CommandContext:
    """Context passed to command handlers."""
    session_manager: "SessionManager"
    console: Console


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
    tools = [
        ("read_file", "读取文件内容"),
        ("write_file", "写入/创建文件"),
        ("list_directory", "列出目录内容"),
        ("delete_file", "删除文件"),
        ("file_exists", "检查文件是否存在"),
    ]
    ctx.console.print()
    ctx.console.print("[bold]可用工具:[/bold]")
    for name, desc in tools:
        ctx.console.print(f"  [cyan]{name:<16}[/cyan] {desc}")
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


@registry.register("/exit", "退出程序")
def cmd_exit(ctx: CommandContext) -> str:
    """Exit the program."""
    ctx.console.print("[dim]再见![/dim]")
    return "exit"

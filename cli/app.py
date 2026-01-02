"""Main CLI application."""

from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.theme import Theme

from agents import Runner

from cli.commands import registry, CommandContext
from cli.completer import SlashCommandSuggest
from cli_agents.assistant import create_assistant
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
    "prompt": "bold #7aa2f7",
    "auto-suggestion": "#565f89",  # Gray inline hint
})


class App:
    """Main CLI application."""

    def __init__(self):
        self.console = Console(theme=_theme)
        self.session_manager = SessionManager()
        self.ctx = CommandContext(self.session_manager, self.console)
        self.prompt_session = PromptSession(
            auto_suggest=SlashCommandSuggest(),
            style=_prompt_style,
        )

    def _show_welcome(self) -> None:
        """Display welcome message."""
        session_id = self.session_manager.get_current_session_id()
        self.console.print()
        self.console.print("[bold]Demo CLI Agent[/bold]")
        self.console.print(f"[dim]会话: {session_id} | 输入 /help 查看帮助[/dim]")

    async def _run_agent(self, user_input: str) -> str:
        """Run the agent with user input."""
        agent = create_assistant()
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
            self.console.print("[dim]输入 /help 查看可用命令[/dim]")
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
        if not self.session_manager.load_latest_session():
            self.session_manager.create_session()

        self._show_welcome()

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

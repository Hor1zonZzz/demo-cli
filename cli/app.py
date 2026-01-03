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
from cli_agents.assistant import create_assistant, ASSISTANT_INSTRUCTIONS
from sessions import SessionManager
from skills import SkillScanner, SkillLoader, SkillMatcher, SkillInjector


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
        self.ctx = CommandContext(self.session_manager, self.console)
        self._selected_command: str | None = None

        # Skills progressive loading (Level 1: Metadata)
        self.skill_scanner = SkillScanner()
        self.skill_loader = SkillLoader()
        self.skill_matcher = SkillMatcher()
        self.skill_injector = SkillInjector()
        self.available_skills = self.skill_scanner.scan_skills_directory()

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

        # Show loaded skills
        if self.available_skills:
            skill_names = [s.name for s in self.available_skills]
            self.console.print(f"[dim]已加载 {len(self.available_skills)} 个 Skills: {', '.join(skill_names)}[/dim]")

    async def _run_agent(self, user_input: str) -> str:
        """Run the agent with user input."""
        # Level 2: Match and load relevant skills
        matched_skills = self.skill_matcher.match_skills(user_input, self.available_skills)

        # Build enhanced instructions
        enhanced_instructions = ASSISTANT_INSTRUCTIONS

        # Always inject Level 1 metadata summary
        if self.available_skills:
            enhanced_instructions = self.skill_injector.inject_metadata_summary(
                enhanced_instructions, self.available_skills
            )

        # Inject Level 2 full instructions for matched skills
        if matched_skills:
            skills_with_content = []
            for skill_meta in matched_skills:
                skill_content = self.skill_loader.load_skill_instructions(skill_meta)
                if skill_content:
                    skills_with_content.append((skill_meta, skill_content))

            if skills_with_content:
                enhanced_instructions = self.skill_injector.inject_multiple_skills(
                    enhanced_instructions, skills_with_content
                )
                # Show which skills were activated
                activated_names = [s[0].name for s in skills_with_content]
                self.console.print(f"[dim]🔧 激活 Skills: {', '.join(activated_names)}[/dim]")

        # Create agent with enhanced instructions
        agent = create_assistant(enhanced_instructions=enhanced_instructions)
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

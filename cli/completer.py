"""Command completer for prompt_toolkit."""

from prompt_toolkit.completion import Completer, Completion

from cli.commands import registry


class SlashCommandCompleter(Completer):
    """Completer for slash commands with styled dropdown menu."""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # Show all commands when just "/" is typed
        if text == "/":
            for cmd in registry.all():
                yield Completion(
                    cmd.name,
                    start_position=-1,
                    display=cmd.name,
                    display_meta=cmd.description,
                )
        # Filter commands as user types more
        elif text.startswith("/"):
            partial = text.lower()
            for cmd in registry.all():
                if cmd.name.startswith(partial):
                    yield Completion(
                        cmd.name,
                        start_position=-len(text),
                        display=cmd.name,
                        display_meta=cmd.description,
                    )

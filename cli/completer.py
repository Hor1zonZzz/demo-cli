"""Command completer for prompt_toolkit."""

from prompt_toolkit.completion import Completer, Completion

from cli.commands import registry


class SlashCommandCompleter(Completer):
    """Completer for slash commands."""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        if text.startswith("/"):
            partial = text.lower()

            for cmd in registry.all():
                if cmd.name.startswith(partial):
                    yield Completion(
                        cmd.name,
                        start_position=-len(text),
                        display=cmd.name,
                        display_meta=cmd.description,
                    )

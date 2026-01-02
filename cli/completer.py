"""Command completer and auto-suggest for prompt_toolkit."""

from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion

from cli.commands import registry


class SlashCommandSuggest(AutoSuggest):
    """Auto-suggest for slash commands (inline gray hint)."""

    def get_suggestion(self, buffer, document):
        text = document.text

        if text.startswith("/"):
            partial = text.lower()

            for cmd in registry.all():
                if cmd.name.startswith(partial) and cmd.name != partial:
                    # Return the remaining part as suggestion
                    return Suggestion(cmd.name[len(text):])

        return None

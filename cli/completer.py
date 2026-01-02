"""Command selector using simple-term-menu."""

from simple_term_menu import TerminalMenu

from cli.commands import registry


def show_command_menu() -> str | None:
    """Show interactive command menu and return selected command."""
    commands = registry.all()

    # Format: "/help  显示帮助信息"
    menu_entries = [f"{cmd.name}  [dim]{cmd.description}[/dim]" for cmd in commands]

    menu = TerminalMenu(
        menu_entries,
        title="Commands",
        menu_cursor="❯ ",
        menu_cursor_style=("fg_purple", "bold"),
        menu_highlight_style=("fg_purple", "bold"),
        search_key=None,  # Disable search, let user type to filter
        cycle_cursor=True,
        clear_screen=False,
    )

    choice = menu.show()

    if choice is not None:
        return commands[choice].name
    return None

# CLAUDE.md - AI Assistant Guide for Demo CLI

This document provides comprehensive guidance for AI assistants working on the Demo CLI codebase.

## Project Overview

Demo CLI is a command-line AI assistant built with Python that provides file operation capabilities through an interactive chat interface. The project uses:

- **Language**: Python 3.13+
- **Framework**: OpenAI Agents SDK with LiteLLM support
- **LLM Provider**: DeepSeek API (configurable)
- **UI Library**: prompt-toolkit, Rich, simple-term-menu
- **Session Persistence**: JSON file-based storage
- **Package Manager**: uv (recommended) or pip/pipx

## Codebase Structure

```
demo-cli/
├── main.py                 # Entry point and DeepSeek client setup
├── pyproject.toml          # Project configuration and dependencies
├── README.md               # User-facing documentation
├── cli/                    # CLI interface layer
│   ├── __init__.py        # Exports App class
│   ├── app.py             # Main application loop and UI logic
│   ├── commands.py        # Command registry and built-in commands
│   └── completer.py       # Interactive command menu
├── cli_agents/            # Agent definitions
│   ├── __init__.py
│   └── assistant.py       # CLI assistant agent configuration
├── sessions/              # Session management
│   ├── __init__.py
│   └── manager.py         # SessionManager class for persistence
└── tools/                 # Agent function tools
    ├── __init__.py        # Tool exports
    └── file_tools.py      # File operation tools (sandboxed)
```

## Key Architecture Patterns

### 1. Layered Architecture

The codebase follows a clear separation of concerns:

- **Entry Point** (`main.py`): Environment setup, client configuration
- **UI Layer** (`cli/`): User interaction, command handling, display
- **Agent Layer** (`cli_agents/`): AI agent configuration and instructions
- **Business Logic** (`tools/`): Core functionality (file operations)
- **Persistence** (`sessions/`): State management and data storage

### 2. OpenAI Agents SDK Integration

The project uses the OpenAI Agents SDK pattern:

```python
from agents import Agent, Runner, function_tool

# Define tools with @function_tool decorator
@function_tool
def read_file(path: str) -> str:
    """Read file contents."""
    ...

# Create agent with tools
agent = Agent(
    name="CLI Assistant",
    instructions="System instructions...",
    model="deepseek-chat",
    tools=[read_file, write_file, ...]
)

# Run agent with message history
result = await Runner.run(agent, messages)
```

### 3. Command Pattern

Slash commands use a registry pattern for extensibility:

```python
from cli.commands import registry, CommandContext

@registry.register("/mycommand", "Description")
def cmd_mycommand(ctx: CommandContext) -> str | None:
    # Return "exit" to exit app, None to continue
    ctx.console.print("Output")
    return None
```

### 4. Security Model

All file operations are sandboxed to the working directory:

```python
def _is_safe_path(path: str, base_dir: Path) -> bool:
    """Ensure path is within base_dir."""
    resolved = Path(path).resolve()
    return str(resolved).startswith(str(base_dir.resolve()))
```

## Development Workflows

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/Hor1zonZzz/demo-cli.git
cd demo-cli

# Create .env file
echo "DEEPSEEK_API_KEY=your_key_here" > .env

# Install with uv
uv sync

# Run locally
uv run demo-cli
```

### Installation Methods

1. **uv (recommended)**: `uv tool install git+https://github.com/Hor1zonZzz/demo-cli.git`
2. **pipx**: `pipx install git+https://github.com/Hor1zonZzz/demo-cli.git`
3. **pip**: `pip install git+https://github.com/Hor1zonZzz/demo-cli.git`

### Package Configuration

The project uses Hatchling as build backend (`pyproject.toml`):

```toml
[project.scripts]
demo-cli = "main:main"  # CLI entry point

[tool.hatch.build.targets.wheel]
packages = ["cli", "cli_agents", "sessions", "tools"]
include = ["main.py"]
```

## File Organization Conventions

### Module Naming

- `cli/`: User interface components (prefix `cli_`)
- `cli_agents/`: AI agent definitions (not CLI-related despite name)
- `tools/`: Reusable function tools for agents
- `sessions/`: Data persistence layer

### Import Style

```python
# Standard library
import os
from pathlib import Path

# Third-party
from agents import Agent, function_tool
from rich.console import Console

# Local
from cli.commands import registry
from tools import read_file
```

### File Headers

All modules include docstrings:

```python
"""Brief module description."""
```

## Key Components Deep Dive

### 1. Application Loop (`cli/app.py`)

**App Class Responsibilities:**
- Initialize Rich console with custom theme
- Set up prompt-toolkit session with key bindings
- Manage main event loop (REPL)
- Route input to commands or agent
- Display agent responses with Markdown rendering

**Key Features:**
- Instant "/" key triggers command menu (no Enter needed)
- Async/await throughout for agent calls
- Exception handling for KeyboardInterrupt/EOFError
- Status spinner during agent thinking

**Entry Flow:**
```
App.run() → load_latest_session() → show_welcome() → main loop:
  → prompt_async() → handle_command() OR handle_chat()
    → _run_agent() → Runner.run() → save_message()
```

### 2. Agent Configuration (`cli_agents/assistant.py`)

**Important Notes:**
- Instructions are in Chinese (target user base)
- Model defaults to "deepseek-chat"
- All tools are file operations (sandboxed)

**Instruction Guidelines:**
- Emphasize security (sandboxing, delete confirmation)
- Request clarification for unclear requests
- Maintain friendly, concise tone

### 3. Tool Implementation (`tools/file_tools.py`)

**All tools follow this pattern:**

```python
@function_tool
def tool_name(param: str) -> str:
    """Docstring becomes tool description for LLM.

    Args:
        param: Parameter description (visible to LLM)

    Returns:
        Success message or error description
    """
    try:
        # Normalize path
        file_path = Path(param)
        if not file_path.is_absolute():
            file_path = WORKING_DIR / file_path

        # Security check
        if not _is_safe_path(str(file_path), WORKING_DIR):
            return f"错误: 无法访问工作目录外的文件: {param}"

        # Perform operation
        # ...

        return "成功: ..."
    except PermissionError:
        return f"错误: 没有权限: {param}"
    except Exception as e:
        return f"错误: {e}"
```

**Key Patterns:**
- Always return `str` (never raise exceptions to agent)
- Chinese error messages
- Validate paths before operations
- Create parent directories for write operations
- Skip hidden files in directory listings

### 4. Session Management (`sessions/manager.py`)

**SessionManager Responsibilities:**
- Generate 8-character UUIDs for sessions
- Store sessions as JSON in `data/sessions/`
- Auto-load latest session on startup
- Persist messages with timestamps

**Message Format:**
```json
{
  "session_id": "a1b2c3d4",
  "created_at": "2026-01-03T10:30:00",
  "messages": [
    {
      "role": "user",
      "content": "Message text",
      "timestamp": "2026-01-03T10:30:05"
    }
  ]
}
```

**API for Agents:**
```python
manager.get_messages()  # Returns simplified format for agent
# [{"role": "user", "content": "..."}]  # No timestamps
```

### 5. Command System (`cli/commands.py`)

**Adding New Commands:**

```python
@registry.register("/newcmd", "Description in Chinese")
def cmd_newcmd(ctx: CommandContext) -> str | None:
    """Command implementation."""
    # Access session: ctx.session_manager
    # Print output: ctx.console.print("[bold]Text[/bold]")
    # Return "exit" to quit app, None to continue
    return None
```

**Built-in Commands:**
- `/help`: Show all commands
- `/tools`: List agent tools
- `/clear`: Create new session
- `/session`: Show current session ID
- `/exit`: Quit application

### 6. Command Menu (`cli/completer.py`)

Uses `simple-term-menu` for interactive selection:

```python
def show_command_menu() -> str | None:
    """Returns selected command or None if cancelled."""
```

**Styling:**
- Purple cursor and highlights
- Minimal, clean interface
- No screen clearing (inline display)

## Coding Conventions

### Type Hints

- Use modern Python 3.13 syntax: `list[str]`, `dict[str, int]`
- Use `| None` instead of `Optional`
- Use `TYPE_CHECKING` for circular imports

### Error Handling

**In Tools:**
```python
# Return error messages, don't raise
return f"错误: {description}"
```

**In CLI Code:**
```python
# Catch and display errors
try:
    # operation
except Exception as e:
    self.console.print(f"[error]错误: {e}[/error]")
```

### Async/Await

- Agent calls are async: `await Runner.run()`
- UI prompts are async: `await prompt_session.prompt_async()`
- Command handlers are sync (for simplicity)

### Rich Styling

**Theme Colors:**
```python
"info": "cyan"      # Informational messages
"warning": "yellow" # Warnings
"error": "red bold" # Errors
"success": "green"  # Success messages
"dim": "dim white"  # Secondary info
```

**Usage:**
```python
console.print("[bold]Heading[/bold]")
console.print("[cyan]Highlighted[/cyan]")
console.print(Markdown("**Bold** markdown"))
```

### Chinese Localization

All user-facing strings are in Chinese:
- Error messages: "错误: ..."
- Success messages: "成功: ..."
- UI prompts: "输入 / 打开命令菜单"

## Working with the Agent

### Agent Instructions (`ASSISTANT_INSTRUCTIONS`)

When modifying agent behavior:

1. Keep instructions concise (current ~150 Chinese characters)
2. List tools explicitly with descriptions
3. Emphasize security constraints
4. Remind about confirmation for destructive operations
5. Encourage clarification questions

### Tool Design Principles

1. **Descriptive Docstrings**: First line becomes tool description
2. **Error Messages in Returns**: Never raise exceptions
3. **Sandbox Everything**: Use `_is_safe_path()` check
4. **Relative Path Support**: Convert to absolute internally
5. **User-Friendly Output**: Format sizes, use emojis (📁/📄)

### Testing Tools Manually

```python
# In Python REPL with uv run
from tools import read_file, list_directory
print(read_file("README.md"))
print(list_directory("."))
```

## Session Management Behavior

### Auto-Resume

On startup, the app automatically loads the most recent session:

```python
if not self.session_manager.load_latest_session():
    self.session_manager.create_session()
```

### Session Persistence

Sessions are saved after every message exchange:

```python
self.session_manager.save_message("user", user_input)
# ... agent runs ...
self.session_manager.save_message("assistant", response)
```

### Session Files Location

- Default: `data/sessions/*.json` (relative to working directory)
- Each session: `{session_id}.json` (8-char UUID)

## Common Development Tasks

### Adding a New Tool

1. Create function in `tools/file_tools.py`:
```python
@function_tool
def new_tool(param: str) -> str:
    """Tool description for LLM."""
    # Implementation with safety checks
    return "成功: ..."
```

2. Export in `tools/__init__.py`:
```python
from .file_tools import new_tool
__all__ = [..., "new_tool"]
```

3. Add to agent in `cli_agents/assistant.py`:
```python
tools=[..., new_tool]
```

4. Update `/tools` command in `cli/commands.py`

### Adding a New Slash Command

1. Register in `cli/commands.py`:
```python
@registry.register("/mycmd", "命令描述")
def cmd_mycmd(ctx: CommandContext) -> str | None:
    ctx.console.print("Output")
    return None
```

2. Command automatically appears in `/` menu

### Changing the LLM Provider

Modify `main.py`:

```python
def setup_client() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = "https://api.openai.com/v1"  # or other provider

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    set_default_openai_client(client)
```

Update model in `cli_agents/assistant.py`:
```python
def create_assistant(model: str = "gpt-4o") -> Agent:
```

### Customizing UI Theme

Edit theme in `cli/app.py`:

```python
_theme = Theme({
    "info": "blue",      # Change colors
    "success": "green",
    # Add new styles
    "custom": "magenta bold"
})
```

Usage:
```python
console.print("[custom]Custom styled text[/custom]")
```

## Important Implementation Notes

### Path Handling

Always use `Path` objects from `pathlib`:

```python
from pathlib import Path

# Good
file_path = Path(user_input)
if file_path.exists():
    ...

# Avoid
if os.path.exists(user_input):  # Old style
```

### Working Directory

`WORKING_DIR` in `tools/file_tools.py` is set to `Path.cwd()`:
- This is the directory where user runs `demo-cli`
- NOT the installation directory
- All file operations are relative to this directory

### Agent SDK Imports

The project imports from `agents` package (OpenAI Agents SDK):

```python
from agents import Agent, Runner, function_tool
from agents import set_default_openai_client, set_default_openai_api
```

**Not to be confused with** `cli_agents/` directory (local agent definitions).

### Async Patterns

The app uses asyncio throughout:

```python
# main.py
def main() -> None:
    setup_deepseek_client()
    app = App()
    asyncio.run(app.run())  # Entry point

# cli/app.py
async def run(self) -> None:
    while True:
        user_input = await self.prompt_session.prompt_async(...)
        response = await self._run_agent(user_input)
```

### Key Binding for Slash Menu

The `/` key is intercepted only when the input buffer is empty:

```python
@kb.add("/", filter=Condition(lambda: True))
def _(event):
    if not event.app.current_buffer.text:
        # Show menu
    else:
        # Normal "/" input
```

This allows:
- Empty input + `/` → Opens menu
- Existing text + `/` → Types "/" character

## Testing and Debugging

### Running Locally

```bash
uv run demo-cli
# Or with custom .env location
DEEPSEEK_API_KEY=... uv run demo-cli
```

### Debug Mode

Add debug prints in code:

```python
import sys
print(f"DEBUG: {variable}", file=sys.stderr)
```

### Session Inspection

View session files:

```bash
cat data/sessions/*.json | jq .
```

### Testing Tool Safety

```python
# Test path traversal prevention
from tools.file_tools import _is_safe_path
from pathlib import Path

base = Path("/home/user/demo-cli")
print(_is_safe_path("../etc/passwd", base))  # False
print(_is_safe_path("README.md", base))      # True
```

## Git Workflow

### Branch Naming

Follow the pattern: `claude/{feature-description}-{session-id}`

Example: `claude/add-new-tool-Ahzbn`

### Commit Messages

Use conventional commit style:

```
feat: Add new file search tool
fix: Prevent path traversal in read_file
docs: Update CLAUDE.md with testing guide
refactor: Simplify session manager API
```

### Development Branch

All changes should be developed on feature branches:

```bash
git checkout -b claude/feature-name-xyz
# Make changes
git add .
git commit -m "feat: Description"
git push -u origin claude/feature-name-xyz
```

## Dependencies Overview

### Core Dependencies

- `openai>=2.14.0`: OpenAI client (used for DeepSeek)
- `openai-agents[litellm]>=0.6.4`: Agent framework with LiteLLM
- `prompt-toolkit>=3.0.52`: Interactive CLI prompts
- `python-dotenv>=1.2.1`: Environment variable loading
- `rich>=14.2.0`: Terminal formatting and rendering
- `simple-term-menu>=1.6.6`: Interactive menu selection

### Why These Choices

- **OpenAI Agents SDK**: Official framework for function calling agents
- **LiteLLM**: Enables using non-OpenAI providers (DeepSeek)
- **prompt-toolkit**: Powerful async REPL with key binding support
- **Rich**: Beautiful terminal output with Markdown rendering
- **simple-term-menu**: Minimal, keyboard-driven menu interface

## Security Considerations

### Sandboxing

All file operations are restricted to working directory:

```python
# This prevents:
read_file("../../../etc/passwd")  # Returns error
read_file("/etc/hosts")           # Returns error

# These work:
read_file("README.md")            # OK
read_file("subdir/file.txt")      # OK
```

### No Remote Code Execution

The agent has NO tools for:
- Running shell commands
- Installing packages
- Network operations
- System modifications

Only file operations within working directory are allowed.

### Environment Variables

Sensitive data in `.env` file:

```bash
DEEPSEEK_API_KEY=sk-...  # Never commit this
```

Add to `.gitignore`:
```
.env
data/sessions/  # Session history may contain sensitive info
```

## Future Enhancement Areas

### Potential Improvements

1. **More Tools**: Git operations, search, grep, diff
2. **Multi-Model Support**: Switch models within session
3. **Session Export**: Export conversations to Markdown
4. **Undo/Redo**: For file operations
5. **Syntax Highlighting**: For code in agent responses
6. **Token Usage Tracking**: Display API costs
7. **Session Search**: Search across past conversations

### Extensibility Points

The architecture supports easy extension:

- **New tools**: Add to `tools/` directory
- **New commands**: Register in `cli/commands.py`
- **New agents**: Create in `cli_agents/` directory
- **Custom themes**: Modify Rich theme in `cli/app.py`

## Troubleshooting Guide

### Common Issues

**"错误: 未设置 DEEPSEEK_API_KEY 环境变量"**
- Create `.env` file with `DEEPSEEK_API_KEY=...`
- Or set environment variable before running

**Agent not responding:**
- Check network connection to DeepSeek API
- Verify API key is valid
- Check for API rate limits

**File operation errors:**
- Ensure files are within working directory
- Check file permissions
- Verify file paths are correct

**Import errors:**
- Run `uv sync` to install dependencies
- Ensure Python 3.13+ is installed

## Best Practices for AI Assistants

When working on this codebase:

1. **Read Before Modifying**: Always read existing files before making changes
2. **Follow Patterns**: Match existing code style and architecture
3. **Test Safety**: Verify path sandboxing for any file operations
4. **Localize**: Use Chinese for user-facing messages
5. **Document**: Update this file when adding major features
6. **Type Hints**: Always include type annotations
7. **Error Handling**: Return errors as strings in tools, catch in UI
8. **Async Consistency**: Use async/await for agent interactions

## Quick Reference

### File Locations

- Entry point: `main.py`
- Main loop: `cli/app.py`
- Agent config: `cli_agents/assistant.py`
- Tools: `tools/file_tools.py`
- Commands: `cli/commands.py`
- Sessions: `sessions/manager.py`
- Config: `pyproject.toml`

### Key Functions

- `main()`: App entry point
- `App.run()`: Main event loop
- `create_assistant()`: Agent factory
- `Runner.run(agent, messages)`: Execute agent
- `registry.register()`: Add slash command
- `@function_tool`: Decorator for agent tools

### Import Shortcuts

```python
from cli import App
from tools import read_file, write_file, list_directory
from cli.commands import registry, CommandContext
from cli_agents.assistant import create_assistant
from sessions import SessionManager
```

---

**Document Version**: 1.0
**Last Updated**: 2026-01-03
**Maintainer**: Demo CLI Project

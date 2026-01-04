# CLAUDE.md - AI Assistant Guide for Demo CLI

This document provides comprehensive guidance for AI assistants working on the Demo CLI codebase.

## Project Overview

Demo CLI is a command-line AI assistant built with Python that provides file operation capabilities through an interactive chat interface. The project uses:

- **Language**: Python 3.13+
- **Framework**: OpenAI Agents SDK with LiteLLM support
- **LLM Provider**: DeepSeek API (configurable)
- **UI Library**: prompt-toolkit, Rich, simple-term-menu
- **Session Persistence**: JSON file-based storage with automatic compression
- **Extensions**: MCP (Model Context Protocol), Skills system
- **Package Manager**: uv (recommended) or pip/pipx

## Codebase Structure

```
demo-cli/
├── main.py                     # Entry point and DeepSeek client setup
├── config.py                   # Application configuration from environment
├── pyproject.toml              # Project configuration and dependencies
├── README.md                   # User-facing documentation
├── demo.mcp.json              # MCP server configuration (optional)
├── .demo-cli/                  # User-level configuration
│   └── skills/                 # Skills directory
│       ├── README.md           # Skills documentation
│       ├── file-analyzer/      # Example skill
│       │   ├── SKILL.md        # Skill definition
│       │   └── examples.md     # Usage examples
│       └── code-reviewer/      # Example skill
│           └── SKILL.md
├── cli/                        # CLI interface layer
│   ├── __init__.py            # Exports App class
│   ├── app.py                 # Main application loop and UI logic
│   ├── commands.py            # Command registry and built-in commands
│   └── completer.py           # Interactive command menu
├── core/                       # Core business logic layer (NEW)
│   ├── __init__.py
│   ├── agent_runner.py        # Agent execution with skills enhancement
│   ├── context_manager.py     # Unified context and compression management
│   └── tracing.py             # Local tracing for debugging
├── demo_agents/                # Agent definitions (RENAMED from cli_agents)
│   ├── __init__.py
│   ├── assistant.py           # CLI assistant agent configuration
│   └── summarizer.py          # Context summarization agent
├── extensions/                 # Extension systems (NEW)
│   ├── __init__.py
│   ├── mcp/                   # MCP integration (MOVED from mcp_support)
│   │   ├── __init__.py        # Exports MCPManager
│   │   └── manager.py         # MCP configuration and server management
│   └── skills/                # Skills system (NEW)
│       ├── __init__.py        # Exports all skill components
│       ├── scanner.py         # Skill discovery and metadata parsing
│       ├── loader.py          # Skill content loading
│       ├── matcher.py         # User input matching
│       └── injector.py        # Instruction injection
├── sessions/                   # Session management
│   ├── __init__.py
│   ├── manager.py             # SessionManager class for persistence
│   └── compression.py         # Context compression (NEW)
├── tools/                      # Agent function tools
│   ├── __init__.py            # Tool exports
│   ├── registry.py            # Unified tool registry (NEW)
│   └── file_tools.py          # File operation tools (sandboxed)
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_mcp_integration.py
│   └── test_skills.py
└── docs/                       # Documentation
    ├── CHANGELOG.md
    └── SKILLS_DESIGN.md       # Skills system design document
```

## Key Architecture Patterns

### 1. Modular Layered Architecture

The codebase follows a refined separation of concerns:

- **Entry Point** (`main.py`): Environment setup, client configuration
- **Configuration** (`config.py`): Environment-based configuration management
- **UI Layer** (`cli/`): User interaction, command handling, display
- **Core Layer** (`core/`): Business logic for agent execution, context management, tracing
- **Agent Layer** (`demo_agents/`): AI agent definitions and instructions
- **Extensions** (`extensions/`): Pluggable systems (MCP, Skills)
- **Business Logic** (`tools/`): Core functionality (file operations)
- **Persistence** (`sessions/`): State management and data storage

### 2. Skills System - Progressive Loading

**Three-Level Loading Architecture:**

**Level 1: Metadata Loading (~100 tokens total)**
- Triggered: Application startup
- Loads: Skill names and descriptions from YAML frontmatter
- Purpose: Lightweight awareness of available skills

**Level 2: Full Instructions Loading (up to 5000 tokens per skill)**
- Triggered: User input semantically matches skill description
- Loads: Complete SKILL.md markdown content
- Purpose: Inject detailed instructions when relevant

**Level 3: Resources Loading (future enhancement)**
- Triggered: Agent requests during execution
- Loads: Supporting files (examples.md, reference.md)
- Purpose: On-demand deep knowledge

**Components:**
```python
from extensions.skills import SkillScanner, SkillLoader, SkillMatcher, SkillInjector

scanner = SkillScanner()  # Discover skills
loader = SkillLoader()    # Load skill content
matcher = SkillMatcher()  # Match user input
injector = SkillInjector() # Inject into instructions
```

### 3. Context Management with Compression

The `ContextManager` unifies session management and automatic compression:

```python
from core import ContextManager
from core.context_manager import ContextConfig

context = ContextManager(
    config=ContextConfig(
        model="deepseek-chat",
        max_context_tokens=65536,
        compression_threshold=0.7,
        keep_last_messages=4,
    )
)

# Automatically compresses when token usage exceeds threshold
await context.maybe_compress()
```

**Compression Process:**
1. Monitors prompt tokens from API responses
2. Triggers when usage exceeds `threshold * max_context_tokens`
3. Uses summarizer agent to compress old messages
4. Keeps last N messages for continuity

### 4. Agent Runner Pattern

The `AgentRunner` separates agent execution from UI:

```python
from core import AgentRunner

runner = AgentRunner(
    context_manager=context,
    model="deepseek-chat",
    mcp_servers=mcp_servers,
)

# Handles skills matching, injection, and execution
response = await runner.run(user_input)
```

### 5. Tool Registry Pattern

Centralized tool management with automatic registration:

```python
from tools import registry

@registry.register("read_file", "读取文件内容")
def read_file(path: str) -> str:
    """Read file contents."""
    ...

# Get all tools for agent
tools = registry.get_builtin_tools()

# Get descriptions for /tools command
descriptions = registry.get_tool_descriptions()
```

### 6. Configuration Management

Environment-based configuration with dataclasses:

```python
from config import AppConfig

config = AppConfig.from_env()
# Reads from environment variables with sensible defaults

# Access paths
config.paths.sessions_path      # Path to sessions directory
config.paths.mcp_config_path    # Path to MCP config
config.paths.skills_path        # Path to skills directory

# Access settings
config.model_name
config.model_max_context_tokens
config.context_compression_threshold
```

### 7. Security Model

All file operations are sandboxed to the working directory:

```python
def _is_safe_path(path: str, base_dir: Path) -> bool:
    """Ensure path is within base_dir."""
    resolved = Path(path).resolve()
    return str(resolved).startswith(str(base_dir.resolve()))
```

## MCP (Model Context Protocol) Integration

Demo CLI supports the Model Context Protocol, allowing you to extend the agent's capabilities with external MCP servers. MCP enables standardized integration with various tools and services.

### Configuration File Format

Create a `demo.mcp.json` file in your working directory:

```json
{
  "mcpServers": [
    {
      "name": "Filesystem MCP",
      "type": "stdio",
      "enabled": true,
      "params": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
      },
      "description": "File system access tools"
    }
  ]
}
```

### Supported MCP Server Types

1. **Stdio MCP Servers** (recommended for local tools)
2. **HTTP MCP Servers** (for remote services)
3. **SSE MCP Servers** (Server-Sent Events)

### MCP Manager API

The `MCPManager` class (`extensions/mcp/manager.py`) provides:

```python
from extensions.mcp import MCPManager

manager = MCPManager("demo.mcp.json")

# Load configuration
manager.load_config()

# Initialize all servers
servers = await manager.initialize_all_servers()

# Cleanup on exit
await manager.cleanup_servers()
```

### Integration with Agent

MCP servers are passed to the agent through the AgentRunner:

```python
runner = AgentRunner(
    context_manager=context,
    model="deepseek-chat",
    mcp_servers=mcp_servers,  # Passed to agent
)
```

## Skills System

### What are Skills?

Skills are modular instruction sets that enhance the agent's capabilities for specific tasks. Based on the [Agent Skills open standard](https://agentskills.io), skills are:

- **Discoverable**: Automatically scanned from `.demo-cli/skills/` directory
- **Context-aware**: Activated when user input matches skill descriptions
- **Progressive**: Loaded in stages to minimize token usage

### Skill Definition Format

Each skill is a directory containing a `SKILL.md` file:

```markdown
---
name: file-analyzer
version: 1.0.0
description: 当需要分析文件内容、统计信息或评估代码质量时使用此skill。
allowed-tools: [read_file, list_directory]
model: deepseek-chat
---

# File Analyzer Skill

详细的任务说明和步骤...

## Responsibilities
- 分析文件结构
- 统计代码行数
- 识别问题模式

## Steps
1. 读取文件内容
2. 分析和统计
3. 生成报告
```

### Creating a New Skill

1. Create directory: `.demo-cli/skills/your-skill-name/`
2. Create `SKILL.md` with YAML frontmatter and instructions
3. (Optional) Add `examples.md`, `reference.md`
4. Restart demo-cli - skill loads automatically

### Skill Matching

Skills are matched using keyword-based matching on user input:

```python
from extensions.skills import SkillMatcher

matcher = SkillMatcher()
matched = matcher.match_skills(user_input, available_skills)
```

**Matching algorithm:**
- Extracts keywords from skill description
- Checks if any keywords appear in user input
- Returns matched skills for activation

### Skills Lifecycle

```
App startup → SkillScanner.scan_skills_directory()
  → Load Level 1 metadata for all skills
  → Store in AgentRunner

User input → SkillMatcher.match_skills()
  → Check user input against skill descriptions
  → Return matched skills

Agent creation → SkillLoader.load_skill_instructions()
  → Load Level 2 full instructions
  → SkillInjector.inject_multiple_skills()
  → Create agent with enhanced instructions
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

### Environment Variables

Configure via `.env` file or environment:

```bash
# Required
DEEPSEEK_API_KEY=sk-...

# Optional
DEEPSEEK_BASE_URL=https://api.deepseek.com
MODEL_NAME=deepseek-chat
MODEL_MAX_CONTEXT_TOKENS=65536
CONTEXT_COMPRESSION_THRESHOLD=0.7
CONTEXT_COMPRESSION_KEEP_LAST_MESSAGES=4

# Paths
SESSIONS_DIR=data/sessions
MCP_CONFIG_FILE=demo.mcp.json
SKILLS_DIRECTORY=.demo-cli/skills
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
packages = ["cli", "core", "demo_agents", "extensions", "sessions", "tools"]
include = ["main.py"]
```

## Key Components Deep Dive

### 1. Application Loop (`cli/app.py`)

**App Class Responsibilities:**
- Initialize Rich console with custom theme
- Load configuration from environment
- Set up ContextManager for session + compression
- Initialize AgentRunner for skills + execution
- Set up MCP servers
- Manage main event loop (REPL)
- Route input to commands or agent
- Display agent responses with Markdown rendering

**Key Features:**
- Instant "/" key triggers command menu (no Enter needed)
- Async/await throughout for agent calls
- Exception handling for KeyboardInterrupt/EOFError
- Status spinner during agent thinking
- Automatic context compression monitoring

**Entry Flow:**
```
App.run() → load_or_create_session() → show_welcome() → main loop:
  → prompt_async() → handle_command() OR handle_chat()
    → AgentRunner.run() → save_message()
    → maybe_compress() (if threshold reached)
```

### 2. Core Layer Components

#### AgentRunner (`core/agent_runner.py`)

Handles agent execution with skills enhancement:

```python
class AgentRunner:
    async def run(self, user_input: str) -> AgentResponse:
        # 1. Match and inject skills
        enhanced_instructions, activated = self._build_instructions(user_input)

        # 2. Create agent with enhanced instructions
        agent = create_assistant(
            model=self._model,
            enhanced_instructions=enhanced_instructions,
            mcp_servers=self._mcp_servers,
        )

        # 3. Run agent
        result = await Runner.run(agent, messages)

        return AgentResponse(content=result.final_output, prompt_tokens=...)
```

#### ContextManager (`core/context_manager.py`)

Unified context management:

```python
class ContextManager:
    # Session management
    def load_or_create_session(self) -> str
    def get_messages(self) -> list[dict]
    def save_message(self, role: str, content: str)

    # Compression management
    def should_compress(self) -> bool
    async def maybe_compress(self) -> bool

    # Token tracking
    def set_last_prompt_tokens(self, tokens: int)
    @staticmethod
    def extract_prompt_tokens(run_result) -> int | None
```

#### Tracing (`core/tracing.py`)

Local tracing for debugging:

```python
from core import setup_local_tracing

# Enable tracing
processor = setup_local_tracing(
    log_to_console=True,
    log_to_file=True,
    log_dir="data/traces",
    verbose=True,
)
```

**Traces include:**
- Trace start/end events
- Span information (tool calls, LLM requests)
- Input/output previews
- Saved to JSON files for analysis

### 3. Agent Configuration (`demo_agents/assistant.py`)

**Important Notes:**
- Instructions are in Chinese (target user base)
- Model defaults to "deepseek-chat"
- Supports enhanced instructions with skills injection
- Uses tool registry for dynamic tool loading

**Instruction Guidelines:**
- Emphasize security (sandboxing, delete confirmation)
- Request clarification for unclear requests
- Maintain friendly, concise tone
- Mention MCP tools if available

**Summarizer Agent (`demo_agents/summarizer.py`):**
- Used for context compression
- Outputs concise summaries preserving key facts
- No tools, pure text processing

### 4. Tool Implementation (`tools/file_tools.py`)

**All tools follow this pattern:**

```python
from tools import registry

@registry.register("tool_name", "中文描述")
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
- Use `@registry.register()` decorator
- Always return `str` (never raise exceptions to agent)
- Chinese error messages
- Validate paths before operations
- Create parent directories for write operations
- Skip hidden files in directory listings

**Built-in Tools:**
- `read_file`: Read file contents
- `write_file`: Write or overwrite file
- `list_directory`: List directory contents
- `delete_file`: Delete file
- `list_tools`: List available tools (includes MCP tools)

### 5. Session Management (`sessions/manager.py`)

**SessionManager Responsibilities:**
- Generate 8-character UUIDs for sessions
- Store sessions as JSON in `data/sessions/`
- Auto-load latest session on startup
- Persist messages with timestamps
- Track last prompt tokens for compression
- Support summary injection

**Message Format:**
```json
{
  "session_id": "a1b2c3d4",
  "created_at": "2026-01-04T10:30:00",
  "messages": [
    {
      "role": "user",
      "content": "Message text",
      "timestamp": "2026-01-04T10:30:05"
    }
  ],
  "last_prompt_tokens": 1500
}
```

**API for Context Manager:**
```python
manager.get_messages()  # Returns simplified format for agent
# [{"role": "user", "content": "..."}]  # No timestamps

manager.get_messages_for_summary()  # Excludes last N messages
manager.apply_summary(summary, keep_last_messages=4)
```

### 6. Context Compression (`sessions/compression.py`)

**CompressionSettings:**
```python
@dataclass(frozen=True)
class CompressionSettings:
    model: str
    max_context_tokens: int
    threshold: float  # 0.0-1.0
    keep_last_messages: int
```

**ContextCompressor:**
- Monitors prompt token usage
- Triggers compression at threshold
- Uses summarizer agent to compress
- Preserves recent messages for continuity

**Compression Flow:**
```
1. Monitor: Extract prompt tokens from API response
2. Check: prompt_tokens >= (max_context_tokens * threshold)?
3. Compress:
   a. Get messages excluding last N
   b. Run summarizer agent
   c. Replace old messages with summary message
4. Continue: Reset token counter
```

### 7. Command System (`cli/commands.py`)

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
- `/tools`: List agent tools (including MCP)
- `/clear`: Create new session
- `/session`: Show current session ID
- `/exit`: Quit application

### 8. Command Menu (`cli/completer.py`)

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
- Use `from __future__ import annotations` for forward references

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

**In Core Layer:**
```python
# Best-effort patterns (don't interrupt flow)
try:
    result = await self._compressor.compress(self._session)
    return result
except Exception:
    # Log and continue
    return False
```

### Async/Await

- Agent calls are async: `await Runner.run()`
- UI prompts are async: `await prompt_session.prompt_async()`
- Command handlers are sync (for simplicity)
- Context compression is async: `await context.maybe_compress()`

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
- Command descriptions: Chinese text

## Working with the Agent

### Agent Instructions (`ASSISTANT_INSTRUCTIONS`)

When modifying agent behavior:

1. Keep instructions concise (current ~150 Chinese characters)
2. Avoid hardcoding tool names; refer to available tools generically
3. Use `list_tools` tool for dynamic tool discovery
4. Emphasize security constraints
5. Remind about confirmation for destructive operations
6. Encourage clarification questions

### Tool Design Principles

1. **Registry Pattern**: Use `@registry.register(name, description)`
2. **Descriptive Docstrings**: First line becomes tool description
3. **Error Messages in Returns**: Never raise exceptions
4. **Sandbox Everything**: Use `_is_safe_path()` check
5. **Relative Path Support**: Convert to absolute internally
6. **User-Friendly Output**: Format sizes, use emojis (📁/📄)

### Testing Tools Manually

```python
# In Python REPL with uv run
from tools import read_file, list_directory
print(read_file("README.md"))
print(list_directory("."))
```

## Common Development Tasks

### Adding a New Tool

1. Add function to `tools/file_tools.py`:
```python
@registry.register("new_tool", "工具描述")
def new_tool(param: str) -> str:
    """Tool description for LLM."""
    # Implementation with safety checks
    return "成功: ..."
```

2. Tool is automatically registered and available to agent

3. No need to update agent code - tools are loaded dynamically

### Adding a New Skill

1. Create directory: `.demo-cli/skills/skill-name/`
2. Create `SKILL.md`:
```markdown
---
name: skill-name
version: 1.0.0
description: 当用户需要XXX时使用此skill。关键词：XXX、YYY
allowed-tools: [read_file, write_file]
---

# Skill Instructions

详细步骤...
```

3. Restart app - skill loads automatically
4. Test with input matching skill description keywords

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
def setup_deepseek_client() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = "https://api.openai.com/v1"  # or other provider

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    set_default_openai_client(client)
```

Update model in `.env`:
```bash
MODEL_NAME=gpt-4o
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

### Configuring Context Compression

Set environment variables:

```bash
# Token limit for your model
MODEL_MAX_CONTEXT_TOKENS=65536

# Trigger compression at 70% usage
CONTEXT_COMPRESSION_THRESHOLD=0.7

# Keep last 4 messages when compressing
CONTEXT_COMPRESSION_KEEP_LAST_MESSAGES=4
```

### Enabling Local Tracing

Modify `core/__init__.py` or `main.py`:

```python
from core import setup_local_tracing

setup_local_tracing(
    log_to_console=True,   # Print to console
    log_to_file=True,      # Save JSON files
    log_dir="data/traces", # Directory for traces
    verbose=True,          # Include detailed info
)
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
from agents.mcp import MCPServerStdio, MCPServerStreamableHttp
```

**Not to be confused with** `demo_agents/` directory (local agent definitions).

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
        response = await self.agent_runner.run(user_input)
        await self.context_manager.maybe_compress()
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

### Trace Inspection

View trace files (if tracing enabled):

```bash
cat data/traces/trace_*.json | jq .
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

### Testing Skills

```python
# Test skill scanning
from extensions.skills import SkillScanner

scanner = SkillScanner()
skills = scanner.scan_skills_directory()
for skill in skills:
    print(f"{skill.name}: {skill.description}")
```

### Running Tests

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
pytest tests/
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
docs: Update CLAUDE.md with skills system
refactor: Extract context management to core layer
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

- `mcp>=1.25.0`: Model Context Protocol support
- `openai>=2.14.0`: OpenAI client (used for DeepSeek)
- `openai-agents>=0.6.4`: Agent framework with LiteLLM
- `prompt-toolkit>=3.0.52`: Interactive CLI prompts
- `python-dotenv>=1.2.1`: Environment variable loading
- `pyyaml>=6.0.0`: YAML parsing for skills frontmatter
- `rich>=14.2.0`: Terminal formatting and rendering
- `simple-term-menu>=1.6.6`: Interactive menu selection

### Dev Dependencies

- `pytest>=8.0.0`: Testing framework

### Why These Choices

- **OpenAI Agents SDK**: Official framework for function calling agents
- **MCP**: Standardized protocol for tool integration
- **prompt-toolkit**: Powerful async REPL with key binding support
- **Rich**: Beautiful terminal output with Markdown rendering
- **PyYAML**: Parse skill definitions with YAML frontmatter
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

The agent has NO built-in tools for:
- Running shell commands
- Installing packages
- Network operations
- System modifications

Only file operations within working directory are allowed.

**Note:** MCP servers may provide additional capabilities - review MCP server permissions carefully.

### Environment Variables

Sensitive data in `.env` file:

```bash
DEEPSEEK_API_KEY=sk-...  # Never commit this
```

Add to `.gitignore`:
```
.env
data/sessions/  # Session history may contain sensitive info
data/traces/    # Trace logs may contain sensitive info
```

## Architecture Decisions

### Why Core Layer?

The `core/` layer was introduced to:
- Separate business logic from UI concerns
- Enable easier testing (AgentRunner can be tested independently)
- Support future features (different UIs, API server)
- Centralize context and compression logic

### Why Progressive Skills Loading?

Three-level loading minimizes token usage:
- Level 1 (metadata): Always loaded, minimal cost (~100 tokens total)
- Level 2 (instructions): Only when relevant (up to 5000 tokens per skill)
- Level 3 (resources): Future enhancement for on-demand loading

This allows supporting many skills without context window bloat.

### Why Unified ContextManager?

Previously `SessionManager` and compression logic were separate. Unifying them:
- Simplifies API for agent execution
- Ensures compression always considers session state
- Reduces coupling between components

### Why Tool Registry?

Centralized registry enables:
- Dynamic tool listing (including MCP tools)
- Better `/tools` command output
- Cleaner separation of concerns
- Future: Tool filtering, access control

## Future Enhancement Areas

### Potential Improvements

1. **More Tools**: Git operations, search, grep, diff, HTTP requests
2. **Multi-Model Support**: Switch models within session
3. **Session Export**: Export conversations to Markdown
4. **Undo/Redo**: For file operations
5. **Syntax Highlighting**: For code in agent responses
6. **Token Usage Tracking**: Display API costs per session
7. **Session Search**: Search across past conversations
8. **Skills Level 3**: Auto-load resource files (examples, references)
9. **Smart Skill Matching**: Use embeddings for semantic matching
10. **Skill Dependencies**: Skills can depend on other skills

### Extensibility Points

The architecture supports easy extension:

- **New tools**: Add to `tools/` directory with `@registry.register()`
- **New commands**: Register in `cli/commands.py`
- **New agents**: Create in `demo_agents/` directory
- **New skills**: Create in `.demo-cli/skills/` with SKILL.md
- **Custom themes**: Modify Rich theme in `cli/app.py`
- **MCP servers**: Add to `demo.mcp.json`

## Troubleshooting Guide

### Common Issues

**"错误: 未设置 DEEPSEEK_API_KEY 环境变量"**
- Create `.env` file with `DEEPSEEK_API_KEY=...`
- Or set environment variable before running

**Agent not responding:**
- Check network connection to DeepSeek API
- Verify API key is valid
- Check for API rate limits
- Check tracing output if enabled

**File operation errors:**
- Ensure files are within working directory
- Check file permissions
- Verify file paths are correct

**Import errors:**
- Run `uv sync` to install dependencies
- Ensure Python 3.13+ is installed

**Skills not loading:**
- Check `.demo-cli/skills/` directory exists
- Verify SKILL.md has valid YAML frontmatter
- Check skill description includes relevant keywords
- Restart app after adding new skills

**Context compression not triggering:**
- Check `MODEL_MAX_CONTEXT_TOKENS` is set correctly
- Verify `CONTEXT_COMPRESSION_THRESHOLD` is between 0.0-1.0
- Monitor prompt tokens in session JSON

**MCP servers not working:**
- Check `demo.mcp.json` format
- Verify server commands are installed (e.g., `npx`)
- Check server `enabled: true`
- Check logs for initialization errors

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
9. **Layer Separation**: Keep UI (cli), logic (core), and data (sessions) separate
10. **Registry Pattern**: Use registries for tools, commands, skills

## Quick Reference

### File Locations

- Entry point: `main.py`
- Configuration: `config.py`
- Main loop: `cli/app.py`
- Agent runner: `core/agent_runner.py`
- Context manager: `core/context_manager.py`
- Agent config: `demo_agents/assistant.py`
- Summarizer: `demo_agents/summarizer.py`
- Tools: `tools/file_tools.py`
- Tool registry: `tools/registry.py`
- Commands: `cli/commands.py`
- Sessions: `sessions/manager.py`
- Compression: `sessions/compression.py`
- MCP manager: `extensions/mcp/manager.py`
- Skills scanner: `extensions/skills/scanner.py`
- Skills loader: `extensions/skills/loader.py`
- Skills matcher: `extensions/skills/matcher.py`
- Skills injector: `extensions/skills/injector.py`
- MCP config: `demo.mcp.json` (optional)
- Skills dir: `.demo-cli/skills/`
- Config: `pyproject.toml`

### Key Functions

- `main()`: App entry point
- `App.run()`: Main event loop
- `AgentRunner.run()`: Execute agent with skills
- `ContextManager.maybe_compress()`: Auto-compress if needed
- `create_assistant()`: Agent factory
- `Runner.run(agent, messages)`: Execute agent (SDK)
- `registry.register()`: Add slash command
- `@registry.register()`: Register tool (tools.registry)
- `setup_local_tracing()`: Enable debugging traces

### Import Shortcuts

```python
# Main components
from cli import App
from config import AppConfig
from core import AgentRunner, ContextManager, setup_local_tracing
from core.context_manager import ContextConfig

# Agents
from demo_agents.assistant import create_assistant
from demo_agents.summarizer import create_summarizer

# Extensions
from extensions.mcp import MCPManager
from extensions.skills import (
    SkillScanner, SkillLoader, SkillMatcher, SkillInjector
)

# Tools and sessions
from tools import registry as tool_registry
from tools import read_file, write_file, list_directory
from sessions import SessionManager

# Commands
from cli.commands import registry, CommandContext
```

---

**Document Version**: 2.0
**Last Updated**: 2026-01-04
**Maintainer**: Demo CLI Project
**Recent Changes**:
- Documented modular architecture refactor (core/ layer)
- Added comprehensive Skills system documentation
- Documented context compression with summarizer agent
- Updated directory structure (cli_agents → demo_agents, mcp_support → extensions/mcp)
- Added tool registry pattern
- Added configuration management system
- Added local tracing support
- Updated all file paths and import examples

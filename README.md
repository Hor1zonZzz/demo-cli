# Demo CLI Agent

A command-line AI assistant with file operation tools.

## Installation

### Using uv (recommended)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install demo-cli
uv tool install git+https://github.com/Hor1zonZzz/demo-cli.git
```

### Using pipx

```bash
pipx install git+https://github.com/Hor1zonZzz/demo-cli.git
```

### Using pip

```bash
pip install git+https://github.com/Hor1zonZzz/demo-cli.git
```

### From source

```bash
git clone https://github.com/Hor1zonZzz/demo-cli.git
cd demo-cli
uv sync
uv run demo-cli
```

## Uninstall

```bash
# If installed with uv
uv tool uninstall demo-cli

# If installed with pipx
pipx uninstall demo-cli

# If installed with pip
pip uninstall demo-cli
```

## Configuration

Create a `.env` file in your home directory or current directory:

```bash
DEEPSEEK_API_KEY=your_api_key_here
```

Optional configuration:

```bash
# Model selection
MODEL_NAME=deepseek-chat

# Context compression
MODEL_MAX_CONTEXT_TOKENS=4096
CONTEXT_COMPRESSION_THRESHOLD=0.8
CONTEXT_COMPRESSION_KEEP_LAST_MESSAGES=6
```

## Usage

After installation, run from any directory:

```bash
demo-cli
```

### Slash Commands

Press `/` to open the command menu:

- `/help` - Show help
- `/tools` - Show available tools
- `/clear` - Clear session
- `/session` - Show session ID
- `/exit` - Exit

### Available Tools

The agent can perform file operations in your current working directory:

- `read_file` - Read file contents
- `write_file` - Write/create files
- `list_directory` - List directory contents
- `delete_file` - Delete files
- `file_exists` - Check if file exists

## MCP (Model Context Protocol) Support

Demo CLI supports MCP servers to extend the agent's capabilities. Create a `demo.mcp.json` file in your working directory to configure MCP servers:

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
      }
    }
  ]
}
```

### Available MCP Servers

- **@modelcontextprotocol/server-filesystem** - Additional file operations
- **@modelcontextprotocol/server-fetch** - HTTP request tools
- **@modelcontextprotocol/server-github** - GitHub API integration
- **@modelcontextprotocol/server-slack** - Slack messaging
- **@modelcontextprotocol/server-postgres** - PostgreSQL database access
- **@modelcontextprotocol/server-brave-search** - Web search

### MCP Server Types

Demo CLI supports three MCP transport types:

1. **stdio** - Local subprocess servers (recommended)
2. **http** - HTTP/REST API servers
3. **sse** - Server-Sent Events servers

See `demo.mcp.json.example` for complete configuration examples.

## License

MIT

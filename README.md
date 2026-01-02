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

## License

MIT

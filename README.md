# Demo CLI Agent

A command-line AI assistant with file operation tools.

## Installation

### From GitHub (recommended)

```bash
pipx install git+https://github.com/Hor1zonZzz/demo-cli.git
```

Or with pip:

```bash
pip install git+https://github.com/Hor1zonZzz/demo-cli.git
```

### From source

```bash
git clone https://github.com/Hor1zonZzz/demo-cli.git
cd demo-cli
pip install -e .
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

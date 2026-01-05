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

## Skills System (On-Demand Loading)

demo-cli 支持 [Agent Skills 开放标准](https://agentskills.io)，AI 助手可以按需加载专业技能来完成特定任务。

### 什么是 Skills？

Skills 是包含专业指令的目录，每个 skill 包含一个 `SKILL.md` 文件，定义了执行特定任务的详细步骤。

**工作原理：**

1. **启动时**：扫描 `.demo-cli/skills/` 目录，加载 skill 元数据（名称、描述、路径）
2. **注入提示**：将 `<available_skills>` XML 注入到系统提示中
3. **按需加载**：Agent 根据用户请求，使用 `read_file` 工具加载相关 skill 的完整内容

这种设计让 Agent 自主决定何时加载哪个 skill，最大化灵活性并最小化 token 消耗。

### 创建 Skill

在项目根目录创建 `.demo-cli/skills/` 目录，然后为每个 skill 创建一个子目录：

```
.demo-cli/skills/
└── my-skill/
    ├── SKILL.md           # 必需：skill 定义和指令
    ├── references/        # 可选：参考文档
    ├── scripts/           # 可选：可执行脚本
    └── assets/            # 可选：模板和静态文件
```

SKILL.md 格式：

```markdown
---
name: my-skill
version: 1.0.0
description: 当用户需要XXX时使用此skill。描述应清晰说明 skill 的用途。
allowed-tools: [read_file, write_file]  # 可选
license: MIT                             # 可选
---

# Skill Instructions

这里是详细的 step-by-step 指令，告诉 AI 如何执行这个任务...

## 步骤
1. 第一步
2. 第二步
...
```

### 内置示例 Skills

demo-cli 包含两个示例 skills：

1. **file-analyzer**: 分析文件内容、统计信息、代码质量
2. **code-reviewer**: 审查代码质量、检查规范、提供改进建议

### 使用 Skills

Agent 会自动识别并加载相关 skills：

1. 系统提示中包含所有可用 skills 的描述和路径
2. 当用户请求与某个 skill 相关时，Agent 使用 `read_file` 加载 `SKILL.md`
3. Agent 遵循 skill 中的专业指令完成任务
4. 如需要，Agent 可以访问 skill 目录下的其他资源文件

### 优势

- 遵循 [Agent Skills 开放标准](https://agentskills.io)
- Agent 自主决定加载时机，更加智能
- 按需加载，最小化 token 消耗
- 支持资源文件（references/, scripts/, assets/）
- 可跨 AI 平台使用（标准化 XML 格式）

### 参考资源

- [Agent Skills 开放标准](https://agentskills.io)
- [Agent Skills 集成指南](https://agentskills.io/integrate-skills)
- [设计文档](docs/SKILLS_DESIGN.md)

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

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

## Skills System (Progressive Loading)

demo-cli 支持 Agent Skills 开放标准，实现了三级渐进式加载架构，可以扩展 AI 助手的能力。

### 什么是 Skills？

Skills 是专门的能力模块，可以教会 AI 助手执行特定任务。与传统方法不同，Skills 采用渐进式加载：

- **Level 1（元数据）**：启动时只加载 skill 名称和描述（~30-50 tokens/skill）
- **Level 2（完整指令）**：当用户请求匹配时才加载完整 instructions（~5000 tokens/skill）
- **Level 3（资源文件）**：按需加载参考文档和示例

这种设计允许你安装无限数量的 skills，而不会影响启动性能。

### 创建 Skill

在项目根目录创建 `.demo-cli/skills/` 目录，然后为每个 skill 创建一个子目录：

```
.demo-cli/skills/
└── my-skill/
    └── SKILL.md
```

SKILL.md 格式：

```markdown
---
name: my-skill
version: 1.0.0
description: 当用户需要XXX时使用此skill。描述要清晰具体，包含触发关键词。
allowed-tools: [read_file, write_file]  # 可选：限制可用工具
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

Skills 会自动激活！当你的请求匹配 skill 的描述时，系统会：

1. 自动识别相关的 skills
2. 加载完整的 skill instructions
3. 显示激活的 skills（🔧 图标）
4. AI 助手会遵循 skill 的专业指令

**示例：**

```
> 帮我分析一下 main.py 文件
🔧 激活 Skills: file-analyzer

[AI 会使用文件分析专家模式回复...]
```

### 优势

- 支持无限数量的 skills，启动开销固定
- 遵循开放的 Agent Skills 标准（agentskills.io）
- 渐进式加载，只在需要时消耗 tokens
- 自动发现和激活，无需手动调用
- 可跨 AI 平台使用（标准化格式）

### 参考资源

- [Agent Skills 官方文档](https://code.claude.com/docs/en/skills)
- [Agent Skills 开放标准](https://agentskills.io)
- [设计文档](SKILLS_DESIGN.md)

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

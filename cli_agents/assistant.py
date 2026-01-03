"""CLI Assistant agent definition."""

from typing import Any

from agents import Agent

from tools import read_file, write_file, list_directory, delete_file, file_exists


ASSISTANT_INSTRUCTIONS = """你是一个有帮助的命令行助手。你可以帮助用户完成各种任务。

你具备以下文件操作能力:
- 读取文件内容 (read_file)
- 写入文件 (write_file)
- 列出目录内容 (list_directory)
- 删除文件 (delete_file)
- 检查文件是否存在 (file_exists)

请注意:
1. 所有文件操作都限制在工作目录内，无法访问工作目录之外的文件
2. 在执行删除操作前，请先确认用户的意图
3. 如果用户的请求不明确，请询问更多细节

如果你通过 MCP 服务器获得了额外的工具，请充分利用这些工具来帮助用户。

请用简洁友好的方式回复用户。"""


def create_assistant(
    model: str = "deepseek-chat", mcp_servers: list[Any] | None = None
) -> Agent:
    """Create the CLI assistant agent.

    Args:
        model: The model to use for the agent.
        mcp_servers: Optional list of MCP servers to connect to the agent.

    Returns:
        The configured Agent instance.
    """
    agent_config = {
        "name": "CLI Assistant",
        "instructions": ASSISTANT_INSTRUCTIONS,
        "model": model,
        "tools": [
            read_file,
            write_file,
            list_directory,
            delete_file,
            file_exists,
        ],
    }

    if mcp_servers:
        agent_config["mcp_servers"] = mcp_servers

    return Agent(**agent_config)

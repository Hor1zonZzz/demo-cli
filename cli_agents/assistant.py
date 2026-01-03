"""CLI Assistant agent definition."""

from typing import Any

from agents import Agent

from tools import read_file, write_file, list_directory, delete_file, file_exists, list_tools


ASSISTANT_INSTRUCTIONS = """你是一个有帮助的命令行助手。你可以帮助用户完成各种任务。

你可以使用系统提供的工具来完成用户请求，工具列表可能会变化。
如果用户询问可用工具或能力，请先调用 list_tools 返回准确列表。

请注意:
1. 所有文件操作都限制在工作目录内，无法访问工作目录之外的文件
2. 在执行删除操作前，请先确认用户的意图
3. 如果用户的请求不明确，请询问更多细节

如果你通过 MCP 服务器获得了额外的工具，请充分利用这些工具来帮助用户。

请用简洁友好的方式回复用户。"""


def create_assistant(
    model: str = "deepseek-chat",
    enhanced_instructions: str | None = None,
    mcp_servers: list[Any] | None = None
) -> Agent:
    """Create the CLI assistant agent.

    Args:
        model: The model to use for the agent.
        enhanced_instructions: Optional enhanced instructions with skills injected.
        mcp_servers: Optional list of MCP servers to connect to the agent.

    Returns:
        The configured Agent instance.
    """
    instructions = enhanced_instructions or ASSISTANT_INSTRUCTIONS

    agent_config = {
        "name": "CLI Assistant",
        "instructions": instructions,
        "model": model,
        "tools": [
            read_file,
            write_file,
            list_directory,
            delete_file,
            file_exists,
            list_tools,
        ],
    }

    if mcp_servers:
        agent_config["mcp_servers"] = mcp_servers

    return Agent(**agent_config)

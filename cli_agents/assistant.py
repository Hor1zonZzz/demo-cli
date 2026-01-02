"""CLI Assistant agent definition."""

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

请用简洁友好的方式回复用户。"""


def create_assistant(model: str = "deepseek-chat") -> Agent:
    """Create the CLI assistant agent.

    Args:
        model: The model to use for the agent.

    Returns:
        The configured Agent instance.
    """
    return Agent(
        name="CLI Assistant",
        instructions=ASSISTANT_INSTRUCTIONS,
        model=model,
        tools=[
            read_file,
            write_file,
            list_directory,
            delete_file,
            file_exists,
        ],
    )

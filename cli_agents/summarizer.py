"""Summarizer agent for context compression."""

from __future__ import annotations

from agents import Agent


SUMMARY_INSTRUCTIONS = """你是对话上下文压缩器。
给定消息列表，请输出用于后续对话的简洁摘要。
要求：
1) 只输出摘要正文，不要添加额外说明或标题
2) 保留重要事实、需求、决定、未完成事项、关键文件/命令/路径
3) 不要编造信息，不要扩展讨论
4) 使用简洁的条目或短段落
"""


def create_summarizer(model: str) -> Agent:
    """Create the summarizer agent."""
    return Agent(
        name="Context Summarizer",
        instructions=SUMMARY_INSTRUCTIONS,
        model=model,
        tools=[],
    )

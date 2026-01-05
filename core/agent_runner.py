"""Agent runner for executing agents with skills enhancement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents import Agent, Runner

from demo_agents.assistant import create_assistant, ASSISTANT_INSTRUCTIONS
from core.context_manager import ContextManager
from extensions.skills import SkillScanner, inject_skills


@dataclass
class AgentResponse:
    """Response from an agent run."""
    content: str
    prompt_tokens: int | None = None


class AgentRunner:
    """Runs agents with skills awareness and context management.

    Skills are injected as metadata into the system prompt. The agent
    dynamically loads skill instructions using file reading tools when needed.
    """

    def __init__(
        self,
        context_manager: ContextManager,
        model: str = "deepseek-chat",
        mcp_servers: list[Any] | None = None,
        skills_path: str = ".demo-cli/skills",
    ) -> None:
        self._context = context_manager
        self._model = model
        self._mcp_servers = mcp_servers or []

        # Skills system - scan once at startup
        self._skill_scanner = SkillScanner(skills_path)
        self._available_skills = self._skill_scanner.scan_skills_directory()

        # Build enhanced instructions with skills awareness
        self._enhanced_instructions = inject_skills(
            ASSISTANT_INSTRUCTIONS, self._available_skills
        )

    @property
    def available_skills(self) -> list:
        """Get available skills metadata."""
        return self._available_skills

    def set_mcp_servers(self, servers: list[Any]) -> None:
        """Update MCP servers."""
        self._mcp_servers = servers

    async def run(self, user_input: str) -> AgentResponse:
        """Run the agent with user input and return response.

        The agent has skills awareness injected into its instructions.
        It will use file reading tools to load skill instructions on-demand.
        """
        # Create agent with skills-aware instructions
        agent = create_assistant(
            model=self._model,
            enhanced_instructions=self._enhanced_instructions,
            mcp_servers=self._mcp_servers if self._mcp_servers else None,
        )

        # Prepare messages
        messages = self._context.get_messages()
        if (
            not messages
            or messages[-1].get("role") != "user"
            or messages[-1].get("content") != user_input
        ):
            messages.append({"role": "user", "content": user_input})

        # Run agent
        result = await Runner.run(agent, messages)
        prompt_tokens = self._context.extract_prompt_tokens(result)

        return AgentResponse(
            content=result.final_output,
            prompt_tokens=prompt_tokens,
        )

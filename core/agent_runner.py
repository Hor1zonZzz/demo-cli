"""Agent runner for executing agents with skills enhancement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents import Agent, Runner

from demo_agents.assistant import create_assistant, ASSISTANT_INSTRUCTIONS
from core.context_manager import ContextManager
from extensions.skills import SkillScanner, SkillLoader, SkillMatcher, SkillInjector


@dataclass
class AgentResponse:
    """Response from an agent run."""
    content: str
    prompt_tokens: int | None = None


class AgentRunner:
    """Runs agents with skills enhancement and context management.
    
    Separates agent execution logic from UI concerns.
    """
    
    def __init__(
        self,
        context_manager: ContextManager,
        model: str = "deepseek-chat",
        mcp_servers: list[Any] | None = None,
    ) -> None:
        self._context = context_manager
        self._model = model
        self._mcp_servers = mcp_servers or []
        
        # Skills system
        self._skill_scanner = SkillScanner()
        self._skill_loader = SkillLoader()
        self._skill_matcher = SkillMatcher()
        self._skill_injector = SkillInjector()
        self._available_skills = self._skill_scanner.scan_skills_directory()
    
    @property
    def available_skills(self) -> list:
        """Get available skills metadata."""
        return self._available_skills
    
    def set_mcp_servers(self, servers: list[Any]) -> None:
        """Update MCP servers."""
        self._mcp_servers = servers
    
    async def run(self, user_input: str) -> AgentResponse:
        """Run the agent with user input and return response.
        
        Handles:
        - Skills matching and injection
        - Context management
        - Agent creation and execution
        """
        # Build enhanced instructions with skills
        enhanced_instructions, activated_skills = self._build_instructions(user_input)
        
        # Create agent
        agent = create_assistant(
            model=self._model,
            enhanced_instructions=enhanced_instructions,
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
    
    def _build_instructions(self, user_input: str) -> tuple[str, list[str]]:
        """Build enhanced instructions with skills.
        
        Returns:
            Tuple of (enhanced_instructions, list of activated skill names)
        """
        instructions = ASSISTANT_INSTRUCTIONS
        activated = []
        
        # Always inject Level 1 metadata summary
        if self._available_skills:
            instructions = self._skill_injector.inject_metadata_summary(
                instructions, self._available_skills
            )
        
        # Match and inject Level 2 full instructions
        matched_skills = self._skill_matcher.match_skills(
            user_input, self._available_skills
        )
        
        if matched_skills:
            skills_with_content = []
            for skill_meta in matched_skills:
                skill_content = self._skill_loader.load_skill_instructions(skill_meta)
                if skill_content:
                    skills_with_content.append((skill_meta, skill_content))
            
            if skills_with_content:
                instructions = self._skill_injector.inject_multiple_skills(
                    instructions, skills_with_content
                )
                activated = [s[0].name for s in skills_with_content]
        
        return instructions, activated
    
    def get_activated_skills(self, user_input: str) -> list[str]:
        """Get names of skills that would be activated for given input."""
        _, activated = self._build_instructions(user_input)
        return activated

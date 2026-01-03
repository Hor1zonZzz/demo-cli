"""Unified extension manager for MCP and Skills."""

from __future__ import annotations

from typing import Any

from extensions.mcp import MCPManager
from extensions.skills import SkillScanner, SkillLoader, SkillMatcher, SkillInjector
from tools import registry as tool_registry


class ExtensionManager:
    """Unified manager for all extensions (MCP and Skills).
    
    Provides a single entry point for initializing, cleaning up,
    and using extension capabilities.
    """
    
    def __init__(self, mcp_config_file: str = "demo.mcp.json") -> None:
        # MCP management
        self._mcp_manager = MCPManager(config_file=mcp_config_file)
        self._mcp_servers: list[Any] = []
        self._mcp_tools: list[tuple[str, str, str]] = []
        
        # Skills management
        self._skill_scanner = SkillScanner()
        self._skill_loader = SkillLoader()
        self._skill_matcher = SkillMatcher()
        self._skill_injector = SkillInjector()
        self._available_skills = self._skill_scanner.scan_skills_directory()
    
    # Properties
    
    @property
    def available_skills(self) -> list:
        """Get available skills metadata."""
        return self._available_skills
    
    @property
    def mcp_servers(self) -> list[Any]:
        """Get initialized MCP servers."""
        return self._mcp_servers
    
    @property
    def mcp_tools(self) -> list[tuple[str, str, str]]:
        """Get cached MCP tools metadata."""
        return self._mcp_tools
    
    # MCP operations
    
    async def initialize_mcp(self) -> list[Any]:
        """Initialize all MCP servers.
        
        Returns:
            List of initialized MCP servers.
        """
        if not self._mcp_manager.load_config():
            return []
        
        servers = await self._mcp_manager.initialize_all_servers()
        self._mcp_servers = servers
        
        # Cache MCP tools metadata
        for server in servers:
            tools = await server.list_tools()
            for tool in tools:
                self._mcp_tools.append(
                    (server.name, tool.name, tool.description)
                )
        
        # Register with tool registry
        tool_registry.register_mcp_tools(self._mcp_tools)
        
        return servers
    
    async def cleanup(self) -> None:
        """Cleanup all extension resources."""
        if self._mcp_servers:
            await self._mcp_manager.cleanup_servers()
            self._mcp_servers.clear()
            self._mcp_tools.clear()
    
    def get_enabled_mcp_server_names(self) -> list[str]:
        """Get names of enabled MCP servers."""
        return self._mcp_manager.get_enabled_server_names()
    
    # Skills operations
    
    def match_skills(self, user_input: str) -> list:
        """Match skills based on user input."""
        return self._skill_matcher.match_skills(user_input, self._available_skills)
    
    def enhance_instructions(
        self,
        base_instructions: str,
        user_input: str,
    ) -> tuple[str, list[str]]:
        """Enhance instructions with skills.
        
        Args:
            base_instructions: Base system instructions.
            user_input: User's input text.
            
        Returns:
            Tuple of (enhanced_instructions, activated_skill_names).
        """
        instructions = base_instructions
        activated = []
        
        # Always inject Level 1 metadata summary
        if self._available_skills:
            instructions = self._skill_injector.inject_metadata_summary(
                instructions, self._available_skills
            )
        
        # Match and inject Level 2 full instructions
        matched_skills = self.match_skills(user_input)
        
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

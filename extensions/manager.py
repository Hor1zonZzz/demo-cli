"""Unified extension manager for MCP and Skills."""

from __future__ import annotations

from typing import Any

from extensions.mcp import MCPManager
from extensions.skills import SkillScanner, inject_skills
from tools import registry as tool_registry


class ExtensionManager:
    """Unified manager for all extensions (MCP and Skills).

    Provides a single entry point for initializing, cleaning up,
    and using extension capabilities.

    Skills are loaded at startup and injected into the system prompt.
    The agent uses file reading tools to load skill instructions on-demand.
    """

    def __init__(
        self,
        mcp_config_file: str = "demo.mcp.json",
        skills_path: str = ".demo-cli/skills",
    ) -> None:
        # MCP management
        self._mcp_manager = MCPManager(config_file=mcp_config_file)
        self._mcp_servers: list[Any] = []
        self._mcp_tools: list[tuple[str, str, str]] = []

        # Skills management - scan once at startup
        self._skill_scanner = SkillScanner(skills_path)
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

    def enhance_instructions(self, base_instructions: str) -> str:
        """Enhance instructions with skills awareness.

        Injects skills metadata into the system prompt. The agent will
        use file reading tools to load full skill instructions on-demand.

        Args:
            base_instructions: Base system instructions.

        Returns:
            Enhanced instructions with skills awareness.
        """
        return inject_skills(base_instructions, self._available_skills)

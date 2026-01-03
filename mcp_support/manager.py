"""MCP configuration manager for loading and managing MCP servers."""

import json
import logging
from pathlib import Path
from typing import Any

from agents.mcp import MCPServerStdio, MCPServerStreamableHttp, MCPServerSse

logger = logging.getLogger(__name__)


class MCPManager:
    """Manages MCP server configuration and initialization."""

    def __init__(self, config_file: str = "demo.mcp.json"):
        """Initialize MCP manager.

        Args:
            config_file: Path to the MCP configuration file.
        """
        self.config_file = Path(config_file)
        self.config: dict[str, Any] = {}
        self.servers: list = []

    def load_config(self) -> bool:
        """Load MCP configuration from file.

        Returns:
            True if configuration was loaded successfully, False otherwise.
        """
        if not self.config_file.exists():
            return False

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)
            return True
        except (json.JSONDecodeError, IOError):
            return False

    def get_server_configs(self) -> list[dict[str, Any]]:
        """Get list of MCP server configurations.

        Returns:
            List of server configuration dictionaries.
        """
        return self.config.get("mcpServers", [])

    async def initialize_server(self, server_config: dict[str, Any]) -> Any | None:
        """Initialize a single MCP server based on configuration.

        Args:
            server_config: Server configuration dictionary.

        Returns:
            Initialized MCP server instance or None if initialization fails.
        """
        server_type = server_config.get("type", "stdio")
        name = server_config.get("name", "MCP Server")
        enabled = server_config.get("enabled", True)

        if not enabled:
            return None

        try:
            if server_type == "stdio":
                return await self._create_stdio_server(name, server_config)
            elif server_type == "http":
                return await self._create_http_server(name, server_config)
            elif server_type == "sse":
                return await self._create_sse_server(name, server_config)
            else:
                logger.warning(f"未知的 MCP 服务器类型: {server_type}")
                return None
        except Exception as e:
            logger.error(f"初始化 MCP 服务器 '{name}' 失败: {e}")
            return None

    async def _create_stdio_server(
        self, name: str, config: dict[str, Any]
    ) -> MCPServerStdio:
        """Create a Stdio MCP server.

        Args:
            name: Server name.
            config: Server configuration.

        Returns:
            Initialized MCPServerStdio instance.
        """
        params = config.get("params", {})
        command = params.get("command", "npx")
        args = params.get("args", [])
        env = params.get("env")

        server_params = {"command": command, "args": args}
        if env:
            server_params["env"] = env

        # Use longer timeout for first run (npx may need to download packages)
        server = MCPServerStdio(
            name=name,
            params=server_params,
            client_session_timeout_seconds=30,
        )
        await server.__aenter__()
        return server

    async def _create_http_server(
        self, name: str, config: dict[str, Any]
    ) -> MCPServerStreamableHttp:
        """Create an HTTP MCP server.

        Args:
            name: Server name.
            config: Server configuration.

        Returns:
            Initialized MCPServerStreamableHttp instance.
        """
        params = config.get("params", {})
        url = params.get("url")
        headers = params.get("headers", {})
        timeout = params.get("timeout", 30)

        if not url:
            raise ValueError(f"HTTP MCP 服务器 '{name}' 缺少 URL 配置")

        server_params = {"url": url, "headers": headers, "timeout": timeout}

        server = MCPServerStreamableHttp(name=name, params=server_params)
        await server.__aenter__()
        return server

    async def _create_sse_server(
        self, name: str, config: dict[str, Any]
    ) -> MCPServerSse:
        """Create an SSE MCP server.

        Args:
            name: Server name.
            config: Server configuration.

        Returns:
            Initialized MCPServerSse instance.
        """
        params = config.get("params", {})
        url = params.get("url")
        headers = params.get("headers", {})

        if not url:
            raise ValueError(f"SSE MCP 服务器 '{name}' 缺少 URL 配置")

        server_params = {"url": url, "headers": headers}

        server = MCPServerSse(name=name, params=server_params)
        await server.__aenter__()
        return server

    async def initialize_all_servers(self) -> list[Any]:
        """Initialize all configured MCP servers.

        Returns:
            List of initialized MCP server instances.
        """
        servers = []
        server_configs = self.get_server_configs()

        for config in server_configs:
            server = await self.initialize_server(config)
            if server:
                servers.append(server)

        self.servers = servers
        return servers

    async def cleanup_servers(self) -> None:
        """Cleanup all initialized MCP servers."""
        for server in self.servers:
            try:
                await server.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"清理 MCP 服务器时出错: {e}")
        self.servers = []

    def get_enabled_server_names(self) -> list[str]:
        """Get names of all enabled MCP servers.

        Returns:
            List of enabled server names.
        """
        configs = self.get_server_configs()
        return [
            config.get("name", "Unknown")
            for config in configs
            if config.get("enabled", True)
        ]

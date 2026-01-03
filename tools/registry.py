"""Unified tool registry for the CLI agent."""

from typing import Callable, Any
from agents import function_tool


class ToolRegistry:
    """Singleton registry for agent tools.
    
    Provides a decorator that wraps @function_tool while automatically
    collecting tool metadata for display and introspection.
    """
    
    _instance: "ToolRegistry | None" = None
    
    def __init__(self) -> None:
        self._tools: dict[str, tuple[Callable, str]] = {}
        self._mcp_tools: list[tuple[str, str, str]] = []
    
    @classmethod
    def instance(cls) -> "ToolRegistry":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def register(self, name: str, description: str) -> Callable:
        """Decorator to register a tool.
        
        Wraps @function_tool while storing metadata.
        
        Usage:
            @registry.register("read_file", "读取文件内容")
            def read_file(path: str) -> str:
                ...
        """
        def decorator(func: Callable) -> Callable:
            wrapped = function_tool(func)
            self._tools[name] = (wrapped, description)
            return wrapped
        return decorator
    
    def get_builtin_tools(self) -> list[Callable]:
        """Get all registered tool functions."""
        return [tool for tool, _ in self._tools.values()]
    
    def get_tool_descriptions(self) -> list[tuple[str, str]]:
        """Get tool names and descriptions."""
        return [(name, desc) for name, (_, desc) in self._tools.items()]
    
    def register_mcp_tools(self, tools: list[tuple[str, str, str]]) -> None:
        """Register MCP tool metadata for list_tools.
        
        Args:
            tools: List of (server_name, tool_name, description) tuples.
        """
        self._mcp_tools = list(tools)
    
    def get_mcp_tools(self) -> list[tuple[str, str, str]]:
        """Get registered MCP tools."""
        return self._mcp_tools
    
    def format_mcp_tools(self) -> list[str]:
        """Format MCP tools for display."""
        if not self._mcp_tools:
            return ["", "MCP 工具: 无"]
        
        lines = ["", "MCP 工具:"]
        current_server = None
        for server_name, tool_name, description in self._mcp_tools:
            if server_name != current_server:
                lines.append(f"{server_name}:")
                current_server = server_name
            
            short_desc = description.strip().splitlines()[0] if description else ""
            if len(short_desc) > 80:
                short_desc = short_desc[:77] + "..."
            
            if short_desc:
                lines.append(f"- {tool_name}: {short_desc}")
            else:
                lines.append(f"- {tool_name}")
        
        return lines


# Global singleton instance
registry = ToolRegistry.instance()

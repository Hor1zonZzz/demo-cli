"""Application configuration loaded from environment variables."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


DEFAULT_MODEL_NAME = "deepseek-chat"
DEFAULT_MAX_CONTEXT_TOKENS = 4096
DEFAULT_COMPRESSION_THRESHOLD = 0.8
DEFAULT_KEEP_LAST_MESSAGES = 6

# Path defaults
DEFAULT_SESSIONS_DIR = "data/sessions"
DEFAULT_MCP_CONFIG_FILE = "demo.mcp.json"
DEFAULT_SKILLS_DIRECTORY = ".demo-cli/skills"


def _get_env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _normalize_threshold(value: float, default: float) -> float:
    if value <= 0 or value > 1:
        return default
    return value


@dataclass(frozen=True)
class PathConfig:
    """Configuration for file and directory paths."""
    sessions_dir: str
    mcp_config_file: str
    skills_directory: str
    
    @classmethod
    def from_env(cls) -> "PathConfig":
        """Create PathConfig from environment variables."""
        return cls(
            sessions_dir=os.getenv("SESSIONS_DIR", DEFAULT_SESSIONS_DIR),
            mcp_config_file=os.getenv("MCP_CONFIG_FILE", DEFAULT_MCP_CONFIG_FILE),
            skills_directory=os.getenv("SKILLS_DIRECTORY", DEFAULT_SKILLS_DIRECTORY),
        )
    
    @property
    def sessions_path(self) -> Path:
        """Get sessions directory as Path."""
        return Path(self.sessions_dir)
    
    @property
    def mcp_config_path(self) -> Path:
        """Get MCP config file as Path."""
        return Path(self.mcp_config_file)
    
    @property
    def skills_path(self) -> Path:
        """Get skills directory as Path."""
        return Path(self.skills_directory)


@dataclass(frozen=True)
class AppConfig:
    """Main application configuration."""
    model_name: str
    model_max_context_tokens: int
    context_compression_threshold: float
    context_compression_keep_last_messages: int
    paths: PathConfig

    @classmethod
    def from_env(cls) -> "AppConfig":
        model_name = os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME)

        max_context_tokens = _get_env_int(
            "MODEL_MAX_CONTEXT_TOKENS", DEFAULT_MAX_CONTEXT_TOKENS
        )
        if max_context_tokens < 0:
            max_context_tokens = DEFAULT_MAX_CONTEXT_TOKENS

        compression_threshold = _normalize_threshold(
            _get_env_float("CONTEXT_COMPRESSION_THRESHOLD", DEFAULT_COMPRESSION_THRESHOLD),
            DEFAULT_COMPRESSION_THRESHOLD,
        )

        keep_last_messages = _get_env_int(
            "CONTEXT_COMPRESSION_KEEP_LAST_MESSAGES", DEFAULT_KEEP_LAST_MESSAGES
        )
        if keep_last_messages < 0:
            keep_last_messages = DEFAULT_KEEP_LAST_MESSAGES

        return cls(
            model_name=model_name,
            model_max_context_tokens=max_context_tokens,
            context_compression_threshold=compression_threshold,
            context_compression_keep_last_messages=keep_last_messages,
            paths=PathConfig.from_env(),
        )

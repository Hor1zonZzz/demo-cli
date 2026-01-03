"""Context manager combining session management and compression."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sessions.manager import SessionManager
from sessions.compression import CompressionSettings, ContextCompressor


@dataclass
class ContextConfig:
    """Configuration for context management."""
    model: str = "deepseek-chat"
    max_context_tokens: int = 65536
    compression_threshold: float = 0.7
    keep_last_messages: int = 4


class ContextManager:
    """Unified context management combining session and compression.
    
    Provides a simple API for conversation context while handling
    compression transparently.
    """
    
    def __init__(
        self,
        session_manager: SessionManager | None = None,
        config: ContextConfig | None = None,
    ) -> None:
        self._session = session_manager or SessionManager()
        self._config = config or ContextConfig()
        self._compressor = ContextCompressor(
            CompressionSettings(
                model=self._config.model,
                max_context_tokens=self._config.max_context_tokens,
                threshold=self._config.compression_threshold,
                keep_last_messages=self._config.keep_last_messages,
            )
        )
        self._last_prompt_tokens: int | None = None
    
    # Session delegation
    
    def load_or_create_session(self) -> str:
        """Load latest session or create a new one. Returns session ID."""
        if not self._session.load_latest_session():
            self._session.create_session()
        return self._session.get_current_session_id()
    
    def get_session_id(self) -> str:
        """Get current session ID."""
        return self._session.get_current_session_id()
    
    def clear_session(self) -> str:
        """Clear current session and create a new one. Returns new session ID."""
        return self._session.clear_session()
    
    def get_messages(self) -> list[dict[str, Any]]:
        """Get all messages in current session."""
        return self._session.get_messages()
    
    def save_message(self, role: str, content: str) -> None:
        """Save a message to the session."""
        self._session.save_message(role, content)
    
    def message_count(self) -> int:
        """Get number of messages in current session."""
        return self._session.message_count()
    
    # Compression management
    
    def set_last_prompt_tokens(self, tokens: int) -> None:
        """Record prompt tokens from last API response."""
        self._last_prompt_tokens = tokens
        self._session.set_last_prompt_tokens(tokens)
    
    def should_compress(self) -> bool:
        """Check if context should be compressed based on token usage."""
        return self._compressor.should_compress(self._last_prompt_tokens)
    
    async def maybe_compress(self) -> bool:
        """Compress context if needed. Returns True if compression occurred."""
        if not self.should_compress():
            return False
        try:
            result = await self._compressor.compress(self._session)
            if result:
                self._last_prompt_tokens = None
            return result
        except Exception:
            # Best-effort compression: avoid interrupting the chat flow.
            return False
    
    @staticmethod
    def extract_prompt_tokens(run_result: Any) -> int | None:
        """Extract prompt tokens from agent run result."""
        return ContextCompressor.extract_prompt_tokens(run_result)

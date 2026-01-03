"""Session manager for multi-turn conversation persistence."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


_SUMMARY_PREFIX = "Conversation summary (for context):"


class SessionManager:
    """Manages conversation sessions with file-based persistence."""

    def __init__(self, data_dir: str = "data/sessions"):
        """Initialize the session manager.

        Args:
            data_dir: Directory to store session files.
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._current_session_id: Optional[str] = None
        self._messages: list[dict] = []
        self._summary: Optional[str] = None
        self._last_prompt_tokens: Optional[int] = None

    def create_session(self) -> str:
        """Create a new session.

        Returns:
            The new session ID.
        """
        self._current_session_id = str(uuid.uuid4())[:8]
        self._messages = []
        self._summary = None
        self._last_prompt_tokens = None
        self._save_session()
        return self._current_session_id

    def load_session(self, session_id: str) -> bool:
        """Load an existing session.

        Args:
            session_id: The session ID to load.

        Returns:
            True if the session was loaded successfully, False otherwise.
        """
        session_file = self.data_dir / f"{session_id}.json"
        if not session_file.exists():
            return False

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._current_session_id = data.get("session_id", session_id)
                self._messages = data.get("messages", [])
                self._summary = data.get("summary")
                self._last_prompt_tokens = data.get("last_prompt_tokens")
                return True
        except (json.JSONDecodeError, IOError):
            return False

    def load_latest_session(self) -> Optional[str]:
        """Load the most recently modified session.

        Returns:
            The session ID if found, None otherwise.
        """
        session_files = list(self.data_dir.glob("*.json"))
        if not session_files:
            return None

        # Sort by modification time, most recent first
        latest = max(session_files, key=lambda f: f.stat().st_mtime)
        session_id = latest.stem

        if self.load_session(session_id):
            return session_id
        return None

    def save_message(self, role: str, content: str) -> None:
        """Save a message to the current session.

        Args:
            role: The role of the message sender ('user' or 'assistant').
            content: The message content.
        """
        self._messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._save_session()

    def get_messages(self) -> list[dict]:
        """Get all messages in the current session.

        Returns:
            List of message dictionaries with 'role' and 'content' keys.
        """
        messages = []
        if self._summary:
            messages.append({"role": "system", "content": self._format_summary()})
        messages.extend(
            [{"role": m["role"], "content": m["content"]} for m in self._messages]
        )
        return messages

    def get_messages_for_summary(self) -> list[dict]:
        """Get messages for summarization, including any existing summary."""
        messages = []
        if self._summary:
            messages.append({"role": "system", "content": self._format_summary()})
        messages.extend(
            [{"role": m["role"], "content": m["content"]} for m in self._messages]
        )
        return messages

    def message_count(self) -> int:
        """Return the number of stored messages."""
        return len(self._messages)

    def set_last_prompt_tokens(self, prompt_tokens: int) -> None:
        """Store the last prompt token count."""
        self._last_prompt_tokens = prompt_tokens
        self._save_session()

    def get_last_prompt_tokens(self) -> Optional[int]:
        """Get the last prompt token count."""
        return self._last_prompt_tokens

    def clear_last_prompt_tokens(self) -> None:
        """Clear the last prompt token count."""
        self._last_prompt_tokens = None
        self._save_session()

    def apply_summary(self, summary: str, keep_last_messages: int = 0) -> None:
        """Apply a summary and drop older messages."""
        self._summary = summary
        self._messages = self._select_messages_to_keep(keep_last_messages)
        self._save_session()

    def clear_session(self) -> str:
        """Clear the current session and create a new one.

        Returns:
            The new session ID.
        """
        return self.create_session()

    def get_current_session_id(self) -> Optional[str]:
        """Get the current session ID.

        Returns:
            The current session ID, or None if no session is active.
        """
        return self._current_session_id

    def _save_session(self) -> None:
        """Save the current session to disk."""
        if not self._current_session_id:
            return

        session_file = self.data_dir / f"{self._current_session_id}.json"
        data = {
            "session_id": self._current_session_id,
            "created_at": datetime.now().isoformat(),
            "messages": self._messages,
            "summary": self._summary,
            "last_prompt_tokens": self._last_prompt_tokens,
        }

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _format_summary(self) -> str:
        summary = self._summary.strip()
        return f"{_SUMMARY_PREFIX}\n{summary}"

    def _select_messages_to_keep(self, keep_last_messages: int) -> list[dict]:
        non_tool_indices = [
            index
            for index, message in enumerate(self._messages)
            if message.get("role") != "tool"
        ]

        if keep_last_messages <= 0:
            keep_indices = set()
        else:
            keep_indices = set(non_tool_indices[-keep_last_messages:])

        for index, message in enumerate(self._messages):
            if message.get("role") == "tool":
                keep_indices.add(index)

        return [message for index, message in enumerate(self._messages) if index in keep_indices]

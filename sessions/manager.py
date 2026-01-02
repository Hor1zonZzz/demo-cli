"""Session manager for multi-turn conversation persistence."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


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

    def create_session(self) -> str:
        """Create a new session.

        Returns:
            The new session ID.
        """
        self._current_session_id = str(uuid.uuid4())[:8]
        self._messages = []
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
        return [{"role": m["role"], "content": m["content"]} for m in self._messages]

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
            "messages": self._messages
        }

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

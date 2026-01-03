"""Context compression helpers for session history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents import Runner

from cli_agents.summarizer import create_summarizer
from sessions.manager import SessionManager


@dataclass(frozen=True)
class CompressionSettings:
    model: str
    max_context_tokens: int
    threshold: float
    keep_last_messages: int


class ContextCompressor:
    """Compresses session context using a summarizer agent."""

    def __init__(self, settings: CompressionSettings) -> None:
        self._settings = settings

    @staticmethod
    def extract_prompt_tokens(run_result: Any) -> int | None:
        raw_responses = getattr(run_result, "raw_responses", None)
        if not raw_responses:
            return None

        prompt_tokens = []
        for response in raw_responses:
            usage = getattr(response, "usage", None)
            if usage is None:
                continue
            tokens = getattr(usage, "input_tokens", None)
            if tokens is None:
                continue
            prompt_tokens.append(tokens)

        if not prompt_tokens:
            return None

        return max(prompt_tokens)

    def should_compress(self, prompt_tokens: int | None) -> bool:
        if prompt_tokens is None:
            return False
        if self._settings.max_context_tokens <= 0:
            return False
        threshold_tokens = int(self._settings.max_context_tokens * self._settings.threshold)
        return prompt_tokens >= threshold_tokens

    async def compress(self, session_manager: SessionManager) -> bool:
        if session_manager.message_count() == 0:
            return False

        messages = session_manager.get_messages_for_summary()
        if not messages:
            return False

        agent = create_summarizer(model=self._settings.model)
        result = await Runner.run(agent, messages)
        summary = result.final_output

        if not isinstance(summary, str) or not summary.strip():
            return False

        session_manager.apply_summary(
            summary.strip(), keep_last_messages=self._settings.keep_last_messages
        )
        session_manager.clear_last_prompt_tokens()
        return True

"""Application configuration loaded from environment variables."""

from __future__ import annotations

from dataclasses import dataclass
import os


DEFAULT_MODEL_NAME = "deepseek-chat"
DEFAULT_MAX_CONTEXT_TOKENS = 4096
DEFAULT_COMPRESSION_THRESHOLD = 0.8
DEFAULT_KEEP_LAST_MESSAGES = 6


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
class AppConfig:
    model_name: str
    model_max_context_tokens: int
    context_compression_threshold: float
    context_compression_keep_last_messages: int

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
        )

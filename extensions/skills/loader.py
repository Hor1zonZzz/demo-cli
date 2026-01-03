"""Skill loader for Level 2 and Level 3 content loading."""

import logging
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from .scanner import SkillMetadata

logger = logging.getLogger(__name__)

# Default cache size limit
DEFAULT_CACHE_SIZE = 100


class LRUCache:
    """Simple LRU cache implementation."""

    def __init__(self, max_size: int = DEFAULT_CACHE_SIZE):
        """Initialize LRU cache.

        Args:
            max_size: Maximum number of items to cache.
        """
        self._cache: OrderedDict[str, str] = OrderedDict()
        self._max_size = max_size

    def get(self, key: str) -> Optional[str]:
        """Get item from cache, moving it to end (most recently used)."""
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def set(self, key: str, value: str) -> None:
        """Set item in cache, evicting oldest if at capacity."""
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)  # Remove oldest
        self._cache[key] = value

    def clear(self) -> None:
        """Clear all items from cache."""
        self._cache.clear()

    def __contains__(self, key: str) -> bool:
        return key in self._cache


class SkillLoader:
    """Loader for skill instructions and resources."""

    def __init__(self, cache_size: int = DEFAULT_CACHE_SIZE):
        """Initialize loader.

        Args:
            cache_size: Maximum number of items to cache.
        """
        self._cache = LRUCache(cache_size)

    def load_skill_instructions(self, skill_metadata: SkillMetadata) -> str:
        """Load full SKILL.md content for Level 2 loading.

        Args:
            skill_metadata: SkillMetadata object.

        Returns:
            Full SKILL.md content with frontmatter removed.
        """
        skill_md = skill_metadata.skill_path / "SKILL.md"

        # Check cache
        cache_key = f"instructions:{skill_metadata.name}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            with open(skill_md, "r", encoding="utf-8") as f:
                content = f.read()

            # Remove YAML frontmatter, keep only instructions
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    instructions = parts[2].strip()
                else:
                    instructions = content
            else:
                instructions = content

            # Cache the result
            self._cache.set(cache_key, instructions)
            return instructions

        except Exception as e:
            logger.error(f"Error loading skill instructions for {skill_metadata.name}: {e}")
            return ""

    def load_skill_resource(
        self, skill_metadata: SkillMetadata, resource_name: str
    ) -> Optional[str]:
        """Load a skill resource file for Level 3 loading.

        Args:
            skill_metadata: SkillMetadata object.
            resource_name: Name of the resource file (e.g., 'reference.md', 'examples.md').

        Returns:
            Resource file content or None if not found.
        """
        resource_path = skill_metadata.skill_path / resource_name

        # Check cache
        cache_key = f"resource:{skill_metadata.name}:{resource_name}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        if not resource_path.exists():
            return None

        try:
            with open(resource_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Cache the result
            self._cache.set(cache_key, content)
            return content

        except Exception as e:
            logger.error(f"Error loading resource {resource_name} for {skill_metadata.name}: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear the loader cache."""
        self._cache.clear()

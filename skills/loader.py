"""Skill loader for Level 2 and Level 3 content loading."""

from pathlib import Path
from typing import Optional

from skills.scanner import SkillMetadata


class SkillLoader:
    """Loader for skill instructions and resources."""

    def __init__(self):
        """Initialize loader."""
        self._cache: dict[str, str] = {}

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
        if cache_key in self._cache:
            return self._cache[cache_key]

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
            self._cache[cache_key] = instructions
            return instructions

        except Exception as e:
            print(f"Error loading skill instructions for {skill_metadata.name}: {e}")
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
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not resource_path.exists():
            return None

        try:
            with open(resource_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Cache the result
            self._cache[cache_key] = content
            return content

        except Exception as e:
            print(f"Error loading resource {resource_name} for {skill_metadata.name}: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear the loader cache."""
        self._cache.clear()

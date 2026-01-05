"""Skill scanner for Level 1 metadata loading."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class SkillMetadata:
    """Lightweight skill metadata following Agent Skills specification.

    See: https://agentskills.io/specification
    """

    # Required fields
    name: str
    description: str
    skill_path: Path

    # Optional fields per specification
    version: Optional[str] = None
    allowed_tools: Optional[list[str]] = None
    model: Optional[str] = None
    license: Optional[str] = None
    compatibility: Optional[str] = None
    metadata: Optional[dict[str, str]] = None

    def to_summary(self) -> str:
        """Convert to summary string for Level 1 loading (deprecated, use to_xml)."""
        version_str = f" (v{self.version})" if self.version else ""
        return f"- **{self.name}**{version_str}: {self.description}"

    def to_xml(self) -> str:
        """Convert to XML format following Agent Skills specification.

        Returns:
            XML string for <available_skills> block.
        """
        lines = [
            "  <skill>",
            f"    <name>{self.name}</name>",
            f"    <description>{self.description}</description>",
            f"    <location>{self.skill_path}</location>",
        ]
        lines.append("  </skill>")
        return "\n".join(lines)

    def get_references_dir(self) -> Path:
        """Get the references directory path."""
        return self.skill_path / "references"

    def get_scripts_dir(self) -> Path:
        """Get the scripts directory path."""
        return self.skill_path / "scripts"

    def get_assets_dir(self) -> Path:
        """Get the assets directory path."""
        return self.skill_path / "assets"


class SkillScanner:
    """Scanner for discovering and parsing skill metadata."""

    def __init__(self, base_path: str = ".demo-cli/skills"):
        """Initialize scanner.

        Args:
            base_path: Base directory containing skills.
        """
        self.base_path = Path(base_path)

    def scan_skills_directory(self) -> list[SkillMetadata]:
        """Scan skills directory and return metadata list.

        Returns:
            List of SkillMetadata objects for all discovered skills.
        """
        if not self.base_path.exists():
            return []

        skills = []
        for skill_dir in self.base_path.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue

            try:
                metadata = self.parse_skill_metadata(skill_md)
                if metadata:
                    skills.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to parse skill at {skill_dir}: {e}")
                continue

        return skills

    def parse_skill_metadata(self, skill_md_path: Path) -> Optional[SkillMetadata]:
        """Parse SKILL.md frontmatter to extract metadata.

        Args:
            skill_md_path: Path to SKILL.md file.

        Returns:
            SkillMetadata object or None if parsing fails.
        """
        try:
            with open(skill_md_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract YAML frontmatter
            if not content.startswith("---"):
                return None

            parts = content.split("---", 2)
            if len(parts) < 3:
                return None

            frontmatter = yaml.safe_load(parts[1])

            if not frontmatter or "name" not in frontmatter or "description" not in frontmatter:
                return None

            return SkillMetadata(
                name=frontmatter["name"],
                description=frontmatter["description"],
                skill_path=skill_md_path.parent,
                version=frontmatter.get("version"),
                allowed_tools=frontmatter.get("allowed-tools"),
                model=frontmatter.get("model"),
                license=frontmatter.get("license"),
                compatibility=frontmatter.get("compatibility"),
                metadata=frontmatter.get("metadata"),
            )

        except Exception as e:
            logger.error(f"Error parsing {skill_md_path}: {e}")
            return None

    def get_skills_summary(self, skills: list[SkillMetadata]) -> str:
        """Generate a summary of available skills for Level 1 injection (deprecated).

        Args:
            skills: List of SkillMetadata objects.

        Returns:
            Formatted summary string in Markdown format.

        Note:
            Use get_skills_xml() for spec-compliant XML format.
        """
        if not skills:
            return ""

        summary_lines = ["## Available Skills\n"]
        for skill in skills:
            summary_lines.append(skill.to_summary())

        return "\n".join(summary_lines)

    def get_skills_xml(self, skills: list[SkillMetadata]) -> str:
        """Generate XML block of available skills following Agent Skills specification.

        Args:
            skills: List of SkillMetadata objects.

        Returns:
            XML formatted string with <available_skills> block.
        """
        if not skills:
            return ""

        lines = ["<available_skills>"]
        for skill in skills:
            lines.append(skill.to_xml())
        lines.append("</available_skills>")

        return "\n".join(lines)

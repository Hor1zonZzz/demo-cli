"""Skill validator following Agent Skills specification.

See: https://agentskills.io/specification
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class ValidationResult:
    """Result of skill validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def __str__(self) -> str:
        """Format validation result as string."""
        lines = []
        if self.valid:
            lines.append("✓ Skill is valid")
        else:
            lines.append("✗ Skill validation failed")

        if self.errors:
            lines.append("\nErrors:")
            for error in self.errors:
                lines.append(f"  - {error}")

        if self.warnings:
            lines.append("\nWarnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        return "\n".join(lines)


class SkillValidator:
    """Validator for Agent Skills specification compliance.

    Validates:
    - Required SKILL.md file exists
    - YAML frontmatter is valid
    - Required fields (name, description) are present
    - Name follows naming conventions
    - Description length limits
    - Directory structure recommendations
    """

    # Name constraints per specification
    NAME_MIN_LENGTH = 1
    NAME_MAX_LENGTH = 64
    NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

    # Description constraints per specification
    DESCRIPTION_MIN_LENGTH = 1
    DESCRIPTION_MAX_LENGTH = 1024

    # Compatibility constraints
    COMPATIBILITY_MAX_LENGTH = 500

    def validate(self, skill_path: Path) -> ValidationResult:
        """Validate a skill directory.

        Args:
            skill_path: Path to the skill directory.

        Returns:
            ValidationResult with errors and warnings.
        """
        result = ValidationResult(valid=True)

        # Check directory exists
        if not skill_path.exists():
            result.add_error(f"Skill directory does not exist: {skill_path}")
            return result

        if not skill_path.is_dir():
            result.add_error(f"Path is not a directory: {skill_path}")
            return result

        # Check SKILL.md exists
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            result.add_error("SKILL.md file not found")
            return result

        # Parse and validate SKILL.md
        self._validate_skill_md(skill_md, skill_path.name, result)

        # Check recommended directory structure
        self._validate_directory_structure(skill_path, result)

        return result

    def _validate_skill_md(
        self, skill_md: Path, dir_name: str, result: ValidationResult
    ) -> None:
        """Validate SKILL.md content and frontmatter."""
        try:
            content = skill_md.read_text(encoding="utf-8")
        except Exception as e:
            result.add_error(f"Failed to read SKILL.md: {e}")
            return

        # Check for YAML frontmatter
        if not content.startswith("---"):
            result.add_error("SKILL.md must start with YAML frontmatter (---)")
            return

        parts = content.split("---", 2)
        if len(parts) < 3:
            result.add_error("Invalid YAML frontmatter format")
            return

        # Parse YAML
        try:
            frontmatter = yaml.safe_load(parts[1])
        except yaml.YAMLError as e:
            result.add_error(f"Invalid YAML in frontmatter: {e}")
            return

        if not frontmatter:
            result.add_error("Empty YAML frontmatter")
            return

        # Validate required fields
        self._validate_name(frontmatter, dir_name, result)
        self._validate_description(frontmatter, result)

        # Validate optional fields
        self._validate_optional_fields(frontmatter, result)

        # Check body content
        body = parts[2].strip()
        if not body:
            result.add_warning("SKILL.md has no instruction content after frontmatter")

    def _validate_name(
        self, frontmatter: dict, dir_name: str, result: ValidationResult
    ) -> None:
        """Validate the name field."""
        if "name" not in frontmatter:
            result.add_error("Missing required field: name")
            return

        name = frontmatter["name"]
        if not isinstance(name, str):
            result.add_error("Field 'name' must be a string")
            return

        # Length check
        if len(name) < self.NAME_MIN_LENGTH:
            result.add_error("Field 'name' is empty")
            return

        if len(name) > self.NAME_MAX_LENGTH:
            result.add_error(
                f"Field 'name' exceeds maximum length of {self.NAME_MAX_LENGTH} characters"
            )

        # Pattern check
        if not self.NAME_PATTERN.match(name):
            result.add_error(
                "Field 'name' must be lowercase alphanumeric with hyphens only, "
                "cannot start/end with hyphen or have consecutive hyphens"
            )

        # Directory name match (per specification)
        if name != dir_name:
            result.add_warning(
                f"Skill name '{name}' does not match directory name '{dir_name}'"
            )

    def _validate_description(
        self, frontmatter: dict, result: ValidationResult
    ) -> None:
        """Validate the description field."""
        if "description" not in frontmatter:
            result.add_error("Missing required field: description")
            return

        description = frontmatter["description"]
        if not isinstance(description, str):
            result.add_error("Field 'description' must be a string")
            return

        if len(description) < self.DESCRIPTION_MIN_LENGTH:
            result.add_error("Field 'description' is empty")
            return

        if len(description) > self.DESCRIPTION_MAX_LENGTH:
            result.add_error(
                f"Field 'description' exceeds maximum length of "
                f"{self.DESCRIPTION_MAX_LENGTH} characters"
            )

        # Check for keywords (recommendation)
        if len(description) < 50:
            result.add_warning(
                "Consider adding more keywords to description for better agent discovery"
            )

    def _validate_optional_fields(
        self, frontmatter: dict, result: ValidationResult
    ) -> None:
        """Validate optional fields."""
        # Validate compatibility if present
        if "compatibility" in frontmatter:
            compatibility = frontmatter["compatibility"]
            if isinstance(compatibility, str):
                if len(compatibility) > self.COMPATIBILITY_MAX_LENGTH:
                    result.add_error(
                        f"Field 'compatibility' exceeds maximum length of "
                        f"{self.COMPATIBILITY_MAX_LENGTH} characters"
                    )
            else:
                result.add_error("Field 'compatibility' must be a string")

        # Validate license if present
        if "license" in frontmatter:
            license_val = frontmatter["license"]
            if not isinstance(license_val, str):
                result.add_error("Field 'license' must be a string")

        # Validate metadata if present
        if "metadata" in frontmatter:
            metadata = frontmatter["metadata"]
            if not isinstance(metadata, dict):
                result.add_error("Field 'metadata' must be a key-value object")
            else:
                for key, value in metadata.items():
                    if not isinstance(key, str) or not isinstance(value, str):
                        result.add_error(
                            "Field 'metadata' must have string keys and string values"
                        )
                        break

        # Validate allowed-tools if present
        if "allowed-tools" in frontmatter:
            tools = frontmatter["allowed-tools"]
            if not isinstance(tools, list):
                result.add_error("Field 'allowed-tools' must be a list")
            else:
                for tool in tools:
                    if not isinstance(tool, str):
                        result.add_error("Field 'allowed-tools' must contain strings")
                        break

    def _validate_directory_structure(
        self, skill_path: Path, result: ValidationResult
    ) -> None:
        """Check for recommended directory structure."""
        # Check for recommended directories
        refs_dir = skill_path / "references"
        scripts_dir = skill_path / "scripts"
        assets_dir = skill_path / "assets"

        # Check for legacy resource files in root
        legacy_files = ["examples.md", "reference.md"]
        for legacy_file in legacy_files:
            if (skill_path / legacy_file).exists():
                result.add_warning(
                    f"Consider moving '{legacy_file}' to references/ directory "
                    "per Agent Skills specification"
                )

        # Info about optional directories (not warnings)
        has_resources = refs_dir.exists() or scripts_dir.exists() or assets_dir.exists()
        if not has_resources:
            # Not a warning, just checking
            pass


def validate_skill(skill_path: Path | str) -> ValidationResult:
    """Convenience function to validate a skill.

    Args:
        skill_path: Path to the skill directory.

    Returns:
        ValidationResult with errors and warnings.
    """
    validator = SkillValidator()
    return validator.validate(Path(skill_path))

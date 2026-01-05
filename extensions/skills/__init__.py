"""Skills system for demo-cli.

Follows the Agent Skills specification: https://agentskills.io/specification

This module provides:
- SkillScanner: Discovers skills and parses metadata from SKILL.md files
- SkillMetadata: Data class for skill metadata
- inject_skills: Injects skills awareness into agent instructions
- SkillValidator: Validates skill format compliance
"""

from .scanner import SkillScanner, SkillMetadata
from .injector import inject_skills
from .validator import SkillValidator, ValidationResult, validate_skill

__all__ = [
    "SkillScanner",
    "SkillMetadata",
    "inject_skills",
    "SkillValidator",
    "ValidationResult",
    "validate_skill",
]

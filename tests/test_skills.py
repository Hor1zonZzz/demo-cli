"""Unit tests for the skills module."""

import tempfile
from pathlib import Path

import pytest

from extensions.skills.scanner import SkillScanner, SkillMetadata
from extensions.skills.injector import inject_skills, SKILLS_INSTRUCTION
from extensions.skills.validator import SkillValidator, ValidationResult, validate_skill


class TestSkillScanner:
    """Tests for SkillScanner."""

    def test_scan_nonexistent_directory(self):
        scanner = SkillScanner("/nonexistent/path")
        skills = scanner.scan_skills_directory()
        assert skills == []

    def test_scan_valid_skills(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a skill
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                """---
name: test-skill
version: 1.0.0
description: A test skill for unit testing
allowed-tools: [read_file]
---

# Test Skill Instructions

This is a test skill.
"""
            )

            scanner = SkillScanner(tmpdir)
            skills = scanner.scan_skills_directory()

            assert len(skills) == 1
            assert skills[0].name == "test-skill"
            assert skills[0].version == "1.0.0"
            assert skills[0].description == "A test skill for unit testing"
            assert skills[0].allowed_tools == ["read_file"]

    def test_parse_skill_without_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "bad-skill"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text("No frontmatter here")

            scanner = SkillScanner(tmpdir)
            skills = scanner.scan_skills_directory()
            assert len(skills) == 0

    def test_scan_skill_with_all_fields(self):
        """Test scanning skill with all specification fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                """---
name: test-skill
version: 1.0.0
description: A test skill
license: MIT
compatibility: Python 3.13+
allowed-tools: [read_file]
metadata:
  author: test
  category: testing
---

Instructions here.
"""
            )

            scanner = SkillScanner(tmpdir)
            skills = scanner.scan_skills_directory()

            assert len(skills) == 1
            skill = skills[0]
            assert skill.name == "test-skill"
            assert skill.license == "MIT"
            assert skill.compatibility == "Python 3.13+"
            assert skill.metadata == {"author": "test", "category": "testing"}

    def test_get_skills_xml(self):
        """Test XML generation for skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                """---
name: test-skill
description: A test skill
---

Instructions here.
"""
            )

            scanner = SkillScanner(tmpdir)
            skills = scanner.scan_skills_directory()
            xml = scanner.get_skills_xml(skills)

            assert "<available_skills>" in xml
            assert "</available_skills>" in xml
            assert "<skill>" in xml
            assert "<name>test-skill</name>" in xml


class TestSkillMetadata:
    """Tests for SkillMetadata."""

    def test_to_xml(self):
        skill = SkillMetadata(
            name="test-skill",
            description="Test description",
            skill_path=Path("/tmp/test-skill"),
        )
        xml = skill.to_xml()

        assert "<skill>" in xml
        assert "<name>test-skill</name>" in xml
        assert "<description>Test description</description>" in xml
        assert "<location>/tmp/test-skill</location>" in xml
        assert "</skill>" in xml

    def test_to_summary(self):
        skill = SkillMetadata(
            name="test-skill",
            description="Test description",
            skill_path=Path("/tmp/test-skill"),
            version="1.0.0",
        )
        summary = skill.to_summary()

        assert "test-skill" in summary
        assert "v1.0.0" in summary
        assert "Test description" in summary


class TestInjectSkills:
    """Tests for inject_skills function."""

    def test_inject_skills_adds_xml(self):
        """Test that skills are injected in XML format."""
        base = "You are a helpful assistant."
        skills = [
            SkillMetadata(
                name="test-skill",
                description="A test skill",
                skill_path=Path("/tmp/test-skill"),
            )
        ]

        result = inject_skills(base, skills)

        assert base in result
        assert "<skills_instructions>" in result
        assert "<available_skills>" in result
        assert "<name>test-skill</name>" in result
        assert "<description>A test skill</description>" in result
        assert "<location>/tmp/test-skill</location>" in result

    def test_inject_skills_empty_list(self):
        """Test that empty skills list returns base unchanged."""
        base = "You are a helpful assistant."
        result = inject_skills(base, [])
        assert result == base

    def test_inject_skills_multiple(self):
        """Test injecting multiple skills."""
        base = "You are a helpful assistant."
        skills = [
            SkillMetadata(
                name="skill-a",
                description="Skill A",
                skill_path=Path("/tmp/skill-a"),
            ),
            SkillMetadata(
                name="skill-b",
                description="Skill B",
                skill_path=Path("/tmp/skill-b"),
            ),
        ]

        result = inject_skills(base, skills)

        assert "<name>skill-a</name>" in result
        assert "<name>skill-b</name>" in result

    def test_skills_instruction_content(self):
        """Test that SKILLS_INSTRUCTION contains key guidance."""
        assert "read_file" in SKILLS_INSTRUCTION
        assert "SKILL.md" in SKILLS_INSTRUCTION
        assert "references/" in SKILLS_INSTRUCTION
        assert "scripts/" in SKILLS_INSTRUCTION
        assert "assets/" in SKILLS_INSTRUCTION


class TestSkillValidator:
    """Tests for SkillValidator."""

    def test_validate_valid_skill(self):
        """Test validating a fully valid skill."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                """---
name: test-skill
description: A test skill for unit testing with keywords for discovery
---

# Test Skill Instructions

This is a test skill with proper instructions.
"""
            )

            result = validate_skill(skill_dir)

            assert result.valid is True
            assert len(result.errors) == 0

    def test_validate_missing_skill_md(self):
        """Test validation fails when SKILL.md is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()

            result = validate_skill(skill_dir)

            assert result.valid is False
            assert any("SKILL.md" in e for e in result.errors)

    def test_validate_missing_name(self):
        """Test validation fails when name is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                """---
description: A test skill
---

Instructions here.
"""
            )

            result = validate_skill(skill_dir)

            assert result.valid is False
            assert any("name" in e for e in result.errors)

    def test_validate_invalid_name_format(self):
        """Test validation fails with invalid name format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                """---
name: Test_Skill
description: A test skill
---

Instructions here.
"""
            )

            result = validate_skill(skill_dir)

            assert result.valid is False
            assert any("lowercase" in e for e in result.errors)

    def test_validate_name_mismatch_warning(self):
        """Test warning when name doesn't match directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                """---
name: different-name
description: A test skill for testing purposes
---

Instructions here.
"""
            )

            result = validate_skill(skill_dir)

            assert any("match" in w for w in result.warnings)

    def test_validate_short_description_warning(self):
        """Test warning for short descriptions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                """---
name: test-skill
description: Short desc
---

Instructions here.
"""
            )

            result = validate_skill(skill_dir)

            assert any("keywords" in w for w in result.warnings)

    def test_validate_all_optional_fields(self):
        """Test validation with all optional fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                """---
name: test-skill
description: A comprehensive test skill for validation testing
license: MIT
compatibility: Python 3.13+, macOS/Linux
allowed-tools: [read_file, write_file]
metadata:
  author: test
  category: testing
---

# Full Instructions

Complete instructions here.
"""
            )

            result = validate_skill(skill_dir)

            assert result.valid is True
            assert len(result.errors) == 0

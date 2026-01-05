"""Unit tests for the skills module."""

import tempfile
from pathlib import Path

import pytest

from extensions.skills.scanner import SkillScanner, SkillMetadata
from extensions.skills.loader import SkillLoader, LRUCache
from extensions.skills.matcher import SkillMatcher, _tokenize, _is_cjk_char
from extensions.skills.injector import SkillInjector
from extensions.skills.validator import SkillValidator, ValidationResult, validate_skill


class TestLRUCache:
    """Tests for LRUCache."""

    def test_set_and_get(self):
        cache = LRUCache(max_size=3)
        cache.set("a", "value_a")
        cache.set("b", "value_b")
        assert cache.get("a") == "value_a"
        assert cache.get("b") == "value_b"

    def test_cache_miss(self):
        cache = LRUCache(max_size=3)
        assert cache.get("nonexistent") is None

    def test_eviction(self):
        cache = LRUCache(max_size=2)
        cache.set("a", "1")
        cache.set("b", "2")
        cache.set("c", "3")  # Should evict "a"
        assert cache.get("a") is None
        assert cache.get("b") == "2"
        assert cache.get("c") == "3"

    def test_lru_order(self):
        cache = LRUCache(max_size=2)
        cache.set("a", "1")
        cache.set("b", "2")
        cache.get("a")  # Access "a" to make it recently used
        cache.set("c", "3")  # Should evict "b" (least recently used)
        assert cache.get("a") == "1"
        assert cache.get("b") is None
        assert cache.get("c") == "3"

    def test_clear(self):
        cache = LRUCache(max_size=3)
        cache.set("a", "1")
        cache.set("b", "2")
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None


class TestCJKTokenization:
    """Tests for CJK character handling."""

    def test_is_cjk_char(self):
        assert _is_cjk_char("中") is True
        assert _is_cjk_char("文") is True
        assert _is_cjk_char("a") is False
        assert _is_cjk_char("1") is False

    def test_tokenize_english(self):
        tokens = _tokenize("This is a test message")
        assert "this" in tokens
        assert "test" in tokens
        assert "message" in tokens
        assert "is" not in tokens  # Too short
        assert "a" not in tokens  # Too short

    def test_tokenize_chinese(self):
        tokens = _tokenize("分析文件内容")
        assert "分" in tokens
        assert "析" in tokens
        assert "文" in tokens
        # Bigrams
        assert "分析" in tokens
        assert "文件" in tokens

    def test_tokenize_mixed(self):
        tokens = _tokenize("分析 Python 代码")
        assert "分析" in tokens
        assert "python" in tokens
        assert "代码" in tokens


class TestSkillMatcher:
    """Tests for SkillMatcher."""

    def setup_method(self):
        self.matcher = SkillMatcher(threshold=0.1)  # Lower threshold for CJK matching
        self.skill1 = SkillMetadata(
            name="file-analyzer",
            description="当用户需要分析文件内容、统计文件信息时使用此skill",
            skill_path=Path("/tmp/skills/file-analyzer"),
            version="1.0.0",
        )
        self.skill2 = SkillMetadata(
            name="code-reviewer",
            description="当用户需要审查代码质量时使用此skill",
            skill_path=Path("/tmp/skills/code-reviewer"),
            version="1.0.0",
        )

    def test_match_by_chinese_keywords(self):
        """Test matching with Chinese keywords."""
        # Use more matching keywords for reliable testing
        matched = self.matcher.match_skills("分析文件内容", [self.skill1, self.skill2])
        assert len(matched) >= 1
        assert self.skill1 in matched

    def test_match_by_skill_name(self):
        """Test matching by skill name."""
        matched = self.matcher.match_skills("use file-analyzer", [self.skill1, self.skill2])
        assert self.skill1 in matched

    def test_no_match(self):
        """Test no match case."""
        matched = self.matcher.match_skills("hello world", [self.skill1, self.skill2])
        # Should not match with unrelated input
        assert len(matched) == 0 or all(
            self.matcher._calculate_match_score("hello world", s) < self.matcher.threshold
            for s in [self.skill1, self.skill2]
        )

    def test_empty_input(self):
        """Test empty input."""
        matched = self.matcher.match_skills("", [self.skill1])
        assert len(matched) == 0

    def test_empty_skills(self):
        """Test empty skills list."""
        matched = self.matcher.match_skills("分析文件", [])
        assert len(matched) == 0


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


class TestSkillLoader:
    """Tests for SkillLoader."""

    def test_load_skill_instructions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                """---
name: test-skill
description: Test
---

# Instructions

Step 1: Do this
Step 2: Do that
"""
            )

            metadata = SkillMetadata(
                name="test-skill",
                description="Test",
                skill_path=skill_dir,
            )

            loader = SkillLoader()
            instructions = loader.load_skill_instructions(metadata)

            assert "# Instructions" in instructions
            assert "Step 1: Do this" in instructions
            assert "---" not in instructions  # Frontmatter should be removed

    def test_load_skill_resource(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            examples_md = skill_dir / "examples.md"
            examples_md.write_text("# Examples\n\nExample content here.")

            metadata = SkillMetadata(
                name="test-skill",
                description="Test",
                skill_path=skill_dir,
            )

            loader = SkillLoader()
            content = loader.load_skill_resource(metadata, "examples.md")

            assert content is not None
            assert "Example content here" in content

    def test_load_nonexistent_resource(self):
        metadata = SkillMetadata(
            name="test-skill",
            description="Test",
            skill_path=Path("/nonexistent"),
        )
        loader = SkillLoader()
        content = loader.load_skill_resource(metadata, "nonexistent.md")
        assert content is None

    def test_caching(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text("---\nname: test\ndescription: test\n---\nContent")

            metadata = SkillMetadata(
                name="test-skill",
                description="Test",
                skill_path=skill_dir,
            )

            loader = SkillLoader()
            result1 = loader.load_skill_instructions(metadata)
            result2 = loader.load_skill_instructions(metadata)

            assert result1 == result2


class TestSkillInjector:
    """Tests for SkillInjector with XML format."""

    def setup_method(self):
        self.injector = SkillInjector()
        self.base_instructions = "You are a helpful assistant."
        self.skill = SkillMetadata(
            name="test-skill",
            description="A test skill",
            skill_path=Path("/tmp"),
            version="1.0.0",
        )

    def test_inject_metadata_summary_xml_format(self):
        """Test that metadata is injected in XML format."""
        skills = [self.skill]
        result = self.injector.inject_metadata_summary(self.base_instructions, skills)

        assert self.base_instructions in result
        assert "<available_skills>" in result
        assert "</available_skills>" in result
        assert "<skill>" in result
        assert "<name>test-skill</name>" in result
        assert "<description>A test skill</description>" in result
        assert "<location>" in result
        assert "<skills_instructions>" in result

    def test_inject_empty_skills(self):
        result = self.injector.inject_metadata_summary(self.base_instructions, [])
        assert result == self.base_instructions

    def test_inject_full_skill_xml_format(self):
        """Test that full skill is injected in XML format."""
        skill_content = "# Test Skill\n\nDo the thing."
        result = self.injector.inject_full_skill(
            self.base_instructions, self.skill, skill_content
        )

        assert self.base_instructions in result
        assert '<skill name="test-skill">' in result
        assert "<instructions>" in result
        assert "Do the thing" in result
        assert "</instructions>" in result
        assert "</skill>" in result

    def test_inject_multiple_skills_xml_format(self):
        """Test that multiple skills are wrapped in active_skills tag."""
        skill2 = SkillMetadata(
            name="another-skill",
            description="Another skill",
            skill_path=Path("/tmp"),
        )
        skills_with_content = [
            (self.skill, "Content 1"),
            (skill2, "Content 2"),
        ]

        result = self.injector.inject_multiple_skills(
            self.base_instructions, skills_with_content
        )

        assert "<active_skills>" in result
        assert "</active_skills>" in result
        assert '<skill name="test-skill">' in result
        assert '<skill name="another-skill">' in result
        assert "Content 1" in result
        assert "Content 2" in result


class TestSkillMetadataXML:
    """Tests for SkillMetadata XML output."""

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

    def test_get_directories(self):
        skill = SkillMetadata(
            name="test-skill",
            description="Test",
            skill_path=Path("/tmp/test-skill"),
        )

        assert skill.get_references_dir() == Path("/tmp/test-skill/references")
        assert skill.get_scripts_dir() == Path("/tmp/test-skill/scripts")
        assert skill.get_assets_dir() == Path("/tmp/test-skill/assets")


class TestSkillLoaderDirectories:
    """Tests for SkillLoader with spec-compliant directories."""

    def test_load_resource_from_references_dir(self):
        """Test loading resource from references/ directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            refs_dir = skill_dir / "references"
            refs_dir.mkdir()
            ref_file = refs_dir / "REFERENCE.md"
            ref_file.write_text("# Reference Content")

            metadata = SkillMetadata(
                name="test-skill",
                description="Test",
                skill_path=skill_dir,
            )

            loader = SkillLoader()
            content = loader.load_skill_resource(metadata, "REFERENCE.md")

            assert content is not None
            assert "Reference Content" in content

    def test_load_script(self):
        """Test loading script from scripts/ directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            scripts_dir = skill_dir / "scripts"
            scripts_dir.mkdir()
            script_file = scripts_dir / "analyze.py"
            script_file.write_text("print('hello')")

            metadata = SkillMetadata(
                name="test-skill",
                description="Test",
                skill_path=skill_dir,
            )

            loader = SkillLoader()
            content = loader.load_script(metadata, "analyze.py")

            assert content is not None
            assert "print('hello')" in content

    def test_list_resources(self):
        """Test listing all available resources."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()

            # Create directories
            (skill_dir / "references").mkdir()
            (skill_dir / "scripts").mkdir()
            (skill_dir / "assets").mkdir()

            # Create files
            (skill_dir / "references" / "REFERENCE.md").write_text("ref")
            (skill_dir / "scripts" / "analyze.py").write_text("script")
            (skill_dir / "assets" / "template.txt").write_text("asset")
            (skill_dir / "examples.md").write_text("legacy")

            metadata = SkillMetadata(
                name="test-skill",
                description="Test",
                skill_path=skill_dir,
            )

            loader = SkillLoader()
            resources = loader.list_resources(metadata)

            assert "REFERENCE.md" in resources["references"]
            assert "analyze.py" in resources["scripts"]
            assert "template.txt" in resources["assets"]
            assert "examples.md" in resources["legacy"]


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

    def test_validate_legacy_files_warning(self):
        """Test warning for legacy resource files in root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "test-skill"
            skill_dir.mkdir()
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                """---
name: test-skill
description: A test skill for testing purposes with keywords
---

Instructions here.
"""
            )
            # Create legacy file
            (skill_dir / "examples.md").write_text("examples")

            result = validate_skill(skill_dir)

            assert any("references/" in w for w in result.warnings)

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


class TestSkillScannerExtendedFields:
    """Tests for SkillScanner with extended fields."""

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

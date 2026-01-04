"""Unit tests for the skills module."""

import tempfile
from pathlib import Path

import pytest

from skills.scanner import SkillScanner, SkillMetadata
from skills.loader import SkillLoader, LRUCache
from skills.matcher import SkillMatcher, _tokenize, _is_cjk_char
from skills.injector import SkillInjector


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
    """Tests for SkillInjector."""

    def setup_method(self):
        self.injector = SkillInjector()
        self.base_instructions = "You are a helpful assistant."
        self.skill = SkillMetadata(
            name="test-skill",
            description="A test skill",
            skill_path=Path("/tmp"),
            version="1.0.0",
        )

    def test_inject_metadata_summary(self):
        skills = [self.skill]
        result = self.injector.inject_metadata_summary(self.base_instructions, skills)

        assert self.base_instructions in result
        assert "Available Skills" in result
        assert "test-skill" in result

    def test_inject_empty_skills(self):
        result = self.injector.inject_metadata_summary(self.base_instructions, [])
        assert result == self.base_instructions

    def test_inject_full_skill(self):
        skill_content = "# Test Skill\n\nDo the thing."
        result = self.injector.inject_full_skill(
            self.base_instructions, self.skill, skill_content
        )

        assert self.base_instructions in result
        assert "Active Skill: test-skill" in result
        assert "Do the thing" in result
        assert "Skill Resources Directory" in result
        assert str(self.skill.skill_path) in result

    def test_inject_multiple_skills(self):
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

        assert "Active Skills" in result
        assert "test-skill" in result
        assert "another-skill" in result
        assert "Content 1" in result
        assert "Content 2" in result
        assert "Skill Resources Directory" in result
        assert str(self.skill.skill_path) in result

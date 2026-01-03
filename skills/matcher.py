"""Skill matcher for determining which skills to activate."""

import re
from typing import List

from skills.scanner import SkillMetadata


def _is_cjk_char(char: str) -> bool:
    """Check if a character is CJK (Chinese, Japanese, Korean)."""
    code = ord(char)
    return (
        0x4E00 <= code <= 0x9FFF  # CJK Unified Ideographs
        or 0x3400 <= code <= 0x4DBF  # CJK Extension A
        or 0x3000 <= code <= 0x303F  # CJK Punctuation
        or 0xFF00 <= code <= 0xFFEF  # Fullwidth chars
    )


def _has_cjk(text: str) -> bool:
    """Check if text contains CJK characters."""
    return any(_is_cjk_char(c) for c in text)


def _tokenize(text: str) -> set[str]:
    """Tokenize text, handling both CJK and non-CJK content.

    For CJK text, extract individual characters and common 2-char phrases.
    For non-CJK text, extract words longer than 2 characters.
    """
    tokens = set()
    text = text.lower()

    # Extract non-CJK words (3+ chars to avoid noise)
    words = re.findall(r'[a-z]+', text)
    tokens.update(w for w in words if len(w) > 2)

    # Extract CJK characters and bigrams
    cjk_chars = [c for c in text if _is_cjk_char(c)]
    tokens.update(cjk_chars)  # Single chars

    # Add bigrams for better matching
    for i in range(len(cjk_chars) - 1):
        tokens.add(cjk_chars[i] + cjk_chars[i + 1])

    return tokens


class SkillMatcher:
    """Matcher for finding relevant skills based on user input."""

    def __init__(self, threshold: float = 0.3):
        """Initialize matcher.

        Args:
            threshold: Minimum match score (0-1) to consider a skill relevant.
        """
        self.threshold = threshold

    def match_skills(
        self, user_input: str, skills: list[SkillMetadata]
    ) -> list[SkillMetadata]:
        """Find skills that match user input.

        Uses simple keyword matching. For production, could use:
        - Semantic embeddings (e.g., sentence-transformers)
        - LLM-based classification
        - More sophisticated NLP

        Args:
            user_input: User's input text.
            skills: List of available SkillMetadata.

        Returns:
            List of matching SkillMetadata objects.
        """
        if not user_input or not skills:
            return []

        user_input_lower = user_input.lower()
        matched = []

        for skill in skills:
            score = self._calculate_match_score(user_input_lower, skill)
            if score >= self.threshold:
                matched.append((skill, score))

        # Sort by score (highest first)
        matched.sort(key=lambda x: x[1], reverse=True)

        return [skill for skill, _ in matched]

    def _calculate_match_score(self, user_input: str, skill: SkillMetadata) -> float:
        """Calculate match score between user input and skill.

        Simple keyword-based scoring:
        - Check if skill name appears in input
        - Check for keywords from description (supports CJK languages)

        Args:
            user_input: Lowercased user input.
            skill: SkillMetadata object.

        Returns:
            Match score (0-1).
        """
        score = 0.0

        # Check if skill name appears in input
        if skill.name.lower() in user_input:
            score += 0.5

        # Tokenize description and user input (supports CJK)
        description_tokens = _tokenize(skill.description)
        user_tokens = _tokenize(user_input)

        if description_tokens and user_tokens:
            overlap = description_tokens.intersection(user_tokens)
            overlap_ratio = len(overlap) / len(description_tokens)
            score += overlap_ratio * 0.5

        return min(score, 1.0)  # Cap at 1.0

"""Skill matcher for determining which skills to activate."""

from typing import List

from skills.scanner import SkillMetadata


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
        - Check for keywords from description

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

        # Extract keywords from description and check overlap
        description_lower = skill.description.lower()
        description_words = set(
            word.strip(".,!?;:")
            for word in description_lower.split()
            if len(word) > 3  # Only consider words longer than 3 chars
        )

        user_words = set(
            word.strip(".,!?;:")
            for word in user_input.split()
            if len(word) > 3
        )

        if description_words and user_words:
            overlap = description_words.intersection(user_words)
            overlap_ratio = len(overlap) / len(description_words)
            score += overlap_ratio * 0.5

        return min(score, 1.0)  # Cap at 1.0

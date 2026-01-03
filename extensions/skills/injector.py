"""Skill injector for adding skills to agent instructions."""

from .scanner import SkillMetadata


class SkillInjector:
    """Injector for adding skills to agent instructions."""

    def inject_metadata_summary(
        self, base_instructions: str, skills: list[SkillMetadata]
    ) -> str:
        """Inject Level 1 metadata summary into agent instructions.

        Args:
            base_instructions: Original agent instructions.
            skills: List of all available skills.

        Returns:
            Enhanced instructions with skills metadata.
        """
        if not skills:
            return base_instructions

        summary_lines = [
            "",
            "---",
            "",
            "## Available Skills",
            "",
            "You have access to the following specialized skills. "
            "These skills will be automatically activated when relevant to the user's request:",
            "",
        ]

        for skill in skills:
            summary_lines.append(f"- **{skill.name}**: {skill.description}")

        summary = "\n".join(summary_lines)
        return base_instructions + summary

    def inject_full_skill(
        self, base_instructions: str, skill_metadata: SkillMetadata, skill_content: str
    ) -> str:
        """Inject Level 2 full skill instructions into agent instructions.

        Args:
            base_instructions: Original agent instructions.
            skill_metadata: Metadata of the skill being injected.
            skill_content: Full skill instructions content.

        Returns:
            Enhanced instructions with full skill content.
        """
        if not skill_content:
            return base_instructions

        skill_section = [
            "",
            "---",
            "",
            f"## Active Skill: {skill_metadata.name}",
            "",
            f"*{skill_metadata.description}*",
            "",
            skill_content,
        ]

        skill_text = "\n".join(skill_section)
        return base_instructions + skill_text

    def inject_multiple_skills(
        self,
        base_instructions: str,
        skills_with_content: list[tuple[SkillMetadata, str]],
    ) -> str:
        """Inject multiple full skills into agent instructions.

        Args:
            base_instructions: Original agent instructions.
            skills_with_content: List of (SkillMetadata, content) tuples.

        Returns:
            Enhanced instructions with all skill contents.
        """
        enhanced = base_instructions

        if not skills_with_content:
            return enhanced

        enhanced += "\n\n---\n\n## Active Skills\n"
        enhanced += "\nThe following skills are active for this request:\n\n"

        for skill_metadata, skill_content in skills_with_content:
            enhanced += f"### {skill_metadata.name}\n\n"
            enhanced += f"*{skill_metadata.description}*\n\n"
            enhanced += skill_content + "\n\n"

        return enhanced

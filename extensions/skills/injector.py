"""Skill injector for adding skills to agent instructions.

Follows the Agent Skills specification: https://agentskills.io/specification
Uses XML format for skill injection as recommended by the specification.
"""

from .scanner import SkillMetadata

# Instruction template for skill activation
SKILLS_INSTRUCTION = """
<skills_instructions>
When users ask you to perform tasks, check if any of the available skills below can help complete the task more effectively. Skills provide specialized capabilities and domain knowledge.

How to use skills:
- Skills are automatically activated when user input matches skill descriptions
- When a skill is activated, you will receive detailed instructions for that skill
- You can use file reading tools to access resources in the skill's directory (references/, scripts/, assets/)
- Examples:
  - If user asks to "analyze this file", the file-analyzer skill may be activated
  - If user asks to "review code quality", the code-reviewer skill may be activated

Important:
- Only use skills listed in <available_skills> below
- Follow skill instructions carefully when activated
- Skills enhance your capabilities but don't replace your core judgment
</skills_instructions>
"""


class SkillInjector:
    """Injector for adding skills to agent instructions.

    Uses XML format following Agent Skills specification for better
    model recognition and processing.
    """

    def inject_metadata_summary(
        self, base_instructions: str, skills: list[SkillMetadata]
    ) -> str:
        """Inject Level 1 metadata summary into agent instructions using XML format.

        Args:
            base_instructions: Original agent instructions.
            skills: List of all available skills.

        Returns:
            Enhanced instructions with skills metadata in XML format.
        """
        if not skills:
            return base_instructions

        # Build XML format as per Agent Skills specification
        xml_lines = ["<available_skills>"]
        for skill in skills:
            xml_lines.append("  <skill>")
            xml_lines.append(f"    <name>{skill.name}</name>")
            xml_lines.append(f"    <description>{skill.description}</description>")
            xml_lines.append(f"    <location>{skill.skill_path}</location>")
            xml_lines.append("  </skill>")
        xml_lines.append("</available_skills>")

        skills_xml = "\n".join(xml_lines)

        return base_instructions + "\n" + SKILLS_INSTRUCTION + "\n" + skills_xml

    def inject_full_skill(
        self, base_instructions: str, skill_metadata: SkillMetadata, skill_content: str
    ) -> str:
        """Inject Level 2 full skill instructions into agent instructions.

        Args:
            base_instructions: Original agent instructions.
            skill_metadata: Metadata of the skill being injected.
            skill_content: Full skill instructions content.

        Returns:
            Enhanced instructions with full skill content in XML format.
        """
        if not skill_content:
            return base_instructions

        skill_section = self._format_active_skill(skill_metadata, skill_content)
        return base_instructions + "\n\n" + skill_section

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
            Enhanced instructions with all skill contents in XML format.
        """
        if not skills_with_content:
            return base_instructions

        active_skills_parts = ["<active_skills>"]

        for skill_metadata, skill_content in skills_with_content:
            active_skills_parts.append(
                self._format_active_skill(skill_metadata, skill_content)
            )

        active_skills_parts.append("</active_skills>")
        active_skills_xml = "\n".join(active_skills_parts)

        return base_instructions + "\n\n" + active_skills_xml

    def _format_active_skill(
        self, skill_metadata: SkillMetadata, skill_content: str
    ) -> str:
        """Format a single active skill in XML format.

        Args:
            skill_metadata: Metadata of the skill.
            skill_content: Full skill instructions content.

        Returns:
            Formatted skill section in XML.
        """
        # Build resource directories info
        resources_info = self._build_resources_info(skill_metadata)

        lines = [
            f"<skill name=\"{skill_metadata.name}\">",
            f"<description>{skill_metadata.description}</description>",
            f"<location>{skill_metadata.skill_path}</location>",
        ]

        if resources_info:
            lines.append(f"<resources>{resources_info}</resources>")

        lines.append("<instructions>")
        lines.append(skill_content)
        lines.append("</instructions>")
        lines.append("</skill>")

        return "\n".join(lines)

    def _build_resources_info(self, skill_metadata: SkillMetadata) -> str:
        """Build resources info string for a skill.

        Args:
            skill_metadata: Metadata of the skill.

        Returns:
            Formatted resources info string.
        """
        resources = []

        # Check for standard directories per specification
        refs_dir = skill_metadata.get_references_dir()
        scripts_dir = skill_metadata.get_scripts_dir()
        assets_dir = skill_metadata.get_assets_dir()

        if refs_dir.exists():
            resources.append(f"references: {refs_dir}")
        if scripts_dir.exists():
            resources.append(f"scripts: {scripts_dir}")
        if assets_dir.exists():
            resources.append(f"assets: {assets_dir}")

        # Also check for legacy resource files in skill root
        skill_path = skill_metadata.skill_path
        for legacy_file in ["examples.md", "reference.md"]:
            legacy_path = skill_path / legacy_file
            if legacy_path.exists():
                resources.append(f"{legacy_file}: {legacy_path}")

        return "; ".join(resources) if resources else ""

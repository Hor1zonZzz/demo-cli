"""Skill injector for adding skills awareness to agent instructions.

Follows the Agent Skills specification: https://agentskills.io/specification
Uses XML format for skill injection as recommended by the specification.

The agent dynamically loads skill instructions using file reading tools
when needed, based on the <location> path provided.
"""

from .scanner import SkillMetadata

# Instruction template guiding agent to load skills on-demand
SKILLS_INSTRUCTION = """
<skills_instructions>
You have access to specialized skills that provide domain expertise and detailed workflows.

## What are Skills?
Skills are instruction sets located in directories containing a SKILL.md file.
Each skill provides step-by-step guidance for specific tasks.

## How to Use Skills
1. Review <available_skills> below to find skills matching the user's task
2. When a skill is relevant, use read_file to load `<location>/SKILL.md`
3. Follow the skill's instructions carefully to complete the task
4. Skills may have additional resources in subdirectories:
   - references/ - documentation and guides
   - scripts/ - executable code
   - assets/ - templates and static files

## Important
- Only load a skill when it's clearly relevant to the current task
- Read the full SKILL.md before starting the task
- You can access any file within the skill's directory using read_file
</skills_instructions>
"""


def inject_skills(base_instructions: str, skills: list[SkillMetadata]) -> str:
    """Inject skills awareness into agent instructions.

    Adds <skills_instructions> and <available_skills> to the base instructions,
    enabling the agent to discover and load skills on-demand.

    Args:
        base_instructions: Original agent instructions.
        skills: List of available SkillMetadata objects.

    Returns:
        Enhanced instructions with skills awareness.
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

# Changelog

All notable changes to demo-cli will be documented in this file.

## [Unreleased]

### Added

- **Skills System with Progressive Loading**: Implemented Agent Skills open standard support
  - Level 1 (Metadata): Loads only skill names and descriptions at startup (~30-50 tokens per skill)
  - Level 2 (Instructions): Loads full SKILL.md content when user input matches skill description
  - Level 3 (Resources): On-demand loading of reference files and examples
  - Automatic skill discovery from `.claude/skills/` directory
  - Smart skill matching based on user input keywords
  - Visual feedback showing activated skills (🔧 icon)

- **Skills Module Components**:
  - `SkillScanner`: Discovers and parses skill metadata from SKILL.md files
  - `SkillLoader`: Loads full skill instructions and resources with caching
  - `SkillMatcher`: Matches user input to relevant skills using keyword scoring
  - `SkillInjector`: Injects skills into agent instructions dynamically

- **Example Skills**:
  - `file-analyzer`: Expert mode for analyzing file contents, structure, and code quality
  - `code-reviewer`: Expert mode for code review, best practices, and improvement suggestions

- **Documentation**:
  - `SKILLS_DESIGN.md`: Comprehensive design documentation for the skills system
  - `.claude/skills/README.md`: Guide for using and creating skills
  - Enhanced README with skills usage instructions

### Changed

- Updated `create_assistant()` to accept optional `enhanced_instructions` parameter
- Modified `App.__init__()` to initialize skills components at startup
- Enhanced `App._run_agent()` to perform skill matching and injection
- Updated `App._show_welcome()` to display loaded skills count
- Added `pyyaml>=6.0.0` dependency for YAML frontmatter parsing
- Added `skills` package to build configuration

## [0.1.0] - Previous Version

### Added
- Initial CLI agent implementation
- File operation tools (read, write, list, delete, exists)
- Session management
- Slash command system
- DeepSeek API integration

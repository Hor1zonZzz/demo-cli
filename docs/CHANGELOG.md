# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Local tracing for agent execution debugging (`ENABLE_TRACING` env var)
- `core/tracing.py` with `LocalTracingProcessor` for console/file logging
- Trace file output to `data/traces/` directory

### Changed

- **BREAKING**: Renamed `cli_agents/` to `demo_agents/` to avoid openai-agents package conflict
- **BREAKING**: Moved `mcp_support/` to `extensions/mcp/`
- **BREAKING**: Moved `skills/` to `extensions/skills/`
- Introduced `core/` layer with `ContextManager` and `AgentRunner`
- Introduced `extensions/` layer with unified `ExtensionManager`
- Added `tools/registry.py` for unified tool registration
- Added `PathConfig` to `config.py` for centralized path management
- Slimmed down `cli/app.py` by extracting business logic to core layer

## [0.2.0] - 2026-01-03

### Added

- Automatic context compression when token usage exceeds threshold
- Skills system with progressive loading (Level 1/2/3)
- `SkillScanner`, `SkillLoader`, `SkillMatcher`, `SkillInjector` components
- Example skills: `file-analyzer`, `code-reviewer`
- Environment variables for compression: `MODEL_MAX_CONTEXT_TOKENS`, `CONTEXT_COMPRESSION_THRESHOLD`, `CONTEXT_COMPRESSION_KEEP_LAST_MESSAGES`

### Changed

- `create_assistant()` now accepts `enhanced_instructions` parameter
- Added `pyyaml>=6.0.0` dependency

## [0.1.0] - 2026-01-01

### Added

- Initial CLI agent implementation
- File operation tools (read, write, list, delete, exists)
- Session management with file-based persistence
- Slash command system (`/help`, `/tools`, `/clear`, `/session`, `/exit`)
- MCP server integration
- DeepSeek API integration

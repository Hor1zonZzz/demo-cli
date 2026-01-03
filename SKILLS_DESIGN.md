# Skills 渐进式加载设计文档

## 背景

基于 Agent Skills 开放标准（agentskills.io），为 demo-cli 项目实现 skills 渐进式加载功能。

## 核心发现

- **openai-agents SDK 0.6.4 不支持原生 skills**
- Agent Skills 是开放标准（Anthropic 发布，2025年12月18日）
- 需要自定义实现 skills 加载机制

## 设计目标

1. 遵循 Agent Skills 标准格式
2. 实现三级渐进式加载架构
3. 自动发现并注入 skills 到项目启动流程
4. 最小化启动时的 token 消耗

## 目录结构

遵循标准的 Claude Code skills 结构：

```
.claude/skills/
├── file-analyzer/
│   ├── SKILL.md          # 必需：skill定义
│   ├── reference.md      # 可选：参考文档
│   └── examples.md       # 可选：使用示例
└── code-reviewer/
    └── SKILL.md
```

## SKILL.md 格式

```markdown
---
name: skill-identifier
description: 当需要XXX时使用此skill。它可以帮助...
allowed-tools: [read_file, write_file]  # 可选
model: deepseek-chat                      # 可选
---

# Skill Instructions

这里是详细的指令...

## Steps
1. 步骤1
2. 步骤2
```

## 三级渐进式加载架构

### Level 1: Metadata Loading (~100 tokens)

**触发时机：** 应用启动时

**加载内容：**
- Skill name
- Skill description
- 元数据（allowed-tools, model）

**实现：**
- 扫描 `.claude/skills/` 目录
- 解析每个 SKILL.md 的 YAML frontmatter
- 存储为轻量级元数据列表

**Token 消耗：** 每个 skill 约 30-50 tokens

### Level 2: Full Instructions Loading

**触发时机：** 用户输入语义匹配 skill description

**加载内容：**
- 完整的 SKILL.md markdown 内容
- 注入到 agent instructions

**实现：**
- 使用简单的关键词匹配或语义相似度
- 动态扩展 agent instructions
- 缓存已加载的 skills

**Token 消耗：** 每个 skill 最多 5000 tokens

### Level 3: Resources Loading

**触发时机：** Agent 执行过程中按需加载

**加载内容：**
- reference.md
- examples.md
- 其他支持文件

**实现：**
- 作为工具结果返回
- 或作为额外上下文注入

## 实现组件

### 1. `skills/scanner.py`

```python
class SkillScanner:
    """扫描和发现 skills"""

    def scan_skills_directory(self, path: str) -> list[SkillMetadata]:
        """扫描 skills 目录，返回元数据列表"""

    def parse_skill_metadata(self, skill_md: str) -> SkillMetadata:
        """解析 SKILL.md 的 frontmatter"""
```

### 2. `skills/loader.py`

```python
class SkillLoader:
    """加载 skill 完整内容"""

    def load_skill_instructions(self, skill_name: str) -> str:
        """加载完整的 SKILL.md 内容"""

    def load_skill_resource(self, skill_name: str, resource: str) -> str:
        """加载 skill 的支持文件"""
```

### 3. `skills/injector.py`

```python
class SkillInjector:
    """将 skills 注入到 agent"""

    def inject_metadata(self, agent_instructions: str, skills: list[SkillMetadata]) -> str:
        """在 agent instructions 中注入 skills 元数据"""

    def inject_full_skill(self, agent_instructions: str, skill_content: str) -> str:
        """注入完整的 skill 指令"""
```

### 4. `skills/matcher.py`

```python
class SkillMatcher:
    """匹配用户输入和 skills"""

    def match_skills(self, user_input: str, skills: list[SkillMetadata]) -> list[str]:
        """返回匹配的 skill names"""
```

## 集成流程

### 启动时（Level 1）

```python
# cli/app.py
def __init__(self):
    # ... 现有代码 ...
    self.skill_scanner = SkillScanner()
    self.skill_loader = SkillLoader()
    self.skills_metadata = self.skill_scanner.scan_skills_directory(".claude/skills")
```

### 处理用户输入时（Level 2）

```python
async def _handle_chat(self, user_input: str) -> None:
    # 匹配相关 skills
    matched_skills = self.skill_matcher.match_skills(user_input, self.skills_metadata)

    # 加载匹配的 skills
    skill_instructions = []
    for skill_name in matched_skills:
        content = self.skill_loader.load_skill_instructions(skill_name)
        skill_instructions.append(content)

    # 创建增强的 agent
    agent = create_assistant(extra_skills=skill_instructions)

    # ... 现有代码 ...
```

## 优势

1. **可扩展性：** 支持无限数量的 skills，启动开销固定
2. **标准兼容：** 遵循开放的 Agent Skills 标准
3. **渐进式：** 只在需要时加载完整内容
4. **灵活性：** 支持项目级和用户级 skills
5. **向后兼容：** 不影响现有功能

## 测试计划

1. 创建示例 skills（文件分析、代码审查）
2. 测试元数据加载性能
3. 测试匹配准确性
4. 测试完整 instructions 注入
5. 端到端集成测试

## 参考资料

- [Agent Skills 官方文档](https://code.claude.com/docs/en/skills)
- [Agent Skills 开放标准](https://agentskills.io)
- [Claude Skills Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [Anthropic Engineering - Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

# Skills 系统设计文档

## 背景

基于 [Agent Skills 开放标准](https://agentskills.io)，为 demo-cli 项目实现简化的 skills 按需加载功能。

## 设计原则

1. **遵循 Agent Skills 标准**：使用 XML 格式注入 skills 信息
2. **Agent 自主加载**：Agent 使用文件读取工具按需加载 skill 内容
3. **最小化复杂度**：无需 matcher/loader 组件，Agent 自行决策
4. **Token 高效**：启动时只加载元数据，完整内容按需加载

## 目录结构

```
.demo-cli/skills/
├── README.md              # Skills 使用说明
├── file-analyzer/
│   ├── SKILL.md           # 必需：skill 定义
│   ├── references/        # 可选：参考文档
│   ├── scripts/           # 可选：可执行脚本
│   └── assets/            # 可选：模板和静态文件
└── code-reviewer/
    └── SKILL.md
```

## SKILL.md 格式

遵循 Agent Skills 规范的 YAML frontmatter：

```markdown
---
name: skill-identifier
version: 1.0.0
description: 清晰描述此 skill 的用途和适用场景。
allowed-tools: [read_file, write_file]  # 可选
model: deepseek-chat                     # 可选
license: MIT                             # 可选
compatibility: ">=1.0.0"                 # 可选
metadata:                                # 可选
  author: "Your Name"
  tags: "analysis, code"
---

# Skill Instructions

详细的任务指令...

## Steps
1. 步骤1
2. 步骤2
```

## 系统架构

### 组件

```
extensions/skills/
├── __init__.py        # 模块导出
├── scanner.py         # SkillScanner - 发现和解析 skill 元数据
├── injector.py        # inject_skills() - 注入 skills 到系统提示
└── validator.py       # SkillValidator - 验证 skill 格式
```

### 数据流

```
启动时:
  SkillScanner.scan_skills_directory()
    → 扫描 .demo-cli/skills/
    → 解析每个 SKILL.md 的 YAML frontmatter
    → 返回 list[SkillMetadata]

创建 Agent 时:
  inject_skills(base_instructions, skills)
    → 添加 <skills_instructions> 指导 Agent 如何使用 skills
    → 添加 <available_skills> XML 列出所有可用 skills
    → 返回增强后的 instructions

Agent 运行时:
  Agent 分析用户请求
    → 判断是否需要某个 skill
    → 使用 read_file(<location>/SKILL.md) 加载完整内容
    → 遵循 skill 指令完成任务
    → 可选：使用 read_file 访问 skill 目录下的其他资源
```

## 注入格式

### Skills Instructions

```xml
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
```

### Available Skills XML

```xml
<available_skills>
  <skill>
    <name>file-analyzer</name>
    <description>分析文件内容、统计信息、代码质量</description>
    <location>.demo-cli/skills/file-analyzer</location>
  </skill>
  <skill>
    <name>code-reviewer</name>
    <description>审查代码质量、检查规范、提供改进建议</description>
    <location>.demo-cli/skills/code-reviewer</location>
  </skill>
</available_skills>
```

## 实现组件

### SkillScanner (`scanner.py`)

```python
@dataclass
class SkillMetadata:
    name: str
    description: str
    skill_path: Path
    version: Optional[str] = None
    allowed_tools: Optional[list[str]] = None
    model: Optional[str] = None
    license: Optional[str] = None
    compatibility: Optional[str] = None
    metadata: Optional[dict[str, str]] = None

class SkillScanner:
    def scan_skills_directory(self) -> list[SkillMetadata]:
        """扫描 skills 目录，返回元数据列表"""

    def parse_skill_metadata(self, skill_md_path: Path) -> Optional[SkillMetadata]:
        """解析 SKILL.md 的 frontmatter"""
```

### inject_skills (`injector.py`)

```python
def inject_skills(base_instructions: str, skills: list[SkillMetadata]) -> str:
    """将 skills 信息注入到 agent instructions"""
```

### SkillValidator (`validator.py`)

```python
class SkillValidator:
    def validate_skill(self, skill_path: Path) -> ValidationResult:
        """验证 skill 格式是否符合规范"""

    def validate_all_skills(self, skills_dir: Path) -> list[ValidationResult]:
        """验证目录下所有 skills"""
```

## 与旧架构对比

### 旧架构（已移除）

- `SkillMatcher`: 基于关键词匹配用户输入
- `SkillLoader`: 显式加载 skill 内容
- 三级渐进式加载（Level 1/2/3）
- 系统决定何时加载哪个 skill

### 新架构

- Agent 自主决定加载时机
- 使用文件读取工具直接访问 skill 内容
- 更简洁的代码结构
- 更灵活的加载策略

## 优势

1. **简洁性**：减少约 500+ 行代码
2. **灵活性**：Agent 自主决策，更智能
3. **标准兼容**：完全遵循 Agent Skills 规范
4. **可维护性**：组件职责单一，易于理解
5. **可扩展性**：支持任意数量的 skills

## 测试

```bash
# 运行 skills 测试
pytest tests/test_skills.py -v
```

测试覆盖：
- SkillScanner 发现和解析
- SkillMetadata 数据结构
- inject_skills() 注入格式
- SkillValidator 验证逻辑

## 参考资料

- [Agent Skills 开放标准](https://agentskills.io)
- [Agent Skills 规范](https://agentskills.io/specification)
- [Agent Skills 集成指南](https://agentskills.io/integrate-skills)

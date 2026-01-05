# Demo-CLI Skills 目录

这个目录包含 demo-cli 的 Agent Skills，遵循 [Agent Skills 开放标准](https://agentskills.io)。

## 工作原理

1. **启动时**：系统扫描此目录，加载每个 skill 的元数据（名称、描述、路径）
2. **注入提示**：`<available_skills>` XML 被注入到 Agent 的系统提示中
3. **按需加载**：Agent 根据用户请求，使用 `read_file` 工具加载相关 skill 的完整内容

## 可用 Skills

### 1. file-analyzer

**描述**: 文件内容分析专家

**使用场景**:
- 分析文件结构和内容
- 统计文件信息（行数、大小等）
- 评估代码质量
- 识别文件模式和问题

### 2. code-reviewer

**描述**: 代码审查专家

**使用场景**:
- 审查代码质量
- 检查编码规范
- 识别潜在问题和bug
- 提供改进建议

## 如何添加新 Skill

1. 在此目录创建新文件夹：`.demo-cli/skills/your-skill-name/`
2. 创建 `SKILL.md` 文件，包含 YAML frontmatter 和详细指令
3. （可选）创建资源子目录：
   - `references/` - 参考文档
   - `scripts/` - 可执行脚本
   - `assets/` - 模板和静态文件
4. 重启 demo-cli，新 skill 会自动发现

## Skill 目录结构

```
your-skill-name/
├── SKILL.md           # 必需：skill 定义和指令
├── references/        # 可选：参考文档
│   └── guide.md
├── scripts/           # 可选：可执行脚本
│   └── helper.py
└── assets/            # 可选：模板和静态文件
    └── template.txt
```

## SKILL.md 格式

```markdown
---
name: your-skill-name
version: 1.0.0
description: 清晰描述此 skill 的用途和适用场景。
allowed-tools: [read_file, write_file]  # 可选
license: MIT                             # 可选
---

# Skill Name

简短介绍这个 skill 的作用。

## 职责

明确列出这个 skill 的具体职责。

## 步骤

1. 第一步做什么
2. 第二步做什么
3. ...

## 输出格式

提供清晰的输出模板或示例。

## 注意事项

- 特殊情况处理
- 边界条件
- 质量标准
```

## Skill 编写最佳实践

### 好的描述示例

```yaml
description: 当用户需要分析Python代码性能、识别瓶颈、或优化算法复杂度时使用此skill。
```

### 不好的描述示例

```yaml
description: 代码分析工具  # 太笼统
```

### 指令编写建议

- 使用清晰的步骤说明
- 提供具体的输出格式
- 说明边界情况和注意事项
- 包含实际示例（可放在 references/ 中）

## 了解更多

- [SKILLS_DESIGN.md](../../docs/SKILLS_DESIGN.md) - 系统设计文档
- [Agent Skills 标准](https://agentskills.io) - 开放标准规范
- [Agent Skills 集成指南](https://agentskills.io/integrate-skills) - 集成方法

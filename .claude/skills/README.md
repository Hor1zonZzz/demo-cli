# Demo-CLI Skills 目录

这个目录包含 demo-cli 的 Agent Skills。

## 可用 Skills

### 1. file-analyzer

**描述**: 文件内容分析专家

**使用场景**:
- 分析文件结构和内容
- 统计文件信息（行数、大小等）
- 评估代码质量
- 识别文件模式和问题

**触发关键词**: 分析文件、检查文件、统计、文件信息

### 2. code-reviewer

**描述**: 代码审查专家

**使用场景**:
- 审查代码质量
- 检查编码规范
- 识别潜在问题和bug
- 提供改进建议

**触发关键词**: 审查代码、代码质量、代码规范、改进建议

## 如何添加新 Skill

1. 在此目录创建新文件夹：`.claude/skills/your-skill-name/`
2. 创建 `SKILL.md` 文件，包含：
   - YAML frontmatter（name, description）
   - 详细的 instructions
3. （可选）添加 `examples.md`、`reference.md` 等支持文件
4. 重启 demo-cli，新 skill 会自动加载

## Skill 编写最佳实践

### 好的描述示例

```yaml
description: 当用户需要分析Python代码性能、识别瓶颈、或优化算法复杂度时使用此skill。关注时间复杂度、空间复杂度和性能优化建议。
```

### 不好的描述示例

```yaml
description: 代码分析工具  # 太笼统，缺少触发关键词
```

### Instructions 结构建议

```markdown
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

## 调试 Skills

如果 skill 没有被激活：

1. 检查描述是否包含相关关键词
2. 确保 SKILL.md 格式正确（YAML frontmatter）
3. 使用更具体的用户请求
4. 检查 skill 名称和目录结构

## 了解更多

- [SKILLS_DESIGN.md](../SKILLS_DESIGN.md) - 系统设计文档
- [Agent Skills 标准](https://agentskills.io) - 开放标准规范
- [Claude Code Skills](https://code.claude.com/docs/en/skills) - 官方文档

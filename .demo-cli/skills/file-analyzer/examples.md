# File Analyzer Examples

## Example 1: Analyzing a Python file

**User request:** "分析一下 main.py 文件"

**Analysis output:**

```markdown
# 文件分析报告: main.py

## 基本信息
- 文件类型: Python 源代码
- 总行数: 42
- 编码: UTF-8

## 内容分析

### 结构
- 导入语句: 6 个
- 函数定义: 2 个 (setup_deepseek_client, main)
- 主要功能: CLI 应用入口点

### 依赖
- dotenv: 环境变量加载
- openai: AsyncOpenAI 客户端
- agents: Agent SDK 集成

### 代码质量
- 清晰的函数职责划分
- 良好的错误处理（API key 检查）
- 适当的文档字符串

## 建议
- 考虑将配置逻辑提取到单独的配置模块
- 可以添加日志记录以便调试
```

## Example 2: Directory analysis

**User request:** "分析 tools 目录下的文件"

**Expected behavior:**
1. List directory contents
2. Read each file
3. Provide summary of each file's purpose
4. Suggest improvements to the module organization

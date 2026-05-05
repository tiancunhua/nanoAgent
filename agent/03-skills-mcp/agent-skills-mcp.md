# 从零开始理解 Agent（三）：Rules、Skills 与 MCP 如何外置能力

> **「从零开始理解 Agent」系列** —— 通过一个极简开源项目 [nanoAgent](https://github.com/GitHubxsy/nanoAgent)，逐层拆解 Agent 背后的核心机制。
>
> - [第一篇：底层原理，约 100 行](../01-essence/agent-essence.md) —— 工具 + 循环
> - [第二篇：Memory](../02-memory/agent-memory.md) —— 让 Agent 记住上一次
> - **第三篇：Rules、Skills 与 MCP**（本文）—— 把能力从代码里拿出来

第一讲让模型能动手，第二讲让模型能记住上一次。第三讲继续往前走：**不要把所有行为、知识和工具都硬编码进 Python 文件里**。

本讲只讲三件事：

1. **Rules**：把项目规则写成文件，启动时注入 prompt。
2. **Skills**：把可复用的任务方法写成 Markdown，启动时注入 prompt。
3. **MCP**：把外部工具定义写成配置，启动时追加到 tools 列表。

这就是能力外置。

---

## 一、为什么要外置能力？

如果所有东西都写死在脚本里，会遇到三个问题：

| 问题 | 外置方式 |
|------|----------|
| 不同项目有不同规范 | 用 `.agent/rules/*.md` |
| 不同任务有不同做法 | 用 `.agent/skills/*/SKILL.md` |
| 不同环境要接不同工具 | 用 `.agent/mcp.json` |

第三讲的重点不是让 Agent 更“聪明”，而是让能力变得可替换、可观察、可配置。

---

## 二、Rule：项目规则进入 prompt

```python
RULES_DIR = ".agent/rules"

def load_rules():
    rules = []
    if not os.path.exists(RULES_DIR):
        return ""
    try:
        for rule_file in sorted(Path(RULES_DIR).glob("*.md")):
            with open(rule_file, "r") as f:
                rules.append(f"# {rule_file.stem}\n{f.read()}")
        return "\n\n".join(rules) if rules else ""
    except:
        return ""
```

Rule 是项目级约束。演示里的最小 Rule 是：

```markdown
# Demo Style

- 回答开头只说明本轮加载了 Rule、Skill、MCP 三类外置能力，不展开工具名。
- 修复优先级最多保留 3 项，顺序从安全风险、阻塞运行、核心功能到文档示例。
- 如果调用了 MCP 工具，在结论里说明它返回了什么。
```

它不是工具，模型不会“调用” Rule。它的作用方式更直接：启动时拼进 system prompt，让模型从一开始就看到这些约束。

---

## 三、Skill：任务方法进入 prompt

```python
SKILLS_DIR = ".agent/skills"

def load_skills():
    skills = []
    if not os.path.exists(SKILLS_DIR):
        return []
    try:
        skill_files = sorted(Path(SKILLS_DIR).glob("*/SKILL.md")) + sorted(
            Path(SKILLS_DIR).glob("*.md")
        )
        for skill_file in skill_files:
            skills.append(parse_markdown_skill(skill_file))
        return skills
    except:
        return []
```

Skill 更像“做事手册”。演示里的 `todo_prioritizer` 不是让模型多一个函数，而是告诉模型：遇到候选修复项时，应该如何排序。

现在 Skill 使用 Markdown 格式：

```markdown
---
name: todo_prioritizer
description: 给候选修复项排序：安全风险第一，阻塞运行第二，核心功能第三，文档或示例最后。
when_to_use: 当任务要求整理修复顺序、挑选优先级或从多个候选问题中选出下一步行动时使用。
triggers: todo_prioritizer, 修复顺序, 优先级, 候选修复项, 最该先修
---

# Todo Prioritizer

## Priority Order

1. 安全风险
2. 阻塞运行
3. 核心功能
4. 文档或示例
```

Markdown 文件会被解析成三部分：frontmatter 里的名称和说明、正文里的操作步骤、以及文件路径。

```python
def parse_markdown_skill(path):
    content = path.read_text(encoding="utf-8")
    metadata = {}
    body = content
    if content.startswith("---\n"):
        end = content.find("\n---", 4)
        if end != -1:
            frontmatter = content[4:end].strip()
            body = content[end + 4 :].strip()
            for line in frontmatter.splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()
    name = metadata.get(
        "name", path.parent.name if path.name == "SKILL.md" else path.stem
    )
    return {
        "name": name,
        "description": metadata.get("description", ""),
        "when_to_use": metadata.get("when_to_use", ""),
        "path": str(path),
        "content": body,
    }
```

最后把 Skill 整理成 prompt 片段：

```python
def format_skill_for_prompt(skill):
    lines = [
        f"## {skill['name']}",
        f"Source: {skill['path']}",
        f"Description: {skill.get('description', '')}",
    ]
    when_to_use = skill.get("when_to_use")
    if when_to_use:
        lines.append(f"When to use: {when_to_use}")
    lines.append(skill["content"])
    return "\n".join(lines)
```

这版演示只讲一个更直接的结论：**Skill 是外置的任务方法，启动时进入 prompt，影响模型做事方式。**

---

## 四、MCP：外部工具进入 tools 列表

```python
MCP_CONFIG = ".agent/mcp.json"

def load_mcp_tools():
    if not os.path.exists(MCP_CONFIG):
        return []
    try:
        with open(MCP_CONFIG, "r") as f:
            config = json.load(f)
            mcp_tools = []
            for server_name, server_config in config.get("mcpServers", {}).items():
                if server_config.get("disabled", False):
                    continue
                for tool in server_config.get("tools", []):
                    mcp_tools.append({"type": "function", "function": tool})
            return mcp_tools
    except:
        return []
```

Rule 和 Skill 进入 prompt，MCP 工具进入 tools 列表。这个差异很重要：

```python
all_tools = base_tools + mcp_tools
```

对模型来说，MCP 加载出来的 `project_guide` 和内置的 `read`、`write`、`bash` 一样，都是可以选择调用的工具。

---

## 五、三类配置如何组装

```python
def run_agent_with_external_capabilities(task):
    rule_count = count_rule_files()
    rules = load_rules()
    skills = load_skills()
    mcp_tools = load_mcp_tools()
    all_tools = base_tools + mcp_tools

    context_parts = [
        "You are a helpful assistant that can interact with the system. Be concise."
    ]
    if rules:
        context_parts.append(f"\n# Rules\n{rules}")
        print(f"[Rules] Loaded {rule_count} rule files")
    if skills:
        context_parts.append(
            f"\n# Skills\n"
            + "\n\n".join(format_skill_for_prompt(skill) for skill in skills)
        )
        skill_names = [skill["name"] for skill in skills]
        print(f"[Skills] Loaded {len(skills)} skill files: {', '.join(skill_names)}")
    if mcp_tools:
        tool_names = [tool["function"]["name"] for tool in mcp_tools]
        print(f"[MCP] Loaded {len(mcp_tools)} MCP tools: {', '.join(tool_names)}")
```

最终结构可以记成一句话：

```text
Rules + Skills → system prompt
MCP            → tools
```

---

## 六、实际运行效果

### 1. 看加载日志，并证明 MCP 生效

```bash
python3 agent/03-skills-mcp/agent-skills-mcp.py "调用 project_guide，用一句话说明 Rule、Skill、MCP 如何接入 Agent"
```

观察点：

```text
[Rules] Loaded 1 rule files
[Skills] Loaded 1 skill files: todo_prioritizer
[MCP] Loaded 1 MCP tools: project_guide
[Tool] project_guide(...)
```

前三行证明外置配置已经被加载；只要看到 `[Tool] project_guide(...)`，就能证明 MCP 工具已经进入 tools 列表，并被模型实际调用。

### 2. 证明 Rule 生效

```bash
python3 agent/03-skills-mcp/agent-skills-mcp.py "不要调用任何工具。请按本项目 Rule 的要求回答：Rule 是否已加载？"
```

观察点：回答会按 `.agent/rules/demo-style.md` 的要求，先说明本轮加载了 Rule、Skill、MCP 三类外置能力。

### 3. 证明 Skill 生效

```bash
python3 agent/03-skills-mcp/agent-skills-mcp.py "按优先级排序：A README 错别字；B 删除接口缺少权限校验；C 应用启动报错；D 搜索分页重复。只输出前三项和舍弃项。"
```

观察回答内容：

```text
1. 优先级 - 安全风险 - 删除用户接口缺少权限校验
2. 优先级 - 阻塞运行 - 应用启动时报错无法运行
3. 优先级 - 核心功能 - 搜索结果分页偶尔重复

舍弃项：README 示例命令有错别字（文档或示例类，优先级最低）。
```

这里可以重点看 Skill：模型不是在扫仓库，也不是靠临场发挥，而是在使用外部 Markdown 里定义好的排序方法。

---

## 七、本讲结论

第三讲只回答一个问题：如何不改 Python 代码，也能改变 Agent 的行为、知识和工具？

答案是三类外置能力：

1. Rule 改变约束。
2. Skill 改变做法。
3. MCP 改变可调用工具。

从第二讲到第三讲，递进关系也很清楚：Memory 解决“记得住”，Rules、Skills、MCP 解决“能力可以从项目配置里长出来”。

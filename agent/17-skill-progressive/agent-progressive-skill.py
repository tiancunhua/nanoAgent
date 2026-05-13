"""
agent-progressive-skill.py - 渐进式 Skill 加载版 Agent
基于 agent.py (115行)，核心新增:

  1. Skill 注册表（registry.json）自动扫描生成
  2. load_skill 工具 —— LLM 按需加载 Skill 详情
  3. Level 0/1/2 三层渐进式披露

目录结构：
  skills/
  ├── docker-deploy/
  │   └── SKILL.md
  ├── doc-search/
  │   ├── SKILL.md
  │   └── data_structure.md
  └── code-review/
      └── SKILL.md

用法：
  # 1. 先初始化示例 Skill 目录
  python agent-progressive-skill.py --init

  # 2. 运行 Agent
  python agent-progressive-skill.py "帮我把项目部署到 Docker"
"""

import json
import os
import re
import subprocess
import sys
import httpx
from pathlib import Path
from openai import OpenAI

# ── 配置 ──────────────────────────────────────────────
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
    http_client=httpx.Client(verify=False),
)

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
SKILLS_DIR = Path("skills")
MAX_ITERATIONS = 10

# ── Skill 注册表 ─────────────────────────────────────

def parse_frontmatter(content: str) -> dict:
    """解析 SKILL.md 开头的 YAML frontmatter"""
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}
    meta = {}
    for line in match.group(1).split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            meta[key.strip()] = val.strip()
    return meta


def build_registry() -> list:
    """扫描 skills/ 目录，生成 Skill 注册表（Level 0）"""
    if not SKILLS_DIR.exists():
        return []
    registry = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        content = skill_file.read_text(encoding="utf-8")
        meta = parse_frontmatter(content)
        registry.append({
            "name": meta.get("name", skill_dir.name),
            "description": meta.get("description", f"Skill: {skill_dir.name}")
        })
    return registry


def format_skill_catalog(registry: list) -> str:
    """格式化 Skill 目录，注入 system prompt（Level 0）"""
    if not registry:
        return ""
    lines = ["\n# Available Skills"]
    lines.append("以下是可用的 Skill 列表。需要某个 Skill 的详细操作指南时，调用 load_skill 工具。")
    for s in registry:
        lines.append(f"- **{s['name']}**: {s['description']}")
    return "\n".join(lines)


# ── 工具实现 ──────────────────────────────────────────

def load_skill(name: str) -> str:
    """加载指定 Skill 的完整 SKILL.md（Level 1）"""
    skill_file = SKILLS_DIR / name / "SKILL.md"
    if not skill_file.exists():
        return f"Error: Skill '{name}' not found. Available skills: {[d.name for d in SKILLS_DIR.iterdir() if d.is_dir()]}"
    content = skill_file.read_text(encoding="utf-8")
    # 去掉 frontmatter，只返回正文
    content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
    return content.strip()


def read_file(filepath: str) -> str:
    """读取 Skill 内部的子文件（Level 2）"""
    p = Path(filepath)
    if not p.exists():
        return f"Error: File '{filepath}' not found"
    return p.read_text(encoding="utf-8")[:10000]  # 截断防止过长


def write_file(filepath: str, content: str) -> str:
    """写入文件"""
    p = Path(filepath)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written to {filepath} ({len(content)} chars)"


def execute_bash(command: str) -> str:
    """执行 bash 命令"""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout + result.stderr
        return output[:5000] or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out (30s)"


# ── 工具注册 ──────────────────────────────────────────

# 基础工具（始终可用）
BASE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read file contents. Use for reading skill sub-files, configs, docs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to file"}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to file"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["filepath", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_bash",
            "description": "Run a shell command. Use for system operations, installing packages, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command"}
                },
                "required": ["command"]
            }
        }
    },
]

# load_skill 工具（渐进式披露的核心）
LOAD_SKILL_TOOL = {
    "type": "function",
    "function": {
        "name": "load_skill",
        "description": "加载一个 Skill 的完整操作指南。当你确定当前任务需要某个 Skill 时调用。调用后会返回该 Skill 的 SKILL.md 内容，包含具体的操作步骤、命令和注意事项。",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Skill 名称，从 Available Skills 列表中选择"
                }
            },
            "required": ["name"]
        }
    }
}

TOOL_FUNCTIONS = {
    "load_skill": lambda args: load_skill(args["name"]),
    "read_file": lambda args: read_file(args["filepath"]),
    "write_file": lambda args: write_file(args["filepath"], args["content"]),
    "execute_bash": lambda args: execute_bash(args["command"]),
}


# ── Agent 主循环 ──────────────────────────────────────

def agent(task: str):
    """带渐进式 Skill 加载的 Agent 主循环"""
    # Level 0：扫描 Skill 目录，生成目录摘要
    registry = build_registry()
    skill_catalog = format_skill_catalog(registry)

    system_prompt = f"""You are a helpful assistant that can use tools to accomplish tasks.
{skill_catalog}
"""

    # 组装工具列表：基础工具 + load_skill（如果有 Skill 的话）
    tools = BASE_TOOLS.copy()
    if registry:
        tools.append(LOAD_SKILL_TOOL)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task}
    ]

    print(f"\n🚀 Task: {task}")
    if registry:
        print(f"📚 Available Skills: {[s['name'] for s in registry]}")
    print("-" * 50)

    for i in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=tools
        )
        msg = response.choices[0].message
        messages.append(msg)

        # 没有工具调用 → 任务完成
        if not msg.tool_calls:
            print(f"\n💬 Agent: {msg.content}")
            return

        # 处理工具调用
        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            print(f"\n🔧 [{i+1}] Calling {name}({json.dumps(args, ensure_ascii=False)[:80]})")

            # 执行工具
            func = TOOL_FUNCTIONS.get(name)
            if func:
                result = func(args)
            else:
                result = f"Error: Unknown tool '{name}'"

            # 打印结果预览
            preview = result[:200] + "..." if len(result) > 200 else result
            print(f"   → {preview}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

    print("\n⚠️ Reached max iterations")


# ── 初始化示例 Skill ─────────────────────────────────

def init_example_skills():
    """创建示例 Skill 目录结构，方便测试"""

    skills = {
        "docker-deploy": {
            "SKILL.md": """---
name: docker-deploy
description: Docker 容器化部署，支持 build / up / down / 健康检查。Use when user asks to deploy, docker, 容器部署, 上线。
---

# Docker Deploy Skill

## 前置检查
1. 确认项目根目录存在 Dockerfile
2. 确认存在 docker-compose.yml（可选）

## 部署步骤

### 单容器部署
```bash
docker build -t <image_name> .
docker run -d --name <container_name> -p <host_port>:<container_port> <image_name>
```

### Compose 部署
```bash
docker-compose build
docker-compose up -d
docker-compose ps  # 验证状态
```

## 健康检查
```bash
docker ps --filter "name=<container_name>"
curl -f http://localhost:<port>/health || echo "Health check failed"
```

## 回滚
```bash
docker-compose down
docker-compose up -d --build
```

## 注意事项
- 生产环境部署前务必确认 .env 文件不包含敏感信息
- 确保端口未被占用
- 建议先在本地用 docker-compose up 测试
"""
        },
        "doc-search": {
            "SKILL.md": """---
name: doc-search
description: 本地文档知识库检索，支持分层导航和渐进式检索。Use when user asks to 查文档, 搜索知识库, 找资料, 查制度。
---

# 文档知识库检索 Skill

## 快速开始
1. 先调用 read_file("skills/doc-search/data_structure.md") 查看目录索引
2. 根据目录描述定位到目标子目录或文件
3. 调用 read_file 读取目标文件内容
4. 信息不足时调整关键词重试，最多 5 轮

## 检索策略
- 从 data_structure.md 开始，逐层导航到目标文件
- 优先局部读取，不要一次性读取大文件
- 信息缺失时如实说明，不要猜测

## 禁止行为
- 不要跳过 data_structure.md 直接猜测文件路径
- 不要一次性读取超过 200 行的内容
""",
            "data_structure.md": """# 文档目录索引

| 目录 | 内容描述 | 关键词 |
|------|----------|--------|
| knowledge/HR/ | 人力资源制度 | 请假、考勤、报销、入职 |
| knowledge/运维/ | 运维操作手册 | 部署、监控、告警、回滚 |
| knowledge/安全/ | 安全合规制度 | 数据分类、访问控制、审计 |
"""
        },
        "code-review": {
            "SKILL.md": """---
name: code-review
description: 代码审查，支持多维度检查和结构化报告。Use when user asks to review, 代码审查, CR, 检查代码。
---

# 代码审查 Skill

## 审查流程
1. 用 execute_bash("find . -name '*.py' | head -20") 了解项目规模
2. 用 read_file 逐个读取关键文件
3. 按以下维度检查：
   - 安全性（SQL 注入、硬编码密钥）
   - 性能（N+1 查询、不必要的循环）
   - 可维护性（命名、注释、复杂度）
4. 输出结构化报告

## 报告格式
```
## 审查报告

### 严重问题
- [文件名:行号] 问题描述

### 建议改进
- [文件名:行号] 改进建议

### 总结
整体评价和优先级建议
```
"""
        }
    }

    for skill_name, files in skills.items():
        skill_dir = SKILLS_DIR / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in files.items():
            (skill_dir / filename).write_text(content.strip() + "\n", encoding="utf-8")
        print(f"  ✅ Created skills/{skill_name}/")

    # 生成 registry.json
    registry = build_registry()
    registry_file = SKILLS_DIR / "registry.json"
    registry_file.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  ✅ Generated skills/registry.json ({len(registry)} skills)")
    print(f"\n目录结构：")
    for line in _tree(SKILLS_DIR):
        print(f"  {line}")


def _tree(path: Path, prefix: str = "") -> list:
    """简单的目录树打印"""
    lines = []
    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{item.name}")
        if item.is_dir():
            extension = "    " if is_last else "│   "
            lines.extend(_tree(item, prefix + extension))
    return lines


# ── 入口 ──────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python agent-progressive-skill.py --init          # 初始化示例 Skill")
        print('  python agent-progressive-skill.py "你的任务"       # 运行 Agent')
        sys.exit(1)

    if sys.argv[1] == "--init":
        print("🔧 Initializing example skills...\n")
        init_example_skills()
    else:
        agent(sys.argv[1])

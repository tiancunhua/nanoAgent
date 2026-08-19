"""外部能力示例：在 Agent 循环中加载 Rules、Skills 与 MCP 工具描述。"""

import os
import json
import subprocess
import sys
import glob as glob_module
import httpx
from pathlib import Path
from typing import Any
from openai import OpenAI

# LLM 只会看到 messages 和工具 schema，不会自动读取本地配置文件。
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
    http_client=httpx.Client(verify=False),
)

RULES_DIR = ".agent/rules"
SKILLS_DIR = ".agent/skills"
MCP_CONFIG = ".agent/mcp.json"
DEFAULT_MAX_ITERATIONS = 10

# 内置工具：schema 描述“如何调用”，下方 Python 函数负责“真正执行”。
base_tools = [
    {
        "type": "function",
        "function": {
            "name": "read",
            "description": "Read file with line numbers",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "offset": {"type": "integer"},
                    "limit": {"type": "integer"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write",
            "description": "Write content to file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit",
            "description": "Replace string in file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_string": {"type": "string"},
                    "new_string": {"type": "string"},
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob",
            "description": "Find files by pattern",
            "parameters": {
                "type": "object",
                "properties": {"pattern": {"type": "string"}},
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Search files for pattern",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run shell command",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
]


def read(path, offset=None, limit=None):
    """按范围读取文件，并附加行号，方便模型精确引用和修改。"""
    try:
        with open(path, "r") as f:
            lines = f.readlines()
        start = offset if offset else 0
        end = start + limit if limit else len(lines)
        numbered = [
            f"{i + 1:4d} {line}" for i, line in enumerate(lines[start:end], start)
        ]
        return "".join(numbered)
    except Exception as e:
        return f"Error: {str(e)}"


def write(path, content):
    """覆盖写入文件。工具捕获异常，将错误也作为观察结果返回。"""
    try:
        with open(path, "w") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error: {str(e)}"


def edit(path, old_string, new_string):
    """只替换唯一匹配项，避免模糊修改误伤多个位置。"""
    try:
        with open(path, "r") as f:
            content = f.read()
        if content.count(old_string) != 1:
            return f"Error: old_string must appear exactly once"
        new_content = content.replace(old_string, new_string)
        with open(path, "w") as f:
            f.write(new_content)
        return f"Successfully edited {path}"
    except Exception as e:
        return f"Error: {str(e)}"


def glob(pattern):
    """用 glob 查找文件，优先返回最近修改的结果。"""
    try:
        files = glob_module.glob(pattern, recursive=True)
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return "\n".join(files) if files else "No files found"
    except Exception as e:
        return f"Error: {str(e)}"


def grep(pattern, path="."):
    """在指定目录递归搜索文本。"""
    try:
        result = subprocess.run(
            f"grep -r '{pattern}' {path}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout if result.stdout else "No matches found"
    except Exception as e:
        return f"Error: {str(e)}"


def bash(command):
    """执行 shell 命令，并设置超时防止进程永久阻塞。"""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {str(e)}"


def demo_release_policy(topic="发布演示"):
    """模拟一个由 MCP 配置暴露的工具实现。"""
    return (
        f"{topic} 的 MCP 发布策略：本次只做演示，不修改文件；"
        "发布前先保数据安全，再保应用能启动，最后处理界面文案。"
    )


# 执行调度表：Tool Call 中的 name 最终在这里找到本地函数。
available_functions = {
    "read": read,
    "write": write,
    "edit": edit,
    "glob": glob,
    "grep": grep,
    "bash": bash,
    "demo_release_policy": demo_release_policy,
}


def parse_tool_arguments(raw_arguments: str) -> dict[str, Any]:
    """把模型生成的 JSON 参数安全地转换成字典。"""
    if not raw_arguments:
        return {}
    try:
        parsed = json.loads(raw_arguments)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError as error:
        return {"_argument_error": f"Invalid JSON arguments: {error}"}


def load_rules():
    """加载所有规则全文；规则会直接进入 system prompt，始终生效。"""
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


def count_rule_files():
    """单独计数只用于终端提示，不影响模型上下文。"""
    if not os.path.exists(RULES_DIR):
        return 0
    return len(list(Path(RULES_DIR).glob("*.md")))


def load_skills():
    """发现目录式 SKILL.md 和兼容的单文件 Markdown Skill。"""
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


def parse_markdown_skill(path):
    """拆分简单 frontmatter 元数据和 Skill 正文。"""
    content = path.read_text(encoding="utf-8")
    metadata = {}
    body = content
    # frontmatter 用于发现和说明；body 才是 Skill 的具体工作指令。
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
    triggers = [
        trigger.strip().lower()
        for trigger in metadata.get("triggers", "").split(",")
        if trigger.strip()
    ]
    return {
        "name": name,
        "description": metadata.get("description", ""),
        "when_to_use": metadata.get("when_to_use", ""),
        "triggers": triggers,
        "path": str(path),
        "content": body,
    }


def format_skill_for_prompt(skill):
    """把结构化 Skill 重新排版为模型易读的 prompt 片段。"""
    lines = [
        f"## {skill['name']}",
        f"Source: {skill['path']}",
        f"Description: {skill.get('description', '')}",
    ]
    when_to_use = skill.get("when_to_use")
    if when_to_use:
        lines.append(f"When to use: {when_to_use}")
    if skill.get("triggers"):
        lines.append(f"Triggers: {', '.join(skill['triggers'])}")
    lines.append(skill["content"])
    return "\n".join(lines)


def load_mcp_tools():
    """从演示配置读取 MCP 工具 schema，并跳过被禁用的服务。"""
    if not os.path.exists(MCP_CONFIG):
        return []
    try:
        with open(MCP_CONFIG, "r") as f:
            config = json.load(f)
            mcp_tools = []
            for server_name, server_config in config.get("mcpServers", {}).items():
                if server_config.get("disabled", False):
                    continue
                # 本章聚焦协议接入，只导入 schema；执行仍走本地演示函数。
                for tool in server_config.get("tools", []):
                    mcp_tools.append({"type": "function", "function": tool})
            return mcp_tools
    except:
        return []


def run_agent_step(messages, tools, max_iterations=DEFAULT_MAX_ITERATIONS):
    """运行标准 Agent 循环：问模型、执行工具、写回结果。"""
    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            tools=tools,
        )
        message = response.choices[0].message
        # 保存带 Tool Call 的 assistant 消息，维持完整的协议上下文。
        messages.append(message)

        # 没有 Tool Call 时，content 就是本轮最终答案。
        if not message.tool_calls:
            return message.content, messages
        for tool_call in message.tool_calls:
            function_payload = getattr(tool_call, "function", None)
            if function_payload is None:
                continue
            function_name = str(getattr(function_payload, "name", ""))
            raw_arguments = str(getattr(function_payload, "arguments", ""))
            function_args = parse_tool_arguments(raw_arguments)
            print(f"[Tool] {function_name}({function_args})")
            function_impl = available_functions.get(function_name)
            if "_argument_error" in function_args:
                function_response = f"Error: {function_args['_argument_error']}"
            elif function_impl is not None:
                function_response = function_impl(**function_args)
            else:
                function_response = f"Error: Unknown tool '{function_name}'"
            # id 把工具执行结果与模型发出的对应调用关联起来。
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": function_response,
                }
            )
    return "Max iterations reached", messages


def run_agent_with_external_capabilities(task):
    """组装 Rules、Skills、MCP 与内置工具，然后启动核心循环。"""
    # 三类扩展的进入方式不同：Rules/Skills 进入 prompt，MCP 进入 tools。
    rule_count = count_rule_files()
    rules = load_rules()
    skills = load_skills()
    mcp_tools = load_mcp_tools()
    all_tools = base_tools + mcp_tools

    # system prompt 是行为上下文；这里按需追加磁盘中发现的规则和技能。
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
    messages = [{"role": "system", "content": "\n".join(context_parts)}]
    messages.append({"role": "user", "content": task})
    final_result, messages = run_agent_step(messages, all_tools)
    print(f"\n{final_result}")
    return final_result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 agent/03-skills-mcp/agent-skills-mcp.py 'your task'")
        print("\nFeatures: Rules, Skills, MCP")
        sys.exit(1)
    task = " ".join(sys.argv[1:])
    run_agent_with_external_capabilities(task)

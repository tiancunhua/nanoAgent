import os
import json
import subprocess
import sys
import glob as glob_module
from pathlib import Path
from typing import Any
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"), base_url=os.environ.get("OPENAI_BASE_URL")
)

RULES_DIR = ".agent/rules"
SKILLS_DIR = ".agent/skills"
MCP_CONFIG = ".agent/mcp.json"
DEFAULT_MAX_ITERATIONS = 10

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
    try:
        with open(path, "w") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error: {str(e)}"


def edit(path, old_string, new_string):
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
    try:
        files = glob_module.glob(pattern, recursive=True)
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return "\n".join(files) if files else "No files found"
    except Exception as e:
        return f"Error: {str(e)}"


def grep(pattern, path="."):
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
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {str(e)}"


def project_guide(topic="Agent demo"):
    return (
        f"Project guide for {topic}: Rules and the Skill Registry are injected into "
        "the prompt; model-selected Skill details are injected later. MCP tools are "
        "appended to the tools list and become callable by name."
    )


available_functions = {
    "read": read,
    "write": write,
    "edit": edit,
    "glob": glob,
    "grep": grep,
    "bash": bash,
    "project_guide": project_guide,
}


def parse_tool_arguments(raw_arguments: str) -> dict[str, Any]:
    if not raw_arguments:
        return {}
    try:
        parsed = json.loads(raw_arguments)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError as error:
        return {"_argument_error": f"Invalid JSON arguments: {error}"}


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


def count_rule_files():
    if not os.path.exists(RULES_DIR):
        return 0
    return len(list(Path(RULES_DIR).glob("*.md")))


def load_skills():
    skills = []
    if not os.path.exists(SKILLS_DIR):
        return []
    try:
        # 这里先只扫描 Skill 文件，不急着把完整内容都交给大模型。
        # 后面会先给模型摘要，再由模型决定是否需要展开完整 Skill。
        skill_files = sorted(Path(SKILLS_DIR).glob("*/SKILL.md")) + sorted(
            Path(SKILLS_DIR).glob("*.md")
        )
        for skill_file in skill_files:
            skills.append(parse_markdown_skill(skill_file))
        return skills
    except:
        return []


def parse_markdown_skill(path):
    content = path.read_text(encoding="utf-8")
    metadata = {}
    body = content
    # frontmatter 是给模型判断用的轻量信息；body 是后续可展开的完整 Skill。
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


def format_skill_summary_for_prompt(skill):
    # 第一阶段：只把 Skill Registry 放进 prompt。
    # 大模型先看到有哪些 Skill、何时使用、详情文件在哪里，但还看不到完整手册。
    lines = [f"- {skill['name']}: {skill.get('description', '')}"]
    when_to_use = skill.get("when_to_use")
    if when_to_use:
        lines.append(f"  When to use: {when_to_use}")
    if skill.get("triggers"):
        lines.append(f"  Triggers: {', '.join(skill['triggers'])}")
    lines.append(f"  Detail file: {skill['path']}")
    return "\n".join(lines)


def parse_selected_skill_names(raw_content, known_names):
    text = (raw_content or "").strip()
    parsed = []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end > start:
            try:
                parsed = json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                parsed = []
    if isinstance(parsed, dict):
        parsed = parsed.get("skills", []) or parsed.get("selected_skills", [])
    if not isinstance(parsed, list):
        parsed = []

    known_lookup = {name.lower(): name for name in known_names}
    selected = []
    for item in parsed:
        skill_name = known_lookup.get(str(item).strip().lower())
        if skill_name and skill_name not in selected:
            selected.append(skill_name)
    if not selected:
        # 有些模型会输出一句解释而不是纯 JSON。这里仍然只解析模型输出，
        # 不根据用户任务做 Python 侧匹配。
        lowered_text = text.lower()
        for name in known_names:
            if name.lower() in lowered_text:
                selected.append(name)
    return selected


def select_skills_with_model(task, skills):
    if not skills:
        return []
    registry = "\n".join(format_skill_summary_for_prompt(skill) for skill in skills)
    # 这里不是 Python 代码替模型做选择，而是发起一次轻量模型决策：
    # 模型只看到 Skill Registry 和用户任务，然后返回本轮要展开的 Skill 名称。
    response = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You decide which skills should be progressively loaded. "
                    "If the task explicitly names a skill, include that skill. "
                    "Only output a JSON array of skill names. Output [] if no skill "
                    "is needed."
                ),
            },
            {
                "role": "user",
                "content": f"# Skill Registry\n{registry}\n\n# User Task\n{task}",
            },
        ],
    )
    raw_selection = response.choices[0].message.content
    selected_names = parse_selected_skill_names(
        raw_selection, [skill["name"] for skill in skills]
    )
    return [skill for skill in skills if skill["name"] in selected_names]


def format_skill_detail_for_prompt(skill):
    # 第二阶段：模型选择该 Skill 后，才把完整 SKILL.md 正文追加到 prompt。
    # 这样上下文不会被所有 Skill 挤满，也能清楚观察“渐进式加载”发生了。
    return f"## {skill['name']}\nSource: {skill['path']}\n\n{skill['content']}"


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


def run_agent_step(messages, tools, max_iterations=DEFAULT_MAX_ITERATIONS):
    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            tools=tools,
        )
        message = response.choices[0].message
        messages.append(message)
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
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": function_response,
                }
            )
    return "Max iterations reached", messages


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
        # 先注册 Skill 摘要，相当于给模型一张能力目录。
        context_parts.append(
            f"\n# Skill Registry\n"
            + "\n".join(format_skill_summary_for_prompt(skill) for skill in skills)
        )
        skill_names = [skill["name"] for skill in skills]
        print(
            f"[Skills] Registered {len(skills)} skill summaries: "
            f"{', '.join(skill_names)}"
        )
    selected_skills = select_skills_with_model(task, skills)
    if selected_skills:
        # 再按模型对本轮任务的选择结果，追加完整 Skill 详情。
        context_parts.append(
            f"\n# Loaded Skill Details\n"
            + "\n\n".join(
                format_skill_detail_for_prompt(skill) for skill in selected_skills
            )
        )
        skill_names = [skill["name"] for skill in selected_skills]
        print(
            f"[Skills] Model selected {len(selected_skills)} skill details: "
            f"{', '.join(skill_names)}"
        )
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

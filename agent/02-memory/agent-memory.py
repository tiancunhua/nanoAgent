"""带长期记忆的 Agent：在最小循环之外，演示记忆的读取、注入和保存。"""

import os
import json
import subprocess
import sys
import httpx
from datetime import datetime
from openai import OpenAI

# 模型仍然是无状态的；所谓“记忆”来自我们每次主动传入的 messages。
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
    http_client=httpx.Client(verify=False),
)

# 用普通 Markdown 保存跨进程记忆，便于直接打开观察数据如何变化。
MEMORY_FILE = "agent_memory.md"

# schema 给模型看，告诉它当前有哪些动作可以选择。
tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_bash",
            "description": "Execute a bash command",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write to a file",
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
]


def execute_bash(command):
    """执行命令，并把输出作为工具观察结果返回。"""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr


def read_file(path):
    """读取文本文件。"""
    with open(path, "r") as f:
        return f.read()


def write_file(path, content):
    """写入文本文件。"""
    with open(path, "w") as f:
        f.write(content)
    return f"Wrote to {path}"


# 模型只返回工具名；调度表负责找到本地实现。
functions = {"execute_bash": execute_bash, "read_file": read_file, "write_file": write_file}


def load_memory():
    """读取最近 50 行长期记忆，避免历史无限占用上下文。"""
    if not os.path.exists(MEMORY_FILE):
        return ""
    with open(MEMORY_FILE, "r") as f:
        lines = f.read().splitlines()
    return "\n".join(lines[-50:])


def save_memory(task, result):
    """把本次任务和最终结果追加到记忆文件，供下次运行使用。"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n## {timestamp}\n**Task:** {task}\n**Result:** {result}\n"
    with open(MEMORY_FILE, "a") as f:
        f.write(entry)
    print(f"[Memory] Saved to {MEMORY_FILE}")


def build_messages(user_message):
    """把长期记忆注入 system prompt，再加入本轮用户任务。"""
    system_prompt = "You are a helpful assistant. Be concise."
    memory = load_memory()
    if memory:
        print(f"[Memory] Loaded {MEMORY_FILE}")
        # 文件本身不会自动进入模型上下文，必须拼进本次请求。
        system_prompt += f"\n\nPrevious context:\n{memory}"
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]


def run_agent(user_message, max_iterations=5):
    """执行工具循环，并在正常结束或超限时保存长期记忆。"""
    # 与第一篇相比，核心循环不变，只是初始 messages 带上了历史记忆。
    messages = build_messages(user_message)
    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            tools=tools,
        )
        message = response.choices[0].message
        # 保留 assistant 的原始 Tool Call，供后续 tool 消息引用。
        messages.append(message)
        if not message.tool_calls:
            # 只把最终回答写入长期记忆，不保存每个中间工具输出。
            save_memory(user_message, message.content)
            return message.content
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            print(f"[Tool] {name}({args})")
            if name not in functions:
                result = f"Error: Unknown tool '{name}'"
            else:
                result = functions[name](**args)
            # 工具结果写回后，模型才能在下一轮看到环境反馈。
            messages.append(
                {"role": "tool", "tool_call_id": tool_call.id, "content": result}
            )
    result = "Max iterations reached"
    # 即使触发上限，也留下结果，便于下一次理解上次为何中断。
    save_memory(user_message, result)
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 agent/02-memory/agent-memory.py 'your task here'")
        sys.exit(1)
    task = " ".join(sys.argv[1:])
    print(run_agent(task))

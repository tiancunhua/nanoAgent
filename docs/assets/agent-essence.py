"""最小 Agent：用约 100 行代码展示“LLM + 工具 + 循环”的完整数据流。"""

import os
import json
import subprocess
import httpx
from openai import OpenAI

# 模型客户端只负责“思考”。工具仍由下面的 Python 代码在本地执行。
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
    http_client=httpx.Client(verify=False),
)

# 工具 schema 是给模型看的说明书：模型据此决定工具名和参数。
# 注意，这里没有真正执行工具的代码；具体实现位于下方同名函数中。
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
    """运行 shell 命令，并把标准输出和错误输出都返回给模型。"""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr


def read_file(path):
    """读取文本文件，让模型能够观察本地文件内容。"""
    with open(path, "r") as f:
        return f.read()


def write_file(path, content):
    """写入文本文件，让模型的决定真正作用到本地环境。"""
    with open(path, "w") as f:
        f.write(content)
    return f"Wrote to {path}"


# 调度表把模型返回的工具名映射到真正的 Python 函数。
functions = {"execute_bash": execute_bash, "read_file": read_file, "write_file": write_file}


def run_agent(user_message, max_iterations=5):
    """运行 Agent，直到模型直接回答，或达到最大循环次数。"""
    # messages 就是 Agent 的短期记忆；每次模型调用都会看到完整历史。
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Be concise."},
        {"role": "user", "content": user_message},
    ]

    # 每轮只有两种结果：模型直接回答，或要求执行一个/多个工具。
    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            tools=tools,
        )
        message = response.choices[0].message

        # 必须先保存 assistant 消息，其中包含模型发出的 tool_call id。
        messages.append(message)

        # 没有工具调用，说明模型认为任务已经完成。
        if not message.tool_calls:
            return message.content

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            # OpenAI 协议中的 arguments 是 JSON 字符串，要先还原成参数字典。
            args = json.loads(tool_call.function.arguments)
            print(f"[Tool] {name}({args})")
            if name not in functions:
                result = f"Error: Unknown tool '{name}'"
            else:
                result = functions[name](**args)

            # tool_call_id 将执行结果和模型刚才的请求配对。
            # 写回 messages 后，模型下一轮才能根据这个“观察”继续判断。
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})

    # 上限用于防止模型陷入无限工具调用，并不是正常完成条件。
    return "Max iterations reached"


if __name__ == "__main__":
    import sys

    # 将命令行中引号后的全部文本合并为一个任务。
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Hello"
    print(run_agent(task))

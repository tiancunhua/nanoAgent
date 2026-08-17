# 从零开始理解 Agent（番外）：nanoDeepSeekHarness——用最小实现理解“一切皆插件”

> [第一篇](../01-essence/agent-essence.md)用约 100 行 Python 写出 Agent 的本质：模型选择工具，代码执行工具，结果回到上下文，然后继续循环。

后来，我们又增加了 Memory、Skills、MCP、SubAgent、上下文压缩和安全机制。这些模型之外的能力合在一起，就是 Harness。

当 Harness 越来越复杂，它自己应该怎样组织？DeepSeek Harness 的答案是：

> **Everything is a Plugin——一切皆插件。**

它不是说 Agent 可以安装很多工具，而是说：**Agent 不再是一份写死的程序，而是一组可以重新组合的能力。**

---

## 一、为什么需要插件

第一篇的 nanoAgent 把四件事写在一个文件里：

```text
模型调用    OpenAI(...)
会话状态    messages
工具能力    read_file / write_file / execute_bash
执行循环    while True
```

用于教学，这最直观。但真实系统中的每一项都可能变化：模型会更换，文件系统会进入沙箱，普通 ReAct 循环也可能变成多 Agent 编排。

如果所有能力都写死在 `run_agent()` 中，每次替换都要修改核心。功能越多，Harness 越容易成为新的巨石。

从第一性原理看，真正应该稳定的是能力之间的连接方式：

```text
Agent = 最小组合内核 + 一组遵守契约的插件
```

所以“一切皆插件”的本质是隔离变化：

> **凡是可能独立变化的能力，都不应该成为不可替换的核心。**

---

## 二、一个最小实现

我们用独立项目 [nanoDeepSeekHarness](https://github.com/GitHubxsy/nanodeepseekharness) 重写第一篇的 nanoAgent。它不依赖 DeepSeek Harness，由 Cordis 负责 Context、插件依赖和生命周期。

### 1. 一次任务是怎样完成的

假设用户输入“读取 README.md”，程序会经历下面这条链路：

```text
用户任务
  → Agent Loop 调用 DeepSeek
  → DeepSeek 选择 read_file("README.md")
  → 本地 TypeScript 读取文件
  → 结果写回 messages
  → DeepSeek 根据结果生成回答
```

模型并没有直接读取文件。它只返回“调用哪个工具、传什么参数”；Harness 找到本地函数执行，再把结果交还给模型。这仍然是第一篇 nanoAgent 的核心循环。

### 2. 把四种职责拆成插件

这个最小实现只有四个组件：

```text
NanoRuntime       保存模型、工具和循环
deepSeekPlugin    调用 DeepSeek
readFilePlugin    提供 read_file 工具
agentLoopPlugin   驱动“模型 → 工具 → 模型”的循环
```

`NanoRuntime` 是最小内核，但它自己不会调用模型、不会读文件，也不会执行 Agent。三种能力都由插件注册进去：

```ts
const ctx = new Context()

await ctx.plugin(NanoRuntime)
await ctx.plugin(deepSeekPlugin())
await ctx.plugin(readFilePlugin)
await ctx.plugin(agentLoopPlugin)

console.log(await ctx.nano.run('读取 README.md'))
await ctx.fiber.dispose()
```

这几行就是“一切皆插件”的实际含义：模型、工具和循环都在组装阶段决定。更换其中一个，不必改动另外两个。

### 3. 插件如何接入这条链路

以 `readFilePlugin` 为例，一个工具由两部分组成：给模型看的 `schema`，以及本地执行的 `execute`。

```ts
export const readFilePlugin = {
  name: 'read-file',
  inject: ['nano'],
  apply(ctx) {
    ctx.effect(() => ctx.nano.addTool({
      schema: {
        type: 'function',
        function: {
          name: 'read_file',
          description: 'Read a UTF-8 text file.',
          parameters: {
            type: 'object',
            properties: { path: { type: 'string' } },
            required: ['path'],
          },
        },
      },
      execute: args => readFile(String(args['path']), 'utf8'),
    }))
  }
}
```

这里有三个容易混淆的概念：

```text
Plugin   能力的安装单元，例如 readFilePlugin
Tool     模型可选择的动作，例如 read_file
Service  插件共享的连接点，例如 ctx.nano
```

`inject: ['nano']` 声明插件依赖 `NanoRuntime`；`ctx.effect()` 让工具跟随插件的生命周期安装和卸载。随后，`agentLoopPlugin` 只做循环：

```ts
const reply = await ctx.nano.complete(messages)

if (reply.toolCalls.length === 0) return reply.content

for (const call of reply.toolCalls) {
  const result = await ctx.nano.execute(
    call.name,
    JSON.parse(call.arguments),
  )
  messages.push({ role: 'tool', tool_call_id: call.id, content: result })
}
```

当模型没有返回 Tool Call，循环结束；否则执行工具，把结果加入 `messages`，再调用模型。第一篇的 Agent 循环没有消失，只是从写死的主程序变成了可替换的插件。

因此，这个最小实现真正证明的是：**内核只负责连接，能力由插件提供。**

---

## 三、运行与验证

```bash
git clone https://github.com/GitHubxsy/nanodeepseekharness.git
cd nanodeepseekharness
npm install

export DEEPSEEK_API_KEY='你的 API Key'
npm run dev -- '使用 read_file 读取 README.md，并用三句话概括'
```

验证完整链路：

```bash
npm run typecheck
npm test
npm run build
npm start -- '必须使用 read_file 读取 package.json，只回答 name 字段'
```

最后一条命令应输出 `nanodeepseekharness`。

为了保持教学最小集，示例没有实现沙箱、权限确认、持久化和并发调度。它要说明的是插件如何组合，而不是复刻生产级 Harness。

---

## 四、回到 Agent 系列

```text
第一篇：Agent 如何行动
       LLM + 工具 + 循环

后续篇：行动如何被支撑
       Memory + Skills + MCP + SubAgent + Compaction + Safety

本文：这些能力如何持续演化
       最小内核 + 可组合插件
```

“一切皆插件”不是消灭核心，而是把核心缩到最小：它只负责 Context、依赖和生命周期这些稳定的连接机制；模型、工具和执行循环等易变能力，则全部交给插件。

```text
以前：Agent 是一份程序
现在：Agent 是一份能力组合方案
```

这才是“一切皆插件”真正想表达的事情。

---

## 参考资料

- [nanoDeepSeekHarness](https://github.com/GitHubxsy/nanodeepseekharness)
- [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)
- [Cordis](https://github.com/cordiverse/cordis)
- [OpenAI Node SDK](https://github.com/openai/openai-node)

---

*本文是「从零开始理解 Agent」系列番外篇。系列正文见 [nanoAgent](https://github.com/GitHubxsy/nanoAgent)，完整代码见 [nanoDeepSeekHarness](https://github.com/GitHubxsy/nanodeepseekharness)。*

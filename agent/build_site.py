import html
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List


_INLINE_CODE_RE = re.compile(r"`([^`]+)`")


def format_inline(text: str) -> str:
    """HTML-escape text and convert markdown `inline code` into <code class="inline">."""
    parts = []
    last = 0
    for match in _INLINE_CODE_RE.finditer(text):
        parts.append(html.escape(text[last:match.start()]))
        parts.append(f'<code class="inline">{html.escape(match.group(1))}</code>')
        last = match.end()
    parts.append(html.escape(text[last:]))
    return "".join(parts)


def strip_inline_marks(text: str) -> str:
    """Drop markdown `backticks` for places where HTML tags are not allowed (e.g. <meta>)."""
    return _INLINE_CODE_RE.sub(r"\1", text)


ROOT = Path(__file__).parent
REPO_ROOT = ROOT.parent
DOCS_DIR = REPO_ROOT / "docs"
ASSETS_DIR = DOCS_DIR / "assets"
REPO_WEB_BASE = "https://github.com/GitHubxsy/nanoAgent"
SITE_URL = "https://githubxsy.github.io/nanoAgent"
SITE_TITLE = "从零开始理解 Agent"
SITE_SUBTITLE = "1 小时技术分享讲义"
SITE_DESCRIPTION = "把 nanoAgent 前七篇内容压缩成一套 1 小时技术分享讲义，只保留最适合科普分享的代码、演示和练习。"


@dataclass
class Snippet:
    title: str
    start: int
    end: int
    focus: str


@dataclass
class Lesson:
    slug: str
    number: str
    title: str
    short_title: str
    stage: str
    lesson_minutes: str
    summary: str
    core: str
    tags: List[str]
    demo_command: str
    demo_goal: str
    demo_expected: List[str]
    student_takeaways: List[str]
    practice_steps: List[str]
    talk_points: List[str]
    pitfalls: List[str]
    workshop_prompt: str
    md_path: Path
    code_path: Path
    snippets: List[Snippet]


def detect_source_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        branch = result.stdout.strip()
        return branch or "main"
    except Exception:
        return "main"


SOURCE_BRANCH = detect_source_branch()


LESSONS = [
    Lesson(
        slug="essence",
        number="01",
        title="底层原理，只有 100 行",
        short_title="最小闭环",
        stage="起步演示",
        lesson_minutes="8 分钟",
        summary="先别谈框架，把 Agent 最小闭环直接跑出来：模型决定工具，代码执行工具，结果继续喂回模型。",
        core="LLM + 工具 + 循环",
        tags=["工具调用", "Agent Loop", "最小实现"],
        demo_command='python agent/01-essence/agent-essence.py "创建 hello.txt，内容是 Hello Agent"',
        demo_goal="让大家当场看到 Agent 不是“回答文字”，而是真的改动了文件系统。",
        demo_expected=[
            "先用循环图说明 Agent 每一轮都在做“思考 -> 选工具 -> 回填结果 -> 再思考”。",
            "终端先打印 `[Tool] write_file(...)`，说明模型选择了工具。",
            "再次要求它读取 `hello.txt`，验证效果已经落到真实文件。",
            "再回头指给大家看 `tools` 列表，说明模型只能从这份清单里挑能力。",
        ],
        student_takeaways=[
            "能解释 Agent 与 Chat 的根本区别。",
            "能看懂 `tools`、`functions`、`messages` 和循环的关系。",
            "知道 Tool 的本质是“模型可见的能力声明”，不是模型自己发明出来的命令。",
            "知道 Agent 的执行权仍然掌握在代码里，不在模型里。",
        ],
        practice_steps=[
            "把 `max_iterations` 改成 2，观察复杂任务会如何提前中断。",
            "把 `write_file` 从 `tools` 里临时删掉，再让 Agent 写文件，观察它为什么做不到。",
            "让 Agent 连续执行“写文件 + 读文件”两个动作，体会循环的必要性。",
            "给 `execute_bash` 加一句更清晰的描述，看看模型是否更容易选对工具。",
        ],
        talk_points=[
            "先讲循环：Agent 不是只回答一次，而是在每一轮里决定要不要继续行动。",
            "LLM 输出的是结构化“调用意图”，不是直接执行系统命令。",
            "再讲 Tool：`tools` 是模型看到的能力清单，`functions` 才是真正落地执行的代码。",
        ],
        pitfalls=[
            "只写 Python 函数、不把它放进 `tools`，模型就根本不知道这项能力存在。",
            "`execute_bash` 功能太强，后面必须加安全边界。",
            "工具报错也要回填给模型，否则它无法自我修正。",
            "只堆工具不设计循环，最后就会退化回普通问答。",
        ],
        workshop_prompt="把它当成一台会自己选工具的“任务执行机”，而不是聊天窗口。",
        md_path=ROOT / "01-essence/agent-essence.md",
        code_path=ROOT / "01-essence/agent-essence.py",
        snippets=[
            Snippet(
                title="先看最小 Agent 循环",
                start=73,
                end=97,
                focus="先抓住这 20 多行：请求模型、拿到 tool call、执行工具、把结果回填，然后进入下一轮。",
            ),
            Snippet(
                title="先看 Tool 声明",
                start=11,
                end=51,
                focus="这段代码决定了模型能看到哪些能力，以及每个工具需要什么参数。",
            ),
            Snippet(
                title="再看工具落地到哪段 Python",
                start=54,
                end=70,
                focus="Tool 不是抽象概念，最后一定要映射到真实函数，模型选中的名字就是从这里执行的。",
            ),
        ],
    ),
    Lesson(
        slug="skills-mcp",
        number="02",
        title="Skills、Rules 与 MCP",
        short_title="能力外置",
        stage="第二步：把能力接进来",
        lesson_minutes="10 分钟",
        summary="第二讲不讲计划，重点讲三层能力扩展：Skill 补知识，Rule 立边界，MCP 接外部工具。真正的重点不是配置细节，而是它们分别进入了上下文还是工具列表。",
        core="Skill + Rule + MCP",
        tags=["Skills", "Rules", "MCP"],
        demo_command='python agent/03-skills-mcp/agent-skills-mcp.py "扫描项目里所有 TODO 并生成修复顺序"',
        demo_goal="展示 Agent 如何在启动时从项目目录加载 Skills、Rules 和 MCP 工具，让能力不再写死在脚本里。",
        demo_expected=[
            "终端先出现 `[Init] Loading ClaudeCode features...`，然后是 `[Rules]`、`[Skills]`、`[MCP]` 各自的加载日志。",
            "回头指给大家看 `all_tools = base_tools + mcp_tools` 这一行，说明 MCP 工具是从外部并入工具列表的。",
            "强调一句主线：Rules / Skills 走的是 prompt，MCP 走的是 tools，进入的层不一样。",
        ],
        student_takeaways=[
            "知道 Skill 负责补充知识，Rule 负责约束行为，MCP 负责接入外部工具。",
            "能看懂 Rules / Skills / MCP 分别从哪里加载，最后怎么拼进上下文和工具列表。",
            "理解工程化 Agent 的关键不是计划，而是能力和约束的外置。",
        ],
        practice_steps=[
            "新建 `.agent/rules/code-style.md`，只写一条简单规范，再运行一次任务。",
            "给 `.agent/skills/` 放一个最小 JSON 技能描述，观察加载输出。",
            "在 `.agent/mcp.json` 里声明一个最小 tool 配置，观察 `all_tools` 是如何变化的。",
        ],
        talk_points=[
            "Skill 补的是知识，Rule 管的是行为，MCP 扩的是工具边界，这三层不要混在一起。",
            "Rules 和 Skills 最后进入 prompt，MCP 最后进入 tools，注入位置不同，作用也不同。",
            "能力外置以后，Agent 才开始像一个项目级系统，而不是单文件脚本。",
        ],
        pitfalls=[
            "把所有东西都塞进 Rule，会让职责边界变糊，模型也更难稳定执行。",
            "Skills 太多会稀释上下文，MCP 工具太多会降低模型的选 tool 准确率。",
            "规则、技能、工具描述互相冲突时，模型的表现会变得不稳定。",
        ],
        workshop_prompt="分享时只演示一个最小 Rule、一个最小 Skill，再指给大家看 MCP 工具是如何接进来的。",
        md_path=ROOT / "03-skills-mcp/agent-skills-mcp.md",
        code_path=ROOT / "03-skills-mcp/agent-skills-mcp.py",
        snippets=[
            Snippet(
                title="先看 Rules / Skills / MCP 怎么加载",
                start=266,
                end=305,
                focus="这段代码把 Rule、Skill 和 MCP 工具从项目目录读出来，是“能力外置”的入口。",
            ),
            Snippet(
                title="再看它们怎么进入上下文和工具列表",
                start=370,
                end=394,
                focus="真正的关键是注入位置：Rules / Skills 进入 prompt，MCP 工具进入 `all_tools`。",
            ),
        ],
    ),
    Lesson(
        slug="memory",
        number="03",
        title="Memory：让 Agent 记住上一次",
        short_title="记忆回放",
        stage="第三步：把历史带回来",
        lesson_minutes="8 分钟",
        summary="这一讲把重点放在 Memory 本身：Agent 如何把一次任务写进 `agent_memory.md`，又如何在下一次运行时把这段历史重新带回上下文。规划只作为补充，不是主线。",
        core="写入记忆 + 回放记忆",
        tags=["Memory", "Persistence", "Context Replay"],
        demo_command='python agent/02-memory/agent-memory.py "创建 launch-note.txt，内容是 Agent Memory Demo"\npython agent/02-memory/agent-memory.py "不重新读文件，只根据记忆说明你上一次完成了什么任务"',
        demo_goal="演示 Agent 如何把一次执行结果写进记忆文件，并在下一次运行时直接把这段历史带回来。",
        demo_expected=[
            "第一次运行结束后，打开 `agent_memory.md`，确认任务和结果已经被追加进去。",
            "第二次运行即使不重新读文件，也能基于刚才的历史说明“上一次做了什么”。",
            "最后指出真正关键的不是 `--plan`，而是 `load_memory()` 和 `save_memory()` 形成了闭环。",
        ],
        student_takeaways=[
            "能说清 Memory 至少包含写入、读取、回放三步。",
            "能看懂 `load_memory()`、`save_memory()` 和 `run_agent_plus()` 是怎么串起来的。",
            "知道规划是可选增强，但这一讲真正的主线是持久记忆。",
        ],
        practice_steps=[
            "连续运行两次任务，再打开 `agent_memory.md`，看日志是如何一条条追加进去的。",
            "把 `load_memory()` 的窗口裁剪改小，看看旧历史是如何衰减的。",
            "临时注释掉 `save_memory()` 或 `load_memory()` 其中一个，再对比 Memory 闭环为什么会失效。",
        ],
        talk_points=[
            "最小 Memory 不需要向量库，先把“写进文件”和“下次读回”这条链路跑通就够了。",
            "真正让 Agent 记住过去的，不是文件本身，而是把历史重新注入了 system prompt。",
            "规划可以以后再展开，但没有 Memory，Agent 每次启动都像失忆重来。",
        ],
        pitfalls=[
            "只写入不读取，不算真正的 Memory，只是留下了一份日志。",
            "历史内容回放过多，后面很快又会碰到上下文膨胀。",
            "把错误结果写进记忆后，下一轮会把污染一起带回来。",
        ],
        workshop_prompt="先连续跑两次任务，再打开 `agent_memory.md` 看看 Agent 是怎么把历史写下来又带回下一轮的。",
        md_path=ROOT / "02-memory/agent-memory.md",
        code_path=ROOT / "02-memory/agent-memory.py",
        snippets=[
            Snippet(
                title="Memory 写入与读取",
                start=109,
                end=127,
                focus="这段代码就是最小 Memory 闭环的前半段：从文件读取历史，再把新结果追加回去。",
            ),
            Snippet(
                title="把旧记忆重新带回上下文",
                start=199,
                end=220,
                focus="真正的关键不是保存了多少历史，而是启动新任务时有没有把旧记忆重新塞回 system prompt。",
            ),
        ],
    ),
    Lesson(
        slug="subagent",
        number="04",
        title="SubAgent 子智能体",
        short_title="任务委派",
        stage="把活拆出去",
        lesson_minutes="8 分钟",
        summary="当一个 Agent 同时想架构、写后端、写前端时，就该把一部分任务委派给更聚焦的子代理。",
        core="独立上下文 + 角色委派",
        tags=["SubAgent", "Delegation", "Role Prompt"],
        demo_command='python agent/04-subagent/agent-subagent.py "创建一个 TODO 应用，包含 Python 后端和 HTML 前端"',
        demo_goal="让大家看到“委派”不是神秘概念，本质上就是把另一个 Agent 也做成工具。",
        demo_expected=[
            "主 Agent 会调用 `subagent(...)`，并给它一个明确角色与任务。",
            "子代理有自己的 `sub_messages`，不会把主代理上下文一股脑复制过去。",
            "子代理返回的是结果摘要，而不是完整内部历史。",
        ],
        student_takeaways=[
            "知道 SubAgent 最关键的是“独立上下文”，不是“多开一个模型”。",
            "能解释为什么分享里要禁止子代理继续派子代理。",
            "能把一个复杂任务拆成主代理 + 子代理两个角色来演示。",
        ],
        practice_steps=[
            "把一个“写 README”任务改成由文档子代理完成。",
            "给子代理新增一个更具体的角色描述，观察输出是否更稳。",
            "让主代理只保留协调职责，避免它同时写所有实现细节。",
        ],
        talk_points=[
            "委派的收益来自上下文收敛，不只是并行化。",
            "角色 prompt 越具体，子代理越像一个真正的“岗位”。",
            "返回摘要而非全量历史，是后面控制上下文成本的关键习惯。",
        ],
        pitfalls=[
            "任务边界不清时，主代理和子代理会重复劳动。",
            "允许无限递归委派，成本和复杂度都会失控。",
            "如果子代理的角色太泛，它只是换了个名字的主代理。",
        ],
        workshop_prompt="最好的分享方式是只演一个前后端双角色案例，让委派的价值立刻可见。",
        md_path=ROOT / "04-subagent/agent-subagent.md",
        code_path=ROOT / "04-subagent/agent-subagent.py",
        snippets=[
            Snippet(
                title="把 subagent 做成一个工具",
                start=104,
                end=142,
                focus="独立 `sub_messages` + 禁止递归，是这段实现最值得讲的两点。",
            )
        ],
    ),
    Lesson(
        slug="teams",
        number="05",
        title="多智能体团队协作",
        short_title="团队编排",
        stage="让角色长期存在",
        lesson_minutes="9 分钟",
        summary="SubAgent 还是一次性临时工；这一讲把角色变成有身份、会通信、能复盘的真正团队。",
        core="持久 Agent + 通信通道",
        tags=["Team", "Inbox", "Lifecycle"],
        demo_command='python agent/05-teams/agent-teams.py "创建一个 TODO 应用，包含 Python 后端和 HTML 前端"',
        demo_goal="把“团队协作”讲成一种可落地的软件结构，而不是抽象概念。",
        demo_expected=[
            "启动后会先由 `plan_team()` 拆出成员与分工。",
            "每个 Agent 都保留自己的 `messages` 和记忆，不会执行一次就消失。",
            "成员完成后通过 `broadcast()` 把信息发给队友，最后 reviewer 再做检查。",
        ],
        student_takeaways=[
            "明白 Team 比 SubAgent 多出来的是持久身份与通信。",
            "能用 `inbox` 这种极简单模型解释 Agent 间消息传递。",
            "知道为什么 reviewer 是分享里最好展示团队价值的角色。",
        ],
        practice_steps=[
            "把 `plan_team()` 固定成两开发一审查的三人团队。",
            "在执行中手动插入一次 `send()`，演示点对点消息和广播的区别。",
            "让 reviewer 再执行一次 `chat()`，体会持久记忆如何带来二次审查。",
        ],
        talk_points=[
            "多智能体最重要的不是人数，而是角色和生命周期。",
            "Agent 的 `inbox` 足够简单，却已经能支持很多协作场景。",
            "团队越大不一定越好，真正有价值的是信息流变清晰。",
        ],
        pitfalls=[
            "如果每个角色都很泛，最后只是多个普通助手轮流说话。",
            "消息太多时又会重新触发上下文压力。",
            "团队协作如果没有 reviewer，很难展示“协作带来的质量提升”。",
        ],
        workshop_prompt="讲 1 小时时，把多智能体团队讲成“带 reviewer 的协作流水线”最容易让大家记住。",
        md_path=ROOT / "05-teams/agent-teams.md",
        code_path=ROOT / "05-teams/agent-teams.py",
        snippets=[
            Snippet(
                title="持久化的 Agent 对象",
                start=150,
                end=210,
                focus="这段代码解释了为什么团队成员会“记得队友之前说过什么”。",
            ),
            Snippet(
                title="Team 管理生命周期与通信",
                start=219,
                end=247,
                focus="招募、广播、解散，这里就是多智能体协作最小骨架。",
            ),
        ],
    ),
    Lesson(
        slug="compact",
        number="06",
        title="上下文压缩",
        short_title="长任务生存",
        stage="防止自我窒息",
        lesson_minutes="7 分钟",
        summary="这一讲不讲理论史，只解决一个分享里特别容易说清的问题：为什么长任务里 Agent 会被自己的历史压死。",
        core="摘要旧消息，保留最近窗口",
        tags=["Context Window", "Compaction", "Summarization"],
        demo_command='python agent/06-compact/agent-compact.py "在当前目录下找到所有 Python 文件，统计每个文件行数并写入 report.txt"',
        demo_goal="让大家看到压缩不是“加分项”，而是 Agent 长任务能不能活下来的生死线。",
        demo_expected=[
            "把阈值调小后，很容易在终端看到 `[Compact]` 日志。",
            "压缩会保留 system prompt 与最近几条消息，只把旧消息折叠成摘要。",
            "强调：压缩也是花 token 的，所以它是工程折中，不是白送能力。",
        ],
        student_takeaways=[
            "知道为什么更大的 context window 不是根治方案。",
            "能解释 `COMPACT_THRESHOLD` 与 `KEEP_RECENT` 的取舍。",
            "理解“记住要点、忘掉细节”是 Agent 的必要能力。",
        ],
        practice_steps=[
            "把 `COMPACT_THRESHOLD` 调到 8，制造一轮可见的压缩。",
            "把 `KEEP_RECENT` 从 6 改成 4，比较当前任务衔接是否变差。",
            "观察压缩前后 messages 的结构变化，不只看日志。",
        ],
        talk_points=[
            "压缩不是为了优雅，是为了不在真实任务里死于上下文溢出。",
            "最不能丢的是 system prompt 和当前工作现场。",
            "旧消息摘要化，本质上是在用模型帮助自己整理历史。",
        ],
        pitfalls=[
            "摘要过度会丢掉关键路径和文件名。",
            "recent window 太短会让 Agent 瞬间断片。",
            "只做截断不做压缩，依然扛不住复杂长任务。",
        ],
        workshop_prompt="分享时把阈值调小，强制触发一次压缩，是最直观的讲法。",
        md_path=ROOT / "06-compact/agent-compact.md",
        code_path=ROOT / "06-compact/agent-compact.py",
        snippets=[
            Snippet(
                title="上下文压缩函数",
                start=129,
                end=190,
                focus="这就是分享里最值钱的 60 行：把旧历史折叠成摘要，把当前现场留下来。",
            )
        ],
    ),
    Lesson(
        slug="safety",
        number="07",
        title="三道安全防线",
        short_title="上线边界",
        stage="能力关进笼子",
        lesson_minutes="5 分钟",
        summary="最后一讲只讲 Agent 真正落地时最不能省的边界：危险命令拦截、人工确认、超长输出截断。",
        core="黑名单 + 人工确认 + 输出截断",
        tags=["Safety", "Approval", "Guardrails"],
        demo_command='python agent/07-safety/agent-safe.py "列出当前目录的文件"',
        demo_goal="让大家形成一个很强的工程直觉：能力越强，越要在人机边界处加护栏。",
        demo_expected=[
            "普通命令会先弹确认，再执行。",
            "危险命令会在黑名单阶段直接被拦下。",
            "超长输出会被截断，顺带呼应上一讲的上下文控制问题。",
        ],
        student_takeaways=[
            "能说清三道防线分别解决什么问题。",
            "知道为什么不能把“是否安全”完全外包给模型自己判断。",
            "理解安全与上下文控制其实是同一件工程责任的两面。",
        ],
        practice_steps=[
            "给 `DANGEROUS_PATTERNS` 自己再补一条高危命令规则。",
            "把 `read_file` 改成只允许读取项目目录，做一个最小白名单。",
            "故意读取一个超长文件，观察截断提示如何返回给模型。",
        ],
        talk_points=[
            "黑名单负责挡住已知高危动作，人工确认负责最后边界。",
            "输出截断既是安全问题，也是稳定性问题。",
            "真正可用的 Agent 一定要允许用户拒绝某一步。",
        ],
        pitfalls=[
            "只靠黑名单是不够的，绕过方式永远存在。",
            "所有动作都确认会严重伤体验，要做分级策略。",
            "`--auto` 只能在你完全信任的隔离环境里用。",
        ],
        workshop_prompt="把安全讲成‘让 Agent 能上线’的最后门槛，大家会更容易记住。",
        md_path=ROOT / "07-safety/agent-safe.md",
        code_path=ROOT / "07-safety/agent-safe.py",
        snippets=[
            Snippet(
                title="危险命令黑名单与确认机制",
                start=49,
                end=107,
                focus="先让大家明白黑名单和确认框各拦哪一层风险。",
            ),
            Snippet(
                title="安全版 execute_bash",
                start=162,
                end=186,
                focus="三道防线是如何串起来的，这段函数最清楚。",
            ),
        ],
    ),
]


SESSION_OUTCOMES = [
    "能从零解释 Agent 的最小工作闭环，而不是只会使用现成产品。",
    "能把一个单文件 Agent 逐步升级到有记忆、可委派、可扩展、可控的原型。",
    "能现场带着大家跑 3 个最小 demo，并把关键代码讲清楚。",
]


SESSION_SETUP = [
    "Python 环境可运行 `agent/*.py` 文件。",
    "已设置 `OPENAI_API_KEY`，并准备一个可用模型。",
    "分享时优先用终端和代码窗口，不用展示全部原文文章。",
]


SESSION_FORMAT = [
    "30% 关键代码：先抓住决定行为的那几行实现，不从概念空讲开始。",
    "40% 现场演示：再用终端把行为跑出来，让代码和结果一一对应。",
    "30% 动手延伸：最后留一个可自己复现的小改动，方便继续探索。",
]


AGENDA = [
    ("00 - 05", "开场：为什么今天不讲大而全", "先建立一个共识：这 1 小时只保留真正能拿去做 Demo 的内容。"),
    ("05 - 13", "第 01 讲：最小闭环", "跑通最小 Agent，让大家看见工具调用、执行和结果回填。"),
    ("13 - 23", "第 02 讲：Skills / Rules / MCP", "把 Skill、Rule、MCP 这三层能力接进来，重点讲它们各自进入了上下文还是工具列表。"),
    ("23 - 31", "第 03 讲：Memory", "演示 Agent 如何把一次执行结果写进记忆文件，并在下一次运行时带回上下文。"),
    ("31 - 39", "第 04 讲：SubAgent", "用前后端双角色案例，解释为什么复杂任务要委派。"),
    ("39 - 48", "第 05 讲：Teams", "把委派升级成长期协作团队，重点演示 reviewer 复盘。"),
    ("48 - 55", "第 06 讲：上下文压缩", "现场把阈值调小，强制触发一次压缩。"),
    ("55 - 60", "第 07 讲：安全防线 + 收尾", "用危险命令拦截与人工确认收束工程边界。"),
]


def github_blob_url(path: Path) -> str:
    relative = path.relative_to(REPO_ROOT).as_posix()
    return f"{REPO_WEB_BASE}/blob/{SOURCE_BRANCH}/{relative}"


def github_lines_url(path: Path, start: int, end: int) -> str:
    return f"{github_blob_url(path)}#L{start}-L{end}"


def page_url(filename: str) -> str:
    if filename == "index.html":
        return f"{SITE_URL}/"
    return f"{SITE_URL}/{filename}"


def build_head(title: str, description: str, filename: str, page_type: str) -> str:
    canonical = page_url(filename)
    plain_description = strip_inline_marks(description)
    return f"""
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(plain_description)}">
  <meta name="theme-color" content="#1f2430">
  <link rel="canonical" href="{html.escape(canonical)}">
  <meta property="og:locale" content="zh_CN">
  <meta property="og:type" content="{page_type}">
  <meta property="og:site_name" content="{html.escape(SITE_TITLE)}">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(plain_description)}">
  <meta property="og:url" content="{html.escape(canonical)}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{html.escape(title)}">
  <meta name="twitter:description" content="{html.escape(plain_description)}">
  <link rel="stylesheet" href="assets/style.css">
  <script defer src="assets/site.js"></script>
""".strip()


def render_tags(tags: List[str], class_name: str) -> str:
    return "".join(f'<span class="{class_name}">{html.escape(tag)}</span>' for tag in tags)


def render_bullets(items: List[str], class_name: str = "lesson-list") -> str:
    body = "".join(f"<li>{format_inline(item)}</li>" for item in items)
    return f'<ul class="{class_name}">{body}</ul>'


def render_steps(items: List[str]) -> str:
    body = "".join(f"<li>{format_inline(item)}</li>" for item in items)
    return f'<ol class="lesson-steps">{body}</ol>'


def code_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def excerpt_code(path: Path, start: int, end: int) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    selected = []
    for number in range(start, min(end, len(lines)) + 1):
        selected.append(f"{number:4d} {lines[number - 1]}")
    return "\n".join(selected)


def lesson_nav(current_slug: str) -> str:
    items = []
    for lesson in LESSONS:
        current_class = " is-current" if lesson.slug == current_slug else ""
        items.append(
            f'''
            <a class="chapter-rail-link{current_class}" href="{lesson.slug}.html">
              <span class="course-step">第 {lesson.number} 讲</span>
              <strong>{html.escape(lesson.title)}</strong>
              <small>{html.escape(lesson.short_title)} · {html.escape(lesson.core)}</small>
            </a>
            '''
        )
    return "".join(items)


def build_footer() -> str:
    return f"""
    <footer class="site-footer">
      <p>这套分享讲义只保留 1 小时技术分享最需要的代码、演示与延伸线索，完整原文与源码请看 GitHub。</p>
      <div class="footer-links">
        <a href="{REPO_WEB_BASE}">GitHub 仓库</a>
        <a href="{github_blob_url(ROOT / 'README_CN.md')}">系列导读</a>
        <a href="{github_blob_url(ROOT / 'build_site.py')}">站点生成器</a>
      </div>
    </footer>
    """


def build_essence_figure() -> str:
    return """
    <figure class="lesson-figure">
      <img src="assets/agent-loop-overview.svg" alt="Agent 循环示意图：用户任务进入模型，模型选择工具，工具执行结果回填给模型，再决定下一步。">
      <figcaption>先记住这一点：Agent 的核心不是某一个 Tool，而是“模型决策、工具执行、结果回填、再次决策”这个循环。</figcaption>
    </figure>
    """


def build_home_page() -> str:
    lesson_cards = []
    for lesson in LESSONS:
        lesson_cards.append(
            f"""
            <article class="lesson-card">
              <p class="lesson-index">第 {lesson.number} 讲 · {html.escape(lesson.stage)}</p>
              <h3>{html.escape(lesson.title)}</h3>
              <p>{format_inline(lesson.summary)}</p>
              <div class="lesson-meta">
                <span>{html.escape(lesson.lesson_minutes)}</span>
                <span>{code_lines(lesson.code_path)} 行代码</span>
                <span>{html.escape(lesson.core)}</span>
              </div>
              <p class="lesson-kicker">分享重点：{format_inline(lesson.workshop_prompt)}</p>
              <div class="lesson-tag-row">{render_tags(lesson.tags, "tag")}</div>
              <a class="lesson-link" href="{lesson.slug}.html">看分享讲义</a>
            </article>
            """
        )

    agenda_items = []
    for time_range, title, note in AGENDA:
        agenda_items.append(
            f"""
            <article class="agenda-item">
              <p class="agenda-time">{html.escape(time_range)}</p>
              <div class="agenda-content">
                <h3>{html.escape(title)}</h3>
                <p>{html.escape(note)}</p>
              </div>
            </article>
            """
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  {build_head(f"{SITE_TITLE}｜{SITE_SUBTITLE}", SITE_DESCRIPTION, "index.html", "website")}
</head>
<body>
  <a class="skip-link" href="#main-content">跳到正文</a>
  <div class="site-shell">
    <header class="site-header">
      <a class="brand" href="index.html">
        <span class="brand-mark">nanoAgent</span>
        <span class="brand-text">{SITE_TITLE}</span>
      </a>
      <nav class="top-nav">
        <a href="#agenda">分享流程</a>
        <a href="#format">分享方式</a>
        <a href="#lessons">七讲讲义</a>
        <a href="{REPO_WEB_BASE}">GitHub</a>
      </nav>
    </header>

    <main id="main-content">
      <section class="hero-panel">
        <div class="hero-copy">
          <p class="eyebrow">{SITE_SUBTITLE}</p>
          <h1>先看关键代码，再把 Agent 跑起来</h1>
          <p class="hero-lead">这套站点把前七篇文章压成一套面向技术分享科普的 1 小时讲义。每一讲都先抓最关键的实现，再用终端验证行为，最后留一个可以自己继续改的动手入口。</p>
          <p class="mode-note">这是一套用于技术分享科普的讲义：重点是把原理讲清楚，把代码讲明白，把 Demo 跑通。</p>
          <div class="hero-actions">
            <a class="primary-btn" href="essence.html">从第 01 讲开始</a>
            <a class="secondary-btn" href="#agenda">先看 60 分钟流程</a>
          </div>
        </div>
        <div class="hero-side">
          <div class="fact-grid">
            <article class="fact-card">
              <strong>60 分钟</strong>
              <span>一小时完整分享</span>
            </article>
            <article class="fact-card">
              <strong>7 讲</strong>
              <span>全部压缩为分享讲义</span>
            </article>
            <article class="fact-card">
              <strong>代码优先</strong>
              <span>先看实现，再看行为结果</span>
            </article>
            <article class="fact-card">
              <strong>可直接复现</strong>
              <span>每讲都有演示命令与动手入口</span>
            </article>
          </div>
        </div>
      </section>

      <section class="section-block" id="format">
        <div class="section-head">
          <p class="eyebrow">Share Format</p>
          <h2>这场技术分享怎么展开</h2>
          <p>核心方法很简单：不从概念空讲开始，而是先抓代码主线，再用终端输出把原理落到可观察的结果上。</p>
        </div>
        <div class="format-grid">
          <article class="format-card">
            <h3>讲清什么</h3>
            {render_bullets(SESSION_OUTCOMES)}
          </article>
          <article class="format-card">
            <h3>怎么准备</h3>
            {render_bullets(SESSION_SETUP)}
          </article>
          <article class="format-card">
            <h3>分享顺序</h3>
            {render_bullets(SESSION_FORMAT)}
          </article>
        </div>
      </section>

      <section class="section-block" id="agenda">
        <div class="section-head">
          <p class="eyebrow">Agenda</p>
          <h2>60 分钟怎么分配</h2>
          <p>核心原则：每一讲都先看关键代码，再用终端验证行为，最后给一个能自己继续改的入口，不把大家淹没在全文里。</p>
        </div>
        <div class="agenda-list">
          {"".join(agenda_items)}
        </div>
      </section>

      <section class="section-block" id="lessons">
        <div class="section-head">
          <p class="eyebrow">Lesson Pack</p>
          <h2>七讲分享讲义</h2>
          <p>每个页面都按“关键代码 -> 现场演示 -> 自己试一轮”的顺序排好，适合在技术分享里直接展开。</p>
        </div>
        <div class="lesson-grid">
          {"".join(lesson_cards)}
        </div>
      </section>
    </main>
    {build_footer()}
  </div>
</body>
</html>
"""


def build_lesson_page(index: int, lesson: Lesson) -> str:
    prev_lesson = LESSONS[index - 1] if index > 0 else None
    next_lesson = LESSONS[index + 1] if index < len(LESSONS) - 1 else None

    toc_links = [
        ("code", "先看关键代码"),
        ("demo", "再看它怎么跑"),
        ("practice", "自己试一轮"),
        ("goals", "这一讲会看懂什么"),
        ("talk", "分享只讲这 3 件事"),
        ("pitfalls", "容易误解"),
        ("extend", "继续深挖"),
    ]

    snippet_cards = []
    for snippet in lesson.snippets:
        snippet_cards.append(
            f"""
            <article class="code-card">
              <div class="code-card-head">
                <div>
                  <p class="lesson-index">{html.escape(snippet.title)}</p>
                  <h3>{format_inline(snippet.focus)}</h3>
                </div>
                <a class="source-link" href="{github_lines_url(lesson.code_path, snippet.start, snippet.end)}">看 GitHub 行号</a>
              </div>
              <pre class="code-block"><code class="language-python">{html.escape(excerpt_code(lesson.code_path, snippet.start, snippet.end))}</code></pre>
            </article>
            """
        )

    prev_link = (
        f'<a class="pager-link" href="{prev_lesson.slug}.html"><span>上一篇</span><strong>{prev_lesson.number}. {html.escape(prev_lesson.short_title)}</strong></a>'
        if prev_lesson
        else ""
    )
    next_link = (
        f'<a class="pager-link" href="{next_lesson.slug}.html"><span>下一篇</span><strong>{next_lesson.number}. {html.escape(next_lesson.short_title)}</strong></a>'
        if next_lesson
        else ""
    )
    visual_html = build_essence_figure() if lesson.slug == "essence" else ""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  {build_head(f"{lesson.number}. {lesson.title}｜{SITE_SUBTITLE}", lesson.summary, f"{lesson.slug}.html", "article")}
</head>
<body class="article-body">
  <a class="skip-link" href="#main-content">跳到正文</a>
  <div class="reading-progress" aria-hidden="true"><span class="reading-progress-bar"></span></div>
  <div class="site-shell">
    <header class="site-header">
      <a class="brand" href="index.html">
        <span class="brand-mark">nanoAgent</span>
        <span class="brand-text">{SITE_TITLE}</span>
      </a>
      <nav class="top-nav">
        <a href="index.html#agenda">分享流程</a>
        <a href="index.html#lessons">七讲讲义</a>
        <a href="{REPO_WEB_BASE}">GitHub</a>
      </nav>
    </header>

    <main class="article-layout" id="main-content">
      <aside class="article-sidebar">
        <div class="sidebar-card">
          <p class="eyebrow">第 {lesson.number} 讲 · {html.escape(lesson.stage)}</p>
          <h2 class="lesson-title">{html.escape(lesson.title)}</h2>
          <p>{format_inline(lesson.summary)}</p>
          <div class="chip-row">
            <span class="chip">{html.escape(lesson.lesson_minutes)}</span>
            <span class="chip">{code_lines(lesson.code_path)} 行代码</span>
            <span class="chip">{html.escape(lesson.core)}</span>
          </div>
        </div>

        <div class="sidebar-card">
          <h2>课程导航</h2>
          <div class="chapter-rail">{lesson_nav(lesson.slug)}</div>
        </div>

        <div class="sidebar-card">
          <h2>页面目录</h2>
          <nav class="toc">
            {"".join(f'<a class="toc-link" href="#{anchor}">{html.escape(label)}</a>' for anchor, label in toc_links)}
          </nav>
        </div>
      </aside>

      <article class="article-main">
        <section class="article-hero">
          <div class="breadcrumbs">
            <a href="index.html">分享首页</a>
            <span>/</span>
            <a href="index.html#lessons">分享讲义</a>
            <span>/</span>
            <span>第 {lesson.number} 讲</span>
          </div>
          <p class="eyebrow">{SITE_SUBTITLE}</p>
          <h1>{lesson.number}. {html.escape(lesson.title)}</h1>
          <p class="lead">{format_inline(lesson.summary)}</p>
          <p class="mode-note">这页按“先看代码，再看演示，最后自己试一轮”的顺序编排，适合技术分享科普场景。</p>
          <div class="tag-row">{render_tags(lesson.tags, "tag")}</div>
          <div class="hero-actions">
            <a class="primary-btn" href="#code">先看关键代码</a>
            <a class="secondary-btn" href="#demo">再看现场演示</a>
          </div>
        </section>

        <section class="lesson-section" id="code">
          <div class="lesson-section-head">
            <p class="eyebrow">Code First</p>
            <h2>先看关键代码</h2>
            <p>先抓住决定行为的那段实现，再去看终端结果，会更容易把 Agent 的工作方式讲清楚。</p>
          </div>
          {visual_html}
          <div class="code-group">
            {"".join(snippet_cards)}
          </div>
        </section>

        <section class="lesson-section" id="demo">
          <div class="lesson-section-head">
            <p class="eyebrow">Live Demo</p>
            <h2>再看它怎么跑</h2>
            <p>{format_inline(lesson.demo_goal)}</p>
          </div>
          <div class="demo-box">
            <p class="lesson-index">演示命令</p>
            <pre class="demo-command"><code>{html.escape(lesson.demo_command)}</code></pre>
            {render_bullets(lesson.demo_expected, "lesson-list")}
          </div>
        </section>

        <section class="lesson-section" id="practice">
          <div class="lesson-section-head">
            <p class="eyebrow">Try It</p>
            <h2>自己试一轮</h2>
            <p>{format_inline(lesson.workshop_prompt)}</p>
          </div>
          {render_steps(lesson.practice_steps)}
        </section>

        <section class="lesson-section" id="goals">
          <div class="lesson-section-head">
            <p class="eyebrow">Takeaway</p>
            <h2>这一讲会看懂什么</h2>
          </div>
          {render_bullets(lesson.student_takeaways)}
        </section>

        <section class="lesson-section" id="talk">
          <div class="lesson-section-head">
            <p class="eyebrow">Share Track</p>
            <h2>分享只讲这 3 件事</h2>
          </div>
          {render_bullets(lesson.talk_points)}
        </section>

        <section class="lesson-section" id="pitfalls">
          <div class="lesson-section-head">
            <p class="eyebrow">Pitfalls</p>
            <h2>容易误解</h2>
          </div>
          {render_bullets(lesson.pitfalls)}
        </section>

        <section class="lesson-section" id="extend">
          <div class="lesson-section-head">
            <p class="eyebrow">Extend</p>
            <h2>继续深挖</h2>
            <p>分享里不展开全文，这里保留完整文章和源码入口，方便继续顺着往下看。</p>
          </div>
          <div class="deep-links">
            <a class="secondary-btn" href="{github_blob_url(lesson.md_path)}">读完整原文</a>
            <a class="secondary-btn" href="{github_blob_url(lesson.code_path)}">看完整代码</a>
          </div>
        </section>

        <nav class="pager">
          {prev_link}
          {next_link}
        </nav>
      </article>
    </main>
    {build_footer()}
  </div>
</body>
</html>
"""


def ensure_dirs() -> None:
    DOCS_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)


def tidy_output(text: str) -> str:
    cleaned = "\n".join(line.rstrip() for line in text.splitlines())
    return f"{cleaned}\n"


def main() -> None:
    ensure_dirs()
    (DOCS_DIR / "index.html").write_text(tidy_output(build_home_page()), encoding="utf-8")
    for index, lesson in enumerate(LESSONS):
        page = tidy_output(build_lesson_page(index, lesson))
        (DOCS_DIR / f"{lesson.slug}.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()

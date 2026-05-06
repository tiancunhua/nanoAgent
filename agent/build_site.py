import html
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import date
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
SITE_SUBTITLE = "60 分钟讲义"
SITE_DESCRIPTION = "一套面向技术分享的 Agent 实战路线：用最小代码和真实演示，从 Tool Loop、Memory、能力外置一路走到压缩与安全边界。"
SITE_AUTHOR = "GitHubxsy"
BUILD_DATE = date.today().isoformat()


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
    scenario: str
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


@dataclass
class Resource:
    number: str
    label: str
    title: str
    short_title: str
    summary: str
    path: Path


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
        title="底层原理，约 100 行",
        short_title="最小闭环",
        stage="起步演示",
        lesson_minutes="8 分钟",
        summary="没有框架，直接运行 Agent 的最小闭环：模型选择工具，代码执行工具，结果回填给模型。",
        core="LLM + 工具 + 循环",
        tags=["工具调用", "Agent Loop", "最小实现"],
        scenario="把“帮我创建 hello.txt，内容写 Hello Agent”这类任务交给 ChatGPT，它只能给你建议；如果希望它真的在文件系统里创建出这个文件，就需要在模型外面再裹一层能调用工具、能循环执行的代码。",
        demo_command='python agent/01-essence/agent-essence.py "创建 hello.txt，内容是 Hello Agent"',
        demo_goal="现场观察 Agent 不只是输出文字，而是真实地改动了文件系统。",
        demo_expected=[
            "对照循环图：Agent 每一轮执行“决策 → 调用工具 → 回填结果 → 再次决策”。",
            "终端首先打印 `[Tool] write_file(...)`，表示模型选择了工具。",
            "再次要求读取 `hello.txt`，确认改动已落到真实文件。",
            "查看 `tools` 列表：模型只能从这份清单中选择能力。",
        ],
        student_takeaways=[
            "能解释 Agent 与 Chat 的本质区别。",
            "能看懂 `tools`、`functions`、`messages` 与循环之间的关系。",
            "理解 Tool 是模型可见的能力声明，而非模型自行生成的命令。",
            "明确 Agent 的执行权由代码掌握，不在模型一侧。",
        ],
        practice_steps=[
            "将 `max_iterations` 改为 2，观察复杂任务如何被提前中断。",
            "临时从 `tools` 中移除 `write_file`，再要求 Agent 写文件，观察其无法完成的原因。",
            "让 Agent 连续执行“写文件 + 读文件”两个动作，体会循环结构的必要性。",
            "为 `execute_bash` 补充更清晰的描述，观察模型是否更易选中正确工具。",
        ],
        talk_points=[
            "循环：Agent 并非只响应一次，而是在每一轮中决定是否继续行动。",
            "LLM 输出的是结构化调用意图，并不直接执行系统命令。",
            "Tool：`tools` 是模型看到的能力清单，`functions` 才是真正落地执行的代码。",
        ],
        pitfalls=[
            "仅实现 Python 函数而未注册到 `tools`，模型无法感知该能力的存在。",
            "`execute_bash` 权限过大，后续需要补充安全边界。",
            "工具报错同样需要回填给模型，否则模型无法自我修正。",
            "只堆叠工具而不设计循环，最终会退化为普通问答。",
        ],
        workshop_prompt="将其视作一台能自主选择工具的任务执行器，而非聊天窗口。",
        md_path=ROOT / "01-essence/agent-essence.md",
        code_path=ROOT / "01-essence/agent-essence.py",
        snippets=[
            Snippet(
                title="最小 Agent 循环",
                start=73,
                end=97,
                focus="围绕这二十余行展开：请求模型、获取 tool call、执行工具、回填结果、进入下一轮。",
            ),
            Snippet(
                title="Tool 声明",
                start=11,
                end=51,
                focus="这段代码决定了模型能看到哪些能力，以及每个工具需要什么参数。",
            ),
            Snippet(
                title="工具映射到真实函数",
                start=54,
                end=70,
                focus="Tool 并非抽象概念，最终会映射到真实函数；模型选中的名字就在这里被执行。",
            ),
        ],
    ),
    Lesson(
        slug="skills-mcp",
        number="03",
        title="Skills、Rules 与 MCP",
        short_title="能力外置",
        stage="第三步：能力外置",
        lesson_minutes="10 分钟",
        summary="本讲聚焦三层能力扩展：一个最小 Rule、一个最小 Skill、一个最小 MCP 工具。重点不在配置多复杂，而在它们分别注入到上下文还是工具列表。",
        core="Skill + Rule + MCP",
        tags=["Skills", "Rules", "MCP"],
        scenario="发布前有三个小问题：删除数据没确认、应用启动报错、按钮颜色不统一。我们不改 Python 代码，只改 Rule、Skill、MCP 配置，就能让 Agent 按固定格式回答、按发布风险排序，并调用外部发布策略。",
        demo_command=(
            'python3 agent/03-skills-mcp/agent-skills-mcp.py "请先调用 demo_release_policy 获取发布策略。'
            '然后按 release_triage 对这三个发布前问题排序：A 应用启动报错；B 删除数据没有二次确认；C 按钮颜色不统一。'
            '最后严格按 Rule 要求输出三行。"'
        ),
        demo_goal="用一条短命令同时证明：Rule 改变输出格式，Skill 改变排序逻辑，MCP 提供可调用的外部策略。",
        demo_expected=[
            "第一屏先看三类日志：`[Rules] Loaded ...`、`[Skills] Loaded 1 skill files: release_triage`、`[MCP] Loaded ...`。",
            "观察 `[Tool] demo_release_policy(...)`，用真实工具调用证明 MCP 已进入 tools。",
            "最终回答应出现 `Rule证据 / Skill证据 / MCP证据` 三行，用输出格式证明 Rule 生效。",
            "排序应为 `B > A > C`：删除数据没确认高于启动报错，按钮颜色排最后，用结果证明 Skill 生效。",
            "MCP 证据行应提到“只做演示、不修改文件”或发布策略，用工具返回内容证明 MCP 生效。",
        ],
        student_takeaways=[
            "知道 Skill 负责补充知识，Rule 负责约束行为，MCP 负责接入外部工具。",
            "能识别 Rules、Skills、MCP 各自的加载来源，以及它们如何拼装进上下文与工具列表。",
            "理解工程化 Agent 的关键不在于继续堆内置逻辑，而在于能力与约束的外置。",
        ],
        practice_steps=[
            "打开 `.agent/rules/demo-style.md`，改一条输出要求，再运行一次任务。",
            "打开 `.agent/skills/release-triage/SKILL.md`，把“无法启动”放到第一位，再运行同一个命令观察排序变化。",
            "打开 `.agent/mcp.json`，将 `demo_release_policy` 改名或禁用，观察 `[MCP]` 日志和工具列表变化。",
        ],
        talk_points=[
            "最小 Rule 用来约束输出格式，最小 Skill 用来补充排序方法，最小 MCP 用来扩展可调用工具。",
            "Rules 与 Skills 最终进入 prompt，MCP 最终进入 tools，注入位置不同，作用也不同。",
            "`DEFAULT_MAX_ITERATIONS = 10` 是演示友好值，能避免复杂搜索在结论前过早中断。",
        ],
        pitfalls=[
            "将所有约束都堆入 Rule，会模糊职责边界，模型也更难稳定执行。",
            "Skills 过多会稀释上下文，MCP 工具过多会降低模型的工具选择准确率。",
            "迭代次数调高会改善演示完整度，但也会增加 token 成本与执行时间。",
            "规则、技能、工具描述互相冲突时，模型表现会显著不稳定。",
        ],
        workshop_prompt="使用一个最小 Rule 与一个最小 Skill 进行演示，再观察 MCP 工具如何接入。",
        md_path=ROOT / "03-skills-mcp/agent-skills-mcp.md",
        code_path=ROOT / "03-skills-mcp/agent-skills-mcp.py",
        snippets=[
            Snippet(
                title="演示迭代上限",
                start=14,
                end=17,
                focus="第三讲把默认循环上限提高到 10，避免现场演示在完成结论前过早中断。",
            ),
            Snippet(
                title="Rules / Skills / MCP 的加载",
                start=208,
                end=302,
                focus="这段代码展示 `load_rules`、Markdown Skill 加载和 MCP 工具加载：Rule 与 Skill 进入 prompt，MCP 进入 tools。",
            ),
            Snippet(
                title="进入上下文与工具列表的方式",
                start=341,
                end=362,
                focus="关键在注入位置：Rules 与 Skills 进入 prompt，MCP 工具进入 `all_tools`。",
            ),
        ],
    ),
    Lesson(
        slug="memory",
        number="02",
        title="Memory：让 Agent 记住上一次",
        short_title="记忆回放",
        stage="第二步：持久记忆",
        lesson_minutes="8 分钟",
        summary="本讲只聚焦 Memory：在第一讲工具循环不变的前提下，增加读取记忆、注入上下文、写回记忆三步。",
        core="写入记忆 + 回放记忆",
        tags=["Memory", "Persistence", "Context Replay"],
        scenario="第一讲的 Agent 每次启动都是一张白纸。现在希望它完成一次任务后留下记录，下一次运行时不用重新读文件，也能知道上一次做过什么。",
        demo_command='python3 agent/02-memory/agent-memory.py "创建 launch-note.txt，内容是 Agent Memory Demo"\npython3 agent/02-memory/agent-memory.py "不重新读文件，只根据记忆说明你上一次完成了什么任务"',
        demo_goal="演示 Agent 将执行结果写入记忆文件，并在下次运行时直接回放这段历史。",
        demo_expected=[
            "第一次运行结束后，打开 `agent_memory.md`，确认任务与结果已追加写入。",
            "第二次运行即便不再读取文件，也能基于上一次的历史说明已完成的内容。",
            "关键是 `load_memory()`、`build_messages()`、`save_memory()` 形成 Memory 闭环。",
        ],
        student_takeaways=[
            "能描述 Memory 的三个最小步骤：写入、读取、回放。",
            "能看懂 `load_memory()`、`save_memory()` 与 `build_messages()` 之间的串接关系。",
            "能说明第二讲相对第一讲只增加 Memory，不改变工具循环。",
        ],
        practice_steps=[
            "连续运行两次任务，再打开 `agent_memory.md`，观察日志如何逐条追加。",
            "调小 `load_memory()` 的窗口，观察旧历史的衰减过程。",
            "临时注释掉 `save_memory()` 或 `load_memory()` 之一，对比 Memory 闭环为何会失效。",
        ],
        talk_points=[
            "最小 Memory 不需要向量库，仅需打通“写入文件”与“下次读回”这条链路。",
            "让 Agent 记住过去的并非文件本身，而是历史被重新注入到 system prompt。",
            "第二讲的递进关系很清楚：第一讲负责能动手，第二讲负责能记住上一次。",
        ],
        pitfalls=[
            "只写入不读取的并非 Memory，仅是日志。",
            "历史回放过多，会再次触发上下文膨胀。",
            "错误结果一旦写入记忆，下一轮会将这些污染一并带回。",
        ],
        workshop_prompt="连续运行两次任务，再打开 `agent_memory.md` 观察历史如何被写入并带回下一轮。",
        md_path=ROOT / "02-memory/agent-memory.md",
        code_path=ROOT / "02-memory/agent-memory.py",
        snippets=[
            Snippet(
                title="Memory 写入与读取",
                start=77,
                end=90,
                focus="这段代码构成最小 Memory 闭环的前半段：从文件读取历史，再将新结果追加写入。",
            ),
            Snippet(
                title="将旧记忆重新带回上下文",
                start=93,
                end=117,
                focus="关键不在于保存了多少历史，而在新任务启动时是否将旧记忆重新写回 system prompt。",
            ),
        ],
    ),
    Lesson(
        slug="subagent",
        number="04",
        title="SubAgent 子智能体",
        short_title="任务委派",
        stage="任务拆分",
        lesson_minutes="8 分钟",
        summary="当单个 Agent 需要同时承担架构、后端、前端工作时，应将部分任务委派给更聚焦的子代理。",
        core="独立上下文 + 角色委派",
        tags=["SubAgent", "Delegation", "Role Prompt"],
        scenario="一个项目同时要做后端、前端、还要写文档，主 Agent 一边在改 Python 一边在改 HTML，上下文越拉越长，最后什么都做不好。把后端的活交给一个专门写后端的子代理，主 Agent 才能集中做协调。",
        demo_command=(
            'python agent/04-subagent/agent-subagent.py "不要直接完成任务。请调用 subagent 工具两次，两个子代理都不要读写文件：'
            '1）role=Python API 设计师，task=为 TODO 应用设计 3 个后端接口，只返回接口清单；'
            '2）role=前端交互设计师，task=为 TODO 应用设计 3 个界面交互，只返回交互清单。'
            '最后主 Agent 用纯文本 4 行汇总，不要表格：后端交付、前端交付、为什么适合委派、主 Agent 没做什么。"'
        ),
        demo_goal="委派并不神秘，本质就是把另一个 Agent 也封装成工具。",
        demo_expected=[
            "终端会连续出现两次 `[Tool] subagent(...)`，说明主 Agent 真的把任务委派出去了。",
            "两段日志会分别显示 `[SubAgent:Python API 设计师]` 与 `[SubAgent:前端交互设计师]`，角色边界一眼可见。",
            "最终回答只做 4 行汇总，不展开子代理内部历史，突出“主 Agent 负责协调，SubAgent 负责专门任务”。",
        ],
        student_takeaways=[
            "理解 SubAgent 的关键在于独立上下文，而非额外启动一个模型实例。",
            "能解释为何应禁止子代理继续派生子代理。",
            "能将一个复杂任务拆解为主代理与子代理两类角色。",
        ],
        practice_steps=[
            "将一个写 README 的任务改由文档子代理完成。",
            "为子代理补充更具体的角色描述，观察输出稳定性的变化。",
            "让主代理仅保留协调职责，避免同时承担所有实现细节。",
        ],
        talk_points=[
            "委派的收益来自上下文收敛，并非单纯的并行化。",
            "角色 prompt 越具体，子代理越容易形成稳定的任务视角。",
            "返回摘要而非全量历史，是后续控制上下文成本的关键习惯。",
        ],
        pitfalls=[
            "任务边界不清时，主代理与子代理会出现重复劳动。",
            "允许无限递归委派，成本与复杂度都会失控。",
            "子代理角色过于宽泛时，它只是换了名字的主代理。",
        ],
        workshop_prompt="使用 API 设计与前端交互两个轻量角色演示，避免文件生成噪音，让委派过程更清楚。",
        md_path=ROOT / "04-subagent/agent-subagent.md",
        code_path=ROOT / "04-subagent/agent-subagent.py",
        snippets=[
            Snippet(
                title="将 subagent 封装为工具",
                start=104,
                end=142,
                focus="独立 `sub_messages` 与禁止递归，是这段实现最值得关注的两点。",
            )
        ],
    ),
    Lesson(
        slug="teams",
        number="05",
        title="多智能体团队协作",
        short_title="团队编排",
        stage="持久化协作",
        lesson_minutes="9 分钟",
        summary="SubAgent 仍属一次性角色；本讲将其升级为具备身份、通信与复盘能力的持久团队。",
        core="持久 Agent + 通信通道",
        tags=["Team", "Inbox", "Lifecycle"],
        scenario="希望团队里有一位“开发”和一位“审查”长期存在：每个新任务都跑同样的流程，开发完成后自动转给审查，审查的意见再反馈回开发。SubAgent 那种一次性角色已经不够用了。",
        demo_command=(
            'python3 -u agent/05-teams/agent-teams.py "固定 3 人发布评审团队演示：登录接口发布前评审。'
            '要求所有成员不要读写文件，只输出短清单；重点观察 [创建]、[记忆]、[收件箱]、[广播]、最终审查、[解散]。"'
        ),
        demo_goal="将团队协作呈现为一种可落地的软件结构，而非抽象概念。",
        demo_expected=[
            "启动后直接看到固定三人团队：`alice` 负责交付摘要，`bob` 负责安全审查，`chris` 负责发布验收。",
            "每个成员完成后都会出现 `[广播]`，说明团队不是各说各话，而是通过 `inbox` 传递成果。",
            "重点观察 `[记忆] chris 第 2 次 chat`：它会带着第一次写下的 G1/G2/G3 验收标准继续做最终审查。",
        ],
        student_takeaways=[
            "理解 Team 相对 SubAgent 增加的是持久身份与通信。",
            "能用 `inbox` 这一极简模型解释 Agent 间的消息传递。",
            "理解为何 reviewer 是体现团队价值最直观的角色。",
        ],
        practice_steps=[
            "将 `plan_team()` 固定为两开发加一审查的三人团队。",
            "在执行过程中手动插入一次 `send()`，对照点对点消息与广播的差异。",
            "让 reviewer 再次执行 `chat()`，体会持久记忆如何支撑二次审查。",
        ],
        talk_points=[
            "多智能体的关键不在人数，而在角色与生命周期。",
            "Agent 的 `inbox` 模型十分简洁，却已能支撑大量协作场景。",
            "团队规模并非越大越好，信息流的清晰度更具价值。",
        ],
        pitfalls=[
            "角色过于宽泛时，团队只是多个普通助手轮流发言。",
            "消息过多时会再次触发上下文压力。",
            "缺少 reviewer 时，难以体现协作带来的质量提升。",
        ],
        workshop_prompt="用发布前评审流水线演示：开发交付、安全审查、发布 reviewer 复盘，团队价值会更明显。",
        md_path=ROOT / "05-teams/agent-teams.md",
        code_path=ROOT / "05-teams/agent-teams.py",
        snippets=[
            Snippet(
                title="持久化的 Agent 对象",
                start=150,
                end=210,
                focus="这段代码解释了团队成员为何能记得队友此前说过的内容。",
            ),
            Snippet(
                title="Team 管理生命周期与通信",
                start=219,
                end=247,
                focus="招募、广播、解散——这里是多智能体协作的最小骨架。",
            ),
        ],
    ),
    Lesson(
        slug="compact",
        number="06",
        title="上下文压缩",
        short_title="长任务生存",
        stage="上下文管理",
        lesson_minutes="7 分钟",
        summary="本讲跳过理论铺垫，专注于一个核心问题：长任务中 Agent 为何会被自身历史拖垮，以及压缩如何缓解。",
        core="摘要旧消息，保留最近窗口",
        tags=["Context Window", "Compaction", "Summarization"],
        scenario="交给 Agent 一个跨几十轮的长任务，会发现它越走越慢、回答越来越含糊——背后是 messages 一直在膨胀，前面所有工具调用结果都被一次次带着走，最终撑爆 context window。",
        demo_command='python agent/06-compact/agent-compact.py "请按步骤执行，不要合并成一个 shell 命令：1. 用 execute_bash 列出 agent 目录下的 Python 文件；2. 分别用 read_file 读取 agent/01-essence/agent-essence.py、agent/02-memory/agent-memory.py、agent/06-compact/agent-compact.py；3. 把三个文件的大致行数写入 compact-demo-report.txt。"',
        demo_goal="压缩并非加分项，而是 Agent 完成长任务的关键能力。",
        demo_expected=[
            "默认演示阈值已调低到 `COMPACT_THRESHOLD = 8`，分步工具调用后可清晰看到 `[Compact]` 日志。",
            "压缩会保留 system prompt 与最近几条消息；如果遇到 tool 调用组，会向前扩展边界，避免切断工具响应。",
            "压缩本身也消耗 token，因此是一种工程折中，并非零成本能力。",
        ],
        student_takeaways=[
            "理解为何更大的 context window 并非根本解决方案。",
            "能解释 `COMPACT_THRESHOLD` 与 `KEEP_RECENT` 的取舍。",
            "理解“保留要点、舍弃细节”是 Agent 的必要能力。",
        ],
        practice_steps=[
            "先直接运行演示命令，观察默认低阈值如何触发压缩。",
            "将 `KEEP_RECENT` 从 4 改为 2，对比当前任务衔接的变化。",
            "观察压缩前后 messages 的结构变化，而不只查看日志。",
        ],
        talk_points=[
            "压缩并非为了形式优雅，而是为了避免在真实任务中因上下文溢出而中断。",
            "需要优先保留的是 system prompt 与当前工作现场。",
            "将旧消息摘要化，本质是借助模型整理自身的历史。",
        ],
        pitfalls=[
            "摘要过度会丢失关键路径与文件名。",
            "recent window 过短会让 Agent 立即丢失工作上下文。",
            "只截断而不压缩，仍无法支撑复杂长任务。",
        ],
        workshop_prompt="默认低阈值配合分步工具调用，是最直观的压缩演示方式。",
        md_path=ROOT / "06-compact/agent-compact.md",
        code_path=ROOT / "06-compact/agent-compact.py",
        snippets=[
            Snippet(
                title="上下文压缩函数",
                start=125,
                end=188,
                focus="这是上下文压缩的核心实现：将旧历史折叠为摘要，保留当前工作现场。",
            )
        ],
    ),
    Lesson(
        slug="safety",
        number="07",
        title="三道安全防线",
        short_title="安全边界",
        stage="工程边界",
        lesson_minutes="5 分钟",
        summary="最后一讲聚焦 Agent 工程使用时常见的三道边界：危险命令拦截、人工确认、超长输出截断。",
        core="黑名单 + 人工确认 + 输出截断",
        tags=["Safety", "Approval", "Guardrails"],
        scenario="让 Agent 清理临时文件时，如果它一句 `rm -rf` 把项目目录也带走，或者读到一个超长文件直接把上下文撑爆，问题就会很具体。能力越强，越需要在它和系统之间留出一道护栏。",
        demo_command='python agent/07-safety/agent-safe.py "列出当前目录的文件"',
        demo_goal="建立明确的工程直觉：能力越强，越需要在人机边界处加上护栏。",
        demo_expected=[
            "普通命令会先经过确认再执行。",
            "危险命令在黑名单阶段会被直接拦截。",
            "超长输出会被截断，与上一讲的上下文控制问题相互呼应。",
        ],
        student_takeaways=[
            "能说清三道防线各自解决的问题。",
            "理解为何不宜将“是否安全”的判断完全交给模型。",
            "理解安全与上下文控制是同一件工程责任的两面。",
        ],
        practice_steps=[
            "为 `DANGEROUS_PATTERNS` 增补一条高危命令规则。",
            "把 `read_file` 调整为仅可读取项目目录，构建最小允许列表。",
            "尝试读取超长文件，观察截断提示如何返回给模型。",
        ],
        talk_points=[
            "黑名单拦截已知高危动作，人工确认守住最后边界。",
            "输出截断既是安全问题，也是稳定性问题。",
            "更可控的 Agent 应允许用户随时拒绝某一步。",
        ],
        pitfalls=[
            "仅依赖黑名单并不充分，绕过方式始终存在。",
            "所有动作都需确认会显著降低体验，应采用分级策略。",
            "`--auto` 仅适合在完全信任的隔离环境中使用。",
        ],
        workshop_prompt="将安全视为让 Agent 能被放心使用的基本前提。",
        md_path=ROOT / "07-safety/agent-safe.md",
        code_path=ROOT / "07-safety/agent-safe.py",
        snippets=[
            Snippet(
                title="危险命令黑名单与确认机制",
                start=49,
                end=107,
                focus="明确黑名单与确认框各自拦截的风险层级。",
            ),
            Snippet(
                title="安全版 execute_bash",
                start=162,
                end=186,
                focus="这段函数清晰展示了三道防线的串联方式。",
            ),
        ],
    ),
]

LESSONS = sorted(LESSONS, key=lambda lesson: lesson.number)


SESSION_OUTCOMES = [
    "理解 Agent 的最小工作闭环，而不止于现成产品的使用层面。",
    "掌握将单文件 Agent 升级为具备记忆、委派、扩展与安全控制的完整原型的路径。",
    "通过最小 Demo 与关键代码片段，建立对 Agent 工程结构的判断力。",
]


SESSION_SETUP = [
    "Python 环境，可运行 `agent/*.py` 文件。",
    "已配置 `OPENAI_API_KEY`，并准备一个可用模型。",
    "终端与代码编辑器即可，无需额外的演示软件。",
]


SESSION_FORMAT = [
    "30% 关键代码：聚焦决定行为的核心实现，不展开抽象概念。",
    "40% 现场演示：用终端输出验证行为，代码与结果一一对应。",
    "30% 动手延伸：留出可独立复现的小改动入口，方便继续深入。",
]


AGENDA = [
    ("00 - 05", "开场：内容范围与目标", "明确这一小时仅覆盖能直接用于 Demo 的核心内容。"),
    ("05 - 13", "第 01 讲：最小闭环", "运行最小 Agent，观察工具调用、执行与结果回填的完整流程。"),
    ("13 - 21", "第 02 讲：Memory", "演示 Agent 将执行结果写入记忆文件，并在下次运行时回放到上下文。"),
    ("21 - 31", "第 03 讲：Skills / Rules / MCP", "接入 Skill、Rule、MCP 三层能力，区分它们注入到上下文还是工具列表。"),
    ("31 - 39", "第 04 讲：SubAgent", "通过前后端双角色案例，说明复杂任务需要委派的原因。"),
    ("39 - 48", "第 05 讲：Teams", "将委派扩展为长期协作团队，演示 reviewer 复盘机制。"),
    ("48 - 55", "第 06 讲：上下文压缩", "用低阈值触发一次完整的压缩流程。"),
    ("55 - 60", "第 07 讲：安全防线 + 收尾", "通过危险命令拦截与人工确认，收束工程化边界。"),
]


SUMMARY_OUTCOMES = [
    "把 Agent 重新看成一套系统：模型负责生成，Harness 负责让它真正干活。",
    "能用“循环、能力外置、记忆、委派、协作、压缩、安全”七个关键词复述整套结构。",
    "知道接下来往哪继续：想补 Agent 工程细节，就看番外；想补底层原理，就回到大模型系列。",
]


SUMMARY_PATHS = [
    ("回看七讲", "重新串起最小闭环到安全边界的完整路径，适合分享结束后收束主线。"),
    ("补 Agent 番外", "继续回答七讲里没展开的问题：文件系统、Streaming、Eval、真实 MCP 等。"),
    ("补模型基础", "把 Agent 再接回大模型正篇十讲与番外六讲，形成完整技术地图。"),
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


def site_publisher() -> dict:
    return {
        "@type": "Organization",
        "name": SITE_AUTHOR,
        "url": REPO_WEB_BASE,
    }


def build_json_ld(payloads: List[dict]) -> str:
    scripts = []
    for payload in payloads:
        scripts.append(
            '<script type="application/ld+json">'
            + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            + "</script>"
        )
    return "\n  ".join(scripts)


def breadcrumb_schema(items: List[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index + 1,
                "name": name,
                "item": url,
            }
            for index, (name, url) in enumerate(items)
        ],
    }


def build_head(
    title: str,
    description: str,
    filename: str,
    page_type: str,
    *,
    robots: str = "index,follow",
    structured_data=None,
) -> str:
    canonical = page_url(filename)
    plain_description = strip_inline_marks(description)
    json_ld = build_json_ld(structured_data) if structured_data else ""
    return f"""
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(plain_description)}">
  <meta name="robots" content="{html.escape(robots)}">
  <meta name="theme-color" content="#1f2430">
  <link rel="canonical" href="{html.escape(canonical)}">
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
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
  {json_ld}
""".strip()


def home_structured_data() -> List[dict]:
    return [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": SITE_TITLE,
            "url": SITE_URL,
            "description": SITE_DESCRIPTION,
            "inLanguage": "zh-CN",
            "publisher": site_publisher(),
        },
        {
            "@context": "https://schema.org",
            "@type": "Course",
            "name": f"{SITE_TITLE}｜{SITE_SUBTITLE}",
            "description": SITE_DESCRIPTION,
            "provider": site_publisher(),
            "educationalLevel": "Intermediate",
            "inLanguage": "zh-CN",
            "url": page_url("index.html"),
        },
    ]


def lesson_structured_data(lesson: Lesson) -> List[dict]:
    return [
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": f"{lesson.number}. {lesson.title}",
            "description": strip_inline_marks(lesson.summary),
            "dateModified": BUILD_DATE,
            "inLanguage": "zh-CN",
            "author": site_publisher(),
            "publisher": site_publisher(),
            "url": page_url(f"{lesson.slug}.html"),
            "keywords": lesson.tags,
            "isPartOf": {
                "@type": "CreativeWorkSeries",
                "name": SITE_TITLE,
                "url": page_url("index.html"),
            },
        },
        breadcrumb_schema(
            [
                ("首页", page_url("index.html")),
                ("七讲讲义", page_url("index.html") + "#lessons"),
                (f"第 {lesson.number} 讲", page_url(f"{lesson.slug}.html")),
            ]
        ),
    ]


def summary_structured_data() -> List[dict]:
    return [
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "总结篇：从七讲到延伸阅读",
            "description": "用一页回顾七讲主线，并给出 Agent 番外篇与大模型系列目录。",
            "dateModified": BUILD_DATE,
            "inLanguage": "zh-CN",
            "author": site_publisher(),
            "publisher": site_publisher(),
            "url": page_url("summary.html"),
        },
        breadcrumb_schema(
            [
                ("首页", page_url("index.html")),
                ("七讲讲义", page_url("index.html") + "#lessons"),
                ("总结篇", page_url("summary.html")),
            ]
        ),
    ]


def render_tags(tags: List[str], class_name: str) -> str:
    return "".join(f'<span class="{class_name}">{html.escape(tag)}</span>' for tag in tags)


def render_bullets(items: List[str], class_name: str = "lesson-list") -> str:
    body = "".join(f"<li>{format_inline(item)}</li>" for item in items)
    return f'<ul class="{class_name}">{body}</ul>'


def render_steps(items: List[str]) -> str:
    body = "".join(f"<li>{format_inline(item)}</li>" for item in items)
    return f'<ol class="lesson-steps">{body}</ol>'


def markdown_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def strip_markdown_text(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("**", "").replace("*", "").replace("`", "")
    text = text.replace("_", "").replace("“", '"').replace("”", '"')
    text = re.sub(r"^>\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -")


def shorten_title(title: str) -> str:
    if "：" in title:
        return title.split("：", 1)[1].strip()
    return title


def truncate_text(text: str, limit: int = 92) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def markdown_summary(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    seen_heading = False
    blockquote_lines: List[str] = []
    paragraph_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not seen_heading:
            if stripped.startswith("# "):
                seen_heading = True
            continue

        if not stripped:
            if blockquote_lines or paragraph_lines:
                break
            continue

        if stripped.startswith(">"):
            blockquote_lines.append(strip_markdown_text(stripped))
            continue

        if stripped.startswith(("#", "-", "*", "|")):
            continue

        paragraph_lines.append(strip_markdown_text(stripped))
        if len(" ".join(paragraph_lines)) >= 120:
            break

    text = " ".join(blockquote_lines or paragraph_lines)
    return truncate_text(text or shorten_title(markdown_title(path)))


def resource_number(path: Path) -> str:
    prefix = path.parent.name.split("-", 1)[0]
    return prefix if prefix.isdigit() else "Full"


def build_resource(path: Path, label: str) -> Resource:
    title = markdown_title(path)
    return Resource(
        number=resource_number(path),
        label=label,
        title=title,
        short_title=shorten_title(title),
        summary=markdown_summary(path),
        path=path,
    )


AGENT_BONUS_PATHS = [
    ROOT / "full/nanoAgent-bonus-harness.md",
    ROOT / "08-filesystem/nanoAgent-bonus-filesystem.md",
    ROOT / "09-token/nanoAgent-bonus-token.md",
    ROOT / "10-tool-selection/nanoAgent-bonus-tool-selection.md",
    ROOT / "11-streaming/nanoAgent-bonus-streaming.md",
    ROOT / "12-command/nanoAgent-bonus-command.md",
    ROOT / "13-observable/nanoAgent-bonus-observable.md",
    ROOT / "14-eval/nanoAgent-bonus-eval.md",
    ROOT / "15-agent-creation-modes/nanoagent-bonus-agent-creation-modes.md",
    ROOT / "16-mcp-real/nanoagent-bonus-mcp-real.md",
]

LLM_SERIES_PATHS = sorted(
    (REPO_ROOT / "llm").glob("*/*.md"),
    key=lambda path: int(path.parent.name.split("-", 1)[0]),
)

AGENT_BONUS_RESOURCES = [build_resource(path, "Agent 番外") for path in AGENT_BONUS_PATHS]
LLM_MAIN_RESOURCES = [build_resource(path, "大模型正篇") for path in LLM_SERIES_PATHS if int(path.parent.name.split("-", 1)[0]) <= 10]
LLM_BONUS_RESOURCES = [build_resource(path, "大模型番外") for path in LLM_SERIES_PATHS if int(path.parent.name.split("-", 1)[0]) > 10]
FULL_AGENT_GUIDE = ROOT / "full/agent-full.md"
FULL_AGENT_CODE = ROOT / "full/agent-full.py"


def code_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def excerpt_code(path: Path, start: int, end: int) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    selected = []
    for number in range(start, min(end, len(lines)) + 1):
        selected.append(f"{number:4d} {lines[number - 1]}")
    return "\n".join(selected)


def render_resource_cards(resources: List[Resource], button_text: str) -> str:
    cards = []
    for resource in resources:
        cards.append(
            f"""
            <article class="lesson-card">
              <p class="lesson-index">{html.escape(resource.label)} · {html.escape(resource.number)}</p>
              <h3>{html.escape(resource.short_title)}</h3>
              <p>{html.escape(resource.summary)}</p>
              <a class="lesson-link" href="{github_blob_url(resource.path)}">{html.escape(button_text)}</a>
            </article>
            """
        )
    return "".join(cards)


def course_nav(current_slug: str) -> str:
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
    summary_class = " is-current" if current_slug == "summary" else ""
    items.append(
        f'''
        <a class="chapter-rail-link{summary_class}" href="summary.html">
          <span class="course-step">总结篇</span>
          <strong>从七讲到延伸阅读</strong>
          <small>主线收束 · Agent 番外 · 大模型目录</small>
        </a>
        '''
    )
    return "".join(items)


def build_footer() -> str:
    return f"""
    <footer class="site-footer">
      <p>本讲义仅保留最关键的代码、演示与延伸线索；总结篇、番外与完整原文请见下方入口。</p>
      <div class="footer-links">
        <a href="summary.html">总结篇</a>
        <a href="{REPO_WEB_BASE}">GitHub 仓库</a>
        <a href="{github_blob_url(ROOT / 'README_CN.md')}">系列导读</a>
        <a href="{github_blob_url(REPO_ROOT / 'llm/README.md')}">大模型导读</a>
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


def build_demo_config_showcase(lesson: Lesson) -> str:
    if lesson.slug != "skills-mcp":
        return ""

    configs = [
        (
            "Rule 配置",
            ".agent/rules/demo-style.md",
            "约束最终回答固定输出三行。",
            REPO_ROOT / ".agent/rules/demo-style.md",
        ),
        (
            "Skill 配置",
            ".agent/skills/release-triage/SKILL.md",
            "用 Markdown 描述发布前问题的排序方法。",
            REPO_ROOT / ".agent/skills/release-triage/SKILL.md",
        ),
        (
            "MCP 配置",
            ".agent/mcp.json",
            "把 demo_release_policy 追加到工具列表。",
            REPO_ROOT / ".agent/mcp.json",
        ),
    ]

    panels = []
    for title, label, note, path in configs:
        panels.append(
            f"""
            <article class="config-panel">
              <div class="config-panel-head">
                <div>
                  <p class="lesson-index">{html.escape(title)}</p>
                  <h3>{html.escape(label)}</h3>
                  <p>{html.escape(note)}</p>
                </div>
                <a class="source-link" href="{github_blob_url(path)}">看源文件</a>
              </div>
              <pre class="code-block"><code>{html.escape(path.read_text(encoding="utf-8").strip())}</code></pre>
            </article>
            """
        )

    return f"""
          <div class="config-showcase">
            <p class="lesson-index">先看具体配置</p>
            <div class="config-grid">
              {"".join(panels)}
            </div>
          </div>"""


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
              <p class="lesson-kicker">要点：{format_inline(lesson.workshop_prompt)}</p>
              <div class="lesson-tag-row">{render_tags(lesson.tags, "tag")}</div>
              <a class="lesson-link" href="{lesson.slug}.html">查看讲义</a>
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

    summary_cards = []
    summary_links = [
        ("summary.html", "查看总结篇"),
        ("summary.html#extras", "查看 Agent 番外"),
        ("summary.html#llm", "查看大模型目录"),
    ]
    for (title, note), (href, label) in zip(SUMMARY_PATHS, summary_links):
        summary_cards.append(
            f"""
            <article class="format-card">
              <h3>{html.escape(title)}</h3>
              <p>{html.escape(note)}</p>
              <a class="secondary-btn" href="{href}">{html.escape(label)}</a>
            </article>
            """
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  {build_head(f"{SITE_TITLE}｜{SITE_SUBTITLE}", SITE_DESCRIPTION, "index.html", "website", structured_data=home_structured_data())}
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
        <a href="#agenda">时间分配</a>
        <a href="#format">讲义结构</a>
        <a href="#lessons">七讲讲义</a>
        <a href="summary.html">总结与延伸</a>
        <a href="{REPO_WEB_BASE}">GitHub</a>
      </nav>
    </header>

    <main id="main-content">
      <section class="hero-panel home-hero">
        <div class="hero-copy">
          <p class="eyebrow">Agent 技术分享 · {SITE_SUBTITLE}</p>
          <h1>把 Agent 拆成一套能运行的工程系统</h1>
          <p class="hero-lead">不是概念清单，而是一条从“让模型能动手”到“让系统可控运行”的实战路线。每一讲都用最小代码、真实命令和可复现结果，拆开 Coding Agent 的共同结构。</p>
          <p class="mode-note">核心路径：Tool Loop → Memory → Rules / Skills / MCP → SubAgent → Teams → Context Compact → Safety</p>
          <div class="hero-actions">
            <a class="primary-btn" href="essence.html">从第 01 讲开始</a>
            <a class="secondary-btn" href="#agenda">查看 60 分钟路线</a>
          </div>
          <div class="hero-metrics">
            <span><strong>7</strong> 个可运行脚本</span>
            <span><strong>60</strong> 分钟实战分享</span>
            <span><strong>1</strong> 条工程主线</span>
          </div>
        </div>
        <div class="hero-side hero-map">
          <div class="hero-map-head">
            <p class="eyebrow">Learning Route</p>
            <h2>从能动手到可控运行</h2>
          </div>
          <div class="route-stack">
            <article class="route-step">
              <span>01</span>
              <div><strong>Tool Loop</strong><p>让模型选择工具，代码执行动作。</p></div>
            </article>
            <article class="route-step">
              <span>02</span>
              <div><strong>Memory</strong><p>把上一次结果重新带回上下文。</p></div>
            </article>
            <article class="route-step">
              <span>03</span>
              <div><strong>Rules / Skills / MCP</strong><p>把规则、方法和工具从代码里拿出来。</p></div>
            </article>
            <article class="route-step">
              <span>04-05</span>
              <div><strong>SubAgent / Teams</strong><p>从一次性委派走到持久协作。</p></div>
            </article>
            <article class="route-step">
              <span>06-07</span>
              <div><strong>Compact / Safety</strong><p>控制上下文，也控制真实执行边界。</p></div>
            </article>
          </div>
        </div>
      </section>

      <section class="section-block" id="format">
        <div class="section-head">
          <p class="eyebrow">Format</p>
          <h2>不是听概念，而是看系统怎么长出来</h2>
          <p>首页往下不是普通目录，而是完整的分享路线：先明确目标和环境，再按时间推进，最后进入每一讲的代码与演示。</p>
        </div>
        <div class="format-grid">
          <article class="format-card">
            <h3>学习目标</h3>
            {render_bullets(SESSION_OUTCOMES)}
          </article>
          <article class="format-card">
            <h3>环境准备</h3>
            {render_bullets(SESSION_SETUP)}
          </article>
          <article class="format-card">
            <h3>结构比例</h3>
            {render_bullets(SESSION_FORMAT)}
          </article>
        </div>
      </section>

      <section class="section-block" id="agenda">
        <div class="section-head">
          <p class="eyebrow">Agenda</p>
          <h2>60 分钟时间分配</h2>
          <p>整体节奏：每一讲先看关键代码，再用终端验证行为，最后给出一个可独立复现的入口。</p>
        </div>
        <div class="agenda-list">
          {"".join(agenda_items)}
        </div>
      </section>

      <section class="section-block" id="lessons">
        <div class="section-head">
          <p class="eyebrow">Lesson Pack</p>
          <h2>七讲讲义</h2>
          <p>每页统一按“关键代码 → 现场演示 → 自己试一轮”的顺序编排。</p>
        </div>
        <div class="lesson-grid">
          {"".join(lesson_cards)}
        </div>
      </section>

      <section class="section-block" id="summary">
        <div class="section-head">
          <p class="eyebrow">Wrap Up</p>
          <h2>总结与延伸</h2>
          <p>七讲讲完之后，不在这里断掉：继续收束主线、跳到 Agent 番外，再回到底层大模型系列。</p>
        </div>
        <div class="format-grid">
          {"".join(summary_cards)}
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
        ("scenario", "什么时候会用到"),
        ("code", "先看关键代码"),
        ("demo", "再看它怎么跑"),
        ("practice", "自己试一轮"),
        ("goals", "这一讲会看懂什么"),
        ("talk", "三个核心要点"),
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
        else '<a class="pager-link" href="summary.html"><span>下一篇</span><strong>总结篇 · 从七讲到延伸阅读</strong></a>'
    )
    visual_html = build_essence_figure() if lesson.slug == "essence" else ""
    demo_config_html = build_demo_config_showcase(lesson)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  {build_head(f"{lesson.number}. {lesson.title}｜{SITE_SUBTITLE}", lesson.summary, f"{lesson.slug}.html", "article", structured_data=lesson_structured_data(lesson))}
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
        <a href="index.html#agenda">时间分配</a>
        <a href="index.html#lessons">七讲讲义</a>
        <a href="summary.html">总结与延伸</a>
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
          <h2>分享导航</h2>
          <div class="chapter-rail">{course_nav(lesson.slug)}</div>
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
            <a href="index.html">首页</a>
            <span>/</span>
            <a href="index.html#lessons">讲义列表</a>
            <span>/</span>
            <span>第 {lesson.number} 讲</span>
          </div>
          <p class="eyebrow">{SITE_SUBTITLE}</p>
          <h1>{lesson.number}. {html.escape(lesson.title)}</h1>
          <p class="lead">{format_inline(lesson.summary)}</p>
          <div class="tag-row">{render_tags(lesson.tags, "tag")}</div>
          <div class="hero-actions">
            <a class="primary-btn" href="#scenario">从场景开始</a>
            <a class="secondary-btn" href="#code">直接看代码</a>
          </div>
        </section>

        <section class="lesson-section" id="scenario">
          <div class="lesson-section-head">
            <p class="eyebrow">Scenario</p>
            <h2>什么时候会用到</h2>
          </div>
          <p class="scenario-text">{format_inline(lesson.scenario)}</p>
        </section>

        <section class="lesson-section" id="code">
          <div class="lesson-section-head">
            <p class="eyebrow">Code First</p>
            <h2>先看关键代码</h2>
            <p>聚焦决定行为的核心实现，再结合终端结果对照，能更直观地理解 Agent 的工作方式。</p>
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
          </div>{demo_config_html}
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
            <p class="eyebrow">Key Points</p>
            <h2>三个核心要点</h2>
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
            <p>本页未展开完整原文，可通过下方入口查看完整文章与源码。</p>
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


def build_summary_page() -> str:
    recap_cards = []
    for lesson in LESSONS:
        recap_cards.append(
            f"""
            <article class="lesson-card">
              <p class="lesson-index">第 {lesson.number} 讲 · {html.escape(lesson.short_title)}</p>
              <h3>{html.escape(lesson.title)}</h3>
              <p>{format_inline(lesson.workshop_prompt)}</p>
              <div class="lesson-meta">
                <span>{html.escape(lesson.lesson_minutes)}</span>
                <span>{html.escape(lesson.core)}</span>
              </div>
              <a class="lesson-link" href="{lesson.slug}.html">回看这一讲</a>
            </article>
            """
        )

    path_cards = []
    path_links = [
        ("summary.html#full", "完整版 Agent"),
        ("summary.html#extras", "Agent 番外"),
        ("summary.html#llm", "大模型目录"),
    ]
    for (title, note), (href, label) in zip(SUMMARY_PATHS, path_links):
        path_cards.append(
            f"""
            <article class="format-card">
              <h3>{html.escape(title)}</h3>
              <p>{html.escape(note)}</p>
              <a class="secondary-btn" href="{href}">{html.escape(label)}</a>
            </article>
            """
        )

    toc_links = [
        ("closure", "一小时之后留下什么"),
        ("map", "七讲怎么串起来"),
        ("full", "完整版 Agent"),
        ("extras", "Agent 番外篇"),
        ("llm", "大模型序列目录"),
        ("next", "下一步怎么继续"),
    ]

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  {build_head(f"总结篇｜{SITE_SUBTITLE}", "用一页回顾七讲主线，并给出 Agent 番外篇与大模型系列目录。", "summary.html", "article", structured_data=summary_structured_data())}
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
        <a href="index.html#agenda">时间分配</a>
        <a href="index.html#lessons">七讲讲义</a>
        <a href="#extras">Agent 番外</a>
        <a href="#llm">大模型目录</a>
        <a href="{REPO_WEB_BASE}">GitHub</a>
      </nav>
    </header>

    <main class="article-layout" id="main-content">
      <aside class="article-sidebar">
        <div class="sidebar-card">
          <p class="eyebrow">总结篇</p>
          <h2 class="lesson-title">从最小闭环到完整 Harness</h2>
          <p>这一页不再展开新概念，而是把七讲串成一张地图，并给出分享结束后的延伸阅读入口。</p>
          <div class="chip-row">
            <span class="chip">主线收束</span>
            <span class="chip">Agent 番外</span>
            <span class="chip">大模型目录</span>
          </div>
        </div>

        <div class="sidebar-card">
          <h2>分享导航</h2>
          <div class="chapter-rail">{course_nav("summary")}</div>
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
            <a href="index.html">首页</a>
            <span>/</span>
            <a href="index.html#lessons">讲义列表</a>
            <span>/</span>
            <span>总结篇</span>
          </div>
          <p class="eyebrow">{SITE_SUBTITLE}</p>
          <h1>总结篇：从七讲到延伸阅读</h1>
          <p class="lead">七讲主线到这里收束：先把最小闭环搭起来，再逐步补上能力外置、记忆、委派、协作、压缩与安全。接下来要么继续补 Agent 工程细节，要么回到底层大模型原理。</p>
          <div class="tag-row">
            <span class="tag">总结篇</span>
            <span class="tag">Agent 番外</span>
            <span class="tag">大模型目录</span>
          </div>
          <div class="hero-actions">
            <a class="primary-btn" href="#map">先看七讲地图</a>
            <a class="secondary-btn" href="#extras">再看延伸目录</a>
          </div>
        </section>

        <section class="lesson-section" id="closure">
          <div class="lesson-section-head">
            <p class="eyebrow">Closure</p>
            <h2>一小时之后留下什么</h2>
            <p>如果只记住三件事，可以先抓住下面这些。</p>
          </div>
          {render_bullets(SUMMARY_OUTCOMES)}
        </section>

        <section class="lesson-section" id="map">
          <div class="lesson-section-head">
            <p class="eyebrow">Map</p>
            <h2>七讲怎么串起来</h2>
            <p>顺序不是随便排的，而是从“让模型能动手”一路走到“让它安全可控地做事”。</p>
          </div>
          <div class="lesson-grid">
            {"".join(recap_cards)}
          </div>
        </section>

        <section class="lesson-section" id="full">
          <div class="lesson-section-head">
            <p class="eyebrow">Full Build</p>
            <h2>完整版 Agent</h2>
            <p>想把七讲里的组件重新拼回一个可直接运行的原型，可以从这里进入。</p>
          </div>
          <div class="lesson-grid">
            <article class="lesson-card">
              <p class="lesson-index">Full · {code_lines(FULL_AGENT_CODE)} 行代码</p>
              <h3>七篇合一：完整 Agent</h3>
              <p>把工具循环、记忆、Rules、Skills、MCP、SubAgent、Teams、上下文压缩和安全防线重新放回一个文件，适合对照七讲之后整体回看。</p>
              <div class="deep-links">
                <a class="lesson-link" href="{github_blob_url(FULL_AGENT_GUIDE)}">看完整说明</a>
                <a class="secondary-btn" href="{github_blob_url(FULL_AGENT_CODE)}">看完整代码</a>
              </div>
            </article>
          </div>
        </section>

        <section class="lesson-section" id="extras">
          <div class="lesson-section-head">
            <p class="eyebrow">Agent Bonus</p>
            <h2>Agent 番外篇</h2>
            <p>这些番外回答七讲里没有展开的问题：为什么需要文件系统、Token 花在哪、Streaming 怎么做、怎么评估是否完成任务、真实 MCP 长什么样。</p>
          </div>
          <div class="lesson-grid">
            {render_resource_cards(AGENT_BONUS_RESOURCES, "读番外原文")}
          </div>
        </section>

        <section class="lesson-section" id="llm">
          <div class="lesson-section-head">
            <p class="eyebrow">LLM Series</p>
            <h2>大模型序列文章目录</h2>
            <p>想把 Agent 再接回底层原理，可以顺着这套目录往回看：先正篇十讲，再番外六讲。</p>
          </div>
          <p class="lesson-index">正篇十讲</p>
          <div class="lesson-grid">
            {render_resource_cards(LLM_MAIN_RESOURCES, "读原文")}
          </div>
          <p class="lesson-index summary-subtitle">番外六讲</p>
          <div class="lesson-grid">
            {render_resource_cards(LLM_BONUS_RESOURCES, "读原文")}
          </div>
        </section>

        <section class="lesson-section" id="next">
          <div class="lesson-section-head">
            <p class="eyebrow">Next Step</p>
            <h2>下一步怎么继续</h2>
            <p>分享结束后，通常从这三条路径继续最顺。</p>
          </div>
          <div class="format-grid">
            {"".join(path_cards)}
          </div>
        </section>

        <nav class="pager">
          <a class="pager-link" href="{LESSONS[-1].slug}.html"><span>上一篇</span><strong>{LESSONS[-1].number}. {html.escape(LESSONS[-1].short_title)}</strong></a>
        </nav>
      </article>
    </main>
    {build_footer()}
  </div>
</body>
</html>
"""


def build_not_found_page() -> str:
    description = "页面不存在。可返回首页、七讲讲义或总结篇继续阅读。"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  {build_head("404｜从零开始理解 Agent", description, "404.html", "website", robots="noindex,follow")}
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
        <a href="index.html">首页</a>
        <a href="summary.html">总结与延伸</a>
        <a href="{REPO_WEB_BASE}">GitHub</a>
      </nav>
    </header>

    <main id="main-content">
      <section class="hero-panel">
        <div class="hero-copy">
          <p class="eyebrow">404</p>
          <h1>这个页面没有找到</h1>
          <p class="hero-lead">链接可能已经变更，或者你访问了一个不存在的地址。可以从首页重新进入，也可以直接跳到总结篇继续阅读。</p>
          <div class="hero-actions">
            <a class="primary-btn" href="index.html">返回首页</a>
            <a class="secondary-btn" href="summary.html">进入总结篇</a>
          </div>
        </div>
        <div class="hero-side">
          <div class="fact-grid">
            <article class="fact-card">
              <strong>7 讲主线</strong>
              <span>从最小闭环到安全边界</span>
            </article>
            <article class="fact-card">
              <strong>总结篇</strong>
              <span>七讲地图与延伸目录</span>
            </article>
            <article class="fact-card">
              <strong>Agent 番外</strong>
              <span>继续补工程细节</span>
            </article>
            <article class="fact-card">
              <strong>LLM 目录</strong>
              <span>回到底层原理继续看</span>
            </article>
          </div>
        </div>
      </section>
    </main>
    {build_footer()}
  </div>
</body>
</html>
"""


def build_robots_txt() -> str:
    return f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""


def build_sitemap_xml() -> str:
    pages = ["index.html", "summary.html", *[f"{lesson.slug}.html" for lesson in LESSONS]]
    entries = []
    for filename in pages:
        entries.append(
            "  <url>\n"
            f"    <loc>{page_url(filename)}</loc>\n"
            f"    <lastmod>{BUILD_DATE}</lastmod>\n"
            "  </url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )


def build_favicon_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-label="nanoAgent">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1f2430" />
      <stop offset="100%" stop-color="#b24c2a" />
    </linearGradient>
  </defs>
  <rect width="128" height="128" rx="28" fill="#f7efe2" />
  <rect x="14" y="14" width="100" height="100" rx="22" fill="url(#g)" />
  <path d="M37 84V44h16l24 24V44h14v40H75L51 60v24H37z" fill="#fff7ef" />
</svg>
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
    (DOCS_DIR / "summary.html").write_text(tidy_output(build_summary_page()), encoding="utf-8")
    (DOCS_DIR / "404.html").write_text(tidy_output(build_not_found_page()), encoding="utf-8")
    (DOCS_DIR / "robots.txt").write_text(build_robots_txt(), encoding="utf-8")
    (DOCS_DIR / "sitemap.xml").write_text(build_sitemap_xml(), encoding="utf-8")
    (ASSETS_DIR / "favicon.svg").write_text(build_favicon_svg(), encoding="utf-8")
    (DOCS_DIR / ".nojekyll").write_text("", encoding="utf-8")


if __name__ == "__main__":
    main()

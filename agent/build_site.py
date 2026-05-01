import html
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List


ROOT = Path(__file__).parent
REPO_ROOT = ROOT.parent
DOCS_DIR = REPO_ROOT / "docs"
ASSETS_DIR = DOCS_DIR / "assets"
REPO_WEB_BASE = "https://github.com/GitHubxsy/nanoAgent"
SITE_URL = "https://githubxsy.github.io/nanoAgent"
SITE_TITLE = "从零开始理解 Agent"
SITE_SUBTITLE = "1 小时实战分享课"
SITE_DESCRIPTION = "把 nanoAgent 前七篇内容压缩成一门 1 小时实战分享课，只保留课堂最需要的任务、代码和练习。"
VIEW_MODE_BOOTSTRAP = """
  <script>
    (function () {
      try {
        var savedMode = window.localStorage.getItem("nanoagent-view-mode");
        var nextMode = savedMode === "shared" ? "shared" : "teacher";
        document.documentElement.dataset.viewMode = nextMode;
      } catch (error) {
        document.documentElement.dataset.viewMode = "teacher";
      }
    })();
  </script>
""".strip()


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
            "终端先打印 `[Tool] write_file(...)`，说明模型选择了工具。",
            "再次要求它读取 `hello.txt`，验证效果已经落到真实文件。",
            "顺手指出 `messages` 会随着每一步持续增长。",
        ],
        student_takeaways=[
            "能解释 Agent 与 Chat 的根本区别。",
            "能看懂 `tools`、`functions`、`messages` 和循环的关系。",
            "知道 Agent 的执行权仍然掌握在代码里，不在模型里。",
        ],
        practice_steps=[
            "把 `max_iterations` 改成 2，观察复杂任务会如何提前中断。",
            "让 Agent 连续执行“写文件 + 读文件”两个动作，体会循环的必要性。",
            "给 `execute_bash` 加一句更清晰的描述，看看模型是否更容易选对工具。",
        ],
        talk_points=[
            "LLM 输出的是结构化“调用意图”，不是直接执行系统命令。",
            "`messages` 是 Agent 的短期工作区，每走一步都要回填现场结果。",
            "循环次数就是 Agent 的行动预算，也是最早的工程约束。",
        ],
        pitfalls=[
            "`execute_bash` 功能太强，后面必须加安全边界。",
            "工具报错也要回填给模型，否则它无法自我修正。",
            "只堆工具不设计循环，最后就会退化回普通问答。",
        ],
        workshop_prompt="把它当成一台会自己选工具的“任务执行机”，而不是聊天窗口。",
        md_path=ROOT / "01-essence/agent-essence.md",
        code_path=ROOT / "01-essence/agent-essence.py",
        snippets=[
            Snippet(
                title="最小 Agent 循环",
                start=73,
                end=97,
                focus="课堂只讲这 20 多行：发请求、拿工具调用、执行工具、把结果回填。",
            )
        ],
    ),
    Lesson(
        slug="memory",
        number="02",
        title="记忆与规划",
        short_title="多步任务",
        stage="从单步到连续工作",
        lesson_minutes="8 分钟",
        summary="给最小 Agent 加上长期记忆和规划能力，让它不只是“做一步”，而是能拆任务、按顺序推进。",
        core="持久记忆 + Plan-then-Execute",
        tags=["Memory", "Planning", "Shared Messages"],
        demo_command='python agent/02-memory/agent-memory.py --plan "分析当前项目结构并给出重构建议"',
        demo_goal="演示 Agent 如何先拆步骤，再逐步执行，还能把结果写进记忆文件。",
        demo_expected=[
            "先看到 `[Planning]` 与拆解出的 3 到 5 个步骤。",
            "再看到每个步骤共用同一个 `messages` 上下文继续推进。",
            "最后检查 `agent_memory.md`，理解持久记忆最简单可以只是一个文件。",
        ],
        student_takeaways=[
            "能区分短期上下文与长期记忆。",
            "知道规划本身也是一次单独的模型调用。",
            "理解多步任务为什么要共享 `messages`。",
        ],
        practice_steps=[
            "先运行一次“创建 demo 文件”，再运行一次“读取刚才文件并补注释”，观察记忆是否生效。",
            "把 `load_memory()` 的窗口裁剪改小，看看历史信息会如何衰减。",
            "删掉 `--plan` 再跑同一任务，对比有规划和无规划的行为差异。",
        ],
        talk_points=[
            "规划不是额外魔法，只是把任务拆解前置了一次。",
            "跨步骤共享 `messages`，就是让 Agent 在执行链路里“不断记住自己刚做了什么”。",
            "长期记忆最开始不用上复杂系统，先把写入和回放跑通。",
        ],
        pitfalls=[
            "记忆窗口过大，后面会迅速碰到上下文爆炸。",
            "规划失败时一定要有降级路径，不能卡死。",
            "把所有历史都塞回 prompt，不等于真正的记忆系统。",
        ],
        workshop_prompt="让大家亲手跑两次连续任务，记住：记忆不是抽象概念，是可观察的文件与上下文。",
        md_path=ROOT / "02-memory/agent-memory.md",
        code_path=ROOT / "02-memory/agent-memory.py",
        snippets=[
            Snippet(
                title="先规划，再执行",
                start=131,
                end=157,
                focus="这段代码展示了规划是如何被建成一个普通函数调用的。",
            ),
            Snippet(
                title="多步任务复用同一个 messages",
                start=160,
                end=220,
                focus="真正的关键不是 `for step in steps`，而是步骤之间共用上下文。",
            ),
        ],
    ),
    Lesson(
        slug="skills-mcp",
        number="03",
        title="Rules、Skills 与 MCP",
        short_title="工程扩展",
        stage="从脚本到框架",
        lesson_minutes="10 分钟",
        summary="这一讲只抓工程化里最值钱的三件事：规则约束、技能注入和工具外接，而不是把配置细节全部讲完。",
        core="规则 + 技能 + 外部工具",
        tags=["Rules", "Skills", "MCP"],
        demo_command='python agent/03-skills-mcp/agent-skills-mcp.py --plan "扫描项目里所有 TODO 并生成修复顺序"',
        demo_goal="展示一个 Agent 为什么会越来越像平台：它开始从文件系统和配置里吸收能力。",
        demo_expected=[
            "如果项目下放了 `.agent/rules` 或 `.agent/skills`，启动时能看到加载日志。",
            "`plan` 不再只是外部函数，而是工具系统的一部分。",
            "讲解时重点放在“分层职责”，而不是每个配置格式的细枝末节。",
        ],
        student_takeaways=[
            "知道 Rule 负责约束行为，Skill 负责补充领域知识，MCP 负责扩展工具边界。",
            "理解为什么 `plan` 变成工具后，主循环会更统一。",
            "能自己给项目加一个最小规则文件并验证它会被注入。",
        ],
        practice_steps=[
            "新建 `.agent/rules/code-style.md`，只写一条简单规范，再运行一次任务。",
            "给 `.agent/skills/` 放一个最小 JSON 技能描述，观察加载输出。",
            "把 `plan` 工具注释掉，对比 Agent 在复杂任务里的差异。",
        ],
        talk_points=[
            "工程化 Agent 的重点不是“多炫”，而是上下文被组织得更可控。",
            "Rules、Skills、MCP 是三层不同问题，不要混成一个“配置系统”。",
            "当能力开始外置，Agent 才有项目感和团队协作价值。",
        ],
        pitfalls=[
            "规则、技能太多时会互相打架，提示词冲突会更隐蔽。",
            "`plan` 工具必须防递归，不然很容易自我套娃。",
            "工具列表不断膨胀后，模型的工具选择准确率会下降。",
        ],
        workshop_prompt="课堂上只演示一个最小规则文件和一个最小技能定义，不展开完整配置宇宙。",
        md_path=ROOT / "03-skills-mcp/agent-skills-mcp.md",
        code_path=ROOT / "03-skills-mcp/agent-skills-mcp.py",
        snippets=[
            Snippet(
                title="把计划注册成工具",
                start=195,
                end=230,
                focus="这是课堂最值得讲的转折点：复杂能力也可以被包装进统一工具协议。",
            ),
            Snippet(
                title="从文件系统加载 Rules / Skills / MCP",
                start=266,
                end=305,
                focus="这段代码把“可配置能力”放进了项目目录，而不是继续硬编码在脚本里。",
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
            "能解释为什么课堂上要禁止子代理继续派子代理。",
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
        workshop_prompt="最好的课堂做法是只演一个前后端双角色案例，让委派的价值立刻可见。",
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
            "知道为什么 reviewer 是课堂里最好展示团队价值的角色。",
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
        summary="这一讲不讲理论史，只解决一个课堂上特别容易说清的问题：为什么长任务里 Agent 会被自己的历史压死。",
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
        workshop_prompt="课堂上把阈值调小，强制触发一次压缩，是最直观的讲法。",
        md_path=ROOT / "06-compact/agent-compact.md",
        code_path=ROOT / "06-compact/agent-compact.py",
        snippets=[
            Snippet(
                title="上下文压缩函数",
                start=129,
                end=190,
                focus="这就是课堂里最值钱的 60 行：把旧历史折叠成摘要，把当前现场留下来。",
            )
        ],
    ),
    Lesson(
        slug="safety",
        number="07",
        title="三道安全防线",
        short_title="上线边界",
        stage="能力关进笼子",
        lesson_minutes="8 分钟",
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
    "课堂上优先用终端演示，不用展示全部原文文章。",
]


SESSION_FORMAT = [
    "20% 概念：只解释最少必要的共识，不做长篇原理展开。",
    "50% 现场演示：每一讲都对应一个可以复制的命令或任务。",
    "30% 动手练习：让大家回去能自己再改一次代码。",
]


AGENDA = [
    ("00 - 05", "开场：为什么今天不讲大而全", "先建立一个共识：这 1 小时只保留真正能拿去做 Demo 的内容。"),
    ("05 - 13", "第 01 讲：最小闭环", "跑通最小 Agent，让大家看见工具调用、执行和结果回填。"),
    ("13 - 21", "第 02 讲：记忆与规划", "演示 `--plan` 和 `agent_memory.md`，让 Agent 会连续工作。"),
    ("21 - 31", "第 03 讲：Rules / Skills / MCP", "把 Agent 从脚本推到工程化外壳，但只讲配置分层和一个最小示例。"),
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
    return f"""
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}">
  <meta name="theme-color" content="#1f2430">
  <link rel="canonical" href="{html.escape(canonical)}">
  <meta property="og:locale" content="zh_CN">
  <meta property="og:type" content="{page_type}">
  <meta property="og:site_name" content="{html.escape(SITE_TITLE)}">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(description)}">
  <meta property="og:url" content="{html.escape(canonical)}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{html.escape(title)}">
  <meta name="twitter:description" content="{html.escape(description)}">
  {VIEW_MODE_BOOTSTRAP}
  <link rel="stylesheet" href="assets/style.css">
  <script defer src="assets/site.js"></script>
""".strip()


def render_tags(tags: List[str], class_name: str) -> str:
    return "".join(f'<span class="{class_name}">{html.escape(tag)}</span>' for tag in tags)


def render_bullets(items: List[str], class_name: str = "lesson-list") -> str:
    body = "".join(f"<li>{html.escape(item)}</li>" for item in items)
    return f'<ul class="{class_name}">{body}</ul>'


def render_steps(items: List[str]) -> str:
    body = "".join(f"<li>{html.escape(item)}</li>" for item in items)
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
      <p>课堂版页面只保留 1 小时分享最需要的实战内容，完整原文与源码请看 GitHub。</p>
      <div class="footer-links">
        <a href="{REPO_WEB_BASE}">GitHub 仓库</a>
        <a href="{github_blob_url(ROOT / 'README_CN.md')}">系列导读</a>
        <a href="{github_blob_url(ROOT / 'build_site.py')}">站点生成器</a>
      </div>
    </footer>
    """


def build_view_switch() -> str:
    return """
    <div class="view-switch" role="group" aria-label="页面视图切换">
      <span class="view-switch-label">视图</span>
      <button type="button" class="view-switch-btn is-active" data-view-mode-option="teacher" aria-pressed="true">教师版</button>
      <button type="button" class="view-switch-btn" data-view-mode-option="shared" aria-pressed="false">共享版</button>
    </div>
    """


def build_shared_lesson_cards(lesson: Lesson) -> str:
    items = [
        ("本讲主线", lesson.core),
        ("现场任务", lesson.demo_goal),
        ("马上动手", lesson.practice_steps[0]),
        (
            "只看代码",
            f"{lesson.snippets[0].title} · L{lesson.snippets[0].start}-L{lesson.snippets[0].end}",
        ),
    ]
    body = "".join(
        f"""
        <article class="shared-focus-card">
          <p>{html.escape(label)}</p>
          <strong>{html.escape(content)}</strong>
        </article>
        """
        for label, content in items
    )
    return f'<div class="shared-card-grid">{body}</div>'


def build_home_page() -> str:
    lesson_cards = []
    for lesson in LESSONS:
        lesson_cards.append(
            f"""
            <article class="lesson-card">
              <p class="lesson-index">第 {lesson.number} 讲 · {html.escape(lesson.stage)}</p>
              <h3>{html.escape(lesson.title)}</h3>
              <p class="teacher-only">{html.escape(lesson.summary)}</p>
              <p class="shared-only">{html.escape(lesson.demo_goal)}</p>
              <div class="lesson-meta">
                <span>{html.escape(lesson.lesson_minutes)}</span>
                <span>{code_lines(lesson.code_path)} 行代码</span>
                <span>{html.escape(lesson.core)}</span>
              </div>
              <p class="lesson-kicker teacher-only">实战重点：{html.escape(lesson.workshop_prompt)}</p>
              <div class="lesson-tag-row">{render_tags(lesson.tags, "tag")}</div>
              <a class="lesson-link" href="{lesson.slug}.html">看课堂版讲义</a>
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

    shared_agenda = []
    for time_range, title, _ in AGENDA:
        shared_agenda.append(
            f"""
            <article class="shared-agenda-card">
              <span>{html.escape(time_range)}</span>
              <strong>{html.escape(title)}</strong>
            </article>
            """
        )

    shared_format_cards = [
        ("一起看的主线", "每一讲只盯住主线、任务和关键代码，不展开全文。"),
        ("课堂推进方式", "先看现场演示，再跟着做课堂练习，最后验证结果。"),
        ("投屏信息密度", "共享版会隐藏主讲备注，让页面更适合边讲边看。"),
        ("课程目标", "听完 60 分钟，大家要能自己改一轮最小 Agent。"),
    ]

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
      <div class="header-tools">
        {build_view_switch()}
        <nav class="top-nav">
          <a href="#agenda">课程流程</a>
          <a href="#format">授课方式</a>
          <a href="#lessons">七讲讲义</a>
          <a href="{REPO_WEB_BASE}">GitHub</a>
        </nav>
      </div>
    </header>

    <main id="main-content">
      <section class="hero-panel">
        <div class="hero-copy">
          <p class="eyebrow">{SITE_SUBTITLE}</p>
          <h1>不讲全量原文，只讲能当场跑起来的 Agent</h1>
          <p class="hero-lead">这套站点把前七篇文章压成一门 1 小时的实战分享课。每一讲只保留课堂必须讲的概念、演示命令、练习步骤和关键代码，帮助你讲得短、讲得稳、讲完大家还能自己动手。</p>
          <p class="mode-note teacher-only">教师版会显示主讲提示、踩坑提醒和课后延伸，适合备课或边讲边控场。</p>
          <p class="mode-note shared-only">共享版会隐藏主讲备注，只保留共同观看时的节奏、重点和任务，适合投屏。</p>
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
              <span>全部压缩为课堂版讲义</span>
            </article>
            <article class="fact-card">
              <strong>实战优先</strong>
              <span>每讲都有演示命令与练习</span>
            </article>
            <article class="fact-card">
              <strong>不贴全文</strong>
              <span>完整文章改为课后延伸</span>
            </article>
          </div>
        </div>
      </section>

      <section class="section-block" id="format">
        <div class="section-head teacher-only">
          <p class="eyebrow">Course Outcome</p>
          <h2>参与者 1 小时后应该带走什么</h2>
        </div>
        <div class="section-head shared-only">
          <p class="eyebrow">Shared View</p>
          <h2>共享版怎么跟着这门课走</h2>
          <p>共享版只保留当前主线、马上要做的任务和关键代码，避免投屏时信息过载。</p>
        </div>
        <div class="format-grid teacher-only">
          <article class="format-card">
            <h3>课程结果</h3>
            {render_bullets(SESSION_OUTCOMES)}
          </article>
          <article class="format-card">
            <h3>上课准备</h3>
            {render_bullets(SESSION_SETUP)}
          </article>
          <article class="format-card">
            <h3>授课节奏</h3>
            {render_bullets(SESSION_FORMAT)}
          </article>
        </div>
        <div class="shared-agenda-grid shared-only">
          {"".join(
              f'''
              <article class="shared-agenda-card">
                <span>{html.escape(label)}</span>
                <strong>{html.escape(content)}</strong>
              </article>
              '''
              for label, content in shared_format_cards
          )}
        </div>
      </section>

      <section class="section-block" id="agenda">
        <div class="section-head">
          <p class="eyebrow">Agenda</p>
          <h2>60 分钟怎么分配</h2>
          <p class="teacher-only">核心原则：每一讲都用“一个演示 + 一段关键代码 + 一个练习”收束，不把大家淹没在全文里。</p>
          <p class="shared-only">共享版只保留时间线和当前讲次，现场口头补充细节即可。</p>
        </div>
        <div class="agenda-list teacher-only">
          {"".join(agenda_items)}
        </div>
        <div class="shared-agenda-grid shared-only">
          {"".join(shared_agenda)}
        </div>
      </section>

      <section class="section-block" id="lessons">
        <div class="section-head">
          <p class="eyebrow">Lesson Pack</p>
          <h2>七讲课堂版讲义</h2>
          <p>每个页面都已经改成适合课堂分享的结构：讲什么、演示什么、大家马上做什么、看哪段代码。</p>
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
        ("goals", "这节课要带走什么"),
        ("demo", "现场演示"),
        ("practice", "课堂练习"),
        ("code", "关键代码"),
        ("talk", "讲课只讲这 3 件事"),
        ("pitfalls", "容易踩坑"),
        ("extend", "课后延伸"),
    ]

    snippet_cards = []
    for snippet in lesson.snippets:
        snippet_cards.append(
            f"""
            <article class="code-card">
              <div class="code-card-head">
                <div>
                  <p class="lesson-index">{html.escape(snippet.title)}</p>
                  <h3>{html.escape(snippet.focus)}</h3>
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
      <div class="header-tools">
        {build_view_switch()}
        <nav class="top-nav">
          <a href="index.html#agenda">课程流程</a>
          <a href="index.html#lessons">七讲讲义</a>
          <a href="{REPO_WEB_BASE}">GitHub</a>
        </nav>
      </div>
    </header>

    <main class="article-layout" id="main-content">
      <aside class="article-sidebar teacher-only">
        <div class="sidebar-card">
          <p class="eyebrow">第 {lesson.number} 讲 · {html.escape(lesson.stage)}</p>
          <h2 class="lesson-title">{html.escape(lesson.title)}</h2>
          <p>{html.escape(lesson.summary)}</p>
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
          <h2>课堂目录</h2>
          <nav class="toc">
            {"".join(f'<a class="toc-link" href="#{anchor}">{html.escape(label)}</a>' for anchor, label in toc_links)}
          </nav>
        </div>
      </aside>

      <article class="article-main">
        <section class="article-hero">
          <div class="breadcrumbs teacher-only">
            <a href="index.html">课程首页</a>
            <span>/</span>
            <a href="index.html#lessons">课堂版讲义</a>
            <span>/</span>
            <span>第 {lesson.number} 讲</span>
          </div>
          <p class="eyebrow">{SITE_SUBTITLE}</p>
          <h1>{lesson.number}. {html.escape(lesson.title)}</h1>
          <p class="lead">{html.escape(lesson.summary)}</p>
          <p class="mode-note teacher-only">教师版显示课堂目录、主讲提示、踩坑和课后延伸，适合备课与授课控制。</p>
          <p class="mode-note shared-only">共享版已隐藏主讲备注，页面会放大重点信息，适合一起观看。</p>
          <div class="tag-row teacher-only">{render_tags(lesson.tags, "tag")}</div>
          <div class="hero-actions">
            <a class="primary-btn" href="{next_lesson.slug + '.html' if next_lesson else 'index.html#lessons'}">{'继续第 ' + next_lesson.number + ' 讲' if next_lesson else '返回课程首页'}</a>
            <a class="secondary-btn teacher-only" href="{github_blob_url(lesson.md_path)}">完整原文</a>
          </div>
        </section>

        <section class="lesson-section shared-only">
          <div class="lesson-section-head">
            <p class="eyebrow">Shared Focus</p>
            <h2>投屏时只看这 4 件事</h2>
          </div>
          {build_shared_lesson_cards(lesson)}
        </section>

        <section class="lesson-section" id="goals">
          <div class="lesson-section-head">
            <p class="eyebrow">Goal</p>
            <h2>这节课要带走什么</h2>
          </div>
          {render_bullets(lesson.student_takeaways)}
        </section>

        <section class="lesson-section" id="demo">
          <div class="lesson-section-head">
            <p class="eyebrow">Live Demo</p>
            <h2>现场演示</h2>
            <p>{html.escape(lesson.demo_goal)}</p>
          </div>
          <div class="demo-box">
            <p class="lesson-index">演示命令</p>
            <pre class="demo-command"><code>{html.escape(lesson.demo_command)}</code></pre>
            {render_bullets(lesson.demo_expected, "lesson-list")}
          </div>
        </section>

        <section class="lesson-section" id="practice">
          <div class="lesson-section-head">
            <p class="eyebrow">Practice</p>
            <h2>课堂练习</h2>
            <p>{html.escape(lesson.workshop_prompt)}</p>
          </div>
          {render_steps(lesson.practice_steps)}
        </section>

        <section class="lesson-section" id="code">
          <div class="lesson-section-head">
            <p class="eyebrow">Code Focus</p>
            <h2>关键代码</h2>
          </div>
          <div class="code-group">
            {"".join(snippet_cards)}
          </div>
        </section>

        <section class="lesson-section teacher-only" id="talk">
          <div class="lesson-section-head">
            <p class="eyebrow">Talk Track</p>
            <h2>讲课只讲这 3 件事</h2>
          </div>
          {render_bullets(lesson.talk_points)}
        </section>

        <section class="lesson-section teacher-only" id="pitfalls">
          <div class="lesson-section-head">
            <p class="eyebrow">Pitfalls</p>
            <h2>容易踩坑</h2>
          </div>
          {render_bullets(lesson.pitfalls)}
        </section>

        <section class="lesson-section teacher-only" id="extend">
          <div class="lesson-section-head">
            <p class="eyebrow">After Class</p>
            <h2>课后延伸</h2>
            <p>课堂里不展示全文，课后再补完整文章和源码细节。</p>
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

import html
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


ROOT = Path(__file__).parent
REPO_ROOT = ROOT.parent
DOCS_DIR = REPO_ROOT / "docs"
ASSETS_DIR = DOCS_DIR / "assets"
REPO_WEB_BASE = "https://github.com/GitHubxsy/nanoAgent"
SITE_URL = "https://githubxsy.github.io/nanoAgent"
SITE_TITLE = "从零开始理解 Agent"
SITE_DESCRIPTION = "基于 nanoAgent 前七篇文章制作的 Agent 技术教学网站，从底层原理到安全控制系统梳理现代 Agent。"


@dataclass
class Article:
    slug: str
    number: str
    title: str
    md_path: Path
    code_path: Path
    short_title: str
    summary: str
    core: str
    difficulty: str
    time_cost: str
    tags: List[str]


ARTICLES = [
    Article(
        slug="essence",
        number="01",
        title="底层原理，只有 100 行",
        md_path=ROOT / "01-essence/agent-essence.md",
        code_path=ROOT / "01-essence/agent-essence.py",
        short_title="本质",
        summary="先把 Agent 的共同底座讲清楚：为什么它不是聊天机器人，而是能自己完成任务的循环系统。",
        core="Agent = LLM + 工具 + 循环",
        difficulty="入门",
        time_cost="12 分钟",
        tags=["工具调用", "Function Calling", "Agent Loop"],
    ),
    Article(
        slug="memory",
        number="02",
        title="记忆与规划",
        md_path=ROOT / "02-memory/agent-memory.md",
        code_path=ROOT / "02-memory/agent-memory.py",
        short_title="记忆",
        summary="从单轮执行走向连续工作，让 Agent 能记住过去、拆解任务、按步骤推进复杂目标。",
        core="持久记忆 + Plan-then-Execute",
        difficulty="入门",
        time_cost="14 分钟",
        tags=["Memory", "Planning", "多步任务"],
    ),
    Article(
        slug="skills-mcp",
        number="03",
        title="Rules、Skills 与 MCP",
        md_path=ROOT / "03-skills-mcp/agent-skills-mcp.md",
        code_path=ROOT / "03-skills-mcp/agent-skills-mcp.py",
        short_title="扩展",
        summary="解释现代 Agent 为什么能像平台一样扩展能力，以及规则、技能、协议分别处在系统的哪一层。",
        core="行为约束 + 外部能力接入",
        difficulty="进阶",
        time_cost="18 分钟",
        tags=["Rules", "Skills", "MCP"],
    ),
    Article(
        slug="subagent",
        number="04",
        title="SubAgent 子智能体",
        md_path=ROOT / "04-subagent/agent-subagent.md",
        code_path=ROOT / "04-subagent/agent-subagent.py",
        short_title="分工",
        summary="从单 Agent 迈向任务委派，理解为什么复杂问题需要拆给更聚焦的子智能体处理。",
        core="委派 + 上下文隔离",
        difficulty="进阶",
        time_cost="15 分钟",
        tags=["SubAgent", "Delegation", "Isolation"],
    ),
    Article(
        slug="teams",
        number="05",
        title="多智能体团队协作",
        md_path=ROOT / "05-teams/agent-teams.md",
        code_path=ROOT / "05-teams/agent-teams.py",
        short_title="协作",
        summary="把多个 Agent 组织成团队，理解角色划分、通信、编排和最终审查这些工程化机制。",
        core="角色化协作 + 生命周期管理",
        difficulty="进阶",
        time_cost="16 分钟",
        tags=["Multi-Agent", "Team", "Orchestration"],
    ),
    Article(
        slug="compact",
        number="06",
        title="上下文压缩",
        md_path=ROOT / "06-compact/agent-compact.md",
        code_path=ROOT / "06-compact/agent-compact.py",
        short_title="压缩",
        summary="专门解决长任务里的上下文爆炸问题，理解摘要、保留窗口和持续工作能力之间的关系。",
        core="Summary + Recent Window",
        difficulty="进阶",
        time_cost="13 分钟",
        tags=["Context Window", "Compaction", "Summarization"],
    ),
    Article(
        slug="safety",
        number="07",
        title="三道安全防线",
        md_path=ROOT / "07-safety/agent-safe.md",
        code_path=ROOT / "07-safety/agent-safe.py",
        short_title="安全",
        summary="最后收束到真实落地最不能跳过的一层：权限、确认、黑名单和风险控制。",
        core="风险隔离 + 人机边界",
        difficulty="关键",
        time_cost="15 分钟",
        tags=["Safety", "Permissions", "Guardrails"],
    ),
]


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


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\u4e00-\u9fff\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text or "section"


def github_blob_url(path: Path) -> str:
    relative = path.relative_to(REPO_ROOT).as_posix()
    return f"{REPO_WEB_BASE}/blob/{SOURCE_BRANCH}/{relative}"


def page_url(filename: str) -> str:
    if filename == "index.html":
        return f"{SITE_URL}/"
    return f"{SITE_URL}/{filename}"


def build_head(title: str, description: str, filename: str, page_type: str) -> str:
    canonical = page_url(filename)
    escaped_title = html.escape(title)
    escaped_description = html.escape(description)
    escaped_canonical = html.escape(canonical)
    return f"""
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <meta name="description" content="{escaped_description}">
  <meta name="theme-color" content="#1f2430">
  <link rel="canonical" href="{escaped_canonical}">
  <meta property="og:locale" content="zh_CN">
  <meta property="og:type" content="{page_type}">
  <meta property="og:site_name" content="{html.escape(SITE_TITLE)}">
  <meta property="og:title" content="{escaped_title}">
  <meta property="og:description" content="{escaped_description}">
  <meta property="og:url" content="{escaped_canonical}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{escaped_title}">
  <meta name="twitter:description" content="{escaped_description}">
  <link rel="stylesheet" href="assets/style.css">
  <script defer src="assets/site.js"></script>
""".strip()


def build_footer() -> str:
    return f"""
    <footer class="site-footer">
      <p>内容基于 nanoAgent 的前七篇文章重组，适配为课程型教学网站。</p>
      <div class="footer-links">
        <a href="{REPO_WEB_BASE}">GitHub 仓库</a>
        <a href="{github_blob_url(ROOT / 'README_CN.md')}">系列导读</a>
        <a href="{github_blob_url(ROOT / 'build_site.py')}">站点生成器</a>
      </div>
    </footer>
    """


def convert_links(target: str) -> str:
    article_map = {article.md_path.name: f"{article.slug}.html" for article in ARTICLES}
    article_map.update({str(article.md_path.relative_to(ROOT)): f"{article.slug}.html" for article in ARTICLES})
    if target.startswith("http://") or target.startswith("https://"):
        return target
    normalized = target.replace("../", "").replace("./", "")
    normalized = normalized.split("#", 1)[0]
    if normalized in article_map:
        return article_map[normalized]
    return target


def render_inline(text: str) -> str:
    placeholders: List[str] = []

    def store_code(match: re.Match[str]) -> str:
        placeholders.append(f"<code>{html.escape(match.group(1))}</code>")
        return f"@@CODE{len(placeholders) - 1}@@"

    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", store_code, escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{html.escape(convert_links(m.group(2)))}">{m.group(1)}</a>',
        escaped,
    )
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    for idx, value in enumerate(placeholders):
        escaped = escaped.replace(f"@@CODE{idx}@@", value)
    return escaped


def flush_paragraph(buffer: List[str], out: List[str]) -> None:
    if not buffer:
        return
    paragraph = " ".join(line.strip() for line in buffer).strip()
    if paragraph:
        out.append(f"<p>{render_inline(paragraph)}</p>")
    buffer.clear()


def flush_list(items: List[Tuple[str, str]], out: List[str]) -> None:
    if not items:
        return
    current_kind = items[0][0]
    tag = "ol" if current_kind == "ol" else "ul"
    out.append(f"<{tag}>")
    for _, item in items:
        out.append(f"<li>{render_inline(item)}</li>")
    out.append(f"</{tag}>")
    items.clear()


def flush_blockquote(buffer: List[str], out: List[str]) -> None:
    if not buffer:
        return
    parts: List[str] = []
    paragraph_lines: List[str] = []
    list_items: List[Tuple[str, str]] = []

    def flush_quote_paragraph() -> None:
        if not paragraph_lines:
            return
        paragraph = " ".join(line.strip() for line in paragraph_lines).strip()
        if paragraph:
            parts.append(f"<p>{render_inline(paragraph)}</p>")
        paragraph_lines.clear()

    def flush_quote_list() -> None:
        if not list_items:
            return
        current_kind = list_items[0][0]
        tag = "ol" if current_kind == "ol" else "ul"
        parts.append(f"<{tag}>")
        for _, item in list_items:
            parts.append(f"<li>{render_inline(item)}</li>")
        parts.append(f"</{tag}>")
        list_items.clear()

    for raw_line in buffer:
        stripped = raw_line.strip()
        ul_match = re.match(r"^[-*]\s+(.*)$", stripped)
        ol_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if ul_match or ol_match:
            flush_quote_paragraph()
            kind = "ul" if ul_match else "ol"
            text = ul_match.group(1) if ul_match else ol_match.group(1)
            if list_items and list_items[0][0] != kind:
                flush_quote_list()
            list_items.append((kind, text))
        else:
            flush_quote_list()
            paragraph_lines.append(raw_line)

    flush_quote_paragraph()
    flush_quote_list()
    out.append(f"<blockquote>{''.join(parts)}</blockquote>")
    buffer.clear()


def flush_table(rows: List[List[str]], out: List[str]) -> None:
    if not rows:
        return
    header = rows[0]
    body = rows[1:]
    out.append("<div class=\"table-wrap\"><table>")
    out.append("<thead><tr>")
    for cell in header:
        out.append(f"<th>{render_inline(cell.strip())}</th>")
    out.append("</tr></thead>")
    if body:
        out.append("<tbody>")
        for row in body:
            out.append("<tr>")
            for cell in row:
                out.append(f"<td>{render_inline(cell.strip())}</td>")
            out.append("</tr>")
        out.append("</tbody>")
    out.append("</table></div>")
    rows.clear()


def markdown_to_html(markdown: str) -> Tuple[str, List[Tuple[int, str, str]]]:
    lines = markdown.splitlines()
    out: List[str] = []
    headings: List[Tuple[int, str, str]] = []
    paragraph: List[str] = []
    items: List[Tuple[str, str]] = []
    quotes: List[str] = []
    table_rows: List[List[str]] = []
    in_code = False
    code_lang = ""
    code_buffer: List[str] = []
    i = 0

    def flush_non_code() -> None:
        flush_paragraph(paragraph, out)
        flush_list(items, out)
        flush_blockquote(quotes, out)
        flush_table(table_rows, out)

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if in_code:
            if stripped.startswith("```"):
                code = html.escape("\n".join(code_buffer))
                out.append(
                    f'<pre class="code-block"><code class="language-{html.escape(code_lang)}">{code}</code></pre>'
                )
                in_code = False
                code_lang = ""
                code_buffer.clear()
            else:
                code_buffer.append(line)
            i += 1
            continue

        if stripped.startswith("```"):
            flush_non_code()
            in_code = True
            code_lang = stripped[3:].strip() or "text"
            i += 1
            continue

        if not stripped:
            flush_non_code()
            i += 1
            continue

        if stripped in {"---", "***"}:
            flush_non_code()
            out.append("<hr>")
            i += 1
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            flush_non_code()
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            anchor = slugify(text)
            headings.append((level, text, anchor))
            out.append(f'<h{level} id="{anchor}">{render_inline(text)}</h{level}>')
            i += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph(paragraph, out)
            flush_list(items, out)
            flush_table(table_rows, out)
            quotes.append(stripped[1:].strip())
            i += 1
            continue

        if "|" in stripped and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if re.match(r"^\|?[\s:-]+\|[\s|:-]*$", next_line):
                flush_non_code()
                header = [cell.strip() for cell in stripped.strip("|").split("|")]
                table_rows.append(header)
                i += 2
                while i < len(lines):
                    table_line = lines[i].strip()
                    if not table_line or "|" not in table_line:
                        break
                    table_rows.append([cell.strip() for cell in table_line.strip("|").split("|")])
                    i += 1
                flush_table(table_rows, out)
                continue

        ul_match = re.match(r"^[-*]\s+(.*)$", stripped)
        ol_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if ul_match or ol_match:
            flush_paragraph(paragraph, out)
            flush_blockquote(quotes, out)
            kind = "ul" if ul_match else "ol"
            text = ul_match.group(1) if ul_match else ol_match.group(1)
            if items and items[0][0] != kind:
                flush_list(items, out)
            items.append((kind, text))
            i += 1
            continue

        paragraph.append(line)
        i += 1

    flush_non_code()
    return "\n".join(out), headings


def extract_intro(markdown: str) -> str:
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(">") or line.startswith("|") or line.startswith("```"):
            continue
        return line
    return ""


def strip_first_h1(article_html: str) -> str:
    return re.sub(r'^<h1 id="[^"]+">.*?</h1>\s*', "", article_html, count=1, flags=re.S)


def build_chapter_rail(current_slug: str) -> str:
    items = []
    for article in ARTICLES:
        current_class = " is-current" if article.slug == current_slug else ""
        items.append(
            f'''
            <a class="chapter-rail-link{current_class}" href="{article.slug}.html">
              <span class="course-step">第 {article.number} 讲</span>
              <strong>{html.escape(article.title)}</strong>
              <small>{html.escape(article.short_title)} · {html.escape(article.core)}</small>
            </a>
            '''
        )
    return "".join(items)


def build_article_page(article: Article, article_html: str, headings: List[Tuple[int, str, str]], intro: str, prev_article: Optional[Article], next_article: Optional[Article], code_lines: int) -> str:
    toc_items = []
    body_html = strip_first_h1(article_html)
    for level, text, anchor in headings:
        if level == 1 or level > 3:
            continue
        toc_items.append(
            f'<a class="toc-link level-{level}" href="#{anchor}">{html.escape(text)}</a>'
        )
    toc = "\n".join(toc_items)
    chapter_rail = build_chapter_rail(article.slug)
    source_article_url = github_blob_url(article.md_path)
    source_code_url = github_blob_url(article.code_path)
    prev_link = (
        f'<a class="pager-link prev" href="{prev_article.slug}.html"><span>上一篇</span><strong>{prev_article.number}. {prev_article.short_title}</strong></a>'
        if prev_article
        else ""
    )
    next_link = (
        f'<a class="pager-link next" href="{next_article.slug}.html"><span>下一篇</span><strong>{next_article.number}. {next_article.short_title}</strong></a>'
        if next_article
        else ""
    )
    primary_action = (
        f'<a class="primary-btn" href="{next_article.slug}.html">继续第 {next_article.number} 讲</a>'
        if next_article
        else '<a class="primary-btn" href="index.html#chapters">返回课程首页</a>'
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  {build_head(f"{article.number}. {article.title} | {SITE_TITLE}", article.summary, f"{article.slug}.html", "article")}
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
        <a href="index.html#path">学习路径</a>
        <a href="index.html#map">能力地图</a>
        <a href="index.html#chapters">全部章节</a>
        <a href="{REPO_WEB_BASE}">GitHub</a>
      </nav>
    </header>

    <main class="article-layout" id="main-content">
      <aside class="article-sidebar">
        <div class="sidebar-card">
          <p class="eyebrow">第 {article.number} 讲</p>
          <h2 class="lesson-title">{html.escape(article.title)}</h2>
          <p>{html.escape(article.summary)}</p>
          <div class="chip-row">
            <span class="chip">{article.difficulty}</span>
            <span class="chip">{article.time_cost}</span>
            <span class="chip">{code_lines} 行代码</span>
          </div>
        </div>

        <div class="sidebar-card">
          <h2>课程导航</h2>
          <div class="chapter-rail">{chapter_rail}</div>
        </div>

        <div class="sidebar-card">
          <h2>本章焦点</h2>
          <p class="focus-line">{html.escape(article.core)}</p>
          <p>{html.escape(intro)}</p>
        </div>

        <div class="sidebar-card">
          <h2>目录</h2>
          <nav class="toc">{toc}</nav>
        </div>

        <div class="sidebar-card">
          <h2>源码入口</h2>
          <a class="source-link" href="{source_article_url}">查看 GitHub 原始文章</a>
          <a class="source-link" href="{source_code_url}">查看 GitHub 示例代码</a>
        </div>
      </aside>

      <article class="article-main">
        <section class="article-hero">
          <div class="breadcrumbs">
            <a href="index.html">课程首页</a>
            <span>/</span>
            <a href="index.html#chapters">章节目录</a>
            <span>/</span>
            <span>第 {article.number} 讲</span>
          </div>
          <p class="eyebrow">Agent Tutorial</p>
          <h1>{article.number}. {html.escape(article.title)}</h1>
          <p class="lead">{html.escape(article.summary)}</p>
          <div class="tag-row">{"".join(f'<span class="tag">{html.escape(tag)}</span>' for tag in article.tags)}</div>
          <div class="hero-actions">
            {primary_action}
            <a class="secondary-btn" href="{source_article_url}">查看 GitHub 原文</a>
          </div>
        </section>

        <section class="content-card markdown-body">
          {body_html}
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


def build_index_page(cards: List[str]) -> str:
    timeline = "\n".join(
        f"""
        <a class="timeline-card" href="{article.slug}.html">
          <div class="timeline-step">{article.number}</div>
          <div>
            <p class="timeline-label">{html.escape(article.short_title)}</p>
            <h3>{html.escape(article.title)}</h3>
            <p>{html.escape(article.summary)}</p>
          </div>
        </a>
        """
        for article in ARTICLES
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  {build_head(f"{SITE_TITLE} | nanoAgent 技术教学网站", SITE_DESCRIPTION, "index.html", "website")}
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
        <a href="#path">学习路径</a>
        <a href="#map">能力地图</a>
        <a href="#chapters">章节阅读</a>
        <a href="{REPO_WEB_BASE}">GitHub</a>
      </nav>
    </header>

    <main id="main-content">
      <section class="hero-panel">
        <div class="hero-copy">
          <p class="eyebrow">Agent Engineering Course</p>
          <h1>把 Agent 从“会用”讲到“会搭”</h1>
          <p class="hero-lead">这个网站把 nanoAgent 的前七篇文章重组成一条连续学习路径，用最小实现解释 OpenClaw、Claude Code、Cursor Agent 这类系统背后的关键架构。</p>
          <div class="hero-actions">
            <a class="primary-btn" href="essence.html">从第 1 讲开始</a>
            <a class="secondary-btn" href="#chapters">直接选章节</a>
          </div>
        </div>
        <div class="hero-card-stack">
          <div class="formula-card">
            <span class="formula-label">一句话公式</span>
            <strong>Agent = LLM + 工具 + 循环</strong>
            <p>之后的记忆、规划、技能、子代理、团队、安全，都是在这个循环外层不断加结构。</p>
          </div>
          <div class="metric-grid">
            <div class="metric-card"><strong>7</strong><span>篇正篇</span></div>
            <div class="metric-card"><strong>2.5k+</strong><span>行教学内容</span></div>
            <div class="metric-card"><strong>100 → 282</strong><span>代码逐步进化</span></div>
            <div class="metric-card"><strong>0</strong><span>前置门槛</span></div>
          </div>
        </div>
      </section>

      <section class="section-block overview-panel">
        <div class="section-head">
          <p class="eyebrow">Overview</p>
          <h2>不是零散文章，而是一门有路径的 Agent 小课</h2>
          <p>适合刚开始接触 Agent 的开发者，也适合已经在用 Claude Code / Cursor，但想把底层结构讲清楚的人。</p>
        </div>
        <div class="overview-grid">
          <article class="overview-card">
            <h3>先抓本质</h3>
            <p>先建立共同底层，再逐步引入记忆、规划、工具扩展、子代理和安全约束。</p>
          </article>
          <article class="overview-card">
            <h3>边读边看代码</h3>
            <p>每篇都有源码入口，适合对照 Python 实现理解，不会停留在概念层。</p>
          </article>
          <article class="overview-card">
            <h3>按工程化视角收束</h3>
            <p>最后落到上下文压缩与安全防线，帮助你把 Agent 从 Demo 思维带到可落地思维。</p>
          </article>
        </div>
      </section>

      <section class="section-block" id="path">
        <div class="section-head">
          <p class="eyebrow">Learning Path</p>
          <h2>七步搭起 Agent 认知框架</h2>
          <p>不是平铺文章列表，而是一条从单体循环到工程化系统的能力生长曲线。</p>
        </div>
        <div class="timeline-grid">
          {timeline}
        </div>
      </section>

      <section class="section-block map-panel" id="map">
        <div class="section-head">
          <p class="eyebrow">Capability Map</p>
          <h2>先理解共性，再理解增强层</h2>
        </div>
        <div class="map-grid">
          <div class="map-card">
            <span class="map-index">01</span>
            <h3>底座</h3>
            <p>工具定义、函数调用、Agent Loop，是一切 Agent 的最小闭环。</p>
          </div>
          <div class="map-card">
            <span class="map-index">02</span>
            <h3>持续工作</h3>
            <p>记忆与规划让 Agent 从“一次回答”变成“多步执行者”。</p>
          </div>
          <div class="map-card">
            <span class="map-index">03-05</span>
            <h3>扩展与分工</h3>
            <p>Rules、Skills、MCP、SubAgent、Teams 共同解释可扩展的现代 Agent 产品形态。</p>
          </div>
          <div class="map-card">
            <span class="map-index">06-07</span>
            <h3>工程化约束</h3>
            <p>上下文压缩解决可持续性，安全防线解决可上线性。</p>
          </div>
        </div>
      </section>

      <section class="section-block" id="chapters">
        <div class="section-head">
          <p class="eyebrow">Chapters</p>
          <h2>选择一讲开始阅读</h2>
          <p>每一页都附带主题摘要、目录导航、原文与代码入口，适合按顺序学，也适合跳读查阅。</p>
        </div>
        <div class="chapter-grid">
          {"".join(cards)}
        </div>
      </section>
    </main>
    {build_footer()}
  </div>
</body>
</html>
"""


def build_card(article: Article, code_lines: int) -> str:
    tags = "".join(f'<span class="mini-tag">{html.escape(tag)}</span>' for tag in article.tags)
    return f"""
    <article class="chapter-card">
      <p class="chapter-index">第 {article.number} 讲</p>
      <h3>{html.escape(article.title)}</h3>
      <p>{html.escape(article.summary)}</p>
      <div class="chapter-meta">
        <span>{article.difficulty}</span>
        <span>{article.time_cost}</span>
        <span>{code_lines} 行代码</span>
      </div>
      <div class="mini-tag-row">{tags}</div>
      <a class="card-link" href="{article.slug}.html">开始阅读</a>
    </article>
    """


def ensure_dirs() -> None:
    DOCS_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)


def main() -> None:
    ensure_dirs()
    cards: List[str] = []

    for idx, article in enumerate(ARTICLES):
        markdown = article.md_path.read_text(encoding="utf-8")
        article_html, headings = markdown_to_html(markdown)
        intro = extract_intro(markdown)
        code_lines = len(article.code_path.read_text(encoding="utf-8").splitlines())
        prev_article = ARTICLES[idx - 1] if idx > 0 else None
        next_article = ARTICLES[idx + 1] if idx < len(ARTICLES) - 1 else None
        page = build_article_page(
            article=article,
            article_html=article_html,
            headings=headings,
            intro=intro,
            prev_article=prev_article,
            next_article=next_article,
            code_lines=code_lines,
        )
        (DOCS_DIR / f"{article.slug}.html").write_text(page, encoding="utf-8")
        cards.append(build_card(article, code_lines))

    (DOCS_DIR / "index.html").write_text(build_index_page(cards), encoding="utf-8")


if __name__ == "__main__":
    main()

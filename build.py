#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ink & Code —— 静态站点生成器

用法：
    python build.py          # 构建到 dist/
    python build.py --serve  # 构建后启动本地预览（默认 8123 端口）

写作流程：
    1. 在 content/posts/ 新建 xxx.md，写入 frontmatter（见示例文章）
    2. 图片放到 assets/img/，正文里用 ![alt](../../assets/img/xxx.png)
    3. 重新运行 python build.py
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

import markdown
from markdown.extensions.toc import slugify_unicode
from pygments.formatters import HtmlFormatter

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
ASSETS = ROOT / "assets"
OUT = ROOT / "dist"
CFG = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))

PER_PAGE = int(CFG.get("postsPerPage", 8))
BRAND = CFG["brand"]
BRAND_EN = CFG.get("brandEn", "")
AUTHOR = CFG.get("author", "")
SITE_URL = (os.environ.get("SITE_URL") or CFG.get("siteUrl", "")).rstrip("/")
CATEGORIES = CFG.get("categories", [])

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# --------------------------------------------------------------------------
# 小工具
# --------------------------------------------------------------------------
def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def fmt_date(d: date) -> str:
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def fmt_iso(d: date) -> str:
    return d.strftime("%Y-%m-%dT%H:%M:%S+08:00")


def tag_dir(tag: str) -> str:
    return tag.replace("/", "-").replace("\\", "-").strip()


def up_prefix(out_rel: str) -> str:
    depth = len(Path(out_rel).parts) - 1
    return "../" * depth


def page_href(href: str, up: str = "") -> str:
    """把目录式链接规范成显式 index.html。

    `blog/` 这种写法只有 Web 服务器会解析成 `blog/index.html`；
    如果用户直接双击 dist/index.html（file:// 协议）就会跳到目录列表。
    配置里保持好写的目录形式，由这里统一补全，保证本地双击也能点通。
    """
    href = str(href).strip()
    # 外链、mailto、页内锚点、站点根绝对路径原样返回
    if re.match(r"^(?:[a-zA-Z][a-zA-Z0-9+.\-]*:|#|/)", href):
        return href
    if href.endswith((".html", ".htm", ".xml", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif")):
        return href
    return href.rstrip("/") + "/index.html"


def crumbs(up: str, trail) -> str:
    """面包屑导航。

    trail: [(label, rel_or_None), ...]，rel 是相对站点根的路径（如 "blog/index.html"）。
    最后一项视为当前页：忽略 rel，渲染成 aria-current="page"。
    中间项 rel 为 None 时渲染为不可点的纯文本（对应页面不存在的情况）。
    """
    items = []
    last = len(trail) - 1
    for i, (label, rel) in enumerate(trail):
        if i == last:
            items.append(f'<li><span aria-current="page">{esc(label)}</span></li>')
        elif rel:
            items.append(f'<li><a href="{up}{page_href(rel)}">{esc(label)}</a></li>')
        else:
            items.append(f'<li><span>{esc(label)}</span></li>')
    return (
        '<nav class="crumbs" aria-label="面包屑导航"><ol>'
        + "".join(items)
        + "</ol></nav>"
    )


ICONS = {
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 3v1.5M12 19.5V21M3 12h1.5M19.5 12H21M5.6 5.6l1.1 1.1M17.3 17.3l1.1 1.1M18.4 5.6l-1.1 1.1M6.7 17.3l-1.1 1.1"/>',
    "moon": '<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a7 7 0 1 0 10.5 10.5Z"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "tag": '<path d="M20.6 13.4 12 22l-9-9V4h9l8.6 8.6a1.4 1.4 0 0 1 0 2Z"/><circle cx="7.5" cy="7.5" r="1.2"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7.5V12l3 2"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.4 2.5 15.6 0 18M12 3c-2.5 2.4-2.5 15.6 0 18"/>',
    "calendar": '<rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M8 3v4M16 3v4M3.5 10h17"/>',
    "arrow-ur": '<path d="M7 17 17 7M9 7h8v8"/>',
    "arrow-r": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "arrow-l": '<path d="M19 12H5M11 18l-6-6 6-6"/>',
    "back": '<path d="M10 19l-7-7 7-7M3 12h18"/>',
    "github": '<path d="M9 19c-4 1.5-4-2.5-6-3m12 5.5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 4.5-1.4 4.5-5a4 4 0 0 0-1.1-2.8 3.7 3.7 0 0 0-.1-2.8s-1.2-.4-3.8 1.4a9.6 9.6 0 0 0-5 0C6.4 3.2 5.2 3.6 5.2 3.6a3.7 3.7 0 0 0-.1 2.8A4 4 0 0 0 4 9.2c0 3.6 1.7 4.7 4.5 5-.6.6-.6 1.2-.5 2V21"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="m3.5 7 8.5 6 8.5-6"/>',
    "rss": '<path d="M4 11a9 9 0 0 1 9 9M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1.6"/>',
    "folder": '<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5h3.7l2 2.5h7.3A2.5 2.5 0 0 1 21 10v7a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 17V7.5Z"/>',
    "file": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z"/><path d="M14 3v5h5"/>',
    "hash": '<path d="M5 9h14M5 15h14M10 4 8 20M16 4l-2 16"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13M3.5 6h.01M3.5 12h.01M3.5 18h.01"/>',
    "up": '<path d="M12 19V5M6 11l6-6 6 6"/>',
    "user": '<circle cx="12" cy="8" r="3.6"/><path d="M4.5 20c1.2-3.5 4-5.2 7.5-5.2s6.3 1.7 7.5 5.2"/>',
    "link": '<path d="M9.5 14.5 14.5 9.5"/><path d="M11 6.5 12.5 5a4.2 4.2 0 0 1 6 6L17 12.5M13 17.5 11.5 19a4.2 4.2 0 0 1-6-6L7 11.5"/>',
    "code": '<path d="m9 8-4 4 4 4M15 8l4 4-4 4"/>',
    "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6.5 6.5l2.5 2.5M15 15l2.5 2.5M17.5 6.5 15 9M9 15l-2.5 2.5"/>',
}


def icon(name: str, cls: str = "") -> str:
    body = ICONS.get(name, "")
    c = f' class="{cls}"' if cls else ""
    return (
        f'<svg{c} viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true">{body}</svg>'
    )


# --------------------------------------------------------------------------
# 解析文章
# --------------------------------------------------------------------------
def parse_front(text: str):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
    meta, body = {}, text
    if m:
        for line in m.group(1).splitlines():
            if not line.strip() or line.strip().startswith("#"):
                continue
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            if v.startswith("[") and v.endswith("]"):
                meta[k] = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
            else:
                meta[k] = v.strip("\"'")
        body = m.group(2)
    return meta, body


def reading_time(text: str) -> int:
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    words = len(re.findall(r"[A-Za-z0-9_]+", text))
    return max(1, round(cjk / 380 + words / 200))


def plain_text(md_text: str) -> str:
    t = re.sub(r"```[\s\S]*?```", " ", md_text)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"[#>*_`|\-]+", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def make_md(style: str):
    return markdown.Markdown(
        extensions=["extra", "sane_lists", "codehilite", "toc", "admonition"],
        extension_configs={
            "codehilite": {
                "css_class": "highlight",
                "guess_lang": False,
                "linenums": False,
                "pygments_style": style,
            },
            "toc": {
                "toc_depth": "2-3",
                "permalink": "#",
                "permalink_class": "anchor",
                "permalink_title": "",
                "slugify": slugify_unicode,
            },
        },
    )


def load_posts():
    posts = []
    for path in sorted((CONTENT / "posts").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta, body = parse_front(raw)
        if str(meta.get("draft", "")).lower() in ("true", "1", "yes"):
            continue

        md = make_md("xcode")
        html_body = md.convert(body)
        toc = md.toc
        toc = toc.replace('<div class="toc">', '<div class="toc-root">')
        toc = re.sub(r"<a href=", '<a class="toc-item" href=', toc)

        d = meta.get("date") or datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
        try:
            pub = datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
        except ValueError:
            pub = date.today()

        upd = None
        if meta.get("updated"):
            try:
                upd = datetime.strptime(str(meta["updated"])[:10], "%Y-%m-%d").date()
            except ValueError:
                upd = None

        slug = meta.get("slug") or path.stem
        text = plain_text(body)
        summary = meta.get("summary") or (text[:110] + "…" if len(text) > 110 else text)

        posts.append({
            "slug": slug,
            "title": meta.get("title", path.stem),
            "date": pub,
            "updated": upd,
            "category": meta.get("category", "随笔"),
            "tags": meta.get("tags", []) if isinstance(meta.get("tags"), list) else [],
            "summary": summary,
            "lang": meta.get("lang", "中文"),
            "html": html_body,
            "toc": toc,
            "minutes": reading_time(body),
            "text": text[:4000],
            "url": f"blog/{slug}/",
        })

    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return posts


# --------------------------------------------------------------------------
# 组件
# --------------------------------------------------------------------------
def render_header(up: str, active: str) -> str:
    nav = []
    for item in CFG.get("nav", []):
        href = page_href(item["href"])
        # key 取首段，兼容 "blog/"、"blog/index.html"、"/blog/" 三种写法
        key = href.strip("/").split("/")[0]
        cur = ' aria-current="page"' if key == active else ""
        nav.append(f'<a href="{up}{href}"{cur}>{esc(item["label"])}</a>')

    return f"""<header class="site-header">
  <a class="brand" href="{up or './'}index.html">
    <span>{esc(BRAND)}</span><span class="brand__sub">{esc(BRAND_EN)}</span>
  </a>
  <div class="header-right">
    <nav class="nav" aria-label="主导航">{''.join(nav)}</nav>
    <div class="header-tools">
      <button class="search-trigger" type="button" data-open-search aria-label="搜索">
        {icon('search')}<span>搜索</span><kbd>Ctrl K</kbd>
      </button>
      <button class="icon-btn" type="button" data-toggle-theme aria-label="切换深浅色">
        <span data-theme-icon="moon">{icon('moon')}</span>
        <span data-theme-icon="sun" hidden>{icon('sun')}</span>
      </button>
      <button class="icon-btn menu-btn" type="button" data-toggle-menu aria-label="菜单" aria-expanded="false">
        {icon('menu')}
      </button>
    </div>
  </div>
</header>"""


def render_footer(up: str) -> str:
    socials = []
    for s in CFG.get("social", []):
        href = s["href"]
        if not re.match(r"^(https?:|mailto:|#)", href):
            href = up + href
        socials.append(
            f'<a href="{href}" aria-label="{esc(s["label"])}" title="{esc(s["label"])}">{icon(s["icon"])}</a>'
        )
    year = date.today().year
    start = CFG.get("startYear", year)
    span = f"{start}–{year}" if start != year else str(year)

    return f"""<footer class="site-footer">
  <div class="site-footer__inner">
    <div class="site-footer__left">
      <span>© {span} {esc(AUTHOR or BRAND)}</span>
      <span class="sep">·</span>
      <span>用 Markdown 写作，由 Python 构建</span>
    </div>
    <div class="site-footer__social">{''.join(socials)}</div>
  </div>
</footer>"""


def render_search_overlay() -> str:
    return f"""<div class="search-overlay" role="dialog" aria-modal="true" aria-label="站内搜索">
  <div class="search-panel">
    <div class="search-field">
      {icon('search')}
      <input type="search" placeholder="搜索文章、标签、正文…" autocomplete="off" spellcheck="false">
      <kbd>ESC</kbd>
    </div>
    <div class="search-results"></div>
    <div class="search-hint"><span>↑ ↓ 选择</span><span>Enter 打开</span><span>Esc 关闭</span></div>
  </div>
</div>"""


def page(out_rel: str, title: str, body: str, active: str = "",
         desc: str = "", extra_head: str = "", body_attr: str = "") -> None:
    up = up_prefix(out_rel)
    root = up or "./"
    full_title = f"{title} · {BRAND}" if title else BRAND
    desc = desc or CFG.get("description", "")

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="{esc(AUTHOR)}">
<meta name="theme-color" content="#0b0b0f" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#fbfcfd" media="(prefers-color-scheme: light)">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<link rel="icon" href="{up}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{up}assets/css/main.css">
<link rel="stylesheet" href="{up}assets/css/highlight.css">
<script>try{{var t=localStorage.getItem('inkcode-theme');var d=t?t==='dark':window.matchMedia('(prefers-color-scheme: dark)').matches;if(d)document.documentElement.classList.add('dark');}}catch(e){{}}</script>
{extra_head}
</head>
<body data-root="{root}"{body_attr}>
<div class="shell">
{render_header(up, active)}
<div class="main">
{body}
</div>
{render_footer(up)}
</div>
{render_search_overlay()}
<button class="to-top" type="button" data-to-top aria-label="回到顶部" hidden>{icon('up')}</button>
<script src="{up}assets/js/search-index.js"></script>
<script src="{up}assets/js/main.js"></script>
</body>
</html>"""

    target = OUT / out_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(doc, encoding="utf-8")


def post_card(p: dict, up: str, delay: int = 0) -> str:
    tags = "".join(
        f'<a class="chip" href="{up}tags/{tag_dir(t)}/index.html">{esc(t)}</a>' for t in p["tags"]
    )
    return f"""<li class="fade-up" style="animation-delay:{delay}ms">
  <div class="post-card">
    <div class="post-card__body">
      <div class="post-card__top">
        <time datetime="{fmt_iso(p['date'])}">{fmt_date(p['date'])}</time>
        <span class="post-card__cat">{esc(p['category'])}</span>
      </div>
      <div class="post-card__row">
        <a class="post-card__link post-card__title" href="{up}{p['url']}index.html">{esc(p['title'])}</a>
        {icon('arrow-ur', 'post-card__arrow')}
      </div>
      <p class="post-card__summary">{esc(p['summary'])}</p>
      <div class="post-card__meta">
        <span>{icon('clock')}{p['minutes']} min</span>
        <span>{icon('globe')}{esc(p['lang'])}</span>
      </div>
      <div class="tag-row">{tags}</div>
    </div>
  </div>
</li>"""


def post_list(posts, up: str) -> str:
    if not posts:
        return '<div class="empty-state">这里还什么都没有。</div>'
    items = "".join(post_card(p, up, i * 45) for i, p in enumerate(posts))
    return f'<ul class="post-list">{items}</ul>'


# --------------------------------------------------------------------------
# 各页面
# --------------------------------------------------------------------------
def build_home(posts):
    up = ""
    newer = posts[:4]
    total_tags = len({t for p in posts for t in p["tags"]})
    years = sorted({p["date"].year for p in posts})
    projects = load_projects()
    featured = [p for p in projects if p.get("featured")][:3] or projects[:3]

    hero = CFG.get("hero", {})
    paragraphs = "".join(f"<p>{esc(x)}</p>" for x in hero.get("paragraphs", []))

    proj_cards = "".join(project_card(pr, up) for pr in featured)
    projects_section = (
        f"""<section class="home-section">
  <div class="section-head">
    <h2>{icon('folder')}项目</h2>
    <a href="projects/index.html">全部项目 →</a>
  </div>
  <div class="project-grid">{proj_cards}</div>
</section>"""
        if featured
        else ""
    )

    entries = [
        ("blog/index.html", "file", "博客",
         "技术笔记、项目复盘与随笔，按分类筛选，按标签检索。", "浏览全部文章"),
        ("projects/index.html", "folder", "项目",
         "做过与正在做的东西，每一个都留着对设计取舍的复盘。", "查看项目"),
        ("archives/index.html", "calendar", "归档",
         "按年份倒序排列的全部文章，适合没有目的地乱翻。", "按时间浏览"),
        ("tags/index.html", "tag", "标签",
         "从关键词进入，把同一主题下的内容一次读完。", "全部标签"),
    ]
    entry_cards = "".join(
        f"""  <a class="entry-card" href="{href}">
    <span class="entry-card__title">{icon(ic)} {esc(label)}</span>
    <span class="entry-card__desc">{esc(desc)}</span>
    <span class="entry-card__more">{esc(more)} {icon('arrow-r')}</span>
  </a>
"""
        for href, ic, label, desc, more in entries
    )

    body = f"""<section class="hero fade-up">
  <div class="hero__eyebrow"><span class="hero__dot"></span>{esc(CFG.get('tagline', ''))}</div>
  <h1>{esc(hero.get('title', CFG.get('description', '')))}</h1>
  {paragraphs}
  <div class="hero__stats">
    <div class="hero__stat"><b>{len(posts)}</b><span>篇文章</span></div>
    <div class="hero__stat"><b>{total_tags}</b><span>个标签</span></div>
    <div class="hero__stat"><b>{len(projects)}</b><span>个项目</span></div>
    <div class="hero__stat"><b>{len(years)}</b><span>年记录</span></div>
  </div>
</section>

<section class="home-section">
  <div class="section-head">
    <h2>{icon('spark')}从这里开始</h2>
    <span class="mono muted">{len(posts)} posts · {len(projects)} projects</span>
  </div>
  <div class="entry-grid">
{entry_cards}  </div>
</section>

<section class="home-section">
  <div class="section-head">
    <h2>{icon('clock')}最近更新</h2>
    <a href="blog/index.html">全部文章 →</a>
  </div>
  {post_list(newer, up)}
</section>

{projects_section}"""

    page("index.html", "", body, desc=CFG.get("description", ""))


def category_pages(posts) -> list:
    """实际会生成分类页的分类集合。build_blog / build_posts / main 都用它，
    避免文章 frontmatter 里的 category 不在配置里时链接到不存在的页面。"""
    return CATEGORIES or sorted({p["category"] for p in posts})


def categories_with_posts(posts) -> list:
    """只保留至少有 1 篇文章的分类，避免生成一堆空分类页和空筛选标签。"""
    return [c for c in category_pages(posts) if any(p["category"] == c for p in posts)]


def build_blog(posts, category=None):
    cats = categories_with_posts(posts)
    if category:
        filtered = [p for p in posts if p["category"] == category]
        base_dir = f"blog/category/{category}/"
        title = f"分类 · {category}"
        active_tab = category
    else:
        filtered = posts
        base_dir = "blog/"
        title = "博客"
        active_tab = None

    pages = max(1, (len(filtered) + PER_PAGE - 1) // PER_PAGE)

    tag_counts = {}
    for p in posts:
        for t in p["tags"]:
            tag_counts[t] = tag_counts.get(t, 0) + 1
    top_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))[:22]

    for page_no in range(1, pages + 1):
        chunk = filtered[(page_no - 1) * PER_PAGE: page_no * PER_PAGE]
        out_rel = f"{base_dir}index.html" if page_no == 1 else f"{base_dir}page/{page_no}/index.html"
        up = up_prefix(out_rel)

        tab_html = (
            f'<a class="filter-tab" href="{up}blog/index.html" '
            f'aria-current="{"true" if not active_tab else "false"}">全部</a>'
        )
        for c in cats:
            cur = "true" if active_tab == c else "false"
            tab_html += (
                f'<a class="filter-tab" href="{up}blog/category/{c}/index.html" '
                f'aria-current="{cur}">{esc(c)}</a>'
            )
        # 没有任何分类时不显示只有一个「全部」的筛选条
        tabs_block = f'<div class="filter-tabs">{tab_html}</div>' if cats else ""
        list_status = (
            f'<div class="list-status">'
            f"<span>第 {page_no} 页 · 共 {len(filtered)} 篇{'' if end == 0 else f'（{start}–{end}）'}</span>"
            f'<a href="{up}archives/index.html">按年份浏览 →</a></div>'
            if filtered
            else ""
        )

        pager = []
        if pages > 1:
            # 用 base_dir 而不是写死的 blog/，否则分类页翻页会串到全部文章
            prev_href = (
                f"{up}{base_dir}index.html" if page_no == 2
                else f"{up}{base_dir}page/{page_no - 1}/index.html"
            )
            next_href = f"{up}{base_dir}page/{page_no + 1}/index.html"
            pager.append(
                f'<a class="{"is-disabled" if page_no == 1 else ""}" '
                f'href="{prev_href if page_no > 1 else "#"}">← 上一页</a>'
            )
            pager.append(f"<span>{page_no} / {pages}</span>")
            pager.append(
                f'<a class="{"is-disabled" if page_no == pages else ""}" '
                f'href="{next_href if page_no < pages else "#"}">下一页 →</a>'
            )

        start = (page_no - 1) * PER_PAGE + 1
        end = min(page_no * PER_PAGE, len(filtered))

        if active_tab:
            trail = [("首页", "index.html"), ("博客", "blog/index.html")]
            trail.append((active_tab, f"{base_dir}index.html" if page_no > 1 else None))
        else:
            trail = [("首页", "index.html"), ("博客", "blog/index.html" if page_no > 1 else None)]
        if page_no > 1:
            trail.append((f"第 {page_no} 页", None))

        # 侧栏：没有标签/年份时整块不渲染，避免留下空壳
        sidebar_blocks = []
        if top_tags:
            sidebar_blocks.append(f"""<div class="sidebar-block">
      <h2>{icon('tag')}标签</h2>
      <div class="tag-cloud">
        {''.join(f'<a class="chip" href="{up}tags/{tag_dir(t)}/index.html">{esc(t)}</a>' for t, _ in top_tags)}
      </div>
      <a class="sidebar__foot" href="{up}tags/index.html">查看全部 →</a>
    </div>""")
        recent_years = sorted({p["date"].year for p in posts}, reverse=True)[:6]
        if recent_years:
            sidebar_blocks.append(f"""<div class="sidebar-block">
      <h2>{icon('calendar')}归档</h2>
      <div class="tag-cloud">
        {''.join(f'<a class="chip" href="{up}archives/index.html#{y}">{y}</a>' for y in recent_years)}
      </div>
    </div>""")
        sidebar_html = f'<aside class="sidebar">{"".join(sidebar_blocks)}</aside>' if sidebar_blocks else ""
        layout_cls = "blog-layout" if sidebar_blocks else "blog-layout blog-layout--full"

        body = f"""<div class="page-head">
  {crumbs(up, trail)}
  <h1 class="page-title">{esc(title)}</h1>
</div>
<div class="{layout_cls}">
  <section id="content">
    {tabs_block}
    {list_status}
    {post_list(chunk, up)}
    {f'<div class="pager">{"".join(pager)}</div>' if pager else ''}
  </section>
  {sidebar_html}
</div>"""

        page(out_rel, title if page_no == 1 else f"{title} · 第 {page_no} 页", body,
             active="blog", desc=f"{BRAND} 的全部文章：技术笔记、项目复盘与随笔。")


def build_posts(posts):
    cats = categories_with_posts(posts)
    for idx, p in enumerate(posts):
        out_rel = f"{p['url']}index.html"
        up = up_prefix(out_rel)
        newer = posts[idx - 1] if idx > 0 else None
        older = posts[idx + 1] if idx + 1 < len(posts) else None

        tags = "".join(
            f'<a class="chip" href="{up}tags/{tag_dir(t)}/index.html">{esc(t)}</a>' for t in p["tags"]
        )
        tag_links = " / ".join(
            f'<a href="{up}tags/{tag_dir(t)}/index.html">{esc(t)}</a>' for t in p["tags"]
        )

        updated = ""
        if p["updated"] and p["updated"] != p["date"]:
            updated = (
                f'<span class="muted">/ 更新于 <time datetime="{fmt_iso(p["updated"])}">'
                f'{fmt_date(p["updated"])}</time></span>'
            )

        nav_items = []
        if older:
            nav_items.append(
                f'<a href="{up}{older["url"]}index.html"><span class="dir">← 更早</span>'
                f'<span class="t">{esc(older["title"])}</span></a>'
            )
        if newer:
            nav_items.append(
                f'<a class="next" href="{up}{newer["url"]}index.html"><span class="dir">更新 →</span>'
                f'<span class="t">{esc(newer["title"])}</span></a>'
            )

        toc_html = ""
        if p["toc"] and p["toc"].count("toc-item") > 1:
            toc_html = f"""<aside class="post-toc">
  <div class="post-toc__label">目录 / Contents</div>
  {p['toc']}
</aside>"""

        trail = [("首页", "index.html"), ("博客", "blog/index.html")]
        trail.append((
            p["category"],
            f"blog/category/{p['category']}/index.html" if p["category"] in cats else None,
        ))
        trail.append((p["title"], None))

        body = f"""<div class="progress-bar"></div>
<div class="page-head">
  {crumbs(up, trail)}
</div>
<div class="post-layout">
  <article class="article">
    <header class="article-head">
      <div class="article-head__meta">
        <span>{icon('calendar')}<time datetime="{fmt_iso(p['date'])}">{fmt_date(p['date'])}</time>{updated}</span>
        <span>{icon('clock')}{p['minutes']} min</span>
        <span>{icon('globe')}{esc(p['lang'])}</span>
        <span>{icon('tag')}{tag_links}</span>
      </div>
      <h1 class="article-title">{esc(p['title'])}</h1>
      <div class="article-desc">{esc(p['summary'])}</div>
      <hr class="article-divider">
    </header>
    <div class="prose">{p['html']}</div>
    <div class="tag-row" style="margin-top:2.5rem">{tags}</div>
    <nav class="post-nav" aria-label="文章导航">{''.join(nav_items)}</nav>
  </article>
  {toc_html}
</div>"""

        page(out_rel, p["title"], body, active="blog", desc=p["summary"])


def build_archives(posts):
    up = up_prefix("archives/index.html")
    groups = {}
    for p in posts:
        groups.setdefault(p["date"].year, []).append(p)

    blocks = []
    for year in sorted(groups, reverse=True):
        items = groups[year]
        rows = "".join(
            f'<li><a class="archive-row" href="{up}{p["url"]}index.html">'
            f'<time datetime="{fmt_iso(p["date"])}">{p["date"].strftime("%m-%d")}</time>'
            f'<span class="t">{esc(p["title"])}</span>'
            f'<span class="c">{esc(p["category"])}</span></a></li>'
            for p in items
        )
        blocks.append(f"""<section class="archive-year" id="{year}">
  <h2 class="archive-year__label">{year}<span class="archive-year__count">{len(items)} POSTS</span></h2>
  <ul class="archive-list">{rows}</ul>
</section>""")

    if posts:
        summary_line = (
            f'<p class="muted" style="margin:-0.75rem 0 2.5rem;font-size:0.875rem">'
            f'共 {len(posts)} 篇文章，{len(groups)} 个年份。按时间倒序排列。</p>'
        )
        archive_body = "".join(blocks)
    else:
        summary_line = ""
        archive_body = '<div class="empty-state">还没有文章。写下的第一篇会出现在这里。</div>'

    body = f"""<div class="page-head">
  {crumbs(up, [("首页", "index.html"), ("归档", None)])}
  <h1 class="page-title">归档</h1>
</div>
{summary_line}
{archive_body}"""

    page("archives/index.html", "归档", body, active="archives",
         desc=f"{BRAND} 文章归档，按年份浏览。")


def build_tags(posts):
    counts = {}
    for p in posts:
        for t in p["tags"]:
            counts.setdefault(t, []).append(p)

    for tag, items in counts.items():
        up = up_prefix(f"tags/{tag_dir(tag)}/index.html")
        body = f"""<div class="page-head">
  {crumbs(up, [("首页", "index.html"), ("标签", "tags/index.html"), (tag, None)])}
  <h1 class="page-title">{esc(tag)}</h1>
</div>
<div class="list-status"><span>共 {len(items)} 篇文章</span></div>
{post_list(items, up)}"""
        page(f"tags/{tag_dir(tag)}/index.html", tag, body, active="tags",
             desc=f"标签「{tag}」下的全部文章。")

    cards = "".join(
        f'<a class="tag-card" href="{tag_dir(t)}/index.html">'
        f'<span>{esc(t)}</span><span class="n">{len(items)}</span></a>'
        for t, items in sorted(counts.items(), key=lambda x: (-len(x[1]), x[0]))
    )
    up = up_prefix("tags/index.html")
    if counts:
        count_line = (
            f'<p class="muted" style="margin:-0.75rem 0 2rem;font-size:0.875rem">'
            f"共 {len(counts)} 个标签</p>"
        )
        tag_body = f'<div class="tag-grid">{cards}</div>'
    else:
        count_line = ""
        tag_body = '<div class="empty-state">还没有标签。文章里写 <code>tags</code> 就会自动汇总到这里。</div>'

    body = f"""<div class="page-head">
  {crumbs(up, [("首页", "index.html"), ("标签", None)])}
  <h1 class="page-title">标签</h1>
</div>
{count_line}
{tag_body}"""
    page("tags/index.html", "标签", body, active="tags", desc=f"{BRAND} 的全部标签。")


# --------------------------------------------------------------------------
# 项目 / 关于
# --------------------------------------------------------------------------
def load_projects():
    path = CONTENT / "projects.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def project_card(pr: dict, up: str) -> str:
    tags = "".join(f'<span class="chip">{esc(t)}</span>' for t in pr.get("tags", []))
    status = pr.get("status", "")
    cls = "status--live" if status in ("已上线", "已完成", "已发布") else "status--wip"
    links = ""
    for label, href in (pr.get("links") or {}).items():
        links += (
            f'<a class="project-card__link" href="{href}" target="_blank" rel="noopener">'
            f'{esc(label)} {icon("arrow-ur")}</a>'
        )
    return f"""<article class="project-card fade-up">
  <div class="project-card__head">
    <h3 class="project-card__name">{icon('folder')}{esc(pr['name'])}</h3>
    {f'<span class="status {cls}">{esc(status)}</span>' if status else ''}
  </div>
  <p class="project-card__desc">{esc(pr.get('desc', ''))}</p>
  <div class="tag-row">{tags}</div>
  <div class="project-card__foot">{links}</div>
</article>"""


def build_projects():
    up = up_prefix("projects/index.html")
    projects = load_projects()
    if projects:
        intro = (
            '<p class="muted" style="margin:-0.75rem 0 2rem;font-size:0.875rem;max-width:38rem;line-height:1.8">'
            "做过的东西、正在做的东西，以及那些写完就再也没打开过的玩具。每一个都留有对设计取舍的复盘。</p>"
        )
        grid = f'<div class="project-grid">{"".join(project_card(pr, up) for pr in projects)}</div>'
    else:
        intro = ""
        grid = '<div class="empty-state">还没有项目记录。</div>'

    body = f"""<div class="page-head">
  {crumbs(up, [("首页", "index.html"), ("项目", None)])}
  <h1 class="page-title">项目</h1>
</div>
{intro}
{grid}"""
    page("projects/index.html", "项目", body, active="projects",
         desc=f"{BRAND} 的项目列表。")


def build_about():
    up = up_prefix("about/index.html")
    src = CONTENT / "about.md"
    raw = src.read_text(encoding="utf-8") if src.exists() else "# 关于\n\n这里还没写。"
    meta, body_md = parse_front(raw)
    md = make_md("xcode")
    html_body = md.convert(body_md)

    initial = (meta.get("avatarText") or BRAND)[:1]
    info = [
        ("身份", meta.get("role", "开发者 / 学生")),
        ("坐标", meta.get("city", "中国")),
        ("在做", meta.get("doing", "写代码、写字")),
        ("邮箱", meta.get("email", CFG.get("email", ""))),
    ]
    info_html = "".join(
        f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in info if v
    )

    body = f"""<div class="page-head">
  {crumbs(up, [("首页", "index.html"), ("关于", None)])}
  <h1 class="page-title">关于</h1>
</div>
<div class="about-grid">
  <div class="prose" style="margin-top:0">{html_body}</div>
  <aside class="about-side">
    <div class="avatar">{esc(initial)}</div>
    <dl class="info-list">{info_html}</dl>
    <a class="chip" href="{up}rss.xml">{icon('rss')} RSS 订阅</a>
  </aside>
</div>"""
    page("about/index.html", "关于", body, active="about",
         desc=meta.get("summary", f"关于 {AUTHOR}"))


def build_404():
    up = ""
    body = f"""<div style="padding:5rem 0;text-align:center">
  <div class="mono muted" style="letter-spacing:0.2em">ERROR 404</div>
  <h1 style="font-size:2rem;font-weight:500;margin:1rem 0 0.75rem">这一页不存在</h1>
  <p class="muted" style="margin-bottom:2rem">它可能被删掉了，或者链接里少了一个字。</p>
  <a class="chip" href="index.html">{icon('back')} 回到首页</a>
</div>"""
    page("404.html", "页面不存在", body)


# --------------------------------------------------------------------------
# 搜索索引 / RSS / 资源
# --------------------------------------------------------------------------
def build_search_index(posts):
    data = [
        {
            "title": p["title"],
            "url": p["url"] + "index.html",
            "path": p["url"],
            "summary": p["summary"],
            "tags": p["tags"],
            "category": p["category"],
            "date": p["date"].isoformat(),
            "text": p["text"],
        }
        for p in posts
    ]
    js = "window.SITE_SEARCH=" + json.dumps(data, ensure_ascii=False) + ";\n"
    (OUT / "assets" / "js").mkdir(parents=True, exist_ok=True)
    (OUT / "assets" / "js" / "search-index.js").write_text(js, encoding="utf-8")


def build_rss(posts):
    items = []
    for p in posts[:20]:
        link = f"{SITE_URL}/{p['url']}"
        items.append(f"""  <item>
    <title>{esc(p['title'])}</title>
    <link>{esc(link)}</link>
    <guid isPermaLink="true">{esc(link)}</guid>
    <pubDate>{p['date'].strftime('%a, %d %b %Y 00:00:00 +0800')}</pubDate>
    <description>{esc(p['summary'])}</description>
    {''.join(f'<category>{esc(t)}</category>' for t in p['tags'])}
  </item>""")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{esc(BRAND)}</title>
  <link>{esc(SITE_URL)}</link>
  <description>{esc(CFG.get('description', ''))}</description>
  <language>zh-CN</language>
  <atom:link href="{esc(SITE_URL)}/rss.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
</channel>
</rss>
"""
    (OUT / "rss.xml").write_text(xml, encoding="utf-8")


def build_highlight_css():
    light = HtmlFormatter(style="xcode").get_style_defs(".highlight")
    dark = HtmlFormatter(style="monokai").get_style_defs(".dark .highlight")
    # 去掉 pygments 自带的背景/前景，交由 main.css 控制
    light = re.sub(r"\.highlight\s*\{[^}]*\}", "", light)
    dark = re.sub(r"\.dark \.highlight\s*\{[^}]*\}", "", dark)
    css = (
        "/* generated by build.py — pygments token colors */\n"
        + light.strip()
        + "\n\n"
        + dark.strip()
        + "\n.dark .highlight .c, .dark .highlight .c1, .dark .highlight .cm { color: #75715e }\n"
    )
    (OUT / "assets" / "css" / "highlight.css").write_text(css, encoding="utf-8")


def copy_assets():
    target = OUT / "assets"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(ASSETS, target)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    posts = load_posts()
    build_home(posts)
    build_blog(posts)
    for cat in categories_with_posts(posts):
        build_blog(posts, category=cat)
    build_posts(posts)
    build_archives(posts)
    build_tags(posts)
    build_projects()
    build_about()
    build_404()
    build_rss(posts)
    copy_assets()
    build_highlight_css()
    build_search_index(posts)

    pages = sum(1 for _ in OUT.rglob("*.html"))
    print(f"✓ 构建完成：{len(posts)} 篇文章，{pages} 个页面 → {OUT}")

    port = parse_port()
    if "--serve" in sys.argv:
        serve(port)
    else:
        print(f"  预览：python build.py --serve   （或 python -m http.server {port} --directory dist）")


def parse_port(default: int = 8123) -> int:
    """支持 --port=8000 覆盖预览端口。"""
    for arg in sys.argv[1:]:
        if arg.startswith("--port="):
            try:
                return int(arg.split("=", 1)[1])
            except ValueError:
                pass
    return default


def serve(port: int) -> None:
    """构建后启动本地预览，Ctrl+C 退出。"""
    import functools
    import http.server
    import socketserver

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"  预览：http://localhost:{port}  （Ctrl+C 停止）")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  已停止。")


if __name__ == "__main__":
    main()

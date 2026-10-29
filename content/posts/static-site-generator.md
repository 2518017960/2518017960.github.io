---
title: 用两百行 Python 写一个静态站点生成器
date: 2026-10-06
updated: 2026-10-09
category: 技术笔记
tags: [Python, 静态站点, Markdown, 工具链]
summary: 不引入 SSG 框架，从 frontmatter 解析、Markdown 渲染到分页、标签、搜索索引，一套最小可用的构建流程。
lang: 中文
---

静态站点生成器听上去很唬人，其实核心只有一句话：**把一堆 Markdown 文件，变成一堆 HTML 文件**。

剩下的都是细节：怎么读元信息、怎么生成目录、怎么分页、怎么让搜索在没有后端的情况下工作。这篇记录我踩过的几个点。

## 一、frontmatter 不必用 YAML 库

绝大多数时候，你只需要很少的字段：

```markdown
---
title: 用两百行 Python 写一个静态站点生成器
date: 2026-10-06
category: 技术笔记
tags: [Python, 静态站点]
summary: 一句话摘要
---
```

为了让构建少一个依赖，我用 `partition` 手写解析，够用且可控：

```python
def parse_front(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        if not v:
            continue
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            meta[k.strip()] = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        else:
            meta[k.strip()] = v.strip("\"'")
    return meta, m.group(2)
```

注意 `re.S`。少了它，`.*?` 遇到第一行换行就停住，你会得到一个永远匹配不上的解析器，然后怀疑人生。

## 二、相对路径是最大的坑

静态站点通常部署在根目录，本地预览却常常是 `file://`。这意味着：

- 用 `/assets/css/main.css` → 本地打开白屏
- 用 `assets/css/main.css` → 深层页面 404

最稳的办法是**按输出深度算前缀**：

```python
def up_prefix(out_rel: str) -> str:
    depth = len(Path(out_rel).parts) - 1
    return "../" * depth
```

于是 `blog/foo/index.html` 的前缀是 `../../`，`index.html` 的前缀是空串。所有链接都写成 `f"{up}assets/css/main.css"`，本地和线上都不会错。

## 三、搜索没有后端怎么办

把索引编译成一个 JS 文件，直接 `window.SITE_SEARCH = [...]` 塞进去：

```python
data = [{
    "title": p["title"],
    "url": p["url"] + "index.html",
    "tags": p["tags"],
    "text": p["text"][:4000],   # 截断，避免索引过大
} for p in posts]
js = "window.SITE_SEARCH=" + json.dumps(data, ensure_ascii=False)
```

比起 `fetch('search.json')`，内联成 JS 的好处是：**双击 HTML 也能搜**。`fetch` 在 `file://` 下会被 CORS 拦掉，而 `<script>` 不会。

排序用最简单的加权打分就够了：

| 命中位置 | 权重 |
| --- | --- |
| 标题开头 | 100 |
| 标题中包含 | 60 |
| 标签 | 24 |
| 摘要 | 16 |
| 正文 | 8 |

## 四、代码高亮：让 Pygments 只负责颜色

`markdown` 的 `codehilite` 扩展会连背景色一起输出，很容易和你的主题打架。我直接把自带的那条规则删掉：

```python
light = HtmlFormatter(style="xcode").get_style_defs(".highlight")
light = re.sub(r"\.highlight\s*\{[^}]*\}", "", light)
```

`codehilite` 输出的是 `<div class="highlight"><pre>...`。我在运行时再包一层 `.code-block`，加一个"复制"按钮：

```javascript
document.querySelectorAll(".prose pre").forEach(function (pre) {
  var wrap = document.createElement("div");
  wrap.className = "code-block";
  pre.parentNode.insertBefore(wrap, pre);
  wrap.appendChild(pre);
});
```

> 用 JS 包裹的好处是：不写 JS 也能正常显示代码块，只是没有复制按钮。渐进增强比一次性渲染更抗退化。

## 五、构建时间

现在这个站点：

- 8 篇文章 → 18 个 HTML 页面
- 全量构建耗时约 **0.4 秒**
- 输出体积约 **600 KB**（其中一半是字体无关的 CSS 和搜索索引）

够用了。真的不够用的时候，再做增量构建——但大概率不会。

## 待办

- [x] frontmatter 解析
- [x] 分页与标签页
- [x] 客户端搜索
- [ ] 图片自动压缩（`Pillow`）
- [ ] 增量构建
- [ ] 把 TOC 生成从 `markdown` 手里接管，输出嵌套层级更准确的列表

---

最后一句经验：**先让它能跑，再让它好看**。我一开始想先把设计做好，结果两天过去了，一个页面都没生成出来。

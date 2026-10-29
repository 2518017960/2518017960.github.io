# 墨与代码 · Ink & Code

一个用来存放**技术学习日记、项目记录和随笔**的个人站点。
视觉与结构参考 [arthals.ink](https://arthals.ink/blog)：极简卡片列表、深浅双色、右侧浮动目录。

线上地址：**https://2518017960.github.io/**

- 纯静态：构建产物是一堆 HTML，没有数据库、没有后端
- 纯文本写作：内容全是 `content/posts/*.md`
- 零前端框架：一个 `build.py`（约 1000 行 Python）+ 一份手写 CSS，没有 npm、没有打包器
- 推上去就上线：`git push` 后 GitHub Actions 自动构建发布，约 40 秒生效
- 本地双击就能看：`dist/index.html` 可以直接用浏览器打开，不依赖服务器
  （所有站内链接都生成为显式 `index.html`，`file://` 协议下导航、标签、分类、上一篇/下一篇都能正常跳转）

---

## 一、目录结构

```text
.
├── site.config.json      站点配置：品牌名、导航、社交链接、分类、首页文案
├── build.py              构建脚本：Markdown → 静态 HTML
├── content/
│   ├── posts/            所有文章（一篇一个 .md）
│   │   └── _template.md  写作模板（draft: true，不参与构建）
│   ├── about.md          关于页
│   └── projects.json     项目列表（当前为空数组）
├── assets/               源文件：CSS / JS / favicon / 图片
├── .github/workflows/
│   └── deploy.yml        推 main 后自动构建并部署到 Pages
└── dist/                 构建产物（自动生成，已 git 忽略，不要手改）
```

## 二、写作流程

### 1. 写一篇新文章

复制 `content/posts/_template.md`，重命名成英文短横线形式，例如 `my-first-post.md`
—— 文件名就是 URL：`/blog/my-first-post/`。

改掉 frontmatter 里的占位值，然后把 `draft: true` 删掉（模板靠这一行跳过构建，
留着它文章就不会出现在站点上）。

正文里需要配图时，先建 `assets/img/` 目录（默认没有），把图片放进去，
用相对路径引用：`![说明](../../assets/img/xxx.png)`。

### 2. 本地预览

```bash
python build.py --serve          # 构建 + 起本地服务，打开 http://localhost:8123
```

换端口加 `--port=8000`。只想构建不启服务就用 `python build.py`。

或者更省事：直接双击 `dist/index.html`，链接一样能点通。

### 3. 发布

```bash
git add -A
git commit -m "新文章：xxx"
git push
```

推完 GitHub Actions 会自动装依赖、构建、发布，不用本地构建，也不要把 `dist/` 提交上去。

### frontmatter 字段

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `title` | 是 | 文章标题 |
| `date` | 是 | `YYYY-MM-DD`，用于排序与归档 |
| `category` | 是 | 必须是 `site.config.json` 里 `categories` 列出的值，否则不会生成对应分类页 |
| `tags` | 否 | `[标签一, 标签二]`，会自动生成标签页 |
| `summary` | 否 | 列表卡片上的摘要，缺省取正文前 110 字 |
| `updated` | 否 | 更新日期，会显示成「更新于 …」 |
| `lang` | 否 | 默认 `中文` |
| `draft` | 否 | `true` 时不参与构建 |

## 三、添加项目

`content/projects.json` 是一个数组，现在是空的（`[]`）。加一个项目就往里追加一项：

```json
[
  {
    "name": "项目名",
    "desc": "一句话说明它解决什么问题，会显示在卡片上。",
    "tags": ["Go", "CLI"],
    "status": "进行中",
    "featured": true,
    "links": { "GitHub": "https://github.com/you/repo" }
  }
]
```

- `name` 必填，其余可省略
- `status` 填 `已上线` / `已完成` / `已发布` 会显示成完成态样式，其他值一律按进行中渲染
- `featured: true` 的项目会出现在首页，首页最多取 3 个；一个都没有则退回显示前 3 个
- `links` 是「文案 → 地址」的映射，渲染成卡片底部的外链

项目为空时，项目页显示一句提示，首页的「项目」区块整块隐藏——不会留下空白格子。

## 四、改自己的信息

**`site.config.json`** —— 站点级：

```json
{
  "brand": "墨与代码",                   // 站点名（左上角）
  "brandEn": "Ink & Code",              // 站点名英文副标题
  "author": "Your Name",                // 页脚版权，还没改成真名
  "email": "you@example.com",
  "siteUrl": "https://2518017960.github.io",  // RSS 里的绝对地址
  "startYear": 2024,                    // 页脚年份区间起点
  "categories": ["技术笔记", "项目复盘", "随笔"],
  "postsPerPage": 6,
  "nav": [ /* 顶部导航，见下 */ ],
  "social": [ /* GitHub / 邮件 / RSS */ ],
  "hero": { /* 首页大标题与介绍段落 */ }
}
```

`nav` 的 `href` 写目录形式即可（`"blog/"`、`"tags/"`），构建时会自动补成
`blog/index.html`——这样直接用浏览器打开 `dist/index.html` 也不会点不动：

```json
"nav": [
  { "label": "博客", "href": "blog/" },
  { "label": "项目", "href": "projects/" },
  { "label": "归档", "href": "archives/" },
  { "label": "标签", "href": "tags/" },
  { "label": "关于", "href": "about/" }
]
```

**`content/about.md`** —— 关于页的自我介绍，frontmatter 里的 `name` / `role` / `city` /
`doing` / `email` 会渲染成右侧信息卡。

## 五、站点包含的功能

| 页面 | 路径 | 说明 |
| --- | --- | --- |
| 首页 | `/` | 介绍 + 分区入口（博客/项目/归档/标签）+ 最近更新 + 精选项目 + 统计 |
| 博客 | `/blog/` | 卡片列表、分类筛选、标签侧栏、分页 |
| 文章 | `/blog/<slug>/` | 阅读进度、右侧目录（滚动高亮）、上一篇/下一篇、代码复制 |
| 归档 | `/archives/` | 按年份分组的全部文章 |
| 标签 | `/tags/`、`/tags/<tag>/` | 标签云与单标签列表 |
| 项目 | `/projects/` | 项目卡片、状态标签、仓库链接 |
| 关于 | `/about/` | Markdown 渲染 + 信息卡 |
| 搜索 | 任意页 `Ctrl/Cmd + K` 或 `/` | 客户端全文搜索，标题加权 |
| RSS | `/rss.xml` | 最近 20 篇 |

除首页外每个页面都有面包屑（`首页 / 博客 / 技术笔记 / 标题`），层级一目了然。

几点构建规则：

- **分类页只给有文章的分类生成**。配置里保留着 `技术笔记` / `项目复盘` / `随笔` 三个分类，
  但某个分类一篇文章都没有时，不会生成对应页面，博客页的分类筛选条也只显示有内容的分类。
- **内容为空时显示提示而不是空壳**。文章、标签、项目、归档为空时各自有一句提示；
  空侧栏、空筛选条、空统计行会整块不渲染。

其他：深浅色主题（跟随系统 + 手动切换 + `localStorage` 记忆）、移动端抽屉菜单、回到顶部、`prefers-reduced-motion` 适配。

## 六、部署

线上跑的是 GitHub Pages + Actions，**已启用**，地址 https://2518017960.github.io/ 。
流水线在 `.github/workflows/deploy.yml`：推 `main` → `pip install markdown pygments` →
`python build.py` → 把 `dist/` 作为 Pages 产物发布。

流水线里的 `SITE_URL` 环境变量会按仓库地址自动算出真实域名并注入构建，
所以 RSS 里的链接不会指向 `example.com`；本地构建时则回落到 `site.config.json` 的 `siteUrl`。

如果哪天要换仓库或重新启用：在 **Settings → Pages → Build and deployment → Source**
选 **GitHub Actions**，然后在 **Actions** 页面点 **Run workflow** 手动触发一次。

其他托管方式同样可用（`dist/` 是纯静态目录）：

- **Vercel / Netlify**：构建命令 `python build.py`，输出目录 `dist`
- **自己的服务器**：`rsync dist/ user@host:/var/www/blog/`

> 如果部署在子路径（如 `user.github.io/blog/`），`site.config.json` 的 `siteUrl` 要写成带子路径的形式。
> 站内链接全部是相对路径，所以换路径不会导致链接失效，只有 RSS 里的绝对地址需要注意。

## 七、依赖

```bash
pip install markdown pygments
```

本地 Python 3.9+ 即可；CI 里用的是 Python 3.12。

## 八、想继续改的话

- 换配色：只改 `assets/css/main.css` 顶部的 `:root` 和 `.dark` 里的 HSL 三个数
- 换首页文案：`site.config.json` 的 `hero`
- 加评论：接 Giscus / Waline（需要一个外部服务）
- 加图片压缩、增量构建：在 `build.py` 里加函数即可，结构已经留好了

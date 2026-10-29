# 墨与代码 · Ink & Code

一个用来存放**技术学习日记、项目记录和随笔**的个人站点。
视觉与结构参考 [arthals.ink](https://arthals.ink/blog)：极简卡片列表、深浅双色、右侧浮动目录。

- 纯静态：构建产物是一堆 HTML，没有数据库、没有后端
- 纯文本写作：内容全是 `content/posts/*.md`
- 零前端框架：只有一个 `build.py` 和一个 ~350 行的 CSS
- 本地双击就能看：`dist/index.html` 可以直接用浏览器打开，不依赖服务器
  （所有站内链接都生成为显式 `index.html`，`file://` 协议下导航、标签、分类、上一篇/下一篇都能正常跳转）

---

## 一、目录结构

```text
.
├── site.config.json      站点配置：品牌名、导航、社交链接、首页文案
├── build.py              构建脚本：Markdown → 静态 HTML
├── content/
│   ├── posts/            所有文章（一篇一个 .md）
│   ├── about.md          关于页
│   └── projects.json     项目列表
├── assets/               源文件：CSS / JS / favicon / 图片
└── dist/                 构建产物（自动生成，不要手改）
```

## 二、写作流程

1. 复制 `content/posts/_template.md`，重命名成英文短横线形式，例如 `my-first-post.md`
   （文件名就是 URL：`/blog/my-first-post/`）
2. 改 frontmatter，把 `draft: true` 删掉
3. 写正文。需要配图就先建 `assets/img/` 目录，把图片放进去，正文里用
   `![alt](../../assets/img/xxx.png)` 引用
4. 运行构建：

```bash
python build.py
```

5. 预览（任选一种）：

```bash
python -m http.server 8123 --directory dist   # 然后打开 http://localhost:8123
```

或者直接双击 `dist/index.html`。

### frontmatter 字段

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `title` | 是 | 文章标题 |
| `date` | 是 | `YYYY-MM-DD`，用于排序与归档 |
| `category` | 是 | `技术笔记` / `项目复盘` / `随笔`（可在配置里改） |
| `tags` | 否 | `[标签一, 标签二]`，会生成对应的标签页 |
| `summary` | 否 | 列表卡片上的摘要，缺省取正文前 110 字 |
| `updated` | 否 | 更新日期，会显示成「更新于 …」 |
| `lang` | 否 | 默认 `中文` |
| `draft` | 否 | `true` 时不参与构建 |

## 三、改自己的信息

全站的个人信息都在两个地方：

**`site.config.json`** —— 站点级：

```json
{
  "brand": "墨与代码",          // 站点名（左上角）
  "brandEn": "Ink & Code",     // 站点名英文副标题
  "author": "Your Name",       // 页脚版权
  "email": "you@example.com",
  "siteUrl": "https://example.com",  // 部署后用真域名，RSS 需要
  "startYear": 2024,           // 页脚年份区间起点
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

**`content/about.md`** —— 关于页的自我介绍（frontmatter 里的 `name`/`role`/`city` 会渲染到右侧信息卡）。

**`content/projects.json`** —— 项目列表，`featured: true` 的项目会出现在首页。

## 四、站点包含的功能

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

其他：深浅色主题（跟随系统 + 手动切换 + `localStorage` 记忆）、移动端抽屉菜单、回到顶部、`prefers-reduced-motion` 适配。

## 五、部署

仓库里已经带了一条 GitHub Actions 流水线（`.github/workflows/deploy.yml`）：
推到 `main` 分支就自动 `pip install markdown pygments` → `python build.py` → 发布 `dist/` 到 Pages。
**不需要在本机构建，也不需要提交 `dist/`**（已在 `.gitignore` 里）。

首次启用（只需做一次）：

1. 在 GitHub 仓库的 **Settings → Pages → Build and deployment → Source** 选 **GitHub Actions**
2. 推一次代码，或在 **Actions** 页面点 **Run workflow** 手动触发
3. 等流水线变绿，访问 `https://<用户名>.github.io`

流水线里的 `SITE_URL` 环境变量会按仓库地址自动算出真实域名并注入构建，
所以 RSS 里的链接不会指向 `example.com`；本地构建时则回落到 `site.config.json` 的 `siteUrl`。

其他托管方式同样可用（`dist/` 是纯静态目录）：

- **Vercel / Netlify**：构建命令 `python build.py`，输出目录 `dist`
- **自己的服务器**：`rsync dist/ user@host:/var/www/blog/`

> 如果部署在子路径（如 `user.github.io/blog/`），`site.config.json` 的 `siteUrl` 要写成带子路径的形式。
> 站内链接全部是相对路径，所以换路径不会导致链接失效，只有 RSS 里的绝对地址需要注意。

## 六、依赖

```bash
pip install markdown pygments
```

Python 3.9+ 即可。

## 七、想继续改的话

- 换配色：只改 `assets/css/main.css` 顶部的 `:root` 和 `.dark` 里的 HSL 三个数
- 换首页文案：`site.config.json` 的 `hero`
- 加评论：接 Giscus / Waline（需要一个外部服务）
- 加图片压缩、增量构建：在 `build.py` 里加函数即可，结构已经留好了

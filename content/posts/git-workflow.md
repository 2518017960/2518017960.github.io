---
title: 我的 Git 工作流：三种分支，足够用了
date: 2026-09-08
category: 技术笔记
tags: [Git, 工程实践, 协作]
summary: 放弃 Git Flow 之后，我把分支模型砍到三个：main、dev、feat/*。这套规则在小团队和个人项目里几乎不用思考。
lang: 中文
---

Git Flow 有五种分支、两条长期线、一套发布流程。它设计于 2010 年，目标客户是「每年发布两次、需要维护多个历史版本」的桌面软件。

而我的项目通常是：一个人写，偶尔两个人，一周发好几次。

用 Git Flow 就像开卡车去买菜。于是我砍成了三个分支。

## 一、三个分支各自的职责

| 分支 | 存活时间 | 规则 |
| --- | --- | --- |
| `main` | 永久 | 永远可部署。只能通过 PR / merge 进入 |
| `dev` | 永久 | 集成分支，允许多次小提交 |
| `feat/xxx` | 数小时到数天 | 一件事一个分支，合并后立刻删除 |

流程短得可以背下来：

```bash
git switch dev && git pull --ff-only
git switch -c feat/search-index
# ... 写代码 ...
git commit -m "feat(search): 支持标题加权排序"
git switch dev
git merge --no-ff feat/search-index
git branch -d feat/search-index
git push origin dev
```

## 二、为什么保留 `dev`

有人会问：一个人开发还要 `dev` 吗？

要。因为 `dev` 是**你的缓冲带**。`main` 上任何一次提交心里默认"这是线上版本"，这种心理压力会让你不敢提交半成品。而 `dev` 允许你一天提交八次"wip"。

> 分支模型的价值不在于分支本身，而在于它给每个提交赋予了不同的心理契约。

## 三、提交信息用 Conventional Commits

```text
feat(search): 支持标题加权排序
fix(toc): 中文标题锚点重复导致跳转错位
docs: 补充构建方式说明
refactor(css): 把颜色收敛为设计令牌
chore: 升级 markdown 到 3.11
```

好处不只是好看：

- `git log --oneline | grep '^fix'` 就能列出所有修 Bug 的提交
- 生成 changelog 时不用再猜哪条是功能、哪条是重构
- 三个月后回来看，能立刻知道"这次改动的影响面"

## 四、几个救命命令

**改错提交信息**（还没推）：

```bash
git commit --amend
```

**把零散提交压成一个**（合并前整理）：

```bash
git rebase -i HEAD~3
```

**找回误删的分支**：

```bash
git reflog            # 找到那串 hash
git switch -c recover <hash>
```

**只想看某个文件的历史**：

```bash
git log --oneline -p -- content/posts/hello.md
```

`reflog` 这个命令我建议每个人都记一下。Git 几乎不真的删东西，只要 `reflog` 还在，犯了错就有退路。

## 五、`.gitignore` 的第一行

```gitignore
dist/
__pycache__/
.DS_Store
```

构建产物不进仓库。它可以从源码重新生成，提交进去只会让 diff 变成噪音。

同理，任何**能生成的东西**都不该手动维护：依赖锁文件要提交，构建结果不要。

## 六、什么时候该换更复杂的模型

三个分支不是银弹。出现下面这些情况，就该加规则了：

- 需要同时维护多个线上版本 → 加 `release/*`
- 有 QA 环境和灰度发布 → 引入环境分支
- 团队超过五人、每天大量合并 → 考虑 trunk-based + 特性开关

但在那之前，简单的模型就是最好的模型。

---

最后一条经验：**分支不是越多越专业，而是越少越省心**。真正让人痛苦的不是合并冲突，是每天要想"我这个改动该提到哪个分支"。

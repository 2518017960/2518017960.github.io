---
title: 我的终端配置：够用、可复制、不折腾
date: 2026-06-30
category: 技术笔记
tags: [工具链, 命令行, 效率]
summary: 一份能在五分钟内配好、五年不用大改的终端方案：zsh + starship + 四个 alias，仅此而已。
lang: 中文
---

我见过把终端配成艺术品的人。他们的 `~/.zshrc` 有八百行，装了十七个插件，启动要一秒半。

我也曾是其中一员。现在我的配置文件不到六十行。

## 一、原则

1. **启动要快。** 打开终端到能输入命令，不超过 100 毫秒。
2. **配置可复制。** 换一台机器，五分钟内恢复。
3. **不装需要"维护"的东西。** 插件越少，越不容易在某次升级后集体崩掉。

## 二、shell 与提示符

`zsh` + `starship`。starship 是单二进制，跨平台，配置就是一个 `toml`：

```toml
# ~/.config/starship.toml
format = """
$directory$git_branch$git_status$python$nodejs
$character"""

[directory]
truncation_length = 3
style = "bold cyan"

[git_branch]
format = "[$branch]($style) "
style = "purple"

[character]
success_symbol = "[❯](bold green)"
error_symbol = "[❯](bold red)"
```

效果：当前目录、Git 分支与状态、当前语言版本，一行内看完。

## 三、四个 alias

```bash
alias ll='eza -la --git --group-directories-first'
alias gs='git status -sb'
alias gc='git commit -m'
alias ..='cd ..'
```

我不再写复杂函数。经验是：**凡是需要三个月才能记住的别名，都不该存在**。

## 四、几个真正提升效率的工具

| 工具 | 替代 | 为什么值得 |
| --- | --- | --- |
| `eza` | `ls` | 彩色、显示 Git 状态、树形 |
| `ripgrep` | `grep` | 快一个数量级，默认忽略 `.gitignore` |
| `fd` | `find` | 语法短，默认行为合理 |
| `fzf` | 手动翻历史 | `Ctrl+R` 模糊搜索命令历史 |
| `bat` | `cat` | 语法高亮 + 行号 |

装了这五个，我在终端里按方向键的次数少了一大半。

## 五、历史记录的两个设置

```bash
HISTSIZE=50000
SAVEHIST=50000
setopt HIST_IGNORE_ALL_DUPS
setopt SHARE_HISTORY
```

`SHARE_HISTORY` 让多个终端窗口共享历史——这个功能我用了三年，回不去了。

## 六、不要做的事

- **不要用花哨的主题。** 提示符占两行、带二十个图标，只会挤掉你真正要看的内容。
- **不要装自动补全全家桶。** 补全建议在你不确定的时候有用，在你很确定的时候是干扰。
- **不要为了配终端而配终端。** 这是最容易逃避正事的方式之一，我深有体会。

---

配置在这里的意义不是"好看"，是**让手不用离开键盘**。凡是需要摸鼠标的动作，都值得花十分钟优化一次——但只优化一次。

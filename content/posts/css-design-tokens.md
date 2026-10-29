---
title: 设计令牌：让深浅色主题不再靠硬编码
date: 2026-09-24
category: 技术笔记
tags: [CSS, 设计系统, 前端]
summary: 用 HSL 三段值 + CSS 变量管理配色，一处改动就能整体换肤，顺便解决深色模式下对比度不够的老问题。
lang: 中文
---

以前我做深色模式的方式很粗暴：写两套颜色，再用 `.dark` 选择器覆盖一遍。页面一多就崩了——总有几个地方忘了改，深色下白得刺眼。

后来我把颜色收敛成一套**令牌（design tokens）**，问题就消失了。

## 一、颜色只写一次，用 HSL 三段值

关键点是：变量里存的是 `200 29% 45%` 这种**不带 `hsl()` 的三段值**，而不是 `#6b8f9e`。

```css
:root {
  --primary: 200 29% 45%;
  --foreground: 240 10% 3.9%;
  --background: 210 33% 99%;
  --muted: 240 4.8% 96%;
  --border: 240 5.9% 88%;
}

.dark {
  --primary: 195 95% 85%;
  --foreground: 0 0% 98%;
  --background: 240 20.54% 5.2%;
  --muted: 240 5.9% 13%;
  --border: 240 3.7% 22.9%;
}
```

为什么这么做？因为你终于可以自由地加透明度了：

```css
.chip { background: hsl(var(--muted)); }
.chip:hover { background: hsl(var(--primary) / 0.12); }
.glow { background: hsl(var(--primary) / 0.06); }
```

如果变量里存的是完整色值，`hsl(var(--primary) / 0.12)` 这种写法就直接失效了。这一条几乎是我这套体系里最有价值的收益。

## 二、语义化命名，而不是"颜色名"

不要叫 `--light-blue`，因为深色模式下它可能变成浅青色。要叫**用途**：

| 令牌 | 用途 |
| --- | --- |
| `--background` | 页面底色 |
| `--foreground` | 正文文字 |
| `--muted` | 次级区域、悬停底色 |
| `--muted-foreground` | 次要文字、日期、注释 |
| `--border` | 所有分割线与卡片描边 |
| `--primary` | 强调色：链接、高亮、选中态 |

好处是深色模式只需重写这些值，**组件 CSS 一行都不用动**。

## 三、深色模式的两个坑

**第一坑：纯黑背景。** `#000` 在大屏上会让文字边缘产生光晕感，盯着累。用 `hsl(240 20% 5.2%)` 这种带一点蓝的近黑，观感舒服很多。

**第二坑：主色对比度不够。** 浅色模式下的主色（中低明度的蓝）放到深色背景上几乎看不见。深色模式必须把主色的明度拉到 85% 以上：

```css
:root { --primary: 200 29% 45%; }   /* 浅色：中等明度 */
.dark { --primary: 195 95% 85%; }   /* 深色：高明度、高饱和 */
```

这不是审美问题，是**可读性下限**问题。

## 四、切换时不闪白

用户存了深色偏好，但页面加载瞬间还是白底一闪——因为 JS 在 `<body>` 之后才执行。

解决办法是在 `<head>` 里同步执行一小段脚本：

```html
<script>
try {
  var t = localStorage.getItem('theme');
  var dark = t ? t === 'dark'
               : window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (dark) document.documentElement.classList.add('dark');
} catch (e) {}
</script>
```

注意 `try/catch`：隐私模式下访问 `localStorage` 会直接抛错。

## 五、别忘了 `color-scheme`

```css
:root { color-scheme: light; }
.dark { color-scheme: dark; }
```

这一行会让浏览器自带的滚动条、表单控件、`<input>` 的默认样式跟着变。少写这一行，深色模式下输入框会白得像个补丁。

## 小结

整套思路其实只有三条：

1. 变量存 **HSL 三段值**，不存完整色值；
2. 令牌按**用途**命名，不按颜色命名；
3. 深色模式**只覆盖令牌**，不覆盖组件。

做完这三件事，你会发现"加一个主题"从一次重构变成了十行 CSS。

> 顺带一提，本站的配色就是照这个思路做的。想看看效果？点右上角的月亮。

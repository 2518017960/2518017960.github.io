/* ==========================================================================
   Ink & Code — 站点交互
   主题切换 / 吸顶导航 / 移动菜单 / 搜索 / 代码复制 / 目录高亮 / 阅读进度
   ========================================================================== */
(function () {
  "use strict";

  var root = document.documentElement;

  /* ---------- 主题 ---------- */
  var STORAGE_KEY = "inkcode-theme";

  function applyTheme(theme) {
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    var icons = document.querySelectorAll("[data-theme-icon]");
    for (var i = 0; i < icons.length; i++) {
      icons[i].hidden = icons[i].getAttribute("data-theme-icon") !==
        (theme === "dark" ? "sun" : "moon");
    }
  }

  function currentTheme() {
    return root.classList.contains("dark") ? "dark" : "light";
  }

  var stored = null;
  try {
    stored = localStorage.getItem(STORAGE_KEY);
  } catch (e) {}

  applyTheme(
    stored ||
      (window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light")
  );

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-toggle-theme]");
    if (!btn) return;
    var next = currentTheme() === "dark" ? "light" : "dark";
    applyTheme(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch (err) {}
  });

  /* ---------- 吸顶导航 / 移动菜单 ---------- */
  var header = document.querySelector(".site-header");

  function onScroll() {
    if (header) {
      header.classList.toggle("is-scrolled", window.scrollY > 12);
    }
    updateProgress();
    spyToc();
    toggleToTop();
  }

  document.addEventListener("click", function (e) {
    var menuBtn = e.target.closest("[data-toggle-menu]");
    if (menuBtn && header) {
      header.classList.toggle("nav-open");
      menuBtn.setAttribute(
        "aria-expanded",
        header.classList.contains("nav-open") ? "true" : "false"
      );
      return;
    }
    if (header && !e.target.closest(".site-header")) {
      header.classList.remove("nav-open");
    }
  });

  /* ---------- 阅读进度 ---------- */
  var bar = document.querySelector(".progress-bar");
  var article = document.querySelector(".prose");

  function updateProgress() {
    if (!bar || !article) return;
    var rect = article.getBoundingClientRect();
    var total = rect.height - window.innerHeight + 200;
    var done = Math.min(Math.max(-rect.top + 120, 0), Math.max(total, 1));
    bar.style.width = (done / Math.max(total, 1)) * 100 + "%";
  }

  /* ---------- 回到顶部 ---------- */
  var topBtn = document.querySelector("[data-to-top]");

  function toggleToTop() {
    if (!topBtn) return;
    topBtn.hidden = window.scrollY < 600;
  }

  if (topBtn) {
    topBtn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /* ---------- 目录高亮 ---------- */
  var tocLinks = [].slice.call(document.querySelectorAll(".toc-item"));
  var headings = tocLinks
    .map(function (a) {
      var id = decodeURIComponent(a.getAttribute("href").slice(1));
      var el = document.getElementById(id);
      return el ? { el: el, link: a } : null;
    })
    .filter(Boolean);

  function spyToc() {
    if (!headings.length) return;
    var offset = 120;
    var active = headings[0];
    for (var i = 0; i < headings.length; i++) {
      if (headings[i].el.getBoundingClientRect().top - offset <= 0) {
        active = headings[i];
      } else {
        break;
      }
    }
    for (var j = 0; j < headings.length; j++) {
      headings[j].link.classList.toggle("is-active", headings[j] === active);
    }
  }

  /* ---------- 代码复制 ---------- */
  document.querySelectorAll(".prose pre").forEach(function (pre) {
    var wrap = document.createElement("div");
    wrap.className = "code-block";
    pre.parentNode.insertBefore(wrap, pre);
    wrap.appendChild(pre);

    var btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.type = "button";
    btn.textContent = "copy";
    btn.addEventListener("click", function () {
      var code = pre.querySelector("code") || pre;
      var text = code.innerText;
      var done = function () {
        btn.textContent = "copied";
        btn.classList.add("is-done");
        setTimeout(function () {
          btn.textContent = "copy";
          btn.classList.remove("is-done");
        }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () {});
      } else {
        var ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        try {
          document.execCommand("copy");
          done();
        } catch (e) {}
        document.body.removeChild(ta);
      }
    });
    wrap.appendChild(btn);
  });

  /* ---------- 站内搜索 ---------- */
  var overlay = document.querySelector(".search-overlay");
  var input = overlay ? overlay.querySelector("input") : null;
  var resultsBox = overlay ? overlay.querySelector(".search-results") : null;
  var index = window.SITE_SEARCH || [];
  var rootPath = document.body.getAttribute("data-root") || "./";

  function escapeHtml(s) {
    return s.replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function highlight(text, q) {
    if (!q) return escapeHtml(text);
    var i = text.toLowerCase().indexOf(q.toLowerCase());
    if (i < 0) return escapeHtml(text);
    return (
      escapeHtml(text.slice(0, i)) +
      "<mark>" +
      escapeHtml(text.slice(i, i + q.length)) +
      "</mark>" +
      escapeHtml(text.slice(i + q.length))
    );
  }

  function score(item, q) {
    var t = item.title.toLowerCase();
    var s = (item.summary || "").toLowerCase();
    var g = (item.tags || []).join(" ").toLowerCase();
    var c = (item.text || "").toLowerCase();
    var v = 0;
    if (t.indexOf(q) > -1) v += 60 - Math.min(t.indexOf(q), 20);
    if (t.indexOf(q) === 0) v += 40;
    if (g.indexOf(q) > -1) v += 24;
    if (s.indexOf(q) > -1) v += 16;
    if (c.indexOf(q) > -1) v += 8;
    return v;
  }

  var activeIndex = -1;

  function renderResults(items, q) {
    if (!resultsBox) return;
    if (!q) {
      resultsBox.innerHTML =
        '<div class="search-empty">输入关键词搜索标题、摘要、标签与正文</div>';
      activeIndex = -1;
      return;
    }
    if (!items.length) {
      resultsBox.innerHTML =
        '<div class="search-empty">没有找到与「' +
        escapeHtml(q) +
        "」相关的内容</div>";
      activeIndex = -1;
      return;
    }
    resultsBox.innerHTML = items
      .map(function (it, i) {
        return (
          '<a class="search-result" data-i="' +
          i +
          '" href="' +
          rootPath +
          it.url +
          '">' +
          '<div class="search-result__t">' +
          highlight(it.title, q) +
          "</div>" +
          '<div class="search-result__m">' +
          it.date +
          " · " +
          escapeHtml(it.category || "") +
          "</div></a>"
        );
      })
      .join("");
    activeIndex = -1;

    resultsBox.querySelectorAll(".search-result").forEach(function (a) {
      a.addEventListener("click", function () {
        overlay.classList.remove("is-open");
      });
    });
  }

  function runSearch(q) {
    var query = q.trim();
    if (!query) return renderResults([], "");
    var items = index
      .map(function (it) {
        return { it: it, s: score(it, query.toLowerCase()) };
      })
      .filter(function (x) {
        return x.s > 0;
      })
      .sort(function (a, b) {
        return b.s - a.s;
      })
      .slice(0, 12)
      .map(function (x) {
        return x.it;
      });
    renderResults(items, query);
  }

  function openSearch() {
    if (!overlay) return;
    overlay.classList.add("is-open");
    document.body.style.overflow = "hidden";
    if (input) {
      input.value = "";
      input.focus();
    }
    renderResults([], "");
  }

  function closeSearch() {
    if (!overlay) return;
    overlay.classList.remove("is-open");
    document.body.style.overflow = "";
  }

  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-open-search]")) {
      e.preventDefault();
      openSearch();
      return;
    }
    if (e.target === overlay || e.target.closest("[data-close-search]")) {
      closeSearch();
    }
  });

  if (input) {
    input.addEventListener("input", function () {
      runSearch(input.value);
    });
    input.addEventListener("keydown", function (e) {
      var nodes = resultsBox.querySelectorAll(".search-result");
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        if (!nodes.length) return;
        activeIndex += e.key === "ArrowDown" ? 1 : -1;
        if (activeIndex < 0) activeIndex = nodes.length - 1;
        if (activeIndex >= nodes.length) activeIndex = 0;
        nodes.forEach(function (n, i) {
          n.classList.toggle("is-active", i === activeIndex);
        });
        nodes[activeIndex].scrollIntoView({ block: "nearest" });
      } else if (e.key === "Enter" && activeIndex > -1 && nodes[activeIndex]) {
        window.location.href = nodes[activeIndex].getAttribute("href");
      }
    });
  }

  document.addEventListener("keydown", function (e) {
    var tag = (e.target.tagName || "").toLowerCase();
    var typing = tag === "input" || tag === "textarea";
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      openSearch();
    } else if (e.key === "/" && !typing) {
      e.preventDefault();
      openSearch();
    } else if (e.key === "Escape") {
      closeSearch();
      if (header) header.classList.remove("nav-open");
    }
  });

  /* ---------- 滚动监听 ---------- */
  var ticking = false;
  window.addEventListener(
    "scroll",
    function () {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(function () {
        onScroll();
        ticking = false;
      });
    },
    { passive: true }
  );

  onScroll();
  spyToc();
})();

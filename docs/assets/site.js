document.addEventListener("DOMContentLoaded", () => {
  const articleHero = document.querySelector(".article-hero");
  const heroTitle = articleHero?.querySelector("h1");
  const body = document.body;

  if (articleHero && heroTitle && body.classList.contains("article-body")) {
    const updateReadingState = () => {
      const collapseAfter = Math.min(96, Math.max(40, articleHero.offsetHeight * 0.22));
      body.classList.toggle("is-reading", window.scrollY > collapseAfter);
    };

    updateReadingState();
    document.addEventListener("scroll", updateReadingState, { passive: true });
    window.addEventListener("resize", updateReadingState);
  }

  const progressBar = document.querySelector(".reading-progress-bar");
  if (progressBar) {
    const updateProgress = () => {
      const scrollTop = window.scrollY;
      const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
      const ratio = scrollHeight > 0 ? Math.min(scrollTop / scrollHeight, 1) : 0;
      progressBar.style.width = `${ratio * 100}%`;
    };

    updateProgress();
    document.addEventListener("scroll", updateProgress, { passive: true });
    window.addEventListener("resize", updateProgress);
  }

  document.querySelectorAll(".demo-box").forEach((box) => {
    const pre = box.querySelector(".demo-command");
    if (!pre) return;

    const wrapper = document.createElement("div");
    wrapper.className = "demo-command-wrapper";
    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(pre);

    const btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.setAttribute("aria-label", "复制命令");
    btn.textContent = "复制";
    wrapper.appendChild(btn);

    btn.addEventListener("click", () => {
      const text = (pre.querySelector("code") || pre).innerText;
      navigator.clipboard.writeText(text).then(() => {
        btn.textContent = "✓ 已复制";
        btn.classList.add("is-copied");
        setTimeout(() => {
          btn.textContent = "复制";
          btn.classList.remove("is-copied");
        }, 2000);
      });
    });
  });

  const tocLinks = [...document.querySelectorAll(".toc-link[href^='#']")];
  if (!tocLinks.length) {
    return;
  }

  const sectionMap = tocLinks
    .map((link) => {
      const id = link.getAttribute("href").slice(1);
      const section = document.getElementById(id);
      return section ? { link, section } : null;
    })
    .filter(Boolean);

  if (!sectionMap.length) {
    return;
  }

  const activateLink = (activeId) => {
    for (const { link, section } of sectionMap) {
      link.classList.toggle("is-active", section.id === activeId);
    }
  };

  const observer = new IntersectionObserver(
    (entries) => {
      const visibleSections = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);

      if (visibleSections.length) {
        activateLink(visibleSections[0].target.id);
      }
    },
    {
      rootMargin: "-18% 0px -65% 0px",
      threshold: [0, 1],
    }
  );

  for (const { section } of sectionMap) {
    observer.observe(section);
  }

  activateLink(sectionMap[0].section.id);
});

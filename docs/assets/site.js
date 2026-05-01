document.addEventListener("DOMContentLoaded", () => {
  const VIEW_MODE_KEY = "nanoagent-view-mode";
  const DEFAULT_MODE = "teacher";
  const root = document.documentElement;
  const body = document.body;
  const modeButtons = [...document.querySelectorAll("[data-view-mode-option]")];

  const setViewMode = (mode) => {
    const nextMode = mode === "shared" ? "shared" : DEFAULT_MODE;
    root.dataset.viewMode = nextMode;
    body.dataset.viewMode = nextMode;
    window.localStorage.setItem(VIEW_MODE_KEY, nextMode);

    for (const button of modeButtons) {
      const isActive = button.dataset.viewModeOption === nextMode;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", String(isActive));
    }
  };

  const savedMode = window.localStorage.getItem(VIEW_MODE_KEY) || DEFAULT_MODE;
  setViewMode(savedMode);

  for (const button of modeButtons) {
    button.addEventListener("click", () => {
      setViewMode(button.dataset.viewModeOption);
    });
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

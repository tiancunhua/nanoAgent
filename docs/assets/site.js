document.addEventListener("DOMContentLoaded", () => {
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

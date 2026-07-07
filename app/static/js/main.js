/* =========================================================
   Schedora — theme handling (light/dark)
   ========================================================= */
(function () {
  // Apply saved theme immediately on script load
  const saved = localStorage.getItem("schedora-theme") || "light";
  document.documentElement.setAttribute("data-theme", saved);

  // Wire up the toggle button once DOM is ready
  document.addEventListener("DOMContentLoaded", function () {
    const btn = document.getElementById("themeToggle");
    if (!btn) return;

    updateIcon(btn, document.documentElement.getAttribute("data-theme"));

    btn.addEventListener("click", function () {
      const current = document.documentElement.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("schedora-theme", next);
      updateIcon(btn, next);
    });
  });

  function updateIcon(btn, theme) {
    btn.innerHTML = theme === "dark"
      ? '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>'
      : '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    btn.setAttribute("aria-label", theme === "dark" ? "Switch to light mode" : "Switch to dark mode");
  }
})();

/* =========================================================
   Sidebar collapse (dashboard pages only)
   ========================================================= */
(function () {
  // Apply saved sidebar state immediately, before the DOM finishes
  // rendering, so there's no flash of the expanded state
  const savedCollapsed = localStorage.getItem("schedora-sidebar") === "collapsed";
  document.addEventListener("DOMContentLoaded", function () {
    const shell = document.querySelector(".dash-shell");
    if (!shell) return;

    if (savedCollapsed) shell.classList.add("collapsed");

    const toggle = document.getElementById("sidebarToggle");
    if (!toggle) return;

    toggle.addEventListener("click", function () {
      shell.classList.toggle("collapsed");
      const isCollapsed = shell.classList.contains("collapsed");
      localStorage.setItem("schedora-sidebar", isCollapsed ? "collapsed" : "expanded");
    });
  });
})();
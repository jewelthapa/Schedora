// ============ Schedora landing page — home.js ============
(function () {
  var root = document.documentElement;

  // ---- Apply saved theme on load ----
  var saved = localStorage.getItem('schedora-theme');
  if (!saved) {
    saved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  root.setAttribute('data-theme', saved);

  // ---- Theme toggle button ----
  var themeBtn = document.getElementById('themeBtn');
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var current = root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
      var next = current === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      localStorage.setItem('schedora-theme', next);
    });
  }

  // ---- Mobile menu toggle ----
  var menuBtn = document.getElementById('menuBtn');
  var navLinks = document.getElementById('navLinks');
  if (menuBtn && navLinks) {
    menuBtn.addEventListener('click', function () {
      navLinks.classList.toggle('active');
      menuBtn.textContent = navLinks.classList.contains('active') ? '✕' : '☰';
    });
    navLinks.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        navLinks.classList.remove('active');
        menuBtn.textContent = '☰';
      });
    });
  }

  // ---- Hero buttons keep their colour once clicked ----
  document.querySelectorAll('.hero-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.hero-btn').forEach(function (b) { b.classList.remove('is-selected'); });
      btn.classList.add('is-selected');
    });
  });
})();
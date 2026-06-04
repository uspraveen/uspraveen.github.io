(function () {
  var bar = document.getElementById('scroll-progress');
  if (bar) {
    function onScrollProgress() {
      var h = document.documentElement;
      var scrolled = (h.scrollTop || document.body.scrollTop) / ((h.scrollHeight - h.clientHeight) || 1);
      bar.style.width = Math.min(100, Math.max(0, scrolled * 100)) + '%';
    }
    window.addEventListener('scroll', onScrollProgress, { passive: true });
    onScrollProgress();
  }

  var toggle = document.getElementById('nav-toggle');
  var overlay = document.getElementById('nav-overlay');
  function closeMenu() {
    document.body.classList.remove('menu-open');
    if (toggle) {
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-label', 'Open menu');
    }
    if (overlay) overlay.setAttribute('aria-hidden', 'true');
  }
  function openMenu() {
    document.body.classList.add('menu-open');
    if (toggle) {
      toggle.setAttribute('aria-expanded', 'true');
      toggle.setAttribute('aria-label', 'Close menu');
    }
    if (overlay) overlay.setAttribute('aria-hidden', 'false');
  }
  if (toggle) {
    toggle.addEventListener('click', function () {
      if (document.body.classList.contains('menu-open')) closeMenu();
      else openMenu();
    });
  }
  if (overlay) {
    overlay.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', closeMenu);
    });
  }

  var year = document.getElementById('footer-year');
  if (year) year.textContent = new Date().getFullYear();
})();

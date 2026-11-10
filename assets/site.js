// Collapsible navigation on phones and tablets.
(() => {
  const nav = document.querySelector('.site-nav');
  const toggle = nav.querySelector('.nav-toggle');
  toggle.hidden = false;
  nav.classList.add('menu-ready');

  function closeMenu() {
    nav.classList.remove('menu-open');
    toggle.setAttribute('aria-expanded', 'false');
  }

  toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('menu-open');
    toggle.setAttribute('aria-expanded', String(open));
  });
  document.addEventListener('click', (event) => {
    if (!nav.contains(event.target)) closeMenu();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && nav.classList.contains('menu-open')) {
      closeMenu();
      toggle.focus();
    }
  });
})();

// Hero dropdowns (Kaggle tracks / dataset mirrors).
(() => {
  const closeAll = () => document.querySelectorAll('.hero-dd.open').forEach(dd => {
    dd.classList.remove('open');
    dd.querySelector('.hero-dd-toggle')?.setAttribute('aria-expanded', 'false');
  });
  document.querySelectorAll('.hero-dd-toggle').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const dd = btn.closest('.hero-dd');
      const wasOpen = dd.classList.contains('open');
      closeAll();
      if (!wasOpen) { dd.classList.add('open'); btn.setAttribute('aria-expanded', 'true'); }
    });
  });
  document.addEventListener('click', closeAll);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeAll(); });
})();

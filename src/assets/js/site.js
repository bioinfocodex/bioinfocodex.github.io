// Shared behaviour for every page. Each route is its own HTML document, so
// there is no client-side router: navigation is ordinary links.

// Kept so any leftover onclick="showPage('x')" still goes somewhere sensible.
var PAGE_PATHS = {
  home: '/', tools: '/tools', 'tool-rnaflow': '/tools/rnaflow', 'tool-genenet': '/tools/genenet',
  edu: '/learn', lessons: '/lessons', resources: '/resources', register: '/download', contact: '/contact'
};
function showPage(name) {
  var key = String(name || '').replace(/^page-/, '');
  window.location.href = PAGE_PATHS[key] || '/tools#roadmap';
}

// ── Mobile menu ───────────────────────────────────────────────────────────
function toggleMobile() {
  document.getElementById('mobile-menu').classList.toggle('open');
}

// ── Tool manual sections (tabs inside /tools/rnaflow) ─────────────────────
// The section is mirrored in the URL hash so a step can be linked to.
function showToolSection(id, el, keepHash) {
  var sec = document.getElementById(id);
  if (!sec) return;
  document.querySelectorAll('.tool-section').forEach(function (s) { s.classList.remove('active'); });
  document.querySelectorAll('.tool-nav-item').forEach(function (i) { i.classList.remove('active'); });
  sec.classList.add('active');
  el = el || document.querySelector('.tool-nav-item[data-section="' + id + '"]');
  if (el) el.classList.add('active');
  if (!keepHash && history.replaceState) history.replaceState(null, '', '#' + id.replace(/^ts-/, ''));
}
(function () {
  var items = document.querySelectorAll('.tool-nav-item[onclick]');
  if (!items.length) return;
  items.forEach(function (el) {
    var m = /showToolSection\('([^']+)'/.exec(el.getAttribute('onclick') || '');
    if (m) el.setAttribute('data-section', m[1]);
  });
  function fromHash() {
    var id = 'ts-' + location.hash.replace('#', '');
    if (location.hash && document.getElementById(id)) showToolSection(id, null, true);
  }
  window.addEventListener('hashchange', fromHash);
  fromHash();
})();

// ── Accordions ────────────────────────────────────────────────────────────
function toggleManualStep(el) { el.classList.toggle('open'); }
function toggleTutStep(el) { el.classList.toggle('open'); }
function toggleFAQ(el) { el.classList.toggle('open'); }

// ── Tool filter ───────────────────────────────────────────────────────────
function filterTools(tag, btn) {
  document.querySelectorAll('.filter-btn').forEach(function (b) { b.classList.remove('active'); });
  btn.classList.add('active');
  document.querySelectorAll('[data-tags]').forEach(function (c) {
    var tags = (c.dataset.tags || '').split(' ');
    c.style.display = (tag === 'all' || tags.indexOf(tag) !== -1) ? '' : 'none';
  });
}

// ── Copy code ─────────────────────────────────────────────────────────────
function copyCode(btn) {
  var block = btn.parentElement;
  var text = Array.prototype.filter.call(block.childNodes, function (n) { return n.nodeType === 3; })
    .map(function (n) { return n.textContent; }).join('');
  navigator.clipboard.writeText(text.trim()).then(function () {
    btn.textContent = '✓ Copied';
    btn.classList.add('ok');
    setTimeout(function () { btn.textContent = 'Copy'; btn.classList.remove('ok'); }, 2000);
  });
}

// ── Scroll reveal ─────────────────────────────────────────────────────────
(function () {
  var els = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) { els.forEach(function (e) { e.classList.add('vis'); }); return; }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('vis'); io.unobserve(e.target); } });
  }, { threshold: 0.1 });
  els.forEach(function (el) { io.observe(el); });
})();

// ── Stat counters ─────────────────────────────────────────────────────────
// The real number is already in the HTML; this only animates up to it.
(function () {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  function ease(t) { return t === 1 ? 1 : 1 - Math.pow(2, -10 * t); }
  function run(el) {
    el.dataset.animated = '1';
    var target = parseInt(el.dataset.count, 10), suffix = el.dataset.suffix || '';
    var start = performance.now();
    (function frame(now) {
      var p = Math.min((now - start) / 1400, 1);
      el.textContent = Math.round(ease(p) * target) + suffix;
      if (p < 1) requestAnimationFrame(frame);
    })(start);
  }
  function check() {
    document.querySelectorAll('[data-count]:not([data-animated])').forEach(function (el) {
      if (el.getBoundingClientRect().top < window.innerHeight * 0.9) run(el);
    });
  }
  window.addEventListener('scroll', check, { passive: true });
  setTimeout(check, 400);
})();

// ── Nav: shadow on scroll, dark while over a dark hero ────────────────────
(function () {
  var nav = document.querySelector('nav');
  var hero = document.body.dataset.hero === 'dark' ? document.querySelector('.hero, .tools-hero, .edu-hero') : null;
  function onScroll() {
    nav.classList.toggle('nav-scrolled', window.scrollY > 12);
    nav.classList.toggle('nav-dark', !!hero && window.scrollY < hero.offsetHeight - 64);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  onScroll();
})();

// ── Keyboard activation for role="button" elements ───────────────────────
document.addEventListener('keydown', function (e) {
  if (e.key !== 'Enter' && e.key !== ' ' && e.key !== 'Spacebar') return;
  var el = e.target.closest('[role="button"][tabindex]');
  if (!el || el.matches('button, a, input, select, textarea')) return;
  e.preventDefault();
  el.click();
});

// Accordions announce their state by mirroring the "open" class.
(function () {
  document.querySelectorAll('[aria-expanded]').forEach(function (head) {
    var sync = function () {
      var want = head.classList.contains('open') ? 'true' : 'false';
      if (head.getAttribute('aria-expanded') !== want) head.setAttribute('aria-expanded', want);
    };
    sync();
    new MutationObserver(sync).observe(head, { attributes: true, attributeFilter: ['class'] });
  });
})();

// ── Forms ─────────────────────────────────────────────────────────────────
// <form data-endpoint="https://formspree.io/f/…"> posts in the background and
// swaps in its [data-form-success] sibling. If the request fails the person is
// told, with the address to write to instead: never a false "sent".
(function () {
  document.querySelectorAll('form[data-endpoint]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = form.querySelector('[type="submit"]');
      var status = form.querySelector('[data-form-status]');
      var label = btn ? btn.textContent : '';
      if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }
      if (status) { status.textContent = ''; status.className = 'form-status'; }
      fetch(form.dataset.endpoint, {
        method: 'POST', body: new FormData(form), headers: { 'Accept': 'application/json' }
      }).then(function (r) {
        if (!r.ok) throw new Error('status ' + r.status);
        var ok = form.parentElement.querySelector('[data-form-success]');
        form.style.display = 'none';
        if (ok) { ok.style.display = 'block'; ok.setAttribute('tabindex', '-1'); ok.focus(); }
      }).catch(function () {
        if (btn) { btn.disabled = false; btn.textContent = label; }
        if (status) {
          status.className = 'form-status error';
          status.textContent = 'That did not go through. Please try again, or email ' +
            (form.dataset.fallback || 'info@bioinfocodex.com') + ' instead.';
        }
      });
    });
  });
})();

// ── Course progress ───────────────────────────────────────────────────────
// Finished topics are remembered in this browser only (localStorage). Nothing
// is sent anywhere, and the pages work the same if storage is unavailable.
(function () {
  var KEY = 'bic_learn_done';
  function read() { try { return JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { return {}; } }
  function write(d) { try { localStorage.setItem(KEY, JSON.stringify(d)); } catch (e) {} }
  var done = read();

  function paint() {
    document.querySelectorAll('[data-topic]').forEach(function (el) {
      el.classList.toggle('done', !!done[el.dataset.topic]);
    });
    document.querySelectorAll('[data-progress]').forEach(function (el) {
      var topics = el.dataset.progress.split(' ').filter(Boolean);
      var n = topics.filter(function (t) { return done[t]; }).length;
      var bar = el.querySelector('.progress-fill');
      var txt = el.querySelector('.progress-text');
      if (bar) bar.style.width = (topics.length ? Math.round(100 * n / topics.length) : 0) + '%';
      if (txt) txt.textContent = n + ' of ' + topics.length + ' topics done';
      el.classList.toggle('complete', topics.length > 0 && n === topics.length);
    });
    var btn = document.getElementById('topic-done');
    if (btn) {
      var on = !!done[btn.dataset.topicId];
      btn.classList.toggle('is-done', on);
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
      btn.querySelector('.topic-done-label').textContent = on ? 'Done. Click to undo' : 'Mark this topic as done';
    }
  }
  var btn = document.getElementById('topic-done');
  if (btn) btn.addEventListener('click', function () {
    var id = btn.dataset.topicId;
    if (done[id]) delete done[id]; else done[id] = 1;
    write(done); paint();
  });
  var reset = document.getElementById('progress-reset');
  if (reset) reset.addEventListener('click', function () { done = {}; write(done); paint(); });
  paint();
})();

// ── Glossary filter ───────────────────────────────────────────────────────
(function () {
  var input = document.getElementById('glossary-filter');
  if (!input) return;
  var items = document.querySelectorAll('.glossary-item');
  var empty = document.getElementById('glossary-empty');
  input.addEventListener('input', function () {
    var q = input.value.trim().toLowerCase(), shown = 0;
    items.forEach(function (it) {
      var hit = !q || it.textContent.toLowerCase().indexOf(q) !== -1;
      it.style.display = hit ? '' : 'none';
      if (hit) shown++;
    });
    if (empty) empty.style.display = shown ? 'none' : 'block';
  });
})();

// Keep the current module's tab in view when the tab bar scrolls sideways.
(function () {
  var bar = document.querySelector('.edu-tabbar');
  var tab = bar && bar.querySelector('.edu-mod-tab.active');
  if (tab) bar.scrollLeft = Math.max(0, tab.offsetLeft - (bar.clientWidth - tab.offsetWidth) / 2);
})();

// Site search. The build writes one JSON index of every page, topic and
// glossary term; this loads it on the search page only and ranks in the
// browser. Nothing typed here leaves the visitor's machine.
(function () {
  var box = document.getElementById('search-results');
  var input = document.getElementById('search-input');
  if (!box || !input) return;
  var index = null;

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function score(entry, terms) {
    var title = entry.t.toLowerCase(), body = entry.x.toLowerCase(), total = 0;
    for (var i = 0; i < terms.length; i++) {
      var w = terms[i], s = 0;
      if (title === w) s += 40;
      if (title.indexOf(w) !== -1) s += 20;
      var at = body.indexOf(w), hits = 0;
      while (at !== -1 && hits < 8) { hits++; at = body.indexOf(w, at + w.length); }
      s += hits * 2;
      if (!s) return 0;            // every term must appear somewhere
      total += s;
    }
    return total;
  }

  function snippet(entry, terms) {
    var body = entry.x, low = body.toLowerCase(), at = -1;
    for (var i = 0; i < terms.length && at === -1; i++) at = low.indexOf(terms[i]);
    if (at === -1) return body.slice(0, 180);
    var from = Math.max(0, at - 70);
    return (from ? '… ' : '') + body.slice(from, from + 200).trim() + ' …';
  }

  function render(q) {
    box.textContent = '';
    var terms = q.toLowerCase().split(/\s+/).filter(function (w) { return w.length > 1; });
    if (!terms.length) { box.appendChild(el('p', 'search-hint', 'Type at least two letters, for example "DESeq2", "FASTQ" or "p-value".')); return; }
    var hits = [];
    index.forEach(function (e) { var s = score(e, terms); if (s) hits.push([s, e]); });
    hits.sort(function (a, b) { return b[0] - a[0]; });
    box.appendChild(el('p', 'search-count', hits.length ? hits.length + (hits.length === 1 ? ' result' : ' results') : 'Nothing matched. Try a shorter or different word.'));
    hits.slice(0, 40).forEach(function (h) {
      var e = h[1];
      var a = el('a', 'search-hit'); a.href = e.u;
      a.appendChild(el('span', 'search-kind', e.k));
      a.appendChild(el('span', 'search-title', e.t));
      a.appendChild(el('span', 'search-snip', snippet(e, terms)));
      box.appendChild(a);
    });
  }

  function go() {
    var q = input.value.trim();
    if (history.replaceState) history.replaceState(null, '', q ? '?q=' + encodeURIComponent(q) : location.pathname);
    if (index) render(q);
  }

  var q0 = new URLSearchParams(location.search).get('q') || '';
  input.value = q0;
  input.addEventListener('input', go);
  document.getElementById('search-form').addEventListener('submit', function (e) { e.preventDefault(); go(); });

  fetch(box.dataset.index).then(function (r) { return r.json(); }).then(function (d) {
    index = d; render(input.value.trim());
  }).catch(function () {
    box.textContent = '';
    box.appendChild(el('p', 'search-count', 'Search could not load. Please refresh the page.'));
  });
  input.focus();
})();

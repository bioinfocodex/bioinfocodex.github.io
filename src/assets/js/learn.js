// Drifting path background for the /learn hero. Decorative only.
(function () {
  function generatePaths(container, position) {
    if (!container) return;
    var paths = [];
    for (var i = 0; i < 16; i++) {
      var d = 'M-' + (380 - i * 5 * position) + ' -' + (189 + i * 6) +
        'C-' + (380 - i * 5 * position) + ' -' + (189 + i * 6) + ' -' + (312 - i * 5 * position) + ' ' + (216 - i * 6) +
        ' ' + (152 - i * 5 * position) + ' ' + (343 - i * 6) +
        'C' + (616 - i * 5 * position) + ' ' + (470 - i * 6) + ' ' + (684 - i * 5 * position) + ' ' + (875 - i * 6) +
        ' ' + (684 - i * 5 * position) + ' ' + (875 - i * 6);
      var dur = 20 + Math.random() * 10;
      paths.push('<path d="' + d + '" stroke="currentColor" stroke-width="' + (0.5 + i * 0.03) +
        '" stroke-opacity="' + (0.1 + i * 0.03) + '" fill="none" style="--dur:' + dur + 's;animation-delay:-' +
        (Math.random() * dur) + 's"/>');
    }
    container.innerHTML = '<svg viewBox="0 0 696 316" fill="none" aria-hidden="true" style="color:rgba(148,163,184,0.6)">' +
      paths.join('') + '</svg>';
  }
  generatePaths(document.getElementById('edu-paths-left'), 1);
  generatePaths(document.getElementById('edu-paths-right'), -1);
})();

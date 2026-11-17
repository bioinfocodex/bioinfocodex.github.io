// Lesson pages. tools/build-lesson.py unpacks each lesson into
// lesson-files/<slug>/; the build prints the title, summary and outline into
// the page, and this script adds the video, simulation, quiz and transcript.
// Everything is built with textContent, never innerHTML: the lesson text is
// model-generated, and a stray "<" in a quiz option should print, not parse.
const LESSON_DIR = '/lesson-files/';

function lessonEl(tag, attrs, children) {
  const node = document.createElement(tag);
  if (attrs) Object.keys(attrs).forEach(function (k) {
    if (k === 'text') node.textContent = attrs[k];
    else if (k === 'on') Object.keys(attrs.on).forEach(function (ev) { node.addEventListener(ev, attrs.on[ev]); });
    else node.setAttribute(k, attrs[k]);
  });
  (children || []).forEach(function (c) { if (c) node.appendChild(c); });
  return node;
}

function lessonMinutes(seconds) {
  return seconds ? Math.max(1, Math.round(seconds / 60)) + ' min' : null;
}

function fetchJSON(url) {
  return fetch(url, { cache: 'no-cache' }).then(function (r) {
    if (!r.ok) throw new Error(url + ' answered ' + r.status);
    return r.json();
  });
}

function lessonBack() {
  return lessonEl('a', { class: 'lesson-back', href: '/lessons', text: '\u2190 All lessons' });
}

function renderLesson(view, L) {
  const base = LESSON_DIR + L.slug + '/';
  view.textContent = '';
  view.appendChild(lessonBack());
  view.appendChild(lessonEl('div', { class: 'label', text: L.subject || 'Lesson' }));
  view.appendChild(lessonEl('h1', { class: 'lesson-title', text: L.title }));
  if (L.summary) view.appendChild(lessonEl('p', { class: 'lead', text: L.summary }));

  if (L.video) {
    const v = lessonEl('video', { class: 'lesson-video', controls: '', preload: 'metadata', playsinline: '' });
    if (L.poster) v.setAttribute('poster', base + L.poster);
    v.appendChild(lessonEl('source', { src: base + L.video, type: 'video/mp4' }));
    if (L.captions) v.appendChild(lessonEl('track', { kind: 'captions', src: base + L.captions, srclang: 'en', label: 'English', default: '' }));
    view.appendChild(v);
  }
  view.appendChild(lessonEl('p', { class: 'lesson-ai-note',
    text: 'This lesson was generated with AI (' + (L.generator || 'OpenMAIC') + '). Spotted a mistake? Let us know on the Contact page.' }));

  view.appendChild(lessonEl('section', { class: 'lesson-block' }, [
    lessonEl('h2', { text: 'In this lesson' }),
    lessonEl('ol', { class: 'lesson-outline' }, L.scenes.map(function (s) { return lessonEl('li', { text: s.title }); }))
  ]));

  L.simulations.forEach(function (sim) { view.appendChild(simulationBlock(base, sim)); });
  if (L.quiz.length) view.appendChild(quizBlock(L.quiz));

  const spoken = L.scenes.filter(function (s) { return s.narration && s.narration.length; });
  if (spoken.length) {
    view.appendChild(lessonEl('details', { class: 'lesson-block lesson-transcript' }, [
      lessonEl('summary', { text: 'Transcript' })
    ].concat(spoken.reduce(function (acc, s) {
      acc.push(lessonEl('h3', { text: s.title }));
      s.narration.forEach(function (line) { acc.push(lessonEl('p', { text: line })); });
      return acc;
    }, []))));
  }

  if (L.module) {
    view.appendChild(lessonEl('a', { class: 'lesson-back', href: '/learn/' + L.module,
      text: 'Go deeper: the matching module in the course \u2192' }));
  }
}

function simulationBlock(base, sim) {
  const box = lessonEl('section', { class: 'lesson-block' }, [
    lessonEl('h2', { text: 'Try it: ' + sim.title }),
    lessonEl('p', { class: 'lesson-card-sum', text: 'An interactive simulation. Change the controls and watch what happens.' })
  ]);
  const btn = lessonEl('button', { class: 'btn btn-green', type: 'button', text: 'Launch simulation', style: 'margin-top:14px;' });
  btn.addEventListener('click', function () {
    btn.disabled = true; btn.textContent = 'Loading…';
    fetch(base + sim.file).then(function (r) { return r.text(); }).then(function (html) {
      const frame = lessonEl('iframe', { class: 'lesson-sim-frame', sandbox: 'allow-scripts', title: sim.title, loading: 'lazy' });
      frame.srcdoc = html;
      btn.replaceWith(frame);
    }).catch(function () { btn.disabled = false; btn.textContent = 'Could not load — try again'; });
  });
  box.appendChild(btn);
  return box;
}

function quizBlock(questions) {
  const kinds = { single: 'choose one', multiple: 'choose all that apply', short_answer: 'self-check, not scored' };
  const form = lessonEl('form', { class: 'lesson-block' }, [lessonEl('h2', { text: 'Check your understanding' })]);
  questions.forEach(function (q, i) {
    const wrap = lessonEl('div', { class: 'quiz-q' }, [
      lessonEl('div', { class: 'quiz-q-text' }, [
        document.createTextNode((i + 1) + '. ' + q.question),
        lessonEl('span', { class: 'quiz-q-kind', text: '(' + (kinds[q.type] || q.type) + ')' })
      ])
    ]);
    if (q.type === 'short_answer') {
      wrap.appendChild(lessonEl('textarea', { name: q.id, 'aria-label': 'Your answer', placeholder: 'Write your answer, then check it against the model answer.' }));
    } else {
      q.options.forEach(function (o) {
        wrap.appendChild(lessonEl('label', { class: 'quiz-opt', 'data-value': o.value }, [
          lessonEl('input', { type: q.type === 'multiple' ? 'checkbox' : 'radio', name: q.id, value: o.value }),
          lessonEl('span', { text: o.label })
        ]));
      });
    }
    wrap.appendChild(lessonEl('div', { class: 'quiz-feedback' }));
    form.appendChild(wrap);
  });
  const score = lessonEl('span', { class: 'quiz-score', 'aria-live': 'polite' });
  const reset = lessonEl('button', { class: 'btn btn-outline', type: 'button', text: 'Try again', style: 'display:none;margin-left:8px;' });
  form.appendChild(lessonEl('div', { style: 'margin-top:18px;display:flex;align-items:center;flex-wrap:wrap;gap:8px;' }, [
    lessonEl('button', { class: 'btn btn-green', type: 'submit', text: 'Check answers' }), reset, score
  ]));

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    let got = 0, total = 0;
    questions.forEach(function (q, i) {
      const wrap = form.querySelectorAll('.quiz-q')[i];
      const fb = wrap.querySelector('.quiz-feedback');
      fb.textContent = '';
      if (q.type === 'short_answer') {
        fb.appendChild(lessonEl('strong', { text: 'Model answer: ' }));
        fb.appendChild(document.createTextNode(q.explanation));
      } else {
        total += q.points;
        const picked = Array.prototype.map.call(wrap.querySelectorAll('input:checked'), function (x) { return x.value; });
        const right = picked.length === q.answer.length && q.answer.every(function (a) { return picked.indexOf(a) !== -1; });
        if (right) got += q.points;
        wrap.querySelectorAll('.quiz-opt').forEach(function (opt) {
          const v = opt.getAttribute('data-value');
          opt.classList.toggle('right', q.answer.indexOf(v) !== -1);
          opt.classList.toggle('wrong', picked.indexOf(v) !== -1 && q.answer.indexOf(v) === -1);
        });
        fb.appendChild(lessonEl('strong', { text: right ? 'Correct. ' : 'Not quite. ' }));
        fb.appendChild(document.createTextNode(q.explanation));
      }
      fb.classList.add('show');
    });
    score.textContent = total ? 'Score: ' + got + ' / ' + total : '';
    reset.style.display = '';
  });
  reset.addEventListener('click', function () {
    form.reset();
    form.querySelectorAll('.quiz-opt').forEach(function (o) { o.classList.remove('right', 'wrong'); });
    form.querySelectorAll('.quiz-feedback').forEach(function (f) { f.classList.remove('show'); });
    score.textContent = ''; reset.style.display = 'none';
  });
  return form;
}

(function () {
  const view = document.getElementById('lesson-view');
  if (!view || !view.dataset.slug) return;
  fetchJSON(LESSON_DIR + view.dataset.slug + '/lesson.json').then(function (lesson) {
    renderLesson(view, lesson);
  }).catch(function () { /* the prerendered outline stays on screen */ });
})();

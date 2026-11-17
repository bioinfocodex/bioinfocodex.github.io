#!/usr/bin/env python3
"""Build bioinfocodex.com from src/ into dist/.

    python3 tools/build-site.py            # build
    python3 tools/build-site.py --serve    # build, then serve dist/ on :8000

Standard library only, so Netlify can run it with no install step.

What goes where
    src/site.json            version numbers, addresses, analytics switch
    src/layout.html          the page shell (head, nav, footer)
    src/pages/*.html         one file per page; a comment block at the top
                             gives its path, title and description
    src/learn/NN-slug.html   one file per course module; each
                             <!--topic 5.2: Title--> marker starts a topic,
                             and every topic becomes its own page
    src/data/                glossary, cheat sheets and the RNAflow changelog
    src/assets/              css (joined in name order) and js
    src/static/              copied to the site root as-is

Every route is written as dist/<path>/index.html with its own title,
description, canonical URL and share card, so nothing depends on JavaScript to
be indexable. The build also writes sitemap.xml, the search index and
_redirects.
"""
import datetime
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
DIST = ROOT / 'dist'
SITE = json.loads((SRC / 'site.json').read_text(encoding='utf-8'))
URL = SITE['site_url']
RF = SITE['rnaflow']
TODAY = datetime.date.today()

# Files that live at the repository root and are published unchanged.
ROOT_FILES = ['favicon.svg', 'favicon.png', 'apple-touch-icon.png', 'icon-192.png',
              'icon-512.png', 'og-image.png', 'site.webmanifest', 'robots.txt']

pages = []          # every page written: dict(path, title, description, kind, text, sitemap)


# ── small helpers ─────────────────────────────────────────────────────────
def read(rel):
    return (SRC / rel).read_text(encoding='utf-8')


def esc(s):
    return html.escape(s, quote=True)


def slugify(s):
    s = html.unescape(re.sub(r'<[^>]+>', '', s)).lower()
    s = s.replace('&', ' and ')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def plain(markup):
    """Markup -> readable text, for descriptions and the search index."""
    s = re.sub(r'<(script|style)\b.*?</\1>', ' ', markup, flags=re.S)
    s = re.sub(r'<button[^>]*copy-code-btn[^>]*>.*?</button>', ' ', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', html.unescape(s)).strip()


def first_sentence(markup, limit=155):
    text = plain(markup)
    m = re.match(r'(.{40,}?[.!?])\s', text + ' ')
    out = m.group(1) if m and len(m.group(1)) <= limit else text[:limit].rsplit(' ', 1)[0] + '…'
    return out


def long_date(iso):
    d = datetime.date.fromisoformat(iso)
    return '%d %s %d' % (d.day, d.strftime('%B'), d.year)


FRONT = re.compile(r'\A<!--\n(.*?)\n-->\n', re.S)


def front_matter(text):
    m = FRONT.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end():]


# ── assets ────────────────────────────────────────────────────────────────
ASSETS = {}


def publish_asset(name, data):
    """Write under /assets with a content hash in the name, so it can be cached forever."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    stem, ext = name.rsplit('.', 1)
    out = 'assets/%s.%s.%s' % (stem, hashlib.sha256(data).hexdigest()[:10], ext)
    (DIST / out).parent.mkdir(parents=True, exist_ok=True)
    (DIST / out).write_bytes(data)
    ASSETS[name] = '/' + out
    return ASSETS[name]


def build_assets():
    css = '\n'.join(p.read_text(encoding='utf-8') for p in sorted((SRC / 'assets/css').glob('*.css')))
    publish_asset('site.css', css)
    for p in sorted((SRC / 'assets/js').glob('*.js')):
        publish_asset(p.name, p.read_text(encoding='utf-8'))


# ── tokens that keep one fact in one place ────────────────────────────────
def tokens(s, extra=None):
    t = {
        'RNAFLOW_VERSION': RF['version'],
        'RNAFLOW_RELEASED': long_date(RF['released']),
        'RNAFLOW_REPO': RF['repo'],
        'RNAFLOW_DL': '%s/releases/download/v%s' % (RF['repo'], RF['version']),
        'RNAFLOW_MANUAL': RF['manual'],
        'RNAFLOW_SITE': RF['app_site'],
        'DOI': RF['doi'],
        'FORM_ENDPOINT': 'https://formspree.io/f/' + SITE['formspree_id'],
        'EMAIL': SITE['contact_email'],
        'GITHUB': SITE['github_org'],
        'YEAR': str(TODAY.year),
    }
    t.update(extra or {})
    return re.sub(r'%%([A-Z_]+)%%', lambda m: t.get(m.group(1), m.group(0)), s)


# ── structured data ───────────────────────────────────────────────────────
def ld(obj):
    return '<script type="application/ld+json">%s</script>\n' % json.dumps(obj, ensure_ascii=False)


def breadcrumbs_ld(trail):
    return ld({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i, 'name': html.unescape(name), 'item': URL + path}
        for i, (name, path) in enumerate(trail, 1)]})


ORG = {'@type': 'Organization', 'name': 'BioInfoCodex', 'url': URL, 'logo': URL + '/icon-512.png',
       'sameAs': [SITE['github_org']]}


def jsonld_for(key):
    if key == 'home':
        return ld({'@context': 'https://schema.org', '@graph': [
            dict(ORG, **{'@id': URL + '/#org'}),
            {'@type': 'WebSite', 'name': 'BioInfoCodex', 'url': URL, 'publisher': {'@id': URL + '/#org'},
             'potentialAction': {'@type': 'SearchAction', 'target': URL + '/search?q={query}',
                                 'query-input': 'required name=query'}}]})
    if key == 'rnaflow':
        return ld({'@context': 'https://schema.org', '@type': 'SoftwareApplication', 'name': 'RNAflow',
                   'applicationCategory': 'ScienceApplication', 'operatingSystem': 'macOS, Linux, Windows (WSL2)',
                   'softwareVersion': RF['version'], 'datePublished': RF['released'],
                   'license': 'https://opensource.org/licenses/MIT', 'url': URL + '/tools/rnaflow',
                   'downloadUrl': URL + '/download', 'codeRepository': RF['repo'],
                   'identifier': 'https://doi.org/' + RF['doi'],
                   'description': 'A guided desktop app for bulk RNA-seq analysis, from raw FASTQ files to '
                                  'differential expression and pathway enrichment, running on your own computer.',
                   'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
                   'author': {'@type': 'Person', 'name': 'Matrika Bhattarai',
                              'identifier': 'https://orcid.org/0000-0003-2627-6251'}})
    return ''


def analytics_tag():
    a = SITE.get('analytics', {})
    if a.get('provider') == 'plausible' and a.get('domain'):
        return '<script defer data-domain="%s" src="https://plausible.io/js/script.js"></script>\n' % esc(a['domain'])
    if a.get('provider') == 'goatcounter' and a.get('code'):
        return ('<script data-goatcounter="https://%s.goatcounter.com/count" async '
                'src="https://gc.zgo.at/count.js"></script>\n' % esc(a['code']))
    return ''


# ── page writer ───────────────────────────────────────────────────────────
LAYOUT = read('layout.html')
SPRITE = read('partials/sprite.html')
LOGO = read('partials/logo.html')
NAV_KEYS = ['home', 'tools', 'learn', 'resources', 'download', 'about', 'contact']


def write_page(path, title, description, content, *, page_id='page', nav='', hero='light', scripts=(),
               jsonld='', kind='Page', sitemap=True, robots='', og_type='website', search_text=None,
               og_image=None, og_image_alt=None, out_file=None):
    canonical = URL + (path if path != '/' else '/')
    description = html.unescape(description)
    if len(description) > 160:
        description = description[:157].rsplit(' ', 1)[0].rstrip(',;:') + '…'
    script_tags = '<script src="%s" defer></script>\n' % ASSETS['site.js']
    for s in scripts:
        script_tags += '<script src="%s" defer></script>\n' % ASSETS[s]
    values = {
        'title': title, 'description': esc(html.unescape(description)), 'canonical': canonical,
        'og_type': og_type, 'og_image': og_image or URL + '/og-image.png',
        'og_image_alt': esc(og_image_alt or 'BioInfoCodex: open-source bioinformatics software and a free course.'),
        'robots': ('<meta name="robots" content="%s">\n' % robots) if robots else '',
        'css': ASSETS['site.css'], 'jsonld': jsonld, 'analytics': analytics_tag(),
        'hero': hero, 'nav': nav, 'id': page_id, 'sprite': SPRITE, 'logo': LOGO,
        'content': content, 'scripts': script_tags, 'github_org': SITE['github_org'], 'year': str(TODAY.year),
    }
    for k in NAV_KEYS:
        values['nav_' + k] = ' active" aria-current="page' if k == nav else ''
    out = re.sub(r'\{\{([a-z_]+)\}\}', lambda m: values.get(m.group(1), m.group(0)), LAYOUT)
    left = re.findall(r'%%[A-Z_]+%%', out)
    if left:
        sys.exit('unresolved tokens on %s: %s' % (path, sorted(set(left))))
    target = DIST / (out_file or (path.strip('/') + '/index.html').lstrip('/'))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(out, encoding='utf-8')
    pages.append({'path': path, 'title': html.unescape(title.split(' | ')[0]), 'kind': kind,
                  'text': plain(content) if search_text is None else search_text,
                  'sitemap': sitemap and not robots})


# ── course ────────────────────────────────────────────────────────────────
TOPIC = re.compile(r'^<!--topic ([\d.]+): (.*?)-->$', re.M)


MORE_KINDS = {'video': 'Video', 'read': 'Read', 'course': 'Tutorial', 'docs': 'Manual', 'paper': 'Paper'}


def decorate_topic(num, text, extras):
    """Add the topic's figure (after its opening paragraph) and its
    "Watch and read more" list, both described in src/data/topic-extras.json."""
    ex = extras.get(num, {})
    svg = SRC / 'static' / 'img' / 'learn' / (num.replace('.', '-') + '.svg')
    if ex.get('fig') and svg.exists():
        m = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg.read_text(encoding='utf-8'))
        w, h = (m.group(1), m.group(2)) if m else ('720', '250')
        src = '/img/learn/%s.svg' % num.replace('.', '-')
        fig = ('\n<figure class="topic-fig"><div class="topic-fig-scroll">'
               '<a href="%s" target="_blank" rel="noopener" aria-label="Open figure %s at full size">'
               '<img src="%s" alt="%s" width="%s" height="%s" loading="lazy"></a></div>'
               '<figcaption><strong>Figure %s.</strong> %s '
               '<span class="fig-hint">Tap the figure to open it at full size.</span>'
               '</figcaption></figure>\n') % (src, num, src, esc(plain(ex['fig'])), w, h, num, ex['fig'])
        cut = text.find('</p>')
        text = text[:cut + 4] + fig + text[cut + 4:] if cut != -1 else fig + text
    if ex.get('more'):
        items = ''.join(
            '<li><a class="more-link more-%s" href="%s" target="_blank" rel="noopener">'
            '<span class="more-kind">%s</span><span class="more-body"><span class="more-title">%s</span>'
            '<span class="more-src">%s</span></span></a></li>' % (
                kind, esc(url), MORE_KINDS.get(kind, 'Read'), title, source)
            for kind, title, source, url in ex['more'])
        text += ('\n<section class="topic-more"><h3>Watch and read more</h3>'
                 '<p class="sub">Free material from other teachers and from the people who wrote the tools. '
                 'Each link opens in a new tab.</p><ul class="more-list">%s</ul></section>\n') % items
    return text


def load_modules():
    mods = []
    extras_file = SRC / 'data' / 'topic-extras.json'
    extras = json.loads(extras_file.read_text(encoding='utf-8')) if extras_file.exists() else {}
    for p in sorted((SRC / 'learn').glob('*.html')):
        meta, body = front_matter(p.read_text(encoding='utf-8'))
        parts = TOPIC.split(body)
        mod = {'n': int(meta['module']), 'slug': meta['slug'], 'short': meta['short'], 'label': meta['label'],
               'title': meta['title'], 'intro': parts[0].strip(), 'topics': [], 'path': '/learn/' + meta['slug']}
        for i in range(1, len(parts), 3):
            num, title, text = parts[i], parts[i + 1], parts[i + 2].strip()
            text = decorate_topic(num, text, extras)
            mod['topics'].append({'num': num, 'title': title, 'body': text,
                                  'path': '%s/%s' % (mod['path'], slugify(title)), 'module': mod})
        mods.append(mod)
    return mods


def module_tabs(mods, current=None):
    tabs = ''.join(
        '<a class="edu-mod-tab%s" href="%s"%s>Module %d<span class="edu-mod-sub">%s</span></a>' % (
            ' active' if m is current else '', m['path'], ' aria-current="page"' if m is current else '',
            m['n'], m['short']) for m in mods)
    return '<div class="edu-tabbar"><div class="edu-tabbar-inner">%s</div></div>\n' % tabs


def crumbs(trail):
    bits = []
    for i, (name, path) in enumerate(trail):
        last = i == len(trail) - 1
        bits.append('<span aria-current="page">%s</span>' % name if last else '<a href="%s">%s</a>' % (path, name))
    return '<div class="breadcrumb" role="navigation" aria-label="Breadcrumb">%s</div>\n' % '<span class="breadcrumb-sep">›</span>'.join(bits)


def build_course(mods, lessons):
    flat = [t for m in mods for t in m['topics']]
    by_module_lesson = {}
    for l in lessons:
        by_module_lesson.setdefault(l.get('module'), []).append(l)

    # /learn
    cards = ''
    for m in mods:
        ids = ' '.join(t['path'] for t in m['topics'])
        cards += '''
      <a class="module-card" href="{path}" data-progress="{ids}">
        <span class="module-num">Module {n}</span>
        <span class="module-title">{title}</span>
        <span class="module-desc">{desc}</span>
        <span class="module-meta"><span>{count} topics</span><span class="progress-text"></span></span>
        <span class="progress-track"><span class="progress-fill"></span></span>
      </a>'''.format(path=m['path'], ids=ids, n=m['n'], title=m['title'],
                     desc=esc(first_sentence(m['intro'], 150)), count=len(m['topics']))
    meta, body = front_matter(read('pages/learn.html'))
    counts = {'MODULE_COUNT': str(len(mods)), 'TOPIC_COUNT': str(len(flat))}
    body = tokens(body, dict(counts, MODULE_CARDS=cards))
    meta['title'], meta['description'] = tokens(meta['title'], counts), tokens(meta['description'], counts)
    course_ld = ld({'@context': 'https://schema.org', '@type': 'Course', 'name': 'Learn Bioinformatics',
                    'description': html.unescape(meta['description']), 'url': URL + '/learn',
                    'provider': ORG, 'isAccessibleForFree': True, 'inLanguage': 'en',
                    'hasCourseInstance': {'@type': 'CourseInstance', 'courseMode': 'Online',
                                          'courseWorkload': 'PT%dH' % max(1, round(sum(len(plain(t['body']).split()) for t in flat) / 200 / 60 * 2))},
                    'hasPart': [{'@type': 'LearningResource', 'name': html.unescape(m['title']), 'url': URL + m['path']}
                                for m in mods]})
    write_page('/learn', meta['title'], meta['description'], body, page_id='edu', nav='learn', hero='dark', scripts=('learn.js',), jsonld=course_ld, kind='Course')

    for mi, m in enumerate(mods):
        ids = ' '.join(t['path'] for t in m['topics'])
        items = ''
        for t in m['topics']:
            words = len(plain(t['body']).split())
            items += '''
        <a class="topic-link" href="{path}" data-topic="{path}">
          <span class="edu-topic-num">{num}</span>
          <span class="topic-link-body"><span class="topic-link-title">{title}</span>
          <span class="topic-link-desc">{desc}</span></span>
          <span class="topic-link-meta">{mins} min read</span>
          <span class="topic-check" aria-hidden="true">✓</span>
        </a>'''.format(path=t['path'], num=t['num'], title=t['title'],
                       desc=esc(first_sentence(t['body'], 140)), mins=max(2, round(words / 200)))
        extras = ''
        for l in by_module_lesson.get(m['slug'], []):
            extras += ('<a class="topic-link topic-link-video" href="/lessons/{slug}"><span class="edu-topic-num">▶</span>'
                       '<span class="topic-link-body"><span class="topic-link-title">Video lesson: {title}</span>'
                       '<span class="topic-link-desc">{sum}</span></span><span class="topic-link-meta">{mins} min</span></a>'
                       ).format(slug=l['slug'], title=esc(l['title']), sum=esc(l.get('summary', '')),
                                mins=max(1, round(l.get('duration', 60) / 60)))
        if m['slug'] == 'rna-seq':
            extras += ('<a class="topic-link" href="/learn/practice-dataset"><span class="edu-topic-num">↗</span>'
                       '<span class="topic-link-body"><span class="topic-link-title">Practice: run this module on a real dataset</span>'
                       '<span class="topic-link-desc">Eight public samples with a known answer, so you can check your own result.</span></span></a>')
        prev_m = mods[mi - 1] if mi else None
        next_m = mods[mi + 1] if mi + 1 < len(mods) else None
        pager = '<div class="pager">%s%s</div>' % (
            '<a class="pager-link" href="%s"><span>Previous module</span>%s</a>' % (prev_m['path'], prev_m['title']) if prev_m else '<span></span>',
            '<a class="pager-link next" href="%s"><span>Next module</span>%s</a>' % (next_m['path'], next_m['title']) if next_m else '<span></span>')
        content = '''{tabs}
<div class="learn-wrap">
  {crumbs}
  <div class="edu-mod-header">
    <div class="label">{label}</div>
    <h1 class="h2">{title}</h1>
    {intro}
    <div class="module-progress" data-progress="{ids}">
      <span class="progress-track"><span class="progress-fill"></span></span><span class="progress-text"></span>
    </div>
  </div>
  <div class="topic-list">{items}
  </div>
  {extras}
  {pager}
</div>'''.format(tabs=module_tabs(mods, m), crumbs=crumbs([('Learn', '/learn'), ('Module %d: %s' % (m['n'], m['short']), m['path'])]),
                 label=m['label'], title=m['title'], intro=m['intro'], ids=ids, items=items,
                 extras=('<div class="topic-list topic-extras">%s</div>' % extras) if extras else '', pager=pager)
        write_page(m['path'], '%s: %s | Learn Bioinformatics' % (m['short'], m['title']),
                   first_sentence(m['intro']), content, page_id='edu', nav='learn', kind='Course module',
                   search_text=plain(m['intro']) + ' ' + ' '.join(html.unescape(t['title']) for t in m['topics']),
                   jsonld=breadcrumbs_ld([('Learn', '/learn'), (m['title'], m['path'])]))

    for i, t in enumerate(flat):
        m = t['module']
        prev_t = flat[i - 1] if i else None
        next_t = flat[i + 1] if i + 1 < len(flat) else None
        side = ''.join('<a href="%s" data-topic="%s"%s><span>%s</span>%s</a>' % (
            o['path'], o['path'], ' class="current" aria-current="page"' if o is t else '', o['num'], o['title'])
            for o in m['topics'])
        pager = '<div class="pager">%s%s</div>' % (
            '<a class="pager-link" href="%s"><span>Previous · %s</span>%s</a>' % (prev_t['path'], prev_t['num'], prev_t['title']) if prev_t else '<span></span>',
            '<a class="pager-link next" href="%s"><span>Next · %s</span>%s</a>' % (next_t['path'], next_t['num'], next_t['title']) if next_t else '<span></span>')
        words = len(plain(t['body']).split())
        content = '''{tabs}
<div class="learn-wrap topic-layout">
  <aside class="topic-side" aria-label="Topics in this module">
    <div class="topic-side-title">Module {n} · {short}</div>
    {side}
    <a class="topic-side-all" href="/learn">All modules</a>
  </aside>
  <article class="topic-article">
    {crumbs}
    <div class="label">Topic {num} · {mins} min read</div>
    <h1 class="h2">{title}</h1>
    <div class="edu-topic-body topic-body">
{body}
    </div>
    <button type="button" class="topic-done" id="topic-done" data-topic-id="{path}" aria-pressed="false">
      <span class="topic-check" aria-hidden="true">✓</span><span class="topic-done-label">Mark this topic as done</span>
    </button>
    {pager}
  </article>
</div>'''.format(tabs=module_tabs(mods, m), n=m['n'], short=m['short'], side=side,
                 crumbs=crumbs([('Learn', '/learn'), ('Module %d: %s' % (m['n'], m['short']), m['path']), (t['title'], t['path'])]),
                 num=t['num'], mins=max(2, round(words / 200)), title=t['title'], body=t['body'], path=t['path'], pager=pager)
        topic_ld = ld({'@context': 'https://schema.org', '@type': 'LearningResource',
                       'name': html.unescape(t['title']), 'url': URL + t['path'], 'inLanguage': 'en',
                       'isAccessibleForFree': True, 'learningResourceType': 'Tutorial',
                       'isPartOf': {'@type': 'Course', 'name': 'Learn Bioinformatics', 'url': URL + '/learn'},
                       'provider': ORG}) + breadcrumbs_ld(
            [('Learn', '/learn'), (m['title'], m['path']), (t['title'], t['path'])])
        write_page(t['path'], '%s | %s | BioInfoCodex' % (t['title'], m['short']), first_sentence(t['body']),
                   content, page_id='edu', nav='learn', kind='Course topic', jsonld=topic_ld, og_type='article',
                   search_text=plain(t['body']))
    return flat


# ── glossary, cheat sheets ────────────────────────────────────────────────
def build_glossary():
    terms = sorted(json.loads(read('data/glossary.json')), key=lambda t: t['term'].lower())
    letters, items = [], ''
    for t in terms:
        letter = t['term'][0].upper()
        anchor = ''
        if letter not in letters:
            letters.append(letter)
            anchor = ' id="letter-%s"' % letter
        tid = slugify(t['term'])
        see = ''
        if t.get('see'):
            see = ' <a class="glossary-see" href="%s">Read more →</a>' % t['see']
        items += '<div class="glossary-item"%s><dt id="%s">%s</dt><dd>%s%s</dd></div>\n' % (anchor, tid, esc(t['term']), t['def'], see)
        pages.append({'path': '/learn/glossary#' + tid, 'title': t['term'], 'kind': 'Glossary',
                      'text': plain(t['def']), 'sitemap': False})
    jump = ''.join('<a href="#letter-%s">%s</a>' % (l, l) for l in letters)
    meta, body = front_matter(read('pages/glossary.html'))
    body = tokens(body, {'GLOSSARY_ITEMS': items, 'GLOSSARY_JUMP': jump, 'TERM_COUNT': str(len(terms))})
    gl_ld = ld({'@context': 'https://schema.org', '@type': 'DefinedTermSet', 'name': 'Bioinformatics glossary',
                'url': URL + '/learn/glossary',
                'hasDefinedTerm': [{'@type': 'DefinedTerm', 'name': t['term'], 'description': plain(t['def'])} for t in terms]})
    write_page('/learn/glossary', meta['title'], tokens(meta['description'], {'TERM_COUNT': str(len(terms))}),
               body, page_id='edu', nav='learn', kind='Reference', jsonld=gl_ld, search_text='')


# ── changelog (a small Markdown subset) ───────────────────────────────────
def md_inline(s):
    s = esc(s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'<a href="\2" rel="noopener">\1</a>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', lambda m: '<a href="%s/blob/main/%s" rel="noopener">%s</a>' % (RF['repo'], m.group(2), m.group(1)), s)
    return s


def md_to_html(md):
    out, para, items, in_code = [], [], [], False

    def flush():
        nonlocal para, items
        if para:
            out.append('<p>%s</p>' % md_inline(' '.join(para)))
            para = []
        if items:
            out.append('<ul>%s</ul>' % ''.join('<li>%s</li>' % md_inline(' '.join(i)) for i in items))
            items = []

    for line in md.split('\n'):
        if line.startswith('```'):
            flush() if not in_code else out.append('</code></pre>')
            if not in_code:
                out.append('<pre class="code-block"><code>')
            in_code = not in_code
            continue
        if in_code:
            out.append(esc(line))
            continue
        if not line.strip():
            if para:
                flush()
            continue
        h = re.match(r'(#{2,4}) (.*)', line)
        if h:
            flush()
            level = len(h.group(1))
            text = h.group(2)
            if level == 2:
                ver = re.match(r'(v[\d.]+)', text)
                out.append('<h2 id="%s">%s</h2>' % (ver.group(1) if ver else slugify(text), md_inline(text)))
            else:
                out.append('<h%d>%s</h%d>' % (level, md_inline(text), level))
            continue
        b = re.match(r'[-*] (.*)', line)
        if b:
            if para:
                flush()
            items.append([b.group(1)])
            continue
        if items and line.startswith('  '):
            items[-1].append(line.strip())
            continue
        if items:
            flush()
        para.append(line.strip())
    flush()
    return '\n'.join(out)


def build_changelog():
    md = read('data/rnaflow-changelog.md')
    md = re.sub(r'\A# .*\n', '', md)
    meta, body = front_matter(read('pages/changelog.html'))
    body = tokens(body, {'CHANGELOG': md_to_html(md)})
    write_page('/tools/rnaflow/changelog', meta['title'], meta['description'], body, page_id='doc', nav='tools',
               kind='Changelog', jsonld=breadcrumbs_ld([('Tools', '/tools'), ('RNAflow', '/tools/rnaflow'),
                                                         ('Changelog', '/tools/rnaflow/changelog')]))


# ── lessons ───────────────────────────────────────────────────────────────
def load_lessons():
    idx = ROOT / 'lesson-files' / 'index.json'
    return json.loads(idx.read_text(encoding='utf-8')) if idx.exists() else []


def build_lessons(lessons):
    cards = ''
    for c in lessons:
        meta_bits = ['%d min' % max(1, round(c.get('duration', 60) / 60)), '%d parts' % c.get('scenes', 0)]
        if c.get('simulations'):
            meta_bits.append('%d simulation%s' % (c['simulations'], 's' if c['simulations'] > 1 else ''))
        if c.get('questions'):
            meta_bits.append('%d quiz questions' % c['questions'])
        cards += '''
      <a class="lesson-card" href="/lessons/{slug}">
        <div class="lesson-thumb" style="background-image:url('/lesson-files/{slug}/{poster}')"></div>
        <div class="lesson-card-body">
          <div class="lesson-card-title">{title}</div>
          <div class="lesson-card-sum">{summary}</div>
          <div class="lesson-meta">{meta}</div>
        </div>
      </a>'''.format(slug=c['slug'], poster=c.get('poster', ''), title=esc(c['title']), summary=esc(c.get('summary', '')),
                     meta=''.join('<span>%s</span>' % b for b in meta_bits))
    meta, body = front_matter(read('pages/lessons.html'))
    body = tokens(body, {'LESSON_CARDS': cards or '<div class="lesson-empty">No lessons yet.</div>'})
    write_page('/lessons', meta['title'], meta['description'], body, page_id='lessons', nav='learn', kind='Lessons')

    for c in lessons:
        L = json.loads((ROOT / 'lesson-files' / c['slug'] / 'lesson.json').read_text(encoding='utf-8'))
        outline = ''.join('<li>%s</li>' % esc(s['title']) for s in L.get('scenes', []))
        transcript = ''
        for s in L.get('scenes', []):
            if s.get('narration'):
                transcript += '<h3>%s</h3>%s' % (esc(s['title']), ''.join('<p>%s</p>' % esc(x) for x in s['narration']))
        content = '''<div class="lesson-wrap" id="lesson-view" data-slug="{slug}">
  <a class="lesson-back" href="/lessons">← All lessons</a>
  <div class="label">{subject}</div>
  <h1 class="lesson-title">{title}</h1>
  <p class="lead">{summary}</p>
  <section class="lesson-block"><h2>In this lesson</h2><ol class="lesson-outline">{outline}</ol></section>
  {transcript}
</div>'''.format(slug=L['slug'], subject=esc(L.get('subject', 'Lesson')), title=esc(L['title']),
                 summary=esc(L.get('summary', '')), outline=outline,
                 transcript=('<details class="lesson-block lesson-transcript"><summary>Transcript</summary>%s</details>' % transcript) if transcript else '')
        video_ld = ''
        if L.get('video'):
            base = '%s/lesson-files/%s/' % (URL, L['slug'])
            video_ld = ld({'@context': 'https://schema.org', '@type': 'VideoObject', 'name': L['title'],
                           'description': L.get('summary', L['title']), 'thumbnailUrl': base + L.get('poster', ''),
                           'contentUrl': base + L['video'], 'duration': 'PT%dS' % int(L.get('duration', 0)),
                           'uploadDate': datetime.date.fromtimestamp(
                               (ROOT / 'lesson-files' / L['slug'] / 'lesson.json').stat().st_mtime).isoformat()})
        write_page('/lessons/' + L['slug'], '%s | Video lesson | BioInfoCodex' % esc(L['title']),
                   L.get('summary', L['title']), content, page_id='lesson', nav='learn', scripts=('lessons.js',),
                   kind='Video lesson', jsonld=video_ld,
                   og_image='%s/lesson-files/%s/%s' % (URL, L['slug'], L.get('poster', '')) if L.get('poster') else None)


# ── plain pages ───────────────────────────────────────────────────────────
GENERATED = {'learn.html', 'glossary.html', 'changelog.html', 'lessons.html', '404.html'}


def build_plain_pages(extra):
    for p in sorted((SRC / 'pages').glob('*.html')):
        if p.name in GENERATED:
            continue
        meta, body = front_matter(p.read_text(encoding='utf-8'))
        body = tokens(body, extra)
        scripts = tuple(s.strip() for s in meta.get('scripts', '').split(',') if s.strip())
        jl = jsonld_for(meta.get('jsonld', ''))
        if meta.get('crumbs'):
            trail = [tuple(x.strip() for x in c.split('=')) for c in meta['crumbs'].split('>')]
            jl += breadcrumbs_ld(trail)
        write_page(meta['path'], tokens(meta['title'], extra), tokens(meta['description'], extra), body,
                   page_id=meta.get('id', 'doc'), nav=meta.get('nav', ''), hero=meta.get('hero', 'light'),
                   scripts=scripts, jsonld=jl, kind=meta.get('kind', 'Page'),
                   robots=meta.get('robots', ''), sitemap=meta.get('sitemap', 'yes') != 'no',
                   og_image=(URL + meta['og_image']) if meta.get('og_image') else None,
                   og_image_alt=meta.get('og_image_alt'))


def build_404():
    meta, body = front_matter(read('pages/404.html'))
    write_page('/404', meta['title'], meta['description'], body, page_id='doc', robots='noindex',
               sitemap=False, out_file='404.html')
    pages.pop()


# ── outputs that describe the site ────────────────────────────────────────
def write_search_index():
    entries = []
    for p in pages:
        if p['path'] in ('/search',):
            continue
        entries.append({'u': p['path'], 't': p['title'], 'k': p['kind'], 'x': p['text'][:6000]})
    return publish_asset('search-index.json', json.dumps(entries, ensure_ascii=False, separators=(',', ':')))


def write_sitemap():
    urls = sorted({p['path'] for p in pages if p['sitemap'] and '#' not in p['path']},
                  key=lambda u: (u.count('/'), u))
    body = ''.join('  <url><loc>%s%s</loc><lastmod>%s</lastmod></url>\n' % (URL, u if u != '/' else '/', TODAY.isoformat())
                   for u in urls)
    (DIST / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s</urlset>\n' % body,
        encoding='utf-8')
    return len(urls)


def write_redirects():
    shutil.copy(SRC / '_redirects', DIST / '_redirects')


def copy_static():
    for name in ROOT_FILES:
        if (ROOT / name).exists():
            shutil.copy(ROOT / name, DIST / name)
    if (ROOT / 'lesson-files').exists():
        shutil.copytree(ROOT / 'lesson-files', DIST / 'lesson-files', ignore=shutil.ignore_patterns('.DS_Store'))
    if (SRC / 'static').exists():
        shutil.copytree(SRC / 'static', DIST, dirs_exist_ok=True, ignore=shutil.ignore_patterns('.DS_Store'))


def check_links():
    """Every internal href must point at a page or file that was written."""
    known = {p['path'].split('#')[0] for p in pages} | {'/'}
    bad = []
    for f in DIST.rglob('*.html'):
        text = f.read_text(encoding='utf-8')
        for href in set(re.findall(r'href="(/[^"#?]*)', text)):
            if href in known or href.rstrip('/') in known:
                continue
            if (DIST / href.lstrip('/')).exists():
                continue
            bad.append((str(f.relative_to(DIST)), href))
    return bad


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    build_assets()
    lessons = load_lessons()
    mods = load_modules()
    flat = build_course(mods, lessons)
    counts = {'MODULE_COUNT': str(len(mods)), 'TOPIC_COUNT': str(len(flat))}
    build_glossary()
    build_changelog()
    build_lessons(lessons)
    build_plain_pages(counts)
    build_404()
    copy_static()
    index_url = write_search_index()
    # the search page needs the hashed index URL, which only exists now
    sp = DIST / 'search' / 'index.html'
    sp.write_text(sp.read_text(encoding='utf-8').replace('__SEARCH_INDEX__', index_url), encoding='utf-8')
    n = write_sitemap()
    write_redirects()
    bad = check_links()
    print('built %d pages (%d in sitemap), %d modules, %d topics' % (
        len(list(DIST.rglob('*.html'))), n, len(mods), len(flat)))
    if bad:
        for f, href in bad[:40]:
            print('  broken link in %s -> %s' % (f, href))
        sys.exit('%d broken internal links' % len(bad))


if __name__ == '__main__':
    main()
    if '--serve' in sys.argv:
        import functools
        import http.server
        port = 8000
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
        print('serving dist/ at http://localhost:%d' % port)
        http.server.ThreadingHTTPServer(('127.0.0.1', port), handler).serve_forever()

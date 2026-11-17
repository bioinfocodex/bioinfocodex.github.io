"""Tiny SVG drawing helpers for the course figures.

Each figure is a plain, self-contained SVG file (no scripts, no external
fonts) so it can be opened and edited in any vector editor afterwards.
"""
import math
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / 'src' / 'static' / 'img' / 'learn'
W = 720
FONT = "system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

# name: (stroke, tint fill, text)
C = {
    'green':  ('#00a87e', '#e6faf5', '#01664b'),
    'blue':   ('#0969da', '#e7f1fd', '#0a4fa3'),
    'purple': ('#7c3aed', '#f1eafe', '#5b21b6'),
    'orange': ('#e0762a', '#fef3ea', '#9a4a06'),
    'red':    ('#e5484d', '#feecec', '#a4262c'),
    'grey':   ('#b6bfca', '#f6f8fa', '#4a5568'),
    'dark':   ('#0d1117', '#0d1117', '#ffffff'),
}
TEXT, MUTED, LINE = '#0d1117', '#5b6472', '#8b95a3'


def esc(t):
    return str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def col(c, i=0):
    return C[c][i] if c in C else c


class Fig:
    def __init__(self, h):
        self.h, self.o = h, []

    def raw(self, s):
        self.o.append(s)

    def rect(self, x, y, w, h, c='grey', r=8, fill=None, stroke=None, sw=1.5, dash=None, op=None):
        self.o.append('<rect x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" stroke="%s" stroke-width="%g"%s%s/>' % (
            x, y, w, h, r, fill if fill is not None else col(c, 1), stroke if stroke is not None else col(c, 0), sw,
            ' stroke-dasharray="%s"' % dash if dash else '', ' opacity="%g"' % op if op else ''))

    def text(self, x, y, t, size=12, c=TEXT, anchor='middle', weight=400, mono=False, italic=False, rot=None):
        self.o.append('<text x="%g" y="%g" font-size="%g" fill="%s" text-anchor="%s" font-weight="%d"%s%s%s>%s</text>' % (
            x, y, size, col(c, 2) if c in C else c, anchor, weight,
            ' font-family="%s"' % MONO if mono else '', ' font-style="italic"' if italic else '',
            ' transform="rotate(%g %g %g)"' % (rot, x, y) if rot is not None else '', esc(t)))

    def box(self, x, y, w, h, label, c='green', sub=None, size=13, weight=600):
        self.rect(x, y, w, h, c)
        lines = label.split('\n')
        n = len(lines) + (1 if sub else 0)
        lh = size + 4
        top = y + h / 2 - (n * lh) / 2 + size - 1
        for i, ln in enumerate(lines):
            self.text(x + w / 2, top + i * lh, ln, size, c, weight=weight)
        if sub:
            self.text(x + w / 2, top + len(lines) * lh, sub, size - 2, MUTED)

    def line(self, x1, y1, x2, y2, c=LINE, w=1.5, dash=None):
        self.o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="%g" stroke-linecap="round"%s/>' % (
            x1, y1, x2, y2, col(c, 0), w, ' stroke-dasharray="%s"' % dash if dash else ''))

    def arrow(self, x1, y1, x2, y2, c=LINE, w=1.6, label=None, dash=None, size=11):
        a = math.atan2(y2 - y1, x2 - x1)
        hx, hy = x2 - 8 * math.cos(a), y2 - 8 * math.sin(a)
        self.line(x1, y1, hx, hy, c, w, dash)
        p = [(x2, y2), (hx + 4.5 * math.sin(a), hy - 4.5 * math.cos(a)), (hx - 4.5 * math.sin(a), hy + 4.5 * math.cos(a))]
        self.o.append('<polygon points="%s" fill="%s"/>' % (' '.join('%.1f,%.1f' % q for q in p), col(c, 0)))
        if label:
            self.text((x1 + x2) / 2, (y1 + y2) / 2 - 6, label, size, MUTED)

    def circle(self, x, y, r, c='green', fill=None, sw=1.5, op=None):
        self.o.append('<circle cx="%g" cy="%g" r="%g" fill="%s" stroke="%s" stroke-width="%g"%s/>' % (
            x, y, r, fill if fill is not None else col(c, 1), col(c, 0), sw, ' opacity="%g"' % op if op else ''))

    def dot(self, x, y, r=3.5, c='green', op=None):
        self.o.append('<circle cx="%g" cy="%g" r="%g" fill="%s"%s/>' % (x, y, r, col(c, 0), ' opacity="%g"' % op if op else ''))

    def path(self, d, c=LINE, w=2, fill='none', dash=None, op=None):
        self.o.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%g" stroke-linecap="round" stroke-linejoin="round"%s%s/>' % (
            d, fill, col(c, 0), w, ' stroke-dasharray="%s"' % dash if dash else '', ' opacity="%g"' % op if op else ''))

    def poly(self, pts, c=LINE, w=2, fill='none', op=None):
        self.path('M' + ' L'.join('%.1f %.1f' % p for p in pts), c, w, fill, op=op)

    def flow(self, labels, y, h=54, x0=16, x1=704, colors=None, subs=None, gap=22, size=12.5):
        """A left-to-right row of boxes joined by arrows. Returns box x positions."""
        n = len(labels)
        bw = (x1 - x0 - gap * (n - 1)) / n
        xs = []
        for i, lab in enumerate(labels):
            x = x0 + i * (bw + gap)
            xs.append(x)
            cs = colors or ['green']
            self.box(x, y, bw, h, lab, cs[i % len(cs)], subs[i] if subs else None, size)
            if i:
                self.arrow(x - gap + 3, y + h / 2, x - 3, y + h / 2)
        return xs, bw

    def axes(self, x, y, w, h, xl=None, yl=None):
        """Axes with origin at bottom-left (x, y+h)."""
        self.line(x, y, x, y + h, TEXT, 1.4)
        self.line(x, y + h, x + w, y + h, TEXT, 1.4)
        if xl:
            self.text(x + w / 2, y + h + 30, xl, 12, MUTED)
        if yl:
            self.text(x - 34, y + h / 2, yl, 12, MUTED, rot=-90)

    def save(self, name, title):
        OUT.mkdir(parents=True, exist_ok=True)
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
               'font-family="%s">\n<title>%s</title>\n<rect width="%d" height="%d" fill="#ffffff"/>\n%s\n</svg>\n') % (
            W, self.h, W, self.h, FONT, esc(title), W, self.h, '\n'.join(self.o))
        (OUT / (name + '.svg')).write_text(svg, encoding='utf-8')


def rng(seed):
    """Small deterministic generator so scatter plots are identical on every build."""
    state = [seed]

    def nxt():
        state[0] = (state[0] * 1103515245 + 12345) % 2147483648
        return state[0] / 2147483648
    return nxt

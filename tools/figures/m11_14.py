"""Figures for modules 11 to 14."""
import math
from lib import Fig, MUTED, TEXT, LINE, C, rng


def track(f, x, y, w, h, peaks, c, base=0.06, seed=3):
    r = rng(seed)
    pts = [(x, y + h)]
    for t in range(0, w + 1, 4):
        v = base * (0.5 + r())
        for mu, sd, amp in peaks:
            v += amp * math.exp(-((t - mu) ** 2) / (2 * sd * sd))
        pts.append((x + t, y + h - min(v, 1) * h))
    pts.append((x + w, y + h))
    f.path('M' + ' L'.join('%.1f %.1f' % p for p in pts) + ' Z', c, 1.2, fill=C[c][1])


def f11_1():
    f = Fig(260)
    x, w = 150, 540
    rows = [('TF ChIP', 'narrow peaks', [(140, 9, 0.9), (400, 10, 0.7)], 'blue'),
            ('H3K27me3 ChIP', 'broad domain', [(270, 90, 0.5)], 'purple'),
            ('Input control', 'background', [], 'grey')]
    for i, (name, sub, pk, c) in enumerate(rows):
        y = 20 + i * 62
        f.text(134, y + 26, name, 12, anchor='end', weight=600)
        f.text(134, y + 41, sub, 10.5, MUTED, anchor='end')
        track(f, x, y, w, 50, pk, c, 0.1, seed=3 + i)
        f.line(x, y + 50, x + w, y + 50, LINE, 1)
    y = 214
    f.line(x, y, x + w, y, TEXT, 1.6)
    f.rect(x + 160, y - 8, 120, 16, 'green', 3)
    f.rect(x + 420, y - 8, 90, 16, 'green', 3)
    f.arrow(x + 150, y - 14, x + 172, y - 14, 'green')
    f.text(134, y + 4, 'Genes', 12, anchor='end', weight=600)
    f.rect(x + 126, 204, 28, 6, 'red', 2, fill=C['red'][0], sw=0)
    f.rect(x + 386, 204, 28, 6, 'red', 2, fill=C['red'][0], sw=0)
    f.text(x + 270, 246, 'Red bars: peaks called where ChIP signal clearly exceeds the input control', 11, MUTED)
    f.save('11-1', 'ChIP-seq signal tracks: narrow peaks, a broad domain and the input control')


def f11_2():
    f = Fig(250)
    f.text(20, 24, 'Chromatin', 12.5, anchor='start', weight=700)
    f.line(30, 80, 690, 80, TEXT, 2)
    for cx in (70, 130, 190, 250, 530, 590, 650):
        f.circle(cx, 80, 24, 'purple')
    f.text(160, 124, 'closed: DNA wrapped on nucleosomes', 11, 'purple')
    f.text(590, 124, 'closed', 11, 'purple')
    f.text(390, 50, 'open region (promoter or enhancer)', 11, 'green', weight=600)
    for cx in (310, 350, 390, 430, 470):
        f.o.append('<polygon points="%d,58 %d,58 %d,74" fill="%s"/>' % (cx - 6, cx + 6, cx, C['orange'][0]))
    f.text(390, 104, 'Tn5 cuts and adds adapters here', 10.5, 'orange')
    f.text(20, 158, 'ATAC-seq signal', 12.5, anchor='start', weight=700)
    track(f, 30, 166, 660, 54, [(360, 44, 0.95)], 'green', 0.07, seed=9)
    f.line(30, 220, 690, 220, LINE, 1)
    f.text(360, 242, 'Reads pile up where the DNA is accessible. No antibody is needed, and 50,000 cells are enough.', 11, MUTED)
    f.save('11-2', 'Tn5 transposase cutting open chromatin in ATAC-seq')


def f11_3():
    f = Fig(250)
    seq = 'ACGTTCGGACGA'
    meth = {1}          # index of the methylated C
    x0, cw = 240, 34
    def row(y, label, letters, colors):
        f.text(220, y + 5, label, 12, anchor='end', weight=600)
        for i, ch in enumerate(letters):
            f.rect(x0 + i * cw, y - 14, cw - 4, 26, colors[i], 4)
            f.text(x0 + i * cw + (cw - 4) / 2, y + 5, ch, 14, colors[i], mono=True, weight=700)
    cols = ['grey'] * len(seq)
    for i, ch in enumerate(seq):
        if ch == 'C':
            cols[i] = 'green' if i in meth else 'orange'
    row(50, 'Original DNA', seq, cols)
    f.text(x0 + 1 * cw + 15, 26, 'methylated', 10.5, 'green')
    conv = ''.join('U' if (ch == 'C' and i not in meth) else ch for i, ch in enumerate(seq))
    row(118, 'After bisulfite', conv, cols)
    final = conv.replace('U', 'T')
    row(186, 'After PCR, as read', final, cols)
    for y in (70, 138):
        f.arrow(x0 + 200, y, x0 + 200, y + 24)
    f.text(x0 + 212, 88, 'unmethylated C becomes U', 10.5, MUTED, anchor='start')
    f.text(x0 + 212, 156, 'U is copied as T', 10.5, MUTED, anchor='start')
    f.text(360, 230, 'A C that is still read as C was methylated; a C read as T was not', 11.5, weight=600)
    f.save('11-3', 'Bisulfite conversion distinguishes methylated from unmethylated cytosines')


def f12_1():
    f = Fig(250)
    f.text(20, 26, 'Reads', 12, anchor='start', weight=700)
    r = rng(4)
    for i in range(16):
        x = 100 + r() * 480
        f.rect(x, 14 + (i % 4) * 11, 90, 6, 'blue', 2, fill=C['blue'][0], sw=0, op=0.8)
    f.arrow(360, 64, 360, 82, label=None)
    f.text(372, 78, 'find overlaps', 10.5, MUTED, anchor='start')
    f.text(20, 106, 'Contigs', 12, anchor='start', weight=700)
    for x, w in [(100, 150), (280, 90), (400, 190), (620, 60)]:
        f.rect(x, 94, w, 16, 'green', 4, fill=C['green'][0], sw=0)
    f.text(265, 88, 'repeat', 9.5, 'red')
    f.text(385, 88, 'repeat', 9.5, 'red')
    f.arrow(360, 120, 360, 138)
    f.text(372, 134, 'link with long reads or Hi-C', 10.5, MUTED, anchor='start')
    f.text(20, 162, 'Scaffolds', 12, anchor='start', weight=700)
    for x, w in [(100, 150), (280, 90), (400, 190)]:
        f.rect(x, 150, w, 16, 'purple', 4, fill=C['purple'][0], sw=0)
    for x1, x2 in [(250, 280), (370, 400)]:
        f.line(x1, 158, x2, 158, 'purple', 1.4, '3 3')
        f.text((x1 + x2) / 2, 180, 'NNN', 9.5, MUTED, mono=True)
    f.rect(620, 150, 60, 16, 'purple', 4, fill=C['purple'][0], sw=0)
    f.arrow(360, 186, 360, 204)
    f.text(20, 226, 'Chromosome', 12, anchor='start', weight=700)
    f.rect(100, 214, 580, 16, 'orange', 8, fill=C['orange'][0], sw=0)
    f.text(390, 246, 'telomere to telomere when every gap is closed', 10.5, MUTED)
    f.save('12-1', 'Genome assembly from reads to contigs, scaffolds and chromosomes')


def f12_2():
    f = Fig(250)
    f.text(360, 24, 'N50: sort contigs longest first, then walk until half the assembly is covered', 12.5, weight=700)
    lens = [80, 70, 50, 40, 30, 20, 10]
    x, total = 60, sum(lens)
    scale = 600 / total
    acc = 0
    for i, L in enumerate(lens):
        w = L * scale
        reached = acc < total / 2 <= acc + L
        c = 'orange' if reached else ('green' if acc + L <= total / 2 else 'grey')
        f.rect(x, 60, w - 3, 40, c, 4)
        f.text(x + w / 2, 85, ('%d kb' if w > 50 else '%d') % L, 11, c, weight=600)
        if reached:
            f.text(x + w / 2, 122, 'N50 = %d kb' % L, 12.5, 'orange', weight=700)
            f.text(x + w / 2, 138, 'L50 = %d contigs' % (i + 1), 11, MUTED)
        x += w
        acc += L
    hx = 60 + total / 2 * scale
    f.line(hx, 44, hx, 108, 'red', 1.6, '5 4')
    f.text(hx, 40, '50% of 300 kb = 150 kb', 10.5, 'red')
    f.text(360, 176, 'Half of all assembled bases sit in contigs of at least the N50 length', 11.5)
    f.text(360, 200, 'A larger N50 means a more contiguous assembly, but it says nothing about correctness:', 11, MUTED)
    f.text(360, 218, 'wrongly joined contigs raise N50, which is why BUSCO completeness is reported with it', 11, MUTED)
    f.save('12-2', 'How the N50 statistic is calculated')


def f12_3():
    f = Fig(260)
    x, w = 170, 520
    f.text(150, 34, 'RNA-seq coverage', 11.5, anchor='end', weight=600)
    for a, b in [(40, 120), (210, 300), (390, 470)]:
        pts = 'M%d 50 L%d 22 L%d 22 L%d 50 Z' % (x + a, x + a + 8, x + b - 8, x + b)
        f.path(pts, 'blue', 1.2, fill=C['blue'][1])
    f.line(x, 50, x + w, 50, LINE, 1)
    f.text(150, 84, 'Protein homology', 11.5, anchor='end', weight=600)
    for a, b in [(56, 120), (210, 300), (390, 452)]:
        f.rect(x + a, 72, b - a, 14, 'purple', 3)
    f.line(x + 120, 79, x + 210, 79, 'purple', 1.2, '3 3'); f.line(x + 300, 79, x + 390, 79, 'purple', 1.2, '3 3')
    f.text(150, 124, 'Ab initio prediction', 11.5, anchor='end', weight=600)
    for a, b in [(48, 120), (210, 300), (330, 350), (390, 462)]:
        f.rect(x + a, 112, b - a, 14, 'orange', 3)
    f.text(x + 340, 106, 'false exon', 9.5, 'red')
    f.line(x, 150, x + w, 150, LINE, 1, '2 4')
    f.text(150, 186, 'Final gene model', 11.5, anchor='end', weight=700)
    f.line(x + 40, 181, x + 470, 181, 'green', 1.6)
    for a, b in [(40, 120), (210, 300), (390, 470)]:
        f.rect(x + a, 172, b - a, 18, 'green', 3, fill=C['green'][0], sw=0)
    f.arrow(x + 474, 181, x + 500, 181, 'green')
    f.text(x + 80, 208, 'exon 1', 10.5, MUTED); f.text(x + 255, 208, 'exon 2', 10.5, MUTED); f.text(x + 430, 208, 'exon 3', 10.5, MUTED)
    f.text(360, 240, 'Annotation pipelines weigh several lines of evidence; agreement between them gives the model', 11, MUTED)
    f.save('12-3', 'Evidence tracks combined into a final gene model')


def f13_1():
    f = Fig(270)
    x, y, w, h = 80, 20, 560, 200
    f.axes(x, y, w, h, 'Frequency of allele A (p)', 'Genotype frequency')
    def curve(fn, c):
        f.poly([(x + t / 100 * w, y + h - fn(t / 100) * h) for t in range(0, 101, 2)], c, 2.4)
    curve(lambda p: p * p, 'blue')
    curve(lambda p: 2 * p * (1 - p), 'green')
    curve(lambda p: (1 - p) ** 2, 'orange')
    for v in (0, 0.25, 0.5, 0.75, 1):
        f.text(x + v * w, y + h + 14, v, 10.5, MUTED)
        f.text(x - 8, y + h - v * h + 4, v, 10.5, MUTED, anchor='end')
    f.text(x + w - 110, y + 22, 'AA = p²', 12, 'blue', weight=700)
    f.text(x + 110, y + 22, 'aa = q²', 12, 'orange', weight=700)
    f.text(x + w / 2, y + h - 0.5 * h - 10, 'Aa = 2pq', 12, 'green', weight=700)
    f.line(x + 0.5 * w, y + h - 0.5 * h, x + 0.5 * w, y + h, LINE, 1, '3 3')
    f.text(360, 262, 'Heterozygotes peak at 50% when both alleles are equally common (p = q = 0.5)', 10.5, MUTED)
    f.save('13-1', 'Hardy-Weinberg genotype frequencies as a function of allele frequency')


def f13_2():
    f = Fig(270)
    x, y, w, h = 70, 20, 620, 190
    f.axes(x, y, w, h, 'Chromosome', '-log10(p)')
    r = rng(21)
    widths = [9, 9, 8, 8, 7, 7, 6, 6, 6, 5, 5, 5, 4, 4, 4, 4, 3, 3, 3, 3, 2, 2]
    tot = sum(widths)
    cx = x
    def Y(v):
        return y + h - v / 14 * h
    for i, cw in enumerate(widths):
        pw = cw / tot * w
        c = 'blue' if i % 2 == 0 else 'grey'
        for k in range(int(cw * 9)):
            v = -math.log10(max(r(), 1e-6)) * 0.95
            f.dot(cx + r() * pw, Y(min(v, 6.2)), 1.9, c, 0.7)
        if i == 5:
            for k in range(22):
                d = (r() - 0.5)
                f.dot(cx + pw / 2 + d * pw * 0.7, Y(12.5 * math.exp(-(d * 3.2) ** 2) - r() * 2.5), 2.2, 'red', 0.85)
        if i < 12 or i % 2 == 1:
            f.text(cx + pw / 2, y + h + 14, i + 1, 9.5, MUTED)
        cx += pw
    f.line(x, Y(7.3), x + w, Y(7.3), 'red', 1.3, '5 4')
    f.text(x + w - 4, Y(7.3) - 5, 'genome-wide significance: p = 5 × 10⁻⁸', 10.5, 'red', anchor='end')
    f.text(x + 232, Y(12.9), 'associated locus', 11, 'red', anchor='start', weight=600)
    f.text(360, 262, 'Illustration with simulated points. Each dot is one SNP tested against the trait.', 10.5, MUTED)
    f.save('13-2', 'A Manhattan plot from a genome-wide association study')


def f14_1():
    f = Fig(250)
    nodes = {'hub': (210, 120), 'a': (120, 60), 'b': (110, 150), 'c': (200, 210), 'd': (290, 190), 'e': (300, 60), 'f': (210, 36),
             'g': (430, 110), 'h': (500, 60), 'i': (520, 150), 'j': (450, 190), 'k': (590, 100)}
    edges = [('hub', k) for k in 'abcdef'] + [('a', 'f'), ('e', 'f'), ('c', 'd'), ('g', 'h'), ('g', 'i'), ('g', 'j'), ('h', 'i'), ('i', 'j'),
                                               ('h', 'k'), ('i', 'k'), ('d', 'g')]
    for a, b in edges:
        bridge = (a, b) == ('d', 'g')
        f.line(nodes[a][0], nodes[a][1], nodes[b][0], nodes[b][1], 'orange' if bridge else LINE, 2.2 if bridge else 1.4)
    for k, (nx, ny) in nodes.items():
        if k == 'hub':
            f.circle(nx, ny, 20, 'red', fill=C['red'][0])
            f.text(nx, ny + 4, 'hub', 10.5, '#ffffff', weight=700)
        else:
            c = 'blue' if k in 'abcdef' else 'green'
            f.circle(nx, ny, 11, c, fill=C[c][0])
    f.text(120, 240, 'Module 1', 11.5, 'blue', weight=700)
    f.text(505, 216, 'Module 2: densely connected = likely a complex', 11.5, 'green', weight=700)
    f.text(372, 166, 'bridge', 10.5, 'orange', weight=600)
    f.text(60, 108, 'degree 6', 10.5, 'red', anchor='start')
    f.text(640, 30, 'node = protein', 11, MUTED, anchor='end')
    f.text(640, 46, 'edge = interaction', 11, MUTED, anchor='end')
    f.save('14-1', 'A protein interaction network with a hub, two modules and a bridging edge')


def f14_2():
    f = Fig(260)
    layers = [('Genome', 'variants, CNV', 'blue'), ('Epigenome', 'methylation, accessibility', 'purple'),
              ('Transcriptome', 'mRNA abundance', 'green'), ('Proteome', 'protein abundance, PTMs', 'orange'),
              ('Metabolome', 'small molecules', 'red')]
    for i, (name, sub, c) in enumerate(layers):
        y = 16 + i * 44
        f.rect(30, y, 300, 36, c)
        f.text(46, y + 22, name, 12.5, c, anchor='start', weight=700)
        f.text(316, y + 22, sub, 10.5, MUTED, anchor='end')
        if i:
            f.arrow(180, y - 8, 180, y - 1)
        f.arrow(332, y + 18, 408, 126 + (i - 2) * 6)
    f.box(410, 86, 130, 80, 'Integration', 'grey', 'MOFA, DIABLO')
    f.arrow(542, 126, 588, 126)
    f.box(590, 86, 114, 80, 'Phenotype', 'dark', None)
    f.text(360, 250, 'Each layer explains part of the phenotype; shared factors across layers point to mechanism', 11, MUTED)
    f.save('14-2', 'Layers of omics data integrated to explain a phenotype')


ALL = [f11_1, f11_2, f11_3, f12_1, f12_2, f12_3, f13_1, f13_2, f14_1, f14_2]

"""Figures for modules 6 to 10."""
import math
from lib import Fig, MUTED, TEXT, LINE, C, rng


def f6_1():
    f = Fig(240)
    f.text(20, 24, 'Per sample', 12, anchor='start', weight=700)
    f.flow(['FASTQ', 'BWA-MEM', 'Sort', 'Mark\nduplicates', 'BQSR', 'Haplotype\nCaller'], 36, 60,
           colors=['orange', 'blue', 'blue', 'blue', 'blue', 'green'],
           subs=['reads', 'align', 'by position', None, 'recalibrate', None], gap=18, size=12)
    f.text(704, 140, 'All samples together', 12, anchor='end', weight=700)
    xs, bw = f.flow(['GVCF per sample', 'Joint genotyping', 'Filter (VQSR or hard)', 'Annotated VCF'], 150, 54,
                    x0=16, x1=704, colors=['green', 'purple', 'purple', 'red'], gap=24, size=12)
    f.path('M650 96 C650 126 80 116 80 148', LINE, 1.5, dash='4 4')
    f.text(360, 230, 'Calling each sample to a GVCF first lets new samples be added without redoing the alignment', 11, MUTED)
    f.save('6-1', 'The GATK germline short-variant pipeline')


def f6_2():
    f = Fig(240)
    cols = [('CHROM', 'chr7', 'blue'), ('POS', '140753336', 'blue'), ('ID', 'rs113488022', 'grey'), ('REF', 'A', 'green'),
            ('ALT', 'T', 'red'), ('QUAL', '812.6', 'orange'), ('FILTER', 'PASS', 'green'), ('INFO', 'DP=64;AF=0.5', 'purple'),
            ('FORMAT', 'GT:AD:DP', 'grey'), ('SAMPLE', '0/1:31,33:64', 'grey')]
    widths = [50, 78, 86, 36, 36, 50, 54, 100, 74, 100]
    x = 16
    notes = {'POS': '1-based position', 'REF': 'reference allele', 'ALT': 'observed allele', 'QUAL': 'Phred confidence',
             'INFO': 'site-level annotations', 'SAMPLE': 'genotype and depths'}
    for (name, val, c), w in zip(cols, widths):
        f.rect(x, 50, w, 26, c, 4)
        f.text(x + w / 2, 67, name, 10.5, c, weight=700)
        f.rect(x, 80, w, 26, 'grey', 4, fill='#ffffff')
        f.text(x + w / 2, 97, val, 9.6, TEXT, mono=True)
        x += w + 4
    f.text(360, 28, 'One line of a VCF file is one variant site', 13, weight=700)
    f.text(30, 140, '0/1', 13, 'purple', anchor='start', mono=True, weight=700)
    f.text(70, 140, 'heterozygous: one reference allele, one alternate', 11.5, anchor='start')
    f.text(30, 164, 'AD 31,33', 13, 'purple', anchor='start', mono=True, weight=700)
    f.text(110, 164, '31 reads support A and 33 support T', 11.5, anchor='start')
    f.text(30, 188, 'DP 64', 13, 'purple', anchor='start', mono=True, weight=700)
    f.text(110, 188, 'total read depth at this position', 11.5, anchor='start')
    f.text(360, 224, 'Genotypes: 0/0 homozygous reference, 0/1 heterozygous, 1/1 homozygous alternate', 11, MUTED)
    f.save('6-2', 'Anatomy of one VCF record')


def f6_3():
    f = Fig(250)
    steps = [('Fragment', 'orange'), ('End repair + A-tail', 'blue'), ('Ligate adapters', 'purple'), ('PCR + index', 'green')]
    f.flow([s for s, _ in steps], 20, 44, colors=[c for _, c in steps], size=12)
    f.text(360, 104, 'The finished library molecule', 12.5, weight=700)
    parts = [(60, 'P5', 'dark'), (56, 'i5 index', 'orange'), (84, 'Read 1 primer', 'blue'), (200, 'DNA insert', 'green'),
             (84, 'Read 2 primer', 'blue'), (56, 'i7 index', 'orange'), (60, 'P7', 'dark')]
    x = 60
    for w, lab, c in parts:
        f.rect(x, 122, w, 34, c, 3)
        f.text(x + w / 2, 143, lab, 10.2, c if c != 'dark' else '#ffffff', weight=600)
        x += w
    f.arrow(204, 172, 330, 172, 'blue')
    f.text(264, 190, 'Read 1', 11, 'blue')
    f.arrow(516, 172, 390, 172, 'blue')
    f.text(456, 190, 'Read 2', 11, 'blue')
    f.text(90, 180, 'binds the flow cell', 10.5, MUTED)
    f.text(630, 180, 'binds the flow cell', 10.5, MUTED)
    f.text(360, 226, 'Indexes are short barcodes that let many samples share one sequencing lane', 11, MUTED)
    f.save('6-3', 'Library preparation steps and the structure of an Illumina library molecule')


def f7_1():
    f = Fig(260)
    x, y, w, h = 70, 30, 600, 170
    f.axes(x, y, w, h, 'p-value', 'Number of genes')
    counts = [152, 66, 52, 47, 45, 42, 44, 41, 43, 40, 42, 41, 39, 42, 40, 41, 43, 40, 41, 42]
    bw = w / 20
    for i, c in enumerate(counts):
        bh = c / 160 * h
        null = min(c, 41) / 160 * h
        f.rect(x + i * bw + 1, y + h - null, bw - 2, null, 'grey', 0, fill='#c9d1db', sw=0)
        if bh > null:
            f.rect(x + i * bw + 1, y + h - bh, bw - 2, bh - null, 'green', 0, fill=C['green'][0], sw=0)
    for v in (0, 0.25, 0.5, 0.75, 1):
        f.text(x + v * w, y + h + 14, v, 10.5, MUTED)
    f.line(x, y + h - 41 / 160 * h, x + w, y + h - 41 / 160 * h, 'red', 1.3, '5 4')
    f.text(x + w - 4, y + h - 41 / 160 * h - 6, 'what pure chance produces (uniform)', 11, 'red', anchor='end')
    f.text(x + 46, y + 22, 'excess of small p-values:', 11.5, 'green', anchor='start', weight=600)
    f.text(x + 46, y + 38, 'genes with a real effect', 11.5, 'green', anchor='start')
    f.text(360, 252, 'A healthy p-value histogram: flat, with a peak near zero. Illustration, not real data.', 10.5, MUTED)
    f.save('7-1', 'A p-value histogram showing true effects above a uniform null')


def f7_2():
    f = Fig(250)
    def panel(x0, title, vals, unit):
        f.text(x0 + 150, 24, title, 12.5, weight=700)
        f.line(x0 + 20, 190, x0 + 290, 190, TEXT, 1.4)
        for i, (lab, v, c) in enumerate(vals):
            bx = x0 + 60 + i * 110
            bh = v / 200 * 130
            f.rect(bx, 190 - bh, 70, bh, c, 3)
            f.text(bx + 35, 190 - bh - 6, ('%g' % v) + unit, 11.5, c, weight=600)
            f.text(bx + 35, 206, lab, 11, MUTED)
    panel(20, 'Raw counts for one gene', [('Sample A', 100, 'blue'), ('Sample B', 200, 'orange')], '')
    panel(380, 'After normalisation', [('Sample A', 100, 'blue'), ('Sample B', 100, 'orange')], '')
    f.text(115, 222, '10 M reads', 10.5, MUTED)
    f.text(225, 222, '20 M reads', 10.5, MUTED)
    f.arrow(330, 120, 384, 120)
    f.text(357, 110, 'divide by', 10, MUTED)
    f.text(357, 138, 'size factor', 10, MUTED)
    f.text(530, 222, 'no real difference', 10.5, MUTED)
    f.text(360, 244, 'Sample B was simply sequenced twice as deeply', 11, MUTED)
    f.save('7-2', 'Why raw counts must be normalised for sequencing depth')


def f7_3():
    f = Fig(270)
    x, y, w, h = 80, 20, 560, 196
    f.axes(x, y, w, h, 'PC1: 62% of variance', 'PC2: 18% of variance')
    r = rng(11)
    for cx, cy, c in [(190, 120, 'blue'), (500, 110, 'orange')]:
        f.o.append('<ellipse cx="%d" cy="%d" rx="66" ry="52" fill="%s" stroke="%s" stroke-dasharray="4 4"/>' % (cx, cy, C[c][1], C[c][0]))
        for i in range(4 if c == 'orange' else 5):
            f.circle(cx + (r() - 0.5) * 80, cy + (r() - 0.5) * 60, 7, c, fill=C[c][0])
    f.circle(430, 186, 7, 'orange', fill=C['orange'][0])
    f.arrow(380, 196, 420, 189, 'red')
    f.text(374, 200, 'outlier: check this sample', 11, 'red', anchor='end')
    f.text(190, 46, 'control', 12, 'blue', weight=700)
    f.text(500, 40, 'treated', 12, 'orange', weight=700)
    f.text(345, 124, 'separation along PC1', 10.5, MUTED)
    f.text(345, 138, '= the treatment effect', 10.5, MUTED)
    f.text(360, 262, 'Illustration. Replicates should cluster together and conditions should separate.', 10.5, MUTED)
    f.save('7-3', 'A PCA plot used for sample quality control')


def f8_1():
    f = Fig(250)
    f.flow(['Tissue', 'Single cells', 'Droplets', 'Library', 'Sequencing', 'Count matrix'], 20, 50,
           colors=['orange', 'orange', 'blue', 'blue', 'purple', 'green'],
           subs=[None, 'suspension', 'cell + bead', 'barcoded cDNA', None, 'cells × genes'], gap=16, size=11.8)
    f.text(180, 104, 'Inside one droplet', 12, weight=700)
    f.circle(110, 170, 52, 'blue')
    f.circle(92, 172, 20, 'orange')
    f.text(92, 176, 'cell', 10.5, 'orange')
    f.circle(134, 166, 15, 'purple')
    f.text(134, 170, 'bead', 9.5, 'purple')
    x = 196
    for w, lab, c in [(70, 'cell barcode', 'purple'), (50, 'UMI', 'orange'), (60, 'poly-T', 'grey'), (90, 'cDNA', 'green')]:
        f.rect(x, 152, w, 30, c, 3)
        f.text(x + w / 2, 171, lab, 10.5, c, weight=600)
        x += w
    f.text(331, 204, 'barcode says which cell; UMI says which original molecule', 10.5, MUTED)
    r = rng(5)
    for cx, cy, c in [(560, 150, 'blue'), (620, 190, 'green'), (650, 130, 'orange'), (580, 208, 'purple')]:
        for i in range(16):
            f.dot(cx + (r() - 0.5) * 44, cy + (r() - 0.5) * 34, 2.4, c, 0.8)
    f.text(606, 104, 'Clusters = cell types', 12, weight=700)
    f.save('8-1', 'Droplet-based single-cell RNA-seq from tissue to clusters')


def f8_2():
    f = Fig(250)
    f.rect(30, 30, 330, 190, 'grey')
    f.text(195, 50, 'All genes tested (background): 15,000', 11, MUTED)
    f.o.append('<circle cx="155" cy="135" r="62" fill="%s" stroke="%s" stroke-width="1.5" opacity="0.85"/>' % (C['blue'][1], C['blue'][0]))
    f.o.append('<circle cx="235" cy="135" r="62" fill="%s" stroke="%s" stroke-width="1.5" opacity="0.7"/>' % (C['orange'][1], C['orange'][0]))
    f.text(124, 132, 'DE genes', 11.5, 'blue', weight=600)
    f.text(124, 148, '500', 11.5, 'blue')
    f.text(274, 132, 'Pathway', 11.5, 'orange', weight=600)
    f.text(274, 148, '200', 11.5, 'orange')
    f.text(195, 132, 'overlap', 10.5, TEXT, weight=600)
    f.text(195, 148, '30', 12, TEXT, weight=700)
    f.text(540, 46, 'Is 30 more than chance?', 12.5, weight=700)
    rows = [('', 'In pathway', 'Not in pathway'), ('DE', '30', '470'), ('Not DE', '170', '14,330')]
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            bx, by = 400 + j * 100, 64 + i * 34
            f.rect(bx, by, 96, 30, 'grey' if (i == 0 or j == 0) else 'green', 3)
            f.text(bx + 48, by + 19, v, 11, TEXT if i and j else MUTED, weight=600 if i and j else 400)
    f.text(548, 190, 'Expected by chance: 500 × 200 / 15,000 ≈ 6.7', 11, MUTED)
    f.text(548, 208, 'Observed 30, so about 4.5 times enriched', 11, 'green', weight=600)
    f.text(548, 226, "Fisher's exact or hypergeometric test gives the p-value", 10.5, MUTED)
    f.save('8-2', 'Over-representation analysis as a two by two table')


def f8_3():
    f = Fig(250)
    f.text(360, 22, '5-fold cross-validation', 13, weight=700)
    for row in range(5):
        y = 38 + row * 30
        f.text(96, y + 16, 'Round %d' % (row + 1), 11, MUTED, anchor='end')
        for k in range(5):
            test = k == row
            f.rect(108 + k * 88, y, 84, 22, 'orange' if test else 'blue', 3)
            f.text(108 + k * 88 + 42, y + 15, 'test' if test else 'train', 10.5, 'orange' if test else 'blue', weight=600 if test else 400)
        f.arrow(552, y + 11, 580, y + 11)
        f.text(586, y + 15, 'score %d' % (row + 1), 11, anchor='start')
    f.text(360, 206, 'Every sample is tested exactly once, and never by a model that saw it during training', 11, MUTED)
    f.text(360, 228, 'Report the mean and spread of the five scores, then confirm on a held-out test set', 11, MUTED)
    f.save('8-3', 'Five-fold cross-validation')


def f8_4():
    f = Fig(250)
    f.box(20, 95, 130, 60, 'Sample DNA', 'grey', 'gut, soil, water')
    f.text(190, 40, '16S amplicon', 12.5, 'blue', weight=700, anchor='start')
    xs, bw = f.flow(['PCR one\nmarker gene', 'Denoise\nto ASVs', 'Taxonomy'], 50, 54, x0=190, x1=560, colors=['blue'], gap=20, size=11.5)
    f.box(580, 50, 124, 54, 'Who is there', 'blue', 'genus level', 12)
    f.arrow(562, 77, 578, 77)
    f.text(190, 146, 'Shotgun metagenomics', 12.5, 'green', weight=700, anchor='start')
    f.flow(['Sequence\nall DNA', 'Remove\nhost reads', 'Classify or\nassemble'], 156, 54, x0=190, x1=560, colors=['green'], gap=20, size=11.5)
    f.box(580, 156, 124, 54, 'Who + what\nthey can do', 'green', None, 12)
    f.arrow(562, 183, 578, 183)
    f.arrow(152, 112, 188, 80)
    f.arrow(152, 138, 188, 180)
    f.text(360, 236, 'Amplicon sequencing is cheaper; shotgun adds species, strains, genes and pathways', 11, MUTED)
    f.save('8-4', '16S amplicon sequencing compared with shotgun metagenomics')


def f9_1():
    f = Fig(260)
    f.flow(['Proteins', 'Trypsin\ndigest', 'LC\nseparation', 'Ionise\n(ESI)', 'MS1', 'Fragment', 'MS2'], 18, 54,
           colors=['purple', 'orange', 'blue', 'blue', 'green', 'orange', 'green'],
           subs=[None, None, None, None, 'peptide m/z', None, 'fragment m/z'], gap=14, size=11.5)
    def spectrum(x0, title, peaks, c):
        f.text(x0 + 140, 108, title, 12, weight=700)
        f.line(x0, 220, x0 + 280, 220, TEXT, 1.3)
        f.line(x0, 120, x0, 220, TEXT, 1.3)
        for px, ph in peaks:
            f.line(x0 + px, 220, x0 + px, 220 - ph, c, 2.4)
        f.text(x0 + 140, 238, 'm/z', 10.5, MUTED)
        f.text(x0 - 10, 170, 'intensity', 10.5, MUTED, rot=-90)
    spectrum(50, 'MS1: intact peptides', [(40, 30), (88, 86), (96, 44), (150, 52), (205, 22), (240, 38)], 'blue')
    spectrum(400, 'MS2: fragments of one peptide', [(24, 28), (52, 50), (84, 36), (112, 80), (144, 58), (176, 40), (210, 66), (246, 24)], 'green')
    f.arrow(140, 126, 140, 134, 'orange')
    f.path('M140 124 C200 96 330 100 396 150', 'orange', 1.4, dash='4 4')
    f.text(300, 130, 'select one, fragment it', 10.5, 'orange')
    f.save('9-1', 'The bottom-up proteomics workflow with MS1 and MS2 spectra')


def f9_2():
    f = Fig(250)
    f.box(20, 30, 150, 54, 'Observed MS2', 'green', 'one spectrum')
    f.box(20, 120, 150, 70, 'Protein database', 'blue', 'in-silico digest')
    f.box(230, 60, 150, 100, 'Search engine', 'purple', 'scores each match')
    f.arrow(172, 57, 228, 90)
    f.arrow(172, 155, 228, 130)
    f.arrow(382, 110, 418, 110)
    x, y, w, h = 430, 30, 270, 150
    f.axes(x, y, w, h, 'match score', None)
    def curve(mu, sd, amp, c):
        pts = [(x + t, y + h - amp * math.exp(-((t - mu) ** 2) / (2 * sd * sd))) for t in range(0, w + 1, 4)]
        f.poly(pts, c, 2)
    curve(80, 32, 120, 'red')
    curve(175, 36, 90, 'green')
    f.text(x + 62, y + 14, 'decoys', 11, 'red', weight=600)
    f.text(x + 196, y + 46, 'targets', 11, 'green', weight=600)
    f.line(x + 148, y + 6, x + 148, y + h, TEXT, 1.3, '5 4')
    f.text(x + 152, y + 16, '1% FDR cut-off', 10.5, anchor='start')
    f.text(360, 232, 'Reversed (decoy) sequences cannot be real, so their scores show how often chance matches occur', 11, MUTED)
    f.save('9-2', 'Database search and target-decoy estimation of the false discovery rate')


def f9_3():
    f = Fig(260)
    cols = [('Label-free (LFQ, DIA)', 'blue', ['separate', 'separate', 'separate', 'separate']),
            ('SILAC', 'green', ['mixed', 'mixed', 'mixed', 'mixed']),
            ('TMT / iTRAQ', 'purple', ['separate', 'separate', 'mixed', 'mixed'])]
    stages = ['Cells', 'Digest', 'Label / pool', 'LC-MS run']
    for j, s in enumerate(stages):
        f.text(120, 78 + j * 38, s, 11.5, anchor='end', weight=600)
    for i, (name, c, st) in enumerate(cols):
        x = 140 + i * 190
        f.text(x + 85, 40, name, 12.5, c, weight=700)
        for j, v in enumerate(st):
            y = 60 + j * 38
            if v == 'separate':
                f.rect(x, y, 80, 28, c, 4)
                f.rect(x + 90, y, 80, 28, c, 4)
                f.text(x + 40, y + 18, 'A', 11, c, weight=600)
                f.text(x + 130, y + 18, 'B', 11, c, weight=600)
            else:
                f.rect(x, y, 170, 28, c, 4, fill=C[c][0])
                f.text(x + 85, y + 18, 'A + B together', 11, '#ffffff', weight=600)
    f.text(425, 228, 'The earlier samples are combined, the less handling variation is added between them', 11, MUTED)
    f.text(425, 246, 'Label-free scales to any number of samples; TMT multiplexes up to 18 in one run', 11, MUTED)
    f.save('9-3', 'When samples are combined in label-free, SILAC and TMT quantification')


def f10_1():
    f = Fig(240)
    titles = [('Primary', 'amino acid sequence', 'blue'), ('Secondary', 'helices and sheets', 'green'),
              ('Tertiary', 'one folded chain', 'purple'), ('Quaternary', 'several chains', 'orange')]
    for i, (t, sub, c) in enumerate(titles):
        x = 20 + i * 176
        f.rect(x, 20, 160, 180, 'grey', fill='#fbfcfd')
        f.text(x + 80, 180, t, 12.5, c, weight=700)
        f.text(x + 80, 194, sub, 10.5, MUTED)
        if i:
            f.arrow(x - 14, 100, x - 2, 100)
    for k, aa in enumerate(['M', 'K', 'V', 'L', 'A']):
        f.circle(48 + k * 26, 96, 11, 'blue')
        f.text(48 + k * 26, 100, aa, 10.5, 'blue', weight=700)
        if k:
            f.line(48 + k * 26 - 15, 96, 48 + k * 26 - 11, 96, 'blue', 2)
    d = 'M216 70 ' + ' '.join('q14 -22 28 0 t28 0' for _ in range(2))
    f.path('M214 74 q10 -26 20 0 q10 26 20 0 q10 -26 20 0 q10 26 20 0 q10 -26 20 0 q10 26 20 0', 'green', 3)
    f.text(276, 54, 'α-helix', 10.5, 'green')
    for k in range(3):
        f.arrow(222, 118 + k * 14, 330, 118 + k * 14, 'green', 3)
    f.text(276, 164, 'β-sheet', 10.5, 'green')
    f.path('M400 60 C460 30 500 80 450 96 C400 112 396 150 450 150 C500 150 510 110 480 104', 'purple', 5)
    f.o.append('<ellipse cx="596" cy="84" rx="34" ry="28" fill="%s" stroke="%s" stroke-width="1.5"/>' % (C['orange'][1], C['orange'][0]))
    f.o.append('<ellipse cx="648" cy="92" rx="34" ry="28" fill="%s" stroke="%s" stroke-width="1.5"/>' % (C['purple'][1], C['purple'][0]))
    f.o.append('<ellipse cx="606" cy="128" rx="34" ry="28" fill="%s" stroke="%s" stroke-width="1.5"/>' % (C['blue'][1], C['blue'][0]))
    f.o.append('<ellipse cx="656" cy="134" rx="30" ry="26" fill="%s" stroke="%s" stroke-width="1.5"/>' % (C['green'][1], C['green'][0]))
    f.text(360, 226, 'Sequence determines fold, and fold determines function', 11, MUTED)
    f.save('10-1', 'The four levels of protein structure')


def f10_2():
    f = Fig(250)
    f.box(16, 60, 110, 60, 'Sequence', 'blue', 'FASTA')
    f.box(156, 30, 130, 50, 'MSA', 'green', 'related sequences')
    f.box(156, 100, 130, 50, 'Templates', 'grey', 'known structures')
    f.box(316, 60, 120, 60, 'Evoformer', 'purple', '48 blocks')
    f.box(466, 60, 120, 60, 'Structure\nmodule', 'purple')
    f.box(616, 60, 90, 60, '3D model', 'orange', '+ pLDDT')
    f.arrow(128, 82, 154, 60); f.arrow(128, 98, 154, 120)
    f.arrow(288, 56, 314, 80); f.arrow(288, 124, 314, 100)
    f.arrow(438, 90, 464, 90); f.arrow(588, 90, 614, 90)
    f.path('M526 122 C526 160 376 160 376 124', LINE, 1.5, dash='4 4')
    f.arrow(376, 128, 376, 122)
    f.text(451, 168, 'recycle 3 times', 10.5, MUTED)
    f.text(20, 204, 'pLDDT confidence:', 11.5, anchor='start', weight=700)
    for i, (lab, colr) in enumerate([('> 90 very high', '#0053d6'), ('70 to 90 confident', '#65cbf3'), ('50 to 70 low', '#ffdb13'), ('< 50 very low', '#ff7d45')]):
        x = 150 + i * 140
        f.rect(x, 192, 18, 16, 'grey', 3, fill=colr, sw=0)
        f.text(x + 24, 205, lab, 11, anchor='start')
    f.text(360, 236, 'Low-confidence regions are often flexible linkers or intrinsically disordered', 11, MUTED)
    f.save('10-2', 'The AlphaFold2 prediction pipeline and its pLDDT confidence scale')


def f10_3():
    f = Fig(250)
    f.box(16, 26, 150, 50, 'Receptor', 'blue', 'add H, charges')
    f.box(16, 96, 150, 50, 'Ligand', 'orange', '3D, protonation')
    xs, bw = f.flow(['Define\nsearch box', 'Sample\nposes', 'Score', 'Rank'], 56, 60, x0=200, x1=704,
                    colors=['purple', 'purple', 'green', 'green'], subs=[None, None, 'kcal/mol', 'top poses'], gap=18, size=12)
    f.arrow(168, 51, 198, 78); f.arrow(168, 121, 198, 94)
    f.rect(60, 168, 130, 68, 'blue')
    f.path('M92 168 C92 200 158 200 158 168', 'blue', 1.5, fill='#ffffff')
    f.o.append('<polygon points="112,172 138,172 148,188 125,200 102,188" fill="%s" stroke="%s" stroke-width="1.5"/>' % (C['orange'][1], C['orange'][0]))
    f.rect(84, 160, 82, 48, 'purple', 2, fill='none', dash='4 3')
    f.text(125, 228, 'binding pocket', 10.5, 'blue')
    f.text(210, 184, 'dashed box = search space', 10.5, 'purple', anchor='start')
    f.text(540, 176, 'Validate before trusting a score:', 11.5, weight=700)
    f.text(540, 196, 're-dock the known ligand (RMSD under 2 Å), compare with', 11, MUTED)
    f.text(540, 212, 'known binders and decoys, then test the best in the lab', 11, MUTED)
    f.save('10-3', 'A molecular docking workflow')


ALL = [f6_1, f6_2, f6_3, f7_1, f7_2, f7_3, f8_1, f8_2, f8_3, f8_4, f9_1, f9_2, f9_3, f10_1, f10_2, f10_3]

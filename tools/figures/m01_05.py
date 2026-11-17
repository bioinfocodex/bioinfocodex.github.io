"""Figures for modules 1 to 5."""
import math
from lib import Fig, MUTED, TEXT, LINE, C, rng


def f1_1():
    f = Fig(250)
    f.text(360, 24, 'From a biological question to an answer', 14, weight=700)
    f.flow(['Question', 'Experiment', 'Raw data', 'Analysis', 'Insight'], 48, 62,
           colors=['purple', 'blue', 'orange', 'green', 'purple'],
           subs=['hypothesis', 'sequencing, MS', 'FASTQ, spectra', 'QC, align, stats', 'genes, pathways'])
    f.text(360, 150, 'Bioinformatics sits where three fields meet', 12, MUTED)
    for i, (lab, c) in enumerate([('Biology', 'green'), ('Computer science', 'blue'), ('Statistics', 'orange')]):
        f.box(120 + i * 165, 166, 150, 44, lab, c)
    f.text(360, 236, 'what to ask  ·  how to compute it  ·  whether to believe it', 11.5, MUTED)
    f.save('1-1', 'The bioinformatics workflow from question to insight')


def f1_2():
    f = Fig(250)
    f.box(40, 70, 150, 70, 'DNA', 'blue', 'stores information', 16)
    f.box(285, 70, 150, 70, 'RNA', 'green', 'carries the message', 16)
    f.box(530, 70, 150, 70, 'Protein', 'purple', 'does the work', 16)
    f.arrow(194, 105, 281, 105, label='transcription')
    f.arrow(439, 105, 526, 105, label='translation')
    f.path('M85 68 C70 20 160 20 145 62', 'blue', 1.6)
    f.arrow(146, 58, 145, 68, 'blue')
    f.text(115, 22, 'replication', 11, MUTED)
    f.arrow(360, 160, 115, 160, 'orange', dash='5 4')
    f.text(238, 176, 'reverse transcription (retroviruses, cDNA synthesis in the lab)', 10.5, MUTED)
    f.text(115, 208, "5'-ATG GCC TGG-3'", 12, 'blue', mono=True)
    f.text(360, 208, "5'-AUG GCC UGG-3'", 12, 'green', mono=True)
    f.text(605, 208, 'Met - Ala - Trp', 12, 'purple', mono=True)
    f.text(360, 234, 'T becomes U in RNA; each codon of three bases gives one amino acid', 11, MUTED)
    f.save('1-2', 'The central dogma: DNA to RNA to protein')


def f1_3():
    f = Fig(250)
    f.text(20, 20, 'Gene on the genome (DNA)', 12.5, anchor='start', weight=700)
    f.line(20, 62, 700, 62, LINE, 2)
    parts = [(40, 60, 'promoter', 'orange'), (110, 36, "5' UTR", 'grey'), (146, 90, 'exon 1', 'green'),
             (330, 80, 'exon 2', 'green'), (510, 90, 'exon 3', 'green'), (600, 44, "3' UTR", 'grey')]
    for x, w, lab, c in parts:
        f.rect(x, 48, w, 28, c, 4)
        f.text(x + w / 2, 94, lab, 10.5, MUTED)
    f.text(283, 56, 'intron 1', 10.5, MUTED)
    f.text(460, 56, 'intron 2', 10.5, MUTED)
    f.arrow(110, 40, 140, 40, 'orange')
    f.text(146, 43, 'TSS', 10, 'orange', anchor='start')
    f.arrow(360, 108, 360, 140, label=None)
    f.text(372, 128, 'transcription, then splicing removes the introns', 11, MUTED, anchor='start')
    f.text(20, 166, 'Mature mRNA', 12.5, anchor='start', weight=700)
    x = 150
    f.circle(x - 14, 196, 9, 'purple')
    f.text(x - 14, 222, 'cap', 10.5, MUTED)
    for w, c in [(36, 'grey'), (90, 'green'), (80, 'green'), (90, 'green'), (44, 'grey')]:
        f.rect(x, 182, w, 28, c, 4)
        x += w
    f.text(x + 34, 201, 'AAAAAA', 12, 'purple', mono=True)
    f.text(x + 34, 222, 'poly-A tail', 10.5, MUTED)
    f.line(186, 218, 446, 218, 'green', 2)
    f.text(316, 236, 'coding sequence (CDS): start codon to stop codon', 10.5, 'green')
    f.save('1-3', 'Structure of a eukaryotic gene and its mature mRNA')


def f1_4():
    f = Fig(250)
    f.text(20, 26, 'Typical read length by platform (log scale)', 12.5, anchor='start', weight=700)
    x0, x1 = 170, 690
    lo, hi = 2, 6  # log10 of 100 bp .. 1 Mb

    def X(bp):
        return x0 + (math.log10(bp) - lo) / (hi - lo) * (x1 - x0)
    for bp, lab in [(100, '100 bp'), (1000, '1 kb'), (10000, '10 kb'), (100000, '100 kb'), (1000000, '1 Mb')]:
        f.line(X(bp), 44, X(bp), 196, '#e3e7ec', 1)
        f.text(X(bp), 214, lab, 10.5, MUTED)
    rows = [('Illumina', 'short reads', 100, 300, 'blue'), ('PacBio HiFi', 'accurate long reads', 10000, 25000, 'purple'),
            ('Oxford Nanopore', 'long to ultra-long', 5000, 300000, 'green')]
    for i, (name, sub, a, b, c) in enumerate(rows):
        y = 58 + i * 48
        f.text(20, y + 12, name, 12.5, anchor='start', weight=600)
        f.text(20, y + 27, sub, 10.5, MUTED, anchor='start')
        f.rect(X(a), y, X(b) - X(a), 26, c, 5)
    f.text(360, 238, 'Short reads are cheap and precise; long reads span repeats and whole transcripts', 11, MUTED)
    f.save('1-4', 'Read lengths of Illumina, PacBio HiFi and Oxford Nanopore sequencing')


def f2_1():
    f = Fig(260)
    f.box(320, 14, 80, 34, '/', 'grey', size=14)
    f.box(300, 74, 120, 34, 'home', 'grey')
    f.box(290, 134, 140, 34, 'you', 'blue', sub=None)
    f.text(444, 156, '~  (your home directory)', 11, MUTED, anchor='start')
    f.line(360, 48, 360, 74)
    f.line(360, 108, 360, 134)
    xs = [(90, 'raw_data', 'orange', 'FASTQ files'), (290, 'scripts', 'purple', 'run_qc.sh'), (490, 'results', 'green', 'BAM, counts')]
    for x, lab, c, sub in xs:
        f.box(x, 196, 140, 46, lab, c, sub)
        f.line(360, 168, x + 70, 196)
    f.text(20, 30, 'pwd', 12, 'blue', anchor='start', mono=True)
    f.text(60, 30, 'where am I?', 11, MUTED, anchor='start')
    f.text(20, 52, 'ls', 12, 'blue', anchor='start', mono=True)
    f.text(60, 52, "what is here?", 11, MUTED, anchor='start')
    f.text(20, 74, 'cd', 12, 'blue', anchor='start', mono=True)
    f.text(60, 74, 'move somewhere else', 11, MUTED, anchor='start')
    f.text(700, 30, 'absolute:  /home/you/raw_data', 11, MUTED, anchor='end', mono=True)
    f.text(700, 52, 'relative:  ../results', 11, MUTED, anchor='end', mono=True)
    f.save('2-1', 'A project directory tree and the commands used to move around it')


def f2_2():
    f = Fig(250)
    f.text(360, 24, 'Channels: where packages come from', 12, MUTED)
    f.box(210, 34, 140, 34, 'conda-forge', 'grey')
    f.box(370, 34, 140, 34, 'bioconda', 'green')
    envs = [(30, 'rnaseq', 'blue', ['hisat2 2.2.1', 'samtools 1.19', 'subread 2.0']),
            (265, 'variants', 'purple', ['bwa 0.7.17', 'gatk4 4.5', 'samtools 1.17']),
            (500, 'r-stats', 'orange', ['r-base 4.3', 'bioconductor-deseq2', 'r-ggplot2'])]
    for x, name, c, pk in envs:
        f.rect(x, 104, 190, 120, c)
        f.text(x + 95, 126, 'environment: ' + name, 12.5, c, weight=700)
        for i, p in enumerate(pk):
            f.text(x + 95, 152 + i * 22, p, 11.5, TEXT, mono=True)
        f.arrow(360, 70, x + 95, 102)
    f.text(360, 242, 'Each environment has its own versions, so tools never break each other', 11, MUTED)
    f.save('2-2', 'Conda channels feeding three isolated environments')


def f2_3():
    f = Fig(240)
    f.box(20, 80, 120, 80, 'samples.txt', 'orange', 'one name per line')
    f.rect(180, 40, 400, 160, 'blue', dash='6 4', fill='#fbfdff')
    f.text(380, 62, 'for sample in $(cat samples.txt); do ... done', 11.5, 'blue', mono=True)
    for i, (lab, c) in enumerate([('fastqc', 'green'), ('fastp', 'green'), ('hisat2', 'green')]):
        x = 200 + i * 126
        f.box(x, 92, 106, 50, lab, c, ['check', 'trim', 'align'][i])
        if i:
            f.arrow(x - 20, 117, x - 2, 117)
    f.text(380, 176, 'the same three steps run once for every sample', 11, MUTED)
    f.arrow(142, 120, 178, 120)
    f.arrow(582, 120, 616, 120)
    f.box(618, 80, 86, 80, 'results/', 'purple', 'one per sample')
    f.text(360, 226, 'A script records exactly what was run, so the analysis can be repeated', 11, MUTED)
    f.save('2-3', 'A bash loop applying the same steps to every sample')


def f2_4():
    f = Fig(240)
    f.box(40, 170, 640, 40, 'R  (the language and base packages)', 'grey')
    f.box(40, 110, 310, 50, 'CRAN', 'blue', 'ggplot2, dplyr, tidyr, pheatmap')
    f.box(370, 110, 310, 50, 'Bioconductor', 'green', 'DESeq2, edgeR, clusterProfiler')
    f.box(40, 50, 640, 50, 'RStudio or Positron', 'purple', 'editor, console, plots and help in one window')
    f.text(360, 28, 'What you install, from the bottom up', 12.5, weight=700)
    f.text(195, 230, 'install.packages("ggplot2")', 11, 'blue', mono=True)
    f.text(525, 230, 'BiocManager::install("DESeq2")', 11, 'green', mono=True)
    f.save('2-4', 'The R ecosystem: base R, CRAN, Bioconductor and an editor')


def f3_1():
    f = Fig(260)
    f.text(360, 24, 'Which database holds what', 13, weight=700)
    cells = [('Raw reads', 'SRA · ENA · DDBJ', 'orange'), ('Sequences', 'GenBank · RefSeq', 'blue'),
             ('Genomes + annotation', 'Ensembl · UCSC · NCBI', 'green'), ('Expression', 'GEO · ArrayExpress · GTEx', 'purple'),
             ('Proteins + structures', 'UniProt · PDB · AlphaFold DB', 'blue'), ('Variants', 'dbSNP · ClinVar · gnomAD', 'red'),
             ('Function + pathways', 'GO · KEGG · Reactome', 'green'), ('Literature', 'PubMed · Europe PMC', 'grey')]
    for i, (a, b, c) in enumerate(cells):
        x, y = 20 + (i % 4) * 172, 44 + (i // 4) * 96
        f.box(x, y, 164, 80, a, c, None, 12.5)
        f.text(x + 82, y + 66, b, 9.8, MUTED)
    f.text(360, 250, 'INSDC partners (NCBI, EMBL-EBI, DDBJ) exchange sequence data daily', 11, MUTED)
    f.save('3-1', 'The main biological databases grouped by the kind of data they hold')


def f3_2():
    f = Fig(240)
    f.flow(['FASTQ', 'SAM / BAM', 'VCF'], 40, 62, x0=40, x1=680, colors=['orange', 'blue', 'red'],
           subs=['reads + qualities', 'reads on the genome', 'variants vs reference'], gap=110)
    f.text(235, 62, 'align', 11, MUTED)
    f.text(485, 62, 'call variants', 11, MUTED)
    f.box(30, 150, 150, 54, 'FASTA', 'green', 'reference sequence')
    f.box(210, 150, 150, 54, 'GTF / GFF', 'purple', 'where the genes are')
    f.box(450, 150, 150, 54, 'Counts table', 'green', 'reads per gene')
    f.arrow(105, 150, 300, 104, dash='4 4')
    f.arrow(285, 150, 350, 104, dash='4 4')
    f.arrow(370, 104, 500, 150)
    f.text(455, 122, 'count', 11, MUTED)
    f.text(190, 226, 'reference files (dashed) are inputs to alignment and counting', 11, MUTED)
    f.save('3-2', 'How the common file formats connect in a sequencing analysis')


def f3_3():
    f = Fig(240)
    rows = [('GSE52778', 'Series: the whole study', 'purple'), ('GSM1275862', 'Sample: one biological sample', 'blue'),
            ('SRX384345', 'Experiment: one library', 'green'), ('SRR1039508', 'Run: one set of reads', 'orange')]
    for i, (acc, lab, c) in enumerate(rows):
        x = 30 + i * 172
        f.box(x, 50, 152, 70, acc, c, None, 13)
        f.text(x + 76, 138, lab, 10.5, MUTED)
        if i:
            f.arrow(x - 20, 85, x - 2, 85)
    f.text(106, 34, 'GEO', 12, 'purple', weight=700)
    f.text(278, 34, 'GEO', 12, 'blue', weight=700)
    f.text(450, 34, 'SRA', 12, 'green', weight=700)
    f.text(622, 34, 'SRA', 12, 'orange', weight=700)
    f.arrow(622, 150, 622, 178)
    f.box(470, 180, 230, 40, 'SRR1039508_1.fastq.gz  + _2', 'grey', size=11.5)
    f.text(30, 196, 'prefetch SRR1039508', 11.5, 'blue', anchor='start', mono=True)
    f.text(30, 216, 'fasterq-dump --split-files SRR1039508', 11.5, 'blue', anchor='start', mono=True)
    f.save('3-3', 'From a GEO series accession down to the FASTQ files of one run')


def f4_1():
    f = Fig(250)
    f.text(20, 24, '1  Break the query into short words', 12, anchor='start', weight=700)
    f.text(40, 48, 'Query:  M K V L A A G I V', 12.5, TEXT, anchor='start', mono=True)
    for i, wd in enumerate(['MKV', 'KVL', 'VLA', 'LAA']):
        f.box(360 + i * 82, 32, 70, 24, wd, 'blue' if wd != 'VLA' else 'orange', size=11.5)
    f.text(20, 92, '2  Find exact word hits in the database (seeds)', 12, anchor='start', weight=700)
    f.rect(60, 104, 600, 20, 'grey', 4)
    f.rect(300, 104, 60, 20, 'orange', 4)
    f.text(680, 119, 'subject', 10.5, MUTED, anchor='start')
    f.text(330, 119, 'VLA', 10.5, 'orange', weight=700)
    f.text(20, 160, '3  Extend the seed in both directions while the score keeps rising', 12, anchor='start', weight=700)
    f.rect(60, 172, 600, 20, 'grey', 4)
    f.rect(190, 172, 290, 20, 'green', 4)
    f.rect(300, 172, 60, 20, 'orange', 4)
    f.arrow(296, 204, 196, 204, 'green')
    f.arrow(364, 204, 474, 204, 'green')
    f.text(335, 228, 'high-scoring segment pair (HSP), reported with a bit score and an E-value', 11, MUTED)
    f.save('4-1', 'The BLAST seed and extend strategy')


def f4_2():
    f = Fig(240)
    seqs = [('Human', 'MKVLAAGIVGLLLAQ'), ('Mouse', 'MKVLAAGIVALLLAQ'), ('Chicken', 'MKILSAGIV-LLLAK'), ('Zebrafish', 'MRVLAAGLV-LLFAQ')]
    cons = ''
    for j in range(15):
        colj = [s[j] for _, s in seqs]
        cons += '*' if len(set(colj)) == 1 else ' '
    x0, cw = 150, 34
    for j in range(15):
        if cons[j] == '*':
            f.rect(x0 + j * cw, 34, cw - 4, 140, 'green', 4, sw=0)
    for i, (name, s) in enumerate(seqs):
        y = 60 + i * 34
        f.text(130, y, name, 12, anchor='end', weight=600)
        for j, ch in enumerate(s):
            f.text(x0 + j * cw + (cw - 4) / 2, y, ch, 14, 'red' if ch == '-' else TEXT, mono=True, weight=600)
    for j in range(15):
        f.text(x0 + j * cw + (cw - 4) / 2, 196, cons[j], 14, 'green', mono=True, weight=700)
    f.text(130, 196, 'conserved', 11, MUTED, anchor='end')
    f.text(360, 226, 'Shaded columns are identical in every species; the red dash is a gap (an insertion or deletion)', 11, MUTED)
    f.save('4-2', 'A multiple sequence alignment with conserved columns and a gap')


def f4_3():
    f = Fig(260)
    tips = [('Human', 40), ('Chimpanzee', 76), ('Mouse', 112), ('Rat', 148), ('Chicken', 184), ('Zebrafish (outgroup)', 220)]
    # horizontal branches: (x1, x2, y)
    for name, y in tips:
        f.text(520, y + 4, name, 12, anchor='start', italic=False)
    H = [(420, 510, 40), (420, 510, 76), (330, 420, 58), (400, 510, 112), (400, 510, 148), (330, 400, 130),
         (230, 330, 94), (230, 510, 184), (140, 230, 139), (140, 510, 220), (90, 140, 180)]
    for x1, x2, y in H:
        f.line(x1, y, x2, y, TEXT, 1.8)
    V = [(420, 40, 76), (400, 112, 148), (330, 58, 130), (230, 94, 184), (140, 139, 220)]
    for x, y1, y2 in V:
        f.line(x, y1, x, y2, TEXT, 1.8)
    for x, y, b in [(414, 52, '100'), (394, 124, '98'), (324, 88, '95'), (224, 133, '72')]:
        f.text(x, y, b, 10.5, 'blue', anchor='end', weight=600)
    f.text(84, 184, 'root', 10.5, MUTED, anchor='end')
    f.line(160, 244, 250, 244, TEXT, 1.6)
    f.text(205, 258, '0.1 substitutions per site', 10, MUTED)
    f.text(30, 30, 'Blue numbers: bootstrap support (%)', 11, 'blue', anchor='start')
    f.text(30, 48, 'Horizontal length: amount of change', 11, MUTED, anchor='start')
    f.text(30, 66, 'Vertical lines carry no meaning', 11, MUTED, anchor='start')
    f.save('4-3', 'How to read a rooted phylogenetic tree with bootstrap values')


def f5_1():
    f = Fig(250)
    def panel(x, title, c, days, verdict):
        f.text(x + 160, 26, title, 12.5, c, weight=700)
        for d, (lab, dots) in enumerate(days):
            bx = x + d * 165
            f.rect(bx, 40, 150, 130, 'grey')
            f.text(bx + 75, 60, lab, 11.5, MUTED)
            for k, dc in enumerate(dots):
                f.circle(bx + 30 + (k % 3) * 45, 96 + (k // 3) * 42, 13, dc, fill=C[dc][0])
        f.text(x + 160, 192, verdict, 11, MUTED)
    panel(20, 'Confounded: do not do this', 'red',
          [('Day 1', ['blue'] * 6), ('Day 2', ['orange'] * 6)], 'batch and treatment cannot be separated')
    panel(380, 'Balanced: do this', 'green',
          [('Day 1', ['blue', 'orange', 'blue', 'orange', 'blue', 'orange']), ('Day 2', ['orange', 'blue', 'orange', 'blue', 'orange', 'blue'])],
          'each batch holds every condition')
    f.circle(270, 226, 8, 'blue', fill=C['blue'][0])
    f.text(284, 230, 'control', 11.5, anchor='start')
    f.circle(380, 226, 8, 'orange', fill=C['orange'][0])
    f.text(394, 230, 'treated', 11.5, anchor='start')
    f.save('5-1', 'A confounded design compared with a balanced, blocked design')


def f5_2():
    f = Fig(260)
    x, y, w, h = 70, 30, 600, 170
    def Y(q):
        return y + h - q / 40 * h
    f.rect(x, Y(40), w, Y(28) - Y(40), 'green', 0, sw=0)
    f.rect(x, Y(28), w, Y(20) - Y(28), 'orange', 0, sw=0)
    f.rect(x, Y(20), w, Y(0) - Y(20), 'red', 0, sw=0)
    f.axes(x, y, w, h, 'Position in read (bp)', 'Phred quality')
    for q in (0, 10, 20, 30, 40):
        f.text(x - 8, Y(q) + 4, q, 10.5, MUTED, anchor='end')
    for p in (1, 25, 50, 75, 100, 125, 150):
        f.text(x + p / 150 * w, y + h + 14, p, 10.5, MUTED)
    pts = []
    for p in range(1, 151, 3):
        q = 33 + 3 * (1 - math.exp(-p / 4)) - 2 if p < 10 else 36 - 0.00045 * max(0, p - 60) ** 2.35
        pts.append((x + p / 150 * w, Y(max(q, 4))))
    f.poly(pts, 'blue', 2.4)
    cut = x + 128 / 150 * w
    f.line(cut, y, cut, y + h, 'red', 1.6, '5 4')
    f.text(cut - 6, y + 14, 'trim from here', 11, 'red', anchor='end')
    f.text(x + 12, Y(34) - 22, 'mean quality per position', 11, 'blue', anchor='start')
    f.text(x + w - 6, Y(31), 'good', 10.5, 'green', anchor='end')
    f.text(x + w - 150, Y(22.5), 'acceptable', 10.5, 'orange', anchor='end')
    f.text(x + 80, Y(8), 'poor: Q20 means 1 error in 100 bases', 10.5, 'red', anchor='start')
    f.save('5-2', 'Per-base sequence quality falling towards the end of the read')


def f5_3():
    f = Fig(240)
    f.text(20, 24, 'Reference genome', 12, anchor='start', weight=700)
    f.line(20, 56, 700, 56, LINE, 2)
    f.rect(80, 42, 190, 28, 'green', 4)
    f.rect(450, 42, 190, 28, 'green', 4)
    f.text(175, 61, 'exon 1', 11.5, 'green', weight=600)
    f.text(545, 61, 'exon 2', 11.5, 'green', weight=600)
    f.text(360, 48, 'intron (not in mRNA)', 10.5, MUTED)
    for x, y in [(96, 96), (150, 112), (470, 96), (520, 112), (500, 128)]:
        f.rect(x, y, 100, 9, 'blue', 3, fill=C['blue'][0], sw=0)
    for y, a, b in [(150, 60, 50), (168, 30, 80), (186, 76, 34)]:
        f.rect(270 - a, y, a, 9, 'orange', 3, fill=C['orange'][0], sw=0)
        f.rect(450, y, b, 9, 'orange', 3, fill=C['orange'][0], sw=0)
        f.line(270, y + 4.5, 450, y + 4.5, 'orange', 1.2, '3 3')
    f.text(700, 90, 'unspliced reads', 11, 'blue', anchor='end')
    f.text(360, 144, 'spliced reads jump the intron', 11, 'orange')
    f.text(360, 222, 'A splice-aware aligner (HISAT2, STAR) is needed because one read can come from two exons', 11, MUTED)
    f.save('5-3', 'Spliced and unspliced RNA-seq reads aligned to a reference genome')


def f5_4():
    f = Fig(250)
    f.line(20, 60, 700, 60, LINE, 2)
    f.rect(60, 46, 90, 28, 'green', 4); f.rect(220, 46, 110, 28, 'green', 4)
    f.rect(300, 46, 60, 28, 'purple', 4, op=0.85); f.rect(470, 46, 120, 28, 'purple', 4)
    f.text(190, 34, 'Gene A', 12, 'green', weight=700)
    f.text(470, 34, 'Gene B', 12, 'purple', weight=700)
    reads = [(70, 'green', 'assigned to A'), (236, 'green', None), (305, 'orange', 'ambiguous: overlaps A and B'),
             (385, 'grey', 'no feature: intron or intergenic'), (490, 'purple', 'assigned to B')]
    for i, (x, c, lab) in enumerate(reads):
        y = 98 + i * 24
        f.rect(x, y, 60, 9, c, 3, fill=C[c][0], sw=0)
        if lab:
            f.text(x + 70, y + 9, lab, 11, MUTED, anchor='start')
    f.rect(86, 218, 60, 9, 'red', 3, fill=C['red'][0], sw=0)
    f.rect(500, 218, 60, 9, 'red', 3, fill=C['red'][0], sw=0)
    f.line(146, 222.5, 500, 222.5, 'red', 1.2, '3 3')
    f.text(323, 240, 'multi-mapping: the same read fits two places, so it is not counted by default', 11, MUTED)
    f.save('5-4', 'How featureCounts assigns reads to genes')


def f5_5():
    f = Fig(280)
    x, y, w, h = 80, 24, 580, 200
    f.axes(x, y, w, h, 'log2 fold change (treated vs control)', '-log10 adjusted p')
    def X(v):
        return x + (v + 6) / 12 * w
    def Y(v):
        return y + h - v / 20 * h
    r = rng(7)
    for i in range(420):
        lfc = (r() + r() + r() - 1.5) * 4.2
        p = max(0.05, abs(lfc) ** 1.5 * (0.15 + r() * 1.6) + r() * 0.9)
        p = min(p, 15.5 + r() * 2)
        sig = p > 1.3 and abs(lfc) > 1
        f.dot(X(lfc), Y(p), 2.6, ('red' if lfc > 0 else 'blue') if sig else 'grey', 0.75)
    f.line(X(-1), y, X(-1), y + h, LINE, 1.2, '4 4')
    f.line(X(1), y, X(1), y + h, LINE, 1.2, '4 4')
    f.line(x, Y(1.3), x + w, Y(1.3), LINE, 1.2, '4 4')
    for v in (-6, -4, -2, 0, 2, 4, 6):
        f.text(X(v), y + h + 14, v, 10.5, MUTED)
    for v in (0, 5, 10, 15, 20):
        f.text(x - 8, Y(v) + 4, v, 10.5, MUTED, anchor='end')
    f.text(X(-4.4), y + 6, 'down in treated', 11.5, 'blue', weight=600)
    f.text(X(4.4), y + 6, 'up in treated', 11.5, 'red', weight=600)
    f.text(x + w - 4, Y(1.3) - 5, 'padj = 0.05', 10.5, MUTED, anchor='end')
    f.text(360, 272, 'Illustration with simulated points. Each dot is one gene.', 10.5, MUTED)
    f.save('5-5', 'A volcano plot: effect size against statistical significance')


ALL = [f1_1, f1_2, f1_3, f1_4, f2_1, f2_2, f2_3, f2_4, f3_1, f3_2, f3_3, f4_1, f4_2, f4_3, f5_1, f5_2, f5_3, f5_4, f5_5]

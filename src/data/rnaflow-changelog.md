# Changelog

## v3.2.1 — 2026-10-16

No changes to the app or its results. This release exists so that Zenodo
archives RNAflow and assigns it a DOI: the repository now carries
`.zenodo.json` metadata (title, creator with ORCID, MIT licence, keywords),
and Zenodo only archives releases published after it is enabled.

## v3.2.0 — 2026-10-16

### Reproducibility

- **Every tool and R package is now installed at a fixed version.** Installs
  used to take whatever was newest, so two people, or the same person a month
  apart, could get different numbers from the same FASTQ files. One pinned
  environment (release 2026.10) covers FastQC, fastp, HISAT2, samtools,
  subread, Salmon, sra-tools, MultiQC, Python, R 4.5.3 and every R package the
  app uses (DESeq2 1.50.2 and Bioconductor 3.22). The set resolves on
  Apple-silicon and Intel Macs and on Linux / WSL2.
- **R and Bioconductor live in the same environment as the command-line
  tools**, replacing the separate R + RStudio + `BiocManager` install. The
  Run buttons already used the environment's `Rscript`; now the packages it
  loads are the pinned ones too.
- An older `rnaseq` environment is brought exactly in line (`--prune`) rather
  than recreated by hand.
- Each run records `results/software_versions.txt`,
  `results/conda_environment_lock.txt` and `results/R_sessionInfo.txt`, so a
  figure can be traced back to the software that produced it.
- The GSEA page installs only the annotation database for your organism, at
  the pinned Bioconductor version, instead of all eight.

### Fixed — these produced wrong, empty or missing results

- **Pathway analysis ran on an empty gene list for every organism.** The GSEA
  page told clusterProfiler the IDs were gene symbols (`GENENAME`, a gene
  description, for yeast), but RNAflow's results carry Ensembl IDs. The key
  types now match the IDs the pipeline produces (`ENSEMBL`, `FLYBASE`, `ORF`,
  `TAIR`), the setup block reports how many genes matched and warns below
  half, and it always loaded the yeast database whatever the organism.
- **KEGG enrichment was given the wrong IDs** for human, mouse, rat,
  zebrafish, fly and worm; the conversion to Entrez existed only as a comment.
  Gene IDs are now converted once and KEGG uses `keyType = "ncbi-geneid"`.
- **GSEA ranked genes by signed −log10 padj**, which ties thousands of genes
  at padj = 1. It now ranks by the DESeq2 Wald statistic.
- **Salmon-route gene IDs kept their Ensembl version** (`ENSG00000120129.12`),
  so they matched no annotation database and differed from the HISAT2 route.
- **FastQC and fastp could not find their input with the default settings.**
  With data from SRA and the Desktop location, paths were quoted as
  `"~/Desktop/…"`, which the shell does not expand. The `~` now stays outside
  the quotes.
- **FastQC failed on new installs.** FastQC 0.13 dropped the `-o` flag; the
  step now uses `--outdir`, which every FastQC version accepts.

### Changed

- **Strandedness is measured, not assumed.** "Auto-detect" is the new default:
  the HISAT2 route counts the first sample both ways round and uses the
  orientation that assigns at least 80% of reads (the nf-core rule), warning
  when the answer is ambiguous. The old default, unstranded, discards up to
  half the reads of a stranded library. Salmon already detected it (`-l A`).
- **Shrunken fold changes.** DESeq2 results gain `log2FoldChange_shrunk`
  (apeglm), and the volcano plot uses it, so low-count genes no longer sit at
  the edges with huge, unreliable fold changes. `padj` is unchanged.

### Added — start from a count table

- **"A count table" data source** (CSV, TSV, TXT or Excel, any sheet): for
  counts from a sequencing core, a collaborator or a paper. Samples are read
  by column name, featureCounts output works as it is, repeated gene IDs are
  summed, and the FASTQ steps are skipped. On the airway counts it reproduces
  DESeq2 on the same table exactly (2,713 genes, max |Δ log2FC| 5 × 10⁻¹⁵).
- Tables that would give wrong results are refused with an explanation:
  missing sample columns (the columns found are listed), text or empty
  cells, negative values, and **TPM or CPM tables**, recognised because every
  sample sums to one million. Non-integer estimated counts are rounded with
  a warning.
- The GSEA page notices when results carry gene symbols rather than Ensembl
  IDs and switches the key type.

### Added — edgeR and limma-voom

- **"Check with edgeR and limma-voom"** on the DESeq2 page runs both methods
  on DESeq2's own samples, filtering and design (pairing included): edgeR's
  quasi-likelihood test after TMM, and limma-voom with sample quality
  weights. For Salmon projects each gets the input its authors recommend with
  tximport. Writes each method's results, `method_comparison.csv` (how many
  methods call each gene) and a three-way Venn diagram. On airway, edgeR
  confirms 91% and limma-voom 87% of DESeq2's genes, and all seven known
  targets are called by all three.
- The explorer shows, for the selected gene, which methods call it.

### Added — fgsea with MSigDB Hallmark

- **fgsea on the 50 Hallmark gene sets** (msigdbr), for human, mouse, rat,
  zebrafish, fly, worm and yeast, ranked by the DESeq2 statistic. Saves the
  table, an NES bar chart and **three-panel enrichment ranking plots**
  (running score, hits, ranked metric). On airway it finds 20 pathways, led
  by adipogenesis and TNF-α signalling, both known glucocorticoid programmes.
  The explorer's enrichment browser reads the results.

### Added — small RNA / miRNA route

- **New method "Small RNA / miRNA"**: fastp trims the kit's 3′ adapter and
  keeps 16–35 nt reads (nothing is clipped from the 5′ end); Bowtie 1 counts
  reads on the species' mature miRNAs; the miRNA table goes to DESeq2,
  edgeR and limma-voom like any count table, with a small-RNA QC summary.
- **The adapter is detected from the reads** by default (TruSeq Small RNA,
  NEBNext or QIAseq). A wrong adapter leaves no reads; a sample with none
  left now stops with "check the adapter" instead of Bowtie crashing.
- **miRBase is pinned to release 22.1 with a checksum.** mirbase.org always
  serves its latest release and was often unreachable, so the same reads
  gave different counts depending on which server answered.
- **Benchmarked on synthetic pools with known fold changes** (Giraldez et
  al. 2018, GSE94585; `benchmark/smallrna/`). Against the designed ratios of
  285 human miRNAs: fold-change correlation 0.991, 99% of 2-fold-or-larger
  changes found, 1 of 33 unchanged miRNAs called, every call in the right
  direction; all six checks pass. DESeq2 on the authors' own counts scores
  0.978, 97% and 15% false positives.
- Also run on nf-core's human small RNA test samples: 22–36% of trimmed reads
  on mature miRNAs, led by miR-148a-3p, miR-21-5p, miR-143-3p and let-7.
- New pinned packages: bowtie 1.3.1, edgeR 4.8.2, msigdbr 26.1.1,
  readr 2.2.0 and readxl 1.5.0.1, re-solved for all three platforms.

### Added — paired designs

- **Optional pairing or batch label per sample** on the Configure page. When
  samples come in pairs (the same donor, animal or cell line before and after
  treatment) or batches, DESeq2 uses `~ pair + condition`. On the airway
  benchmark this finds 1,296 genes instead of 1,142 at padj < 0.05, and the
  share confirmed by the reference rises from 94% to 96%. A pairing that
  cannot be fitted (wrong count, all labels unique, or pairs that coincide
  with the treatment groups) is explained on the page, and the design falls
  back to `~ condition` rather than failing in R.

### Project

- MIT `LICENSE` file (the app already declared MIT), README, contributing
  guide, `CITATION.cff`, and a JOSS paper draft in `paper/`.

### Added — explore results interactively

- **Explore results** card on the Results page, built into the app with no
  plotting library: a volcano plot that shows the gene under the pointer and
  opens it on click, padj and fold-change cut-offs, shrunken or unshrunken
  fold changes, gene search, each sample's normalised counts for the chosen
  gene, a sortable table of significant genes with CSV download, and a
  searchable browser for the GO / KEGG / Reactome tables.
- **Gene names everywhere.** The reference step writes `gene_names.tsv` from
  the GTF, and DESeq2 results gain a `symbol` column, so the volcano plot
  labels DUSP1 instead of ENSG00000120129. (grep before awk: macOS awk took
  50 s on a human GTF; this takes under a second.)
- DESeq2 also writes `normalized_counts.csv` and `samples.csv`.

### Added — one-click setup

- **The desktop app installs everything on first launch.** On a Mac or Linux
  machine with no conda, it offers to install Miniforge privately into
  `~/.rnaflow/miniforge3`: no administrator password, no change to shell
  settings. The release is pinned (26.7.2-0) and its SHA-256 checksum is
  built into the app, so a tampered download is refused. The app then opens
  and builds the pinned tool set itself, with live progress.
- **"Run" on the Install page now installs the tools** through a new server
  endpoint, `/setup`, so no terminal is needed. It accepts only a well-formed
  RNAflow environment file (named channels, pinned `package=version` lines).
- When the tools are missing, the app says so and links to the one-click
  install, instead of every step failing with "command not found". The
  server notices a newly created environment within 20 seconds; it used to
  check once, at start-up.
- The server runs on a conda Python when one exists, never on macOS's
  `python3` stub, which opens an "install developer tools" dialog.
- The page now follows the server it was served from, so `RNAFLOW_PORT`
  works (it always called port 7788).
- Windows is unchanged: bioconda tools need WSL2, and the app points there.

### Fixed — the Salmon route could not produce results

- **DESeq2 stopped with "None of the transcripts in the quantification files
  are present in the first column of tx2gene"** on every Salmon-route
  project. `tximport(ignoreTxVersion = TRUE)` strips versions from Salmon's
  transcript IDs, but the transcript-to-gene map kept them, so nothing
  matched. Found by the airway benchmark; reproduced with tximport 1.34 and
  1.38. The map is now written without versions.

### Added — quality control

- **QC summary step** after quantification (Gene Counting page, and in
  `run_all.sh`). Per sample it reports mapped %, rRNA % and mitochondrial %,
  with a PASS / WARN verdict (mapped ≥ 70%, rRNA < 10%, mito < 30%), and
  gathers everything into one MultiQC report, `qc/rnaflow_final_qc.html`.
- **Genome route: Qualimap RNA-seq** for read origin (exonic / intronic /
  intergenic), 5′–3′ gene-body coverage bias and junctions, plus rRNA share
  from a `gene_biotype` count. Qualimap 2.3 and its Java runtime join the
  pinned environment.
- **Salmon route: non-coding transcripts are indexed too.** Ensembl's cDNA
  file leaves out rRNA and lncRNA, so rRNA contamination could not be
  measured and lncRNAs were never quantified. The ncRNA FASTA is now added
  to the index; species without one carry on with cDNA alone.
- **Reference downloads survive a re-run.** A complete file is kept (checked
  with `gzip -t`), so a second run no longer spends an hour re-downloading
  from Ensembl. Downloads also fail on HTTP errors (`curl -f`) instead of
  saving an error page under a `.fa.gz` name.

### Development

- **The app is now built from `src/`.** `RNAflow_App.html` was one
  6,000-line file edited by hand. Its source is split into 39 files (one per
  page, the script by job), and `node tools/build.mjs` joins them back into
  the same single file — byte-identical at the split, so nothing changed for
  users. See `src/README.md`.
- **Tests run on every push and pull request** (`.github/workflows/test.yml`,
  Linux and macOS): the built file must match `src/`, the `files/` and
  `website/` copies must match the root, 11 tests of the generated commands
  must pass, and 12 server tests must pass. Each command test guards a bug
  listed above; against v3.0.0, 10 of the 11 fail.

### Added

- `benchmark/`: an end-to-end test on the airway dataset (GSE52778). It runs
  the commands the app generates and scores them against published results.

## v3.0.0 — 2026-08-24

The headline change is that the local server is no longer open to any web page
you happen to have open. Everything else follows from a review of where the app
produced wrong or lost results.

### Security

- **The local server required no authentication.** It accepted `POST /run` from
  any origin and returned `Access-Control-Allow-Origin: *`, so any website open
  in your browser could execute shell commands on your machine. Every command
  endpoint now requires a per-session access token.
- The `Host` header is validated, which blocks DNS-rebinding attacks.
- CORS is restricted to the local app instead of `*`.

The server prints a URL on startup; open it and the app pairs automatically. If
you open `RNAflow_App.html` from disk, paste the token once.

### Fixed — these produced wrong or missing results

- **R blocks were piped into a shell** and could never run. They now execute
  through `Rscript`.
- **Gene family analysis matched patterns against gene IDs**, so it returned
  nothing for most organisms — a count matrix is indexed by `ENSG…`/`AT1G…`,
  not by `MYB12`. IDs are now mapped to symbols using the project's GTF, and
  the patterns are anchored so `MYB` no longer matches any gene containing
  those letters.
- **DESeq2 selected count columns by position.** A failed sample shifted every
  column and silently mislabelled conditions. Columns are now matched by name.
- **Reference URLs pointed at a retired Ensembl release.** Refreshed to
  Ensembl 116 / Ensembl Genomes 63 and each one verified. Six organisms had
  been renamed in the meantime (rat → GRCr8, fly → BDGP6.54, tomato → SL4.0,
  yarrowia moved to Ensembl Fungi).
- **The "local FASTQ folder" setting did nothing.** Projects using your own
  sequencing data now work end to end.
- The CPU setting never reached the tools; HPC job scripts wrote to a `logs/`
  directory that was never created; the progress counter read "15 / 13".

### Added

- **Import samples from a GEO or SRA accession.** Paste `GSE52778` and every
  run in the study is fetched, with read type and organism detected.
- **Salmon route.** Quantifies against the transcriptome, so no genome index is
  built — the step that stops most people working on human data on a laptop.
- **Results viewer.** Plots, MultiQC reports and count tables open inside the
  app instead of being hunted for in a file manager.
- **Export to nf-core/rnaseq**, or to a single `run_all.sh` script.
- **Projects persist** across reloads and can be exported as a file. A running
  job survives a page refresh and reattaches with its output intact.

### Changed

- Alignment streams into `samtools sort` rather than writing a SAM file and
  deleting it, saving roughly 100 GB of scratch I/O per human sample.
- The multi-factor, batch-correction and GSEA pages now follow your project
  instead of staying pinned to the yeast demo values.

## v2.0.0 — 2026-07-13

Desktop application for macOS, Windows and Linux.

## v1.0.0 — 2026-03-21

First release.

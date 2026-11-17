# bioinfocodex.com

Open-source bioinformatics software and a free course. The site is static:
`tools/build-site.py` turns `src/` into `dist/`, and Netlify publishes `dist/`.

## Build and preview

```bash
python3 tools/build-site.py --serve
```

That builds the site and serves it at http://localhost:8000. It needs Python 3
and nothing else. The build stops with an error if any internal link is broken.

## Where things are

| To change | Edit |
|---|---|
| RNAflow version, release date, DOI, form address, analytics | `src/site.json` |
| A page (home, tools, download, about, contact, cite) | `src/pages/<name>.html` |
| A course module or topic | `src/learn/NN-slug.html` |
| Glossary terms | `src/data/glossary.json` |
| The RNAflow changelog page | `src/data/rnaflow-changelog.md` (copy of the repo's `CHANGELOG.md`) |
| Header, navigation, footer | `src/layout.html` |
| Styles and scripts | `src/assets/` |
| Old addresses that should redirect | `src/_redirects` |
| Video lessons | `tools/build-lesson.py`, which writes `lesson-files/` |

Each file in `src/pages/` starts with a comment block that gives its address,
title and description. In a module file, a line such as
`<!--topic 5.2: Quality Control-->` starts a new topic, and every topic becomes
its own page.

## Releasing a new RNAflow version

1. Set `version` and `released` in `src/site.json`. Every page, download link
   and citation reads from there.
2. Replace `src/data/rnaflow-changelog.md` with the new `CHANGELOG.md`.
3. Push. Netlify rebuilds the site.

## Analytics

Off by default. To turn on cookie-free analytics, fill in the `analytics` block
in `src/site.json` (`plausible` with a domain, or `goatcounter` with a code).

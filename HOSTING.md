# Making the routes indexable

**Done — the site moved to Netlify on 24 August 2026.** `/tools/rnaflow` and the
other 27 routes now answer 200 and are in the sitemap. What follows is kept as
the record of why, and what to check if it ever regresses.

Current shape:

- `bioinfocodex.com` → Netlify (ANAME on the apex to apex-loadbalancer.netlify.com,
  `www` CNAME to the Netlify site). Rewrites live in `_redirects`.
- `rnaflow.bioinfocodex.com` → still GitHub Pages, from the `rnaflow` repo.
  Deliberately untouched; external DNS was chosen over Netlify DNS precisely so
  moving the apex could not take this subdomain with it.
- Certificates are issued by Netlify and renew themselves.

The check that matters, if anything ever looks wrong:

```
curl -sI https://bioinfocodex.com/tools/rnaflow | head -1   # expect 200, not 404
```

---

The site has real URLs — `/tools/rnaflow`, `/learn/rna-seq`, 28 in all, each
with its own `<title>`, description and canonical. They work for anyone using
the site: deep links, refresh, back and forward all behave.

They are not indexable, and that is a hosting limit rather than an app one.

## The problem

GitHub Pages cannot rewrite. A cold request for `/tools/rnaflow` finds no such
file, so Pages answers with `404.html` **and an HTTP 404 status**. The script in
that file redirects the browser, so a person lands on the right page and never
notices. A crawler does not get that far: it has already been told the URL does
not exist.

```
$ curl -sI https://bioinfocodex.com/tools/rnaflow | head -1
HTTP/2 404
```

That is why `sitemap.xml` lists one URL instead of 28. Advertising paths that
answer 404 fills Search Console with errors and helps nothing.

## The fix: serve from Netlify

Everything needed is already committed — `_redirects` and `netlify.toml`. Both
are inert on GitHub Pages, so they change nothing until the domain moves.

1. Create a Netlify site from `bioinfocodex/bioinfocodex.github.io`.
   Build command: none. Publish directory: `.`
2. Point `rnaflow.bioinfocodex.com`'s parent domain at Netlify: in your DNS,
   replace the GitHub Pages records for `bioinfocodex.com` with Netlify's.
   Netlify issues its own certificate automatically.
3. Disable the GitHub Pages deploy so the two do not fight:
   delete `.github/workflows/deploy-site.yml`, or turn Pages off in repo
   settings.
4. Regenerate the sitemap now that the routes answer 200:

   ```
   python3 tools/build-sitemap.py
   ```

5. Confirm, then submit the sitemap in Search Console:

   ```
   curl -sI https://bioinfocodex.com/tools/rnaflow | head -1   # expect 200
   ```

## The alternative: pre-render

If you would rather stay on GitHub Pages, the other route is generating one
static file per URL, each containing only that page's content. That needs no
hosting change and no JavaScript to read, but it is a real build step and the
in-app navigation has to fall back to a full page load when a section is not
in the DOM. More work, and worth it mainly if moving hosts is off the table.

## One quirk worth knowing

`https://bioinfocodex.com/_redirects` returns 404 today, and that is expected —
GitHub Pages runs Jekyll, which excludes files whose names begin with an
underscore from the published output. The file is in the repository, which is
what matters: Netlify reads it from the repo, not from the Pages build.

```
$ curl -sI https://raw.githubusercontent.com/bioinfocodex/bioinfocodex.github.io/main/_redirects | head -1
HTTP/2 200
```

If you ever want Pages itself to stop running Jekyll, add an empty `.nojekyll`
file at the root. Not needed for the switch, so it is deliberately not here —
no reason to change how the current deploy is processed while it works.

## What not to do

Do not use a `301` in `_redirects` for the app routes. A redirect changes the
URL and would bounce every deep link to the home page; `200` is a rewrite,
which keeps the path and serves `index.html` behind it.

# Functions

## verify-code

Checks an access code server-side and returns a signed token.

It exists because the previous gate was not one. `BIC_CODES` sat in the page
source, so `RNAFLOW2025` was readable with View Source, and the expiry was a
client-side date comparison. Registering also printed the code on screen and
typed it into the box for you.

### Required environment variables

Set these in Netlify under **Project configuration → Environment variables**.
None of them belong in this repository.

| Variable | Example | Notes |
|---|---|---|
| `BIC_ACCESS_CODES` | `RNAFLOW2026,LAB-SEAT-01` | Comma-separated. Case-insensitive. |
| `BIC_TOKEN_SECRET` | 40+ random characters | Signs the token. Changing it logs everyone out. |
| `BIC_EXPIRY` | `2026-12-30T23:59:59Z` | Optional. Omit for no expiry. |

Generate a secret with:

```
openssl rand -base64 48
```

**Use new codes.** The three old ones have been public in the page source for
months and should be treated as compromised.

### Behaviour

- Wrong code → `401`, no token, same response shape as success
- More than 8 attempts from one IP in 10 minutes → `429`
- Past `BIC_EXPIRY` → `403`, even for a valid code
- Missing configuration → `500` and a log line; it fails closed, never open

Codes are compared with `crypto.timingSafeEqual` after a length check, so the
response time does not leak how much of a code was right.

### What this does and does not protect

It stops someone reading the codes out of the page, guessing them by brute
force, or skipping the expiry. That is a real gate where there was none.

It does not protect the software. The desktop installers are public GitHub
release assets, and the standalone files are served at plain URLs. Anyone who
wants them can find them without a code. Making that genuinely private means
private releases and streaming the bytes through a function — a larger change,
and only worth it if the goal is protection rather than capturing registrations.

---

## send-code

Emails the access code to someone who has just registered, replacing the manual
step where you sent it by hand.

### Additional environment variables

| Variable | Example | Notes |
|---|---|---|
| `RESEND_API_KEY` | `re_…` | From resend.com. Free tier covers 3,000 emails/month. |
| `BIC_FROM_EMAIL` | `BioInfoCodex <access@bioinfocodex.com>` | The domain must be verified in Resend or nothing is delivered. |
| `BIC_AUTO_CODE` | `RNAFLOW2026` | Optional. Defaults to the first entry in `BIC_ACCESS_CODES`. |
| `BIC_NOTIFY_EMAIL` | `info@bioinfocodex.com` | Optional copy to you, so registrations stay visible. |

### Setup

1. Create a free account at resend.com.
2. Add `bioinfocodex.com` as a domain and publish the DNS records it gives you
   at Name.com. Without this, Resend refuses to send as your domain.
3. Create an API key and set the variables above, all scopes.
4. Redeploy — functions only receive variables at deploy time.

### Behaviour

- Malformed address, or one with a comma or angle bracket that could smuggle a
  second recipient → `400`, nothing sent
- More than 5 sends per IP per hour, or 3 to the same address → `429`
- Provider error → `502`, and the page tells the visitor a human will follow up
- Missing configuration → `500` naming the variables

Formspree is untouched, so your existing registration notifications continue
either way, and a mail failure never costs you the registration.

### The trade-off you accepted

Automatic sending means anyone with a working email address gets a code. Your
approval is no longer part of the loop — the gate now proves someone can
receive email, not that you have vetted them. If you want approval back, unset
`RESEND_API_KEY` and the page falls back to telling people a human will be in
touch.

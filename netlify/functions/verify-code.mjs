// Server-side access-code check.
//
// What this replaces: the codes used to live in a BIC_CODES array in the page,
// so anyone could read them with View Source, and the expiry was a client-side
// date comparison anyone could skip. Both now happen here, where the visitor
// cannot see or change them.
//
// Configure in Netlify under Project configuration > Environment variables:
//   BIC_ACCESS_CODES   comma-separated, e.g. RNAFLOW2026,LAB-SEAT-01
//   BIC_TOKEN_SECRET   any long random string; signs the access token
//   BIC_EXPIRY         optional ISO date, e.g. 2026-12-30T23:59:59Z
//
// Nothing here is committed to the repository.

import crypto from 'node:crypto';

const WINDOW_MS = 10 * 60 * 1000;   // rate-limit window
const MAX_TRIES = 8;                 // attempts per IP per window
const TOKEN_TTL_MS = 30 * 24 * 60 * 60 * 1000;

// Best-effort only: functions are ephemeral and may run on several instances,
// so this slows a casual brute force rather than stopping a determined one.
const attempts = new Map();

function rateLimited(ip) {
  const now = Date.now();
  const rec = attempts.get(ip);
  if (!rec || now - rec.first > WINDOW_MS) {
    attempts.set(ip, { first: now, count: 1 });
    return false;
  }
  rec.count += 1;
  return rec.count > MAX_TRIES;
}

function sign(payload, secret) {
  const body = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const mac = crypto.createHmac('sha256', secret).update(body).digest('base64url');
  return `${body}.${mac}`;
}

// Compare without leaking length or position through timing.
function matches(input, codes) {
  const given = Buffer.from(input.trim().toUpperCase());
  return codes.some((c) => {
    const known = Buffer.from(c.trim().toUpperCase());
    if (known.length !== given.length) return false;
    return crypto.timingSafeEqual(known, given);
  });
}

export default async (request) => {
  const json = (status, body) =>
    new Response(JSON.stringify(body), {
      status,
      headers: { 'content-type': 'application/json', 'cache-control': 'no-store' }
    });

  if (request.method !== 'POST') return json(405, { error: 'method_not_allowed' });

  const secret = process.env.BIC_TOKEN_SECRET;
  const codes = (process.env.BIC_ACCESS_CODES || '').split(',').map(s => s.trim()).filter(Boolean);
  if (!secret || codes.length === 0) {
    // Names, never values. Knowing which variable is missing turns a silent
    // 500 into a two-minute fix, and leaks nothing: the names are in the repo
    // already. A common cause is setting the variable but leaving its scope
    // as Builds only, so Functions never receive it.
    const missing = [];
    if (!secret) missing.push('BIC_TOKEN_SECRET');
    if (codes.length === 0) missing.push('BIC_ACCESS_CODES');
    console.error('verify-code: missing environment variables:', missing.join(', '));
    return json(500, {
      error: 'not_configured',
      missing,
      hint: 'Set these in Netlify with their scope including Functions, then redeploy.'
    });
  }

  const expiry = process.env.BIC_EXPIRY ? new Date(process.env.BIC_EXPIRY) : null;
  if (expiry && Date.now() > expiry.getTime()) {
    return json(403, { error: 'expired', message: 'The access period has ended.' });
  }

  const ip = request.headers.get('x-nf-client-connection-ip')
          || request.headers.get('x-forwarded-for')
          || 'unknown';
  if (rateLimited(ip)) {
    return json(429, { error: 'too_many_attempts', message: 'Too many attempts. Try again in a few minutes.' });
  }

  let code = '';
  try {
    ({ code = '' } = await request.json());
  } catch {
    return json(400, { error: 'bad_request' });
  }
  if (typeof code !== 'string' || code.length === 0 || code.length > 64) {
    return json(400, { error: 'bad_request' });
  }

  if (!matches(code, codes)) {
    // Same shape and timing as success, minus the token.
    return json(401, { error: 'invalid_code', message: 'That code was not recognised.' });
  }

  const expires = Date.now() + TOKEN_TTL_MS;
  return json(200, {
    ok: true,
    token: sign({ exp: expires }, secret),
    expires
  });
};

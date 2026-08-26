// Emails an access code to someone who has just registered.
//
// Replaces the manual step: registration used to notify you via Formspree and
// then wait for you to email the code by hand.
//
// Environment variables (Netlify > Project configuration > Environment variables):
//   RESEND_API_KEY   from resend.com — free tier covers 3,000 emails/month
//   BIC_FROM_EMAIL   e.g. BioInfoCodex <access@bioinfocodex.com>
//                    the domain must be verified in Resend or delivery fails
//   BIC_ACCESS_CODES already set; the first code listed is the one sent
//   BIC_AUTO_CODE    optional, to send a code other than the first
//   BIC_NOTIFY_EMAIL optional, gets a copy so you still see registrations
//
// Formspree is left in place, so your existing record of registrations is
// unchanged whether or not this succeeds.

const WINDOW_MS = 60 * 60 * 1000;
const MAX_PER_IP = 5;         // an address can be retried, not farmed
const MAX_PER_EMAIL = 3;      // stops this being used to mailbomb someone

const byIp = new Map();
const byEmail = new Map();

function overLimit(map, key, max) {
  const now = Date.now();
  const rec = map.get(key);
  if (!rec || now - rec.first > WINDOW_MS) {
    map.set(key, { first: now, count: 1 });
    return false;
  }
  rec.count += 1;
  return rec.count > max;
}

// Excludes the characters that would let someone smuggle a second recipient
// (comma, semicolon, angle brackets, quotes, whitespace) while allowing dots
// in the domain — an earlier version did not, and rejected perfectly ordinary
// addresses like name@cdfd.org.in and name@dept.ac.uk.
const EMAIL_RE = /^[^\s@,;<>"']+@[^\s@,;<>"']+\.[a-z]{2,}$/i;

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

export default async (request) => {
  const json = (status, body) => new Response(JSON.stringify(body), {
    status, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' }
  });

  if (request.method !== 'POST') return json(405, { error: 'method_not_allowed' });

  const key = process.env.RESEND_API_KEY;
  const from = process.env.BIC_FROM_EMAIL;
  const codes = (process.env.BIC_ACCESS_CODES || '').split(',').map(s => s.trim()).filter(Boolean);
  const code = process.env.BIC_AUTO_CODE || codes[0];

  if (!key || !from || !code) {
    const missing = [];
    if (!key) missing.push('RESEND_API_KEY');
    if (!from) missing.push('BIC_FROM_EMAIL');
    if (!code) missing.push('BIC_ACCESS_CODES');
    console.error('send-code: missing environment variables:', missing.join(', '));
    // Registration itself already succeeded, so this is not the visitor's
    // problem to solve — report it without implying their form failed.
    return json(500, { error: 'not_configured', missing });
  }

  let email = '', name = '', institution = '';
  try {
    ({ email = '', name = '', institution = '' } = await request.json());
  } catch {
    return json(400, { error: 'bad_request' });
  }

  email = String(email).trim();
  if (!EMAIL_RE.test(email) || email.length > 254) {
    return json(400, { error: 'invalid_email' });
  }

  const ip = request.headers.get('x-nf-client-connection-ip')
          || request.headers.get('x-forwarded-for') || 'unknown';
  if (overLimit(byIp, ip, MAX_PER_IP) ||
      overLimit(byEmail, email.toLowerCase(), MAX_PER_EMAIL)) {
    return json(429, { error: 'too_many_requests' });
  }

  const first = escapeHtml((name || 'there').split(' ')[0]).slice(0, 40);
  const safeCode = escapeHtml(code);

  const html = `
    <div style="font-family:system-ui,-apple-system,Segoe UI,sans-serif;font-size:15px;line-height:1.6;color:#161a22;max-width:520px">
      <p>Hi ${first},</p>
      <p>Thanks for registering for RNAflow. Your access code is:</p>
      <p style="font-family:ui-monospace,Menlo,monospace;font-size:22px;font-weight:600;letter-spacing:3px;
                background:#ecfdf5;border:1px solid #86efac;border-radius:10px;padding:14px 22px;display:inline-block;color:#047857">
        ${safeCode}
      </p>
      <p>Enter it at <a href="https://bioinfocodex.com/download">bioinfocodex.com/download</a> to unlock the
         downloads — macOS, Windows and Linux installers, plus the standalone browser version.</p>
      <p>RNAflow runs entirely on your own machine. Your data never leaves it.</p>
      <p>The manual is at <a href="https://rnaflow.bioinfocodex.com/manual.html">rnaflow.bioinfocodex.com/manual.html</a>.</p>
      <p style="color:#5a6274">— BioInfoCodex</p>
    </div>`;

  const text = `Hi ${first},

Thanks for registering for RNAflow. Your access code is:

  ${code}

Enter it at https://bioinfocodex.com/download to unlock the downloads —
macOS, Windows and Linux installers, plus the standalone browser version.

RNAflow runs entirely on your own machine. Your data never leaves it.

Manual: https://rnaflow.bioinfocodex.com/manual.html

— BioInfoCodex`;

  try {
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${key}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from, to: [email], subject: 'Your RNAflow access code', html, text
      })
    });
    if (!res.ok) {
      const detail = await res.text().catch(() => '');
      console.error('send-code: Resend returned', res.status, detail.slice(0, 300));
      return json(502, { error: 'send_failed' });
    }
  } catch (err) {
    console.error('send-code: could not reach Resend:', err.message);
    return json(502, { error: 'send_failed' });
  }

  // Optional copy to you, so registrations remain visible even if you ever
  // drop Formspree. A failure here must not fail the visitor's request.
  const notify = process.env.BIC_NOTIFY_EMAIL;
  if (notify) {
    try {
      await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${key}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from, to: [notify],
          subject: `RNAflow code sent to ${email}`,
          text: `${name || '(no name)'}\n${institution || '(no institution)'}\n${email}\n\nCode sent automatically.`
        })
      });
    } catch { /* best effort */ }
  }

  return json(200, { ok: true });
};

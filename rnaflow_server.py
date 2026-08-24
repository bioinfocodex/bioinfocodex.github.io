#!/usr/bin/env python3
"""
RNAflow Local Server  v3.0
===========================
Works on:  macOS · Linux · Windows (PowerShell / CMD / WSL)
Requires:  Python 3.6+  (no extra packages needed)

HOW TO USE
----------
  macOS / Linux (Terminal):
      python3 rnaflow_server.py

  Windows (PowerShell or Anaconda Prompt):
      python rnaflow_server.py

The server prints a paired URL on startup. Open that URL and the app is
ready to run commands. If you prefer to open RNAflow_App.html from disk,
paste the access token shown on startup into the app's Connect box once.

SECURITY (new in v3.0)
----------------------
  * Every command endpoint requires a per-session access token.
  * The Host header must be localhost — this blocks DNS-rebinding attacks.
  * CORS is restricted to the local app instead of "*", so a random web
    page you have open can no longer execute commands on your machine.

This server ONLY listens on 127.0.0.1 (your own computer).
It is NEVER accessible from any other machine. Press Ctrl+C to stop.
"""

import http.server
import json
import subprocess
import threading
import uuid
import os
import sys
import signal
import platform
import shutil
import secrets
import time
import stat

# ── PLATFORM DETECTION ────────────────────────────────────────────────────
SYSTEM   = platform.system()   # 'Darwin' | 'Linux' | 'Windows'
IS_MAC   = SYSTEM == 'Darwin'
IS_LINUX = SYSTEM == 'Linux'
IS_WIN   = SYSTEM == 'Windows'

VERSION   = "3.0"
PORT      = int(os.environ.get("RNAFLOW_PORT", 7788))
HOST      = "127.0.0.1"
CONDA_ENV = os.environ.get("RNAFLOW_ENV", "rnaseq")

APP_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "RNAflow_App.html")

# ── SESSION STATE DIRECTORY ───────────────────────────────────────────────
STATE_DIR = os.path.join(os.path.expanduser("~"), ".rnaflow")
LOG_DIR   = os.path.join(STATE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Token: reuse RNAFLOW_TOKEN when a launcher (e.g. the Electron app) supplies
# one, otherwise mint a fresh one for this session.
TOKEN = os.environ.get("RNAFLOW_TOKEN") or secrets.token_urlsafe(24)

SESSION_FILE = os.path.join(STATE_DIR, "session.json")


def write_session_file():
    """Record the live token so a launcher can pair without user typing."""
    try:
        with open(SESSION_FILE, "w") as fh:
            json.dump({"token": TOKEN, "port": PORT, "pid": os.getpid(),
                       "version": VERSION, "started": time.time()}, fh)
        os.chmod(SESSION_FILE, stat.S_IRUSR | stat.S_IWUSR)  # owner-only
    except Exception:
        pass


# ── FIND CONDA ────────────────────────────────────────────────────────────
def find_conda():
    c = shutil.which("conda")
    if c:
        return c
    home = os.path.expanduser("~")
    if IS_WIN:
        checks = [
            os.path.join(home, "anaconda3",  "Scripts", "conda.exe"),
            os.path.join(home, "miniconda3", "Scripts", "conda.exe"),
            os.path.join(home, "miniforge3", "Scripts", "conda.exe"),
            r"C:\ProgramData\Anaconda3\Scripts\conda.exe",
            r"C:\ProgramData\Miniconda3\Scripts\conda.exe",
            r"C:\ProgramData\miniforge3\Scripts\conda.exe",
            os.path.join(home, "AppData", "Local", "anaconda3",  "Scripts", "conda.exe"),
            os.path.join(home, "AppData", "Local", "miniconda3", "Scripts", "conda.exe"),
            os.path.join(home, "AppData", "Local", "miniforge3", "Scripts", "conda.exe"),
        ]
    else:
        checks = [
            os.path.join(home, "miniforge3",  "bin", "conda"),
            os.path.join(home, "miniconda3",  "bin", "conda"),
            os.path.join(home, "anaconda3",   "bin", "conda"),
            os.path.join(home, "opt", "miniforge3", "bin", "conda"),
            os.path.join(home, "opt", "miniconda3", "bin", "conda"),
            "/opt/miniforge3/bin/conda",
            "/opt/miniconda3/bin/conda",
            "/opt/anaconda3/bin/conda",
            "/usr/local/bin/conda",
            "/usr/local/Caskroom/miniforge/base/bin/conda",
            "/usr/local/Caskroom/miniconda/base/bin/conda",
        ]
    for p in checks:
        if os.path.isfile(p):
            return p
    return None


CONDA_PATH = find_conda()


def conda_env_exists():
    """True when CONDA_ENV is present, None when we cannot tell."""
    if not CONDA_PATH:
        return None
    try:
        out = subprocess.run([CONDA_PATH, "env", "list", "--json"],
                             capture_output=True, text=True, timeout=25)
        envs = json.loads(out.stdout).get("envs", [])
        if not envs:
            return None
        # The first entry is the base prefix, whose directory is named after
        # the installer (miniforge3/anaconda3) rather than "base".
        if CONDA_ENV == "base":
            return True
        return any(os.path.basename(e) == CONDA_ENV for e in envs[1:])
    except Exception:
        return None


ENV_PRESENT = None  # resolved lazily on first /status call


# ── BUILD COMMAND ─────────────────────────────────────────────────────────
def build_command(raw_cmd):
    if IS_WIN:
        if CONDA_PATH:
            base_dir = os.path.dirname(os.path.dirname(CONDA_PATH))
            act_bat  = os.path.join(base_dir, "Scripts", "activate.bat")
            if os.path.exists(act_bat):
                full = f'call "{act_bat}" {CONDA_ENV} && {raw_cmd}'
            else:
                full = raw_cmd
        else:
            full = raw_cmd
        return ["cmd.exe", "/C", full]
    else:
        home = os.path.expanduser("~")
        inits = []
        for base in [
            os.path.join(home, "miniforge3"),
            os.path.join(home, "miniconda3"),
            os.path.join(home, "anaconda3"),
            os.path.join(home, "opt", "miniforge3"),
            os.path.join(home, "opt", "miniconda3"),
            "/opt/miniforge3", "/opt/miniconda3", "/opt/anaconda3",
            "/usr/local/Caskroom/miniforge/base",
            "/usr/local/Caskroom/miniconda/base",
        ]:
            sh = os.path.join(base, "etc", "profile.d", "conda.sh")
            if os.path.isfile(sh):
                inits.append(f'. "{sh}"')
        for rc in ["~/.zshrc", "~/.bashrc", "~/.bash_profile"]:
            rc2 = os.path.expanduser(rc)
            if os.path.isfile(rc2):
                inits.append(f'. "{rc2}" >/dev/null 2>&1')
        init_block = " ; ".join(inits) if inits else "true"
        # Fail loudly instead of silently running in (base) with tools missing
        activate = (f'if ! conda activate {CONDA_ENV} 2>/dev/null; then '
                    f'echo "[RNAflow] Could not activate conda env \'{CONDA_ENV}\'. '
                    f'Run the Install Tools step first." >&2; exit 78; fi')
        full = f'{init_block} ; {activate} ; {raw_cmd}'
        shell = "/bin/zsh" if IS_MAC and os.path.exists("/bin/zsh") else "/bin/bash"
        return [shell, "-c", full]


# ── JOB STORE ─────────────────────────────────────────────────────────────
# Each job keeps its full output in memory AND on disk, so a browser refresh
# can reattach to a running job and replay everything it missed.
jobs      = {}
jobs_lock = threading.Lock()
MAX_JOBS  = 200


def prune_jobs():
    """Drop the oldest finished jobs so a long session cannot leak memory."""
    with jobs_lock:
        if len(jobs) <= MAX_JOBS:
            return
        finished = sorted(
            (jid for jid, j in jobs.items() if j["status"] in ("done", "error", "killed")),
            key=lambda jid: jobs[jid]["started"])
        for jid in finished[:len(jobs) - MAX_JOBS]:
            jobs.pop(jid, None)


def new_job(raw_cmd, lang, label):
    job_id = uuid.uuid4().hex[:12]
    job = {
        "id": job_id, "cmd": raw_cmd, "lang": lang, "label": label,
        "process": None, "status": "queued", "exit_code": None,
        "lines": [], "cond": threading.Condition(), "started": time.time(),
        "log_path": os.path.join(LOG_DIR, f"{job_id}.log"),
    }
    with jobs_lock:
        jobs[job_id] = job
    prune_jobs()
    return job


def emit(job, text):
    """Append one output chunk and wake every attached reader."""
    with job["cond"]:
        job["lines"].append(text)
        job["cond"].notify_all()
    try:
        with open(job["log_path"], "a") as fh:
            fh.write(text)
    except Exception:
        pass


def finish(job, status, exit_code):
    with job["cond"]:
        job["status"]    = status
        job["exit_code"] = exit_code
        job["cond"].notify_all()


def materialise_r_script(job):
    """R is not shell — write it to a file and run it through Rscript."""
    path = os.path.join(LOG_DIR, f"{job['id']}.R")
    with open(path, "w") as fh:
        fh.write(job["cmd"])
    return f'Rscript --vanilla "{path}"'


def run_job(job):
    try:
        raw = materialise_r_script(job) if job["lang"] == "r" else job["cmd"]
        args   = build_command(raw)
        kwargs = dict(stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                      text=True, bufsize=1, env=os.environ.copy())
        if not IS_WIN:
            kwargs["preexec_fn"] = os.setsid
        else:
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        proc = subprocess.Popen(args, **kwargs)
        with jobs_lock:
            job["process"] = proc
            job["status"]  = "running"

        for line in proc.stdout:
            emit(job, line)

        proc.wait()
        code = proc.returncode
        if job["status"] == "killed":
            finish(job, "killed", -1)
        else:
            finish(job, "done" if code == 0 else "error", code)

    except Exception as e:
        emit(job, f"[Server error] {e}\n")
        finish(job, "error", 1)


def kill_job(job):
    proc = job.get("process")
    job["status"] = "killed"
    if proc:
        try:
            if IS_WIN:
                proc.send_signal(signal.CTRL_BREAK_EVENT)
                proc.terminate()
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            pass
    else:
        finish(job, "killed", -1)


# ── RESULTS BROWSING SCOPE ────────────────────────────────────────────────
# /ls and /file only ever reach inside a project folder the app has
# registered. An authenticated caller can already run shell commands, so this
# is not the security boundary — the token is — but it keeps a stray path from
# turning the viewer into a general-purpose file reader.
HOME       = os.path.realpath(os.path.expanduser("~"))
scopes     = set()
scope_lock = threading.Lock()

# Only formats the viewer actually renders. Everything else is refused rather
# than guessed at, so the browser is never asked to sniff a content type.
VIEWABLE = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".svg": "image/svg+xml", ".webp": "image/webp",
    ".pdf": "application/pdf",
    ".html": "text/html", ".htm": "text/html",
    ".csv": "text/plain", ".tsv": "text/plain", ".txt": "text/plain",
    ".log": "text/plain", ".json": "application/json",
    ".sf": "text/plain", ".summary": "text/plain",
}
MAX_VIEW_BYTES = 40 * 1024 * 1024


def add_scope(path):
    """Register a project folder. Must be a real directory inside $HOME."""
    real = os.path.realpath(os.path.expanduser(path or ""))
    if not real.startswith(HOME + os.sep) and real != HOME:
        return None, "Project folder must be inside your home directory."
    if not os.path.isdir(real):
        return None, f"Not a folder: {real}"
    with scope_lock:
        scopes.add(real)
    return real, None


def resolve_in_scope(path):
    """Resolve a request path, refusing anything outside a registered scope.

    realpath() is what defeats both ../ traversal and symlinks pointing out
    of the project, so the check must happen on the resolved path.
    """
    if not path:
        return None, "No path given."
    real = os.path.realpath(os.path.expanduser(path))
    with scope_lock:
        allowed = list(scopes)
    if not any(real == root or real.startswith(root + os.sep) for root in allowed):
        return None, "Path is outside the registered project folder."
    if any(part.startswith(".") for part in real[len(HOME):].split(os.sep) if part):
        return None, "Hidden files are not served."
    return real, None


# ── HTTP HANDLER ──────────────────────────────────────────────────────────
ALLOWED_HOSTS   = {f"127.0.0.1:{PORT}", f"localhost:{PORT}", f"[::1]:{PORT}"}
ALLOWED_ORIGINS = {f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}", "null"}


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        try:
            if int(args[1]) >= 400:
                super().log_message(fmt, *args)
        except Exception:
            pass

    # ── security helpers ──────────────────────────────────────────────
    def host_ok(self):
        """Reject DNS-rebinding: the browser must have asked for localhost."""
        return (self.headers.get("Host") or "").lower() in ALLOWED_HOSTS

    def origin(self):
        return self.headers.get("Origin") or ""

    def token_ok(self):
        supplied = self.headers.get("X-RNAflow-Token")
        if not supplied and "?" in self.path:
            from urllib.parse import urlparse, parse_qs
            supplied = (parse_qs(urlparse(self.path).query).get("token") or [""])[0]
        return bool(supplied) and secrets.compare_digest(supplied, TOKEN)

    def cors(self):
        org = self.origin()
        # file:// pages send Origin: null; the served app sends its own origin.
        self.send_header("Access-Control-Allow-Origin",
                         org if org in ALLOWED_ORIGINS else "null")
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-RNAflow-Token")

    def guard(self, need_token=True):
        """Returns True when the request may proceed."""
        if not self.host_ok():
            self.reply(403, {"error": "bad_host",
                             "detail": "Reach this server as 127.0.0.1 only."})
            return False
        if need_token and not self.token_ok():
            self.reply(401, {"error": "unauthorized",
                             "detail": "Missing or wrong access token. "
                                       "Paste the token printed by the server."})
            return False
        return True

    # ── reply helpers ─────────────────────────────────────────────────
    def reply(self, code, obj, ctype="application/json"):
        body = json.dumps(obj).encode() if ctype == "application/json" else obj
        self.send_response(code)
        self.cors()
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_OPTIONS(self):
        if not self.host_ok():
            self.reply(403, {"error": "bad_host"}); return
        self.send_response(204); self.cors()
        self.send_header("Content-Length", "0"); self.end_headers()

    # ── GET ───────────────────────────────────────────────────────────
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        p      = parsed.path
        query  = parse_qs(parsed.query)

        # Serve the app itself so it runs same-origin with the token injected
        if p in ("/", "/index.html", "/RNAflow_App.html"):
            self.serve_app(query.get("token", [""])[0])
            return

        if p == "/status":
            global ENV_PRESENT
            if not self.host_ok():
                self.reply(403, {"error": "bad_host"}); return
            if ENV_PRESENT is None:
                ENV_PRESENT = conda_env_exists()
            self.reply(200, {
                "ok": True, "version": VERSION, "system": SYSTEM,
                "conda": CONDA_PATH or "not found", "env": CONDA_ENV,
                "env_present": ENV_PRESENT,
                "python": sys.version.split()[0],
                # Lets the app write absolute paths into files that other
                # tools read — Nextflow does not expand "~" inside a CSV field.
                "home": HOME,
                "authed": self.token_ok(),
            })
            return

        if p == "/jobs":
            if not self.guard():
                return
            with jobs_lock:
                listing = [{"id": j["id"], "label": j["label"], "lang": j["lang"],
                            "status": j["status"], "exit_code": j["exit_code"],
                            "started": j["started"], "lines": len(j["lines"])}
                           for j in jobs.values()]
            listing.sort(key=lambda j: j["started"], reverse=True)
            self.reply(200, {"jobs": listing})
            return

        if p == "/ls":
            if not self.guard():
                return
            self.list_dir((query.get("path") or [""])[0])
            return

        if p == "/file":
            if not self.guard():
                return
            self.serve_file((query.get("path") or [""])[0])
            return

        if p.startswith("/output/"):
            if not self.guard():
                return
            self.stream_output(p[len("/output/"):],
                               int((query.get("from") or ["0"])[0]))
            return

        if p.startswith("/kill/"):
            if not self.guard():
                return
            job = jobs.get(p[len("/kill/"):])
            if job:
                kill_job(job)
            self.reply(200, {"ok": bool(job)})
            return

        self.reply(404, {"error": "not_found"})

    # ── serve the app with the token baked in ─────────────────────────
    def serve_app(self, supplied_token):
        if not self.host_ok():
            self.reply(403, {"error": "bad_host"}); return
        if not os.path.isfile(APP_FILE):
            self.reply(404, {"error": "app_missing",
                             "detail": f"RNAflow_App.html not found next to the server "
                                       f"({APP_FILE})."})
            return
        try:
            with open(APP_FILE, "r", encoding="utf-8") as fh:
                html = fh.read()
        except Exception as e:
            self.reply(500, {"error": "read_failed", "detail": str(e)}); return

        # Only inject when the caller already knows the token.
        inject = ""
        if supplied_token and secrets.compare_digest(supplied_token, TOKEN):
            inject = ("<script>window.__RNAFLOW_TOKEN__=" +
                      json.dumps(TOKEN) + ";</script>")
        html = html.replace("</head>", inject + "</head>", 1) if inject else html
        self.reply(200, html.encode("utf-8"), ctype="text/html; charset=utf-8")

    # ── RESULTS BROWSING ──────────────────────────────────────────────
    def list_dir(self, path):
        real, err = resolve_in_scope(path)
        if err:
            self.reply(403, {"error": "out_of_scope", "detail": err}); return
        if not os.path.isdir(real):
            self.reply(404, {"error": "not_a_directory", "detail": real}); return
        entries = []
        try:
            for name in sorted(os.listdir(real)):
                if name.startswith("."):
                    continue
                full = os.path.join(real, name)
                try:
                    st = os.stat(full)
                except OSError:
                    continue
                is_dir = os.path.isdir(full)
                ext = os.path.splitext(name)[1].lower()
                entries.append({
                    "name": name, "path": full, "dir": is_dir,
                    "size": 0 if is_dir else st.st_size,
                    "mtime": st.st_mtime,
                    "viewable": (not is_dir) and ext in VIEWABLE,
                    "kind": "dir" if is_dir else VIEWABLE.get(ext, ""),
                })
        except OSError as e:
            self.reply(500, {"error": "read_failed", "detail": str(e)}); return
        self.reply(200, {"path": real, "entries": entries})

    def serve_file(self, path):
        real, err = resolve_in_scope(path)
        if err:
            self.reply(403, {"error": "out_of_scope", "detail": err}); return
        if not os.path.isfile(real):
            self.reply(404, {"error": "not_found", "detail": real}); return
        ext = os.path.splitext(real)[1].lower()
        ctype = VIEWABLE.get(ext)
        if not ctype:
            self.reply(415, {"error": "not_viewable",
                             "detail": f"{ext or 'this file type'} is not served by the viewer."})
            return
        size = os.path.getsize(real)
        if size > MAX_VIEW_BYTES:
            self.reply(413, {"error": "too_large",
                             "detail": f"{size} bytes — open it outside RNAflow."})
            return
        try:
            with open(real, "rb") as fh:
                body = fh.read()
        except OSError as e:
            self.reply(500, {"error": "read_failed", "detail": str(e)}); return

        self.send_response(200)
        self.cors()
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        # Never let the browser sniff a different type than we declared.
        self.send_header("X-Content-Type-Options", "nosniff")
        # Only HTML can carry script, so only HTML gets the locked-down CSP.
        # Applying "sandbox" to an image response makes Chrome refuse to
        # render it, which is why this is not sent for every type.
        if ctype == "text/html":
            # No script, no network, no plugins — a report renders, but cannot
            # call home or touch the app. The "sandbox" CSP *directive* is
            # deliberately omitted: Chrome refuses the frame load outright
            # (ERR_BLOCKED_BY_CLIENT), and the iframe's own sandbox attribute
            # already gives the opaque origin.
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; img-src 'self' data: blob:; "
                             "style-src 'unsafe-inline'; font-src data:; "
                             "script-src 'none'; frame-ancestors 'self'")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    # ── SSE with replay ───────────────────────────────────────────────
    def stream_output(self, job_id, start):
        job = jobs.get(job_id)
        if not job:
            self.reply(404, {"error": "no_such_job"}); return

        self.send_response(200)
        self.cors()
        self.send_header("Content-Type",      "text/event-stream")
        self.send_header("Cache-Control",     "no-cache")
        self.send_header("Connection",        "close")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        def push(msg):
            self.wfile.write(f"data: {json.dumps(msg)}\n\n".encode())
            self.wfile.flush()

        idx = max(0, start)
        try:
            while True:
                with job["cond"]:
                    while idx >= len(job["lines"]) and job["status"] in ("queued", "running"):
                        if not job["cond"].wait(timeout=20):
                            break
                    pending  = job["lines"][idx:]
                    consumed = idx + len(pending)
                    finished = job["status"] not in ("queued", "running")
                    code     = job["exit_code"]

                if pending:
                    push({"type": "output", "index": consumed,
                          "data": "".join(pending)})
                    idx = consumed
                elif not finished:
                    self.wfile.write(b": keepalive\n\n"); self.wfile.flush()

                if finished and idx >= len(job["lines"]):
                    push({"type": "done", "exit_code": code, "index": idx})
                    break
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    # ── POST ──────────────────────────────────────────────────────────
    def do_POST(self):
        p = self.path.split("?")[0]
        if p == "/scope":
            if not self.guard():
                return
            length = int(self.headers.get("Content-Length", 0) or 0)
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                self.reply(400, {"error": "bad_json"}); return
            real, err = add_scope(payload.get("root"))
            if err:
                self.reply(400, {"error": "bad_scope", "detail": err}); return
            self.reply(200, {"ok": True, "root": real})
            return

        if p != "/run":
            self.reply(404, {"error": "not_found"}); return
        if not self.guard():
            return

        length = int(self.headers.get("Content-Length", 0) or 0)
        if length > 2_000_000:
            self.reply(413, {"error": "too_large"}); return
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self.reply(400, {"error": "bad_json"}); return

        raw_cmd = (payload.get("cmd") or "").strip()
        lang    = (payload.get("lang") or "bash").lower()
        label   = (payload.get("label") or "command")[:80]
        if not raw_cmd:
            self.reply(400, {"error": "empty_command"}); return
        if lang not in ("bash", "r"):
            self.reply(400, {"error": "bad_lang"}); return

        job = new_job(raw_cmd, lang, label)
        threading.Thread(target=run_job, args=(job,), daemon=True).start()
        self.reply(200, {"job_id": job["id"], "log": job["log_path"]})


# ── STARTUP ───────────────────────────────────────────────────────────────
def main():
    write_session_file()
    server = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
    server.daemon_threads = True
    conda_display = CONDA_PATH or "NOT FOUND — install Miniforge first"
    url = f"http://{HOST}:{PORT}/?token={TOKEN}"
    W = 74
    print()
    print("=" * W)
    print(f"  RNAflow Local Server  v{VERSION}  🧬".center(W))
    print("=" * W)
    print(f"  OS        : {SYSTEM} ({platform.machine()})")
    print(f"  Python    : {sys.version.split()[0]}")
    print(f"  Conda     : {conda_display}")
    print(f"  Env       : {CONDA_ENV}")
    print(f"  Job logs  : {LOG_DIR}")
    print("-" * W)
    print("  OPEN THIS URL — the app connects automatically:")
    print()
    print(f"    {url}")
    print()
    print("  Or, if you opened RNAflow_App.html from disk, paste this token")
    print("  into the app's Connect box (top right), once:")
    print()
    print(f"    {TOKEN}")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * W)
    print()
    if not CONDA_PATH:
        print("  WARNING: Conda not found.")
        print("  Install from: https://github.com/conda-forge/miniforge/releases")
        print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopping — terminating any running jobs…")
        with jobs_lock:
            live = [j for j in jobs.values() if j["status"] == "running"]
        for j in live:
            kill_job(j)
        try:
            os.remove(SESSION_FILE)
        except Exception:
            pass
        print("  Server stopped.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()

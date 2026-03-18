#!/usr/bin/env python3
"""
RNAflow Local Server  v2.0
===========================
Works on:  macOS · Linux · Windows (PowerShell / CMD / WSL)
Requires:  Python 3.6+  (no extra packages needed)

HOW TO USE
----------
  macOS / Linux (Terminal):
      python3 rnaflow_server.py

  Windows (PowerShell or Anaconda Prompt):
      python rnaflow_server.py

Then open RNAflow_App.html in your browser.

This server ONLY listens on 127.0.0.1 (your own computer).
It is NEVER accessible from any other machine. Press Ctrl+C to stop.
"""

import http.server
import json
import subprocess
import threading
import queue
import uuid
import os
import sys
import signal
import platform
import shutil

# ── PLATFORM DETECTION ────────────────────────────────────────────────────
SYSTEM   = platform.system()   # 'Darwin' | 'Linux' | 'Windows'
IS_MAC   = SYSTEM == 'Darwin'
IS_LINUX = SYSTEM == 'Linux'
IS_WIN   = SYSTEM == 'Windows'

PORT      = 7788
HOST      = "127.0.0.1"
CONDA_ENV = "rnaseq"


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
                inits.append(f'. "{rc2}" 2>/dev/null')
        init_block = " ; ".join(inits) if inits else "true"
        full = f'{init_block} ; conda activate {CONDA_ENV} 2>/dev/null ; {raw_cmd}'
        shell = "/bin/zsh" if IS_MAC and os.path.exists("/bin/zsh") else "/bin/bash"
        return [shell, "-c", full]


# ── JOB STORE ─────────────────────────────────────────────────────────────
jobs      = {}
jobs_lock = threading.Lock()


def run_job(job_id, raw_cmd):
    q = jobs[job_id]["queue"]
    try:
        args   = build_command(raw_cmd)
        kwargs = dict(stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                      text=True, bufsize=1, env=os.environ.copy())
        if not IS_WIN:
            kwargs["preexec_fn"] = os.setsid

        proc = subprocess.Popen(args, **kwargs)
        with jobs_lock:
            jobs[job_id]["process"] = proc
            jobs[job_id]["status"]  = "running"

        for line in proc.stdout:
            q.put({"type": "output", "data": line})

        proc.wait()
        exit_code = proc.returncode
        with jobs_lock:
            jobs[job_id]["status"]    = "done"
            jobs[job_id]["exit_code"] = exit_code
        q.put({"type": "done", "exit_code": exit_code})

    except Exception as e:
        with jobs_lock:
            jobs[job_id]["status"]    = "error"
            jobs[job_id]["exit_code"] = 1
        q.put({"type": "output", "data": f"[Server error] {e}\n"})
        q.put({"type": "done",   "exit_code": 1})


# ── HTTP HANDLER ──────────────────────────────────────────────────────────
class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        try:
            if int(args[1]) >= 400:
                super().log_message(fmt, *args)
        except Exception:
            pass

    def cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200); self.cors(); self.end_headers()

    def do_GET(self):
        p = self.path.split("?")[0]

        if p == "/status":
            self.send_response(200); self.cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": True, "version": "2.0", "system": SYSTEM,
                "conda": CONDA_PATH or "not found", "env": CONDA_ENV,
                "python": sys.version.split()[0],
            }).encode())
            return

        if p.startswith("/output/"):
            job_id = p[len("/output/"):]
            if job_id not in jobs:
                self.send_response(404); self.end_headers(); return
            self.send_response(200); self.cors()
            self.send_header("Content-Type",      "text/event-stream")
            self.send_header("Cache-Control",      "no-cache")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            q = jobs[job_id]["queue"]
            try:
                while True:
                    try:
                        msg = q.get(timeout=30)
                    except queue.Empty:
                        self.wfile.write(b": keepalive\n\n"); self.wfile.flush(); continue
                    self.wfile.write(f"data: {json.dumps(msg)}\n\n".encode())
                    self.wfile.flush()
                    if msg.get("type") == "done":
                        break
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            return

        if p.startswith("/kill/"):
            job_id = p[len("/kill/"):]
            if job_id in jobs:
                proc = jobs[job_id].get("process")
                if proc:
                    try:
                        if IS_WIN:
                            proc.terminate()
                        else:
                            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    except Exception:
                        pass
                jobs[job_id]["status"] = "killed"
                jobs[job_id]["queue"].put({"type": "done", "exit_code": -1})
            self.send_response(200); self.cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers(); self.wfile.write(b'{"ok":true}')
            return

        self.send_response(404); self.end_headers()

    def do_POST(self):
        p = self.path.split("?")[0]
        if p == "/run":
            length  = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length))
            raw_cmd = payload.get("cmd", "").strip()
            if not raw_cmd:
                self.send_response(400); self.end_headers(); return
            job_id = str(uuid.uuid4())[:8]
            with jobs_lock:
                jobs[job_id] = {"process": None, "queue": queue.Queue(),
                                "status": "queued", "exit_code": None, "cmd": raw_cmd}
            threading.Thread(target=run_job, args=(job_id, raw_cmd), daemon=True).start()
            self.send_response(200); self.cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"job_id": job_id}).encode())
            return
        self.send_response(404); self.end_headers()


# ── STARTUP ───────────────────────────────────────────────────────────────
def main():
    server = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
    conda_display = CONDA_PATH or "NOT FOUND — install Miniforge first"
    W = 60
    print()
    print("=" * W)
    print("  RNAflow Local Server  v2.0  🧬".center(W))
    print("=" * W)
    print(f"  OS        : {SYSTEM} ({platform.machine()})")
    print(f"  Python    : {sys.version.split()[0]}")
    print(f"  Conda     : {conda_display}")
    print(f"  Env       : {CONDA_ENV}")
    print(f"  Listening : http://{HOST}:{PORT}")
    print("-" * W)
    print("  Open RNAflow_App.html in your browser")
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
        print("\n  Server stopped.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()

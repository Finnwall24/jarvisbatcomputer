#!/usr/bin/env python3
"""Batcomputer's local Claude Code bridge -- click-to-run only.

Listens on 127.0.0.1 ONLY (never reachable from another computer or the internet). It only ever
operates inside PROJECT_DIR below (this "Personal Apps" folder, where Batcomputer's own files live)
-- it is never given any other folder on your computer.

Two safeguards, both required:
  1. A KEY. The first time this runs it generates one and saves it next to this script
     (.batcomputer_bridge_key, never in the published batcomputer-web/ folder or git). Paste it into
     CONFIG once. Every request must send it (Authorization: Bearer <key>) or the bridge refuses it --
     so nothing else running on your Mac can quietly trigger this just by knowing the URL.
  2. A HUMAN CLICK. The assistant inside Batcomputer can only ever PROPOSE a task -- it shows up on
     screen as a CLAUDE_CODE_REQUEST that YOU have to click RUN on. It cannot make this bridge actually
     touch a file on its own judgment; every real run starts from your own click, every time.

Run it with:  python3 tools/claude_code_bridge.py
(or just double-click Batcomputer.command / Batcomputer Hands-Free.command -- both start this too)
"""
import hmac, json, os, secrets, shutil, subprocess, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_PATH = os.path.join(PROJECT_DIR, ".batcomputer_bridge_key")
PORT = int(os.environ.get("BATCOMPUTER_BRIDGE_PORT", "8791"))
TIMEOUT_S = 280  # a real code change can take a couple of minutes; the app's own fetch waits longer than this
RUN_LOCK = threading.Lock()  # only one Claude Code run at a time, so two requests can't edit the same files at once


def load_or_make_key():
    if os.path.isfile(KEY_PATH):
        return open(KEY_PATH).read().strip()
    key = secrets.token_hex(24)
    with open(KEY_PATH, "w") as f:
        f.write(key + "\n")
    os.chmod(KEY_PATH, 0o600)
    print("=" * 70)
    print("Generated a new Claude Code bridge key. Paste it into Batcomputer's")
    print("CONFIG screen (CLAUDE_CODE_KEY field) once:")
    print()
    print(f"  {key}")
    print()
    print(f"(saved to {KEY_PATH} -- never shown again after this)")
    print("=" * 70)
    return key


KEY = load_or_make_key()


def claude_path():
    return shutil.which("claude")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # keep the terminal quiet; the important lines still print via print() below

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authed(self):
        got = (self.headers.get("Authorization") or "").removeprefix("Bearer ").strip()
        return bool(got) and hmac.compare_digest(got, KEY)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            # deliberately does NOT require the key and deliberately does NOT return it -- this just lets the
            # app show "bridge is running" / "claude cli found" before anyone has pasted a key in at all
            return self._json({"ok": True, "project_dir": PROJECT_DIR, "claude_cli": claude_path() or None, "keyed": True})
        self._json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path != "/run":
            return self._json({"error": "not found"}, 404)
        if not self._authed():
            return self._json({"ok": False, "error": "Missing or wrong key. Paste the CLAUDE_CODE_KEY from this bridge's terminal window into CONFIG."}, 401)
        n = int(self.headers.get("Content-Length") or 0)
        try:
            data = json.loads(self.rfile.read(n).decode() or "{}")
        except Exception:
            return self._json({"ok": False, "error": "Bad request body (expected JSON with a prompt field)."}, 400)
        prompt = str(data.get("prompt") or "").strip()
        if not prompt:
            return self._json({"ok": False, "error": "prompt is required."}, 400)
        cli = claude_path()
        if not cli:
            return self._json({"ok": False, "error": "The `claude` command was not found on this Mac's PATH. Install Claude Code, then restart this bridge."})
        if not RUN_LOCK.acquire(blocking=False):
            return self._json({"ok": False, "error": "Claude Code is already running one task; wait for it to finish before starting another."}, 429)
        try:
            print(f"[claude_code_bridge] operator clicked RUN: {prompt[:120]}")
            proc = subprocess.run(
                [cli, "-p", prompt, "--output-format", "json", "--permission-mode", "acceptEdits"],
                cwd=PROJECT_DIR, capture_output=True, text=True, timeout=TIMEOUT_S,
            )
            out = (proc.stdout or "").strip()
            try:
                parsed = json.loads(out)
            except Exception:
                parsed = None
            if parsed is not None:
                if parsed.get("is_error"):
                    return self._json({"ok": False, "error": parsed.get("result") or "Claude Code reported an error.", "raw": parsed})
                return self._json({
                    "ok": True,
                    "result": parsed.get("result", ""),
                    "cost_usd": parsed.get("total_cost_usd"),
                    "num_turns": parsed.get("num_turns"),
                    "session_id": parsed.get("session_id"),
                })
            err = (proc.stderr or "").strip()[:2000]
            return self._json({"ok": False, "error": err or out[:2000] or f"Claude Code exited with code {proc.returncode} and no output."})
        except subprocess.TimeoutExpired:
            return self._json({"ok": False, "error": f"Claude Code did not finish within {TIMEOUT_S} seconds. Try a smaller, more specific request."})
        except Exception as e:
            return self._json({"ok": False, "error": f"Could not run Claude Code: {e}"})
        finally:
            RUN_LOCK.release()


def main():
    cli = claude_path()
    print(f"Batcomputer Claude Code bridge on http://127.0.0.1:{PORT}  (project: {PROJECT_DIR})")
    print(f"claude CLI: {cli or 'NOT FOUND on PATH -- install Claude Code, or this bridge will just report that back to the app'}")
    print("Every /run request needs the key AND only ever starts from your own RUN click in the app.")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()

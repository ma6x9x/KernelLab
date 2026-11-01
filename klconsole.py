#!/usr/bin/env python3
# klconsole.py — KernelLab Console
#
# Localhost UI over kernellab.py: target list / set / show, default diff,
# and the allowlisted sim stub. Binds 127.0.0.1 only. The saved target is
# target.json, written by `kernellab target set` — this process does not
# keep a second store.
#
#   python3 klconsole.py            -> http://127.0.0.1:8737

import html
import json
import os
import re
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORT = int(os.environ.get("KL_PORT", "8737"))
BUILD_RE = re.compile(r"^[0-9]{2}[A-Z][0-9]{2,4}[a-z]?$")
TABLE_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
STUB_RE = re.compile(r"^[a-z][a-z0-9._-]{0,31}$")

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>KernelLab Console</title>
<style>
body {
  background: #0b0e14;
  color: #c8d2e0;
  font: 1rem/1.5 ui-monospace, Menlo, monospace;
  margin: 0;
  padding: 1.25rem;
}
h1 {
  font-size: 1rem;
  color: #8ab4ff;
  letter-spacing: 0.08em;
  margin: 0 0 0.5rem;
}
.dims { opacity: 0.7; font-size: 0.85rem; margin-block-end: 1rem; max-width: 52rem; }
fieldset {
  border: 1px solid #2c3a55;
  border-radius: 8px;
  margin-block-end: 1rem;
  padding: 0.75rem 1rem 1rem;
}
legend { color: #8ab4ff; padding-inline: 0.4rem; }
label { display: block; margin-block: 0.6rem 0.25rem; }
button, select {
  background: #1c2333;
  color: #c8d2e0;
  border: 1px solid #2c3a55;
  border-radius: 6px;
  padding: 0.6rem 0.9rem;
  margin: 0.25rem 0.4rem 0.25rem 0;
  min-height: 48px;
  font: inherit;
  box-sizing: border-box;
}
button { color: #8ab4ff; cursor: pointer; }
button:hover { background: #263049; }
select { background: #131a28; min-width: 12rem; }
button:focus-visible, select:focus-visible {
  outline: 3px solid #8ab4ff;
  outline-offset: 2px;
}
#current { margin-block-start: 0.75rem; white-space: pre-wrap; }
#out {
  white-space: pre-wrap;
  background: #0d1220;
  border: 1px solid #1c2540;
  border-radius: 8px;
  padding: 0.9rem;
  margin-block-start: 0.5rem;
  min-height: 16rem;
  max-height: 60vh;
  overflow: auto;
}
</style>
</head>
<body>
<h1>KERNELLAB CONSOLE</h1>
<p class="dims">localhost only. Pick a saved kernelcache, diff it against the baseline, then dry-run the allowlisted ident stub. Unicorn is not EL1. A stock kernelcache is not the live jailbroken kernel. An EMU row is not a device receipt. Set target writes the same target.json the CLI uses. APPLE-SUBMIT stays closed: this console cannot open the kread/KRW gate.</p>
<form id="lab" action="/api" method="get">
  <fieldset>
    <legend>Target</legend>
    <label for="build">Build</label>
    <select id="build" name="build">__BUILD_OPTIONS__</select>
    <label for="baseline">Baseline</label>
    <select id="baseline" name="baseline">__BASELINE_OPTIONS__</select>
    <button type="submit" name="cmd" value="target-set">Set target</button>
    <p id="current">__CURRENT__</p>
  </fieldset>
  <fieldset>
    <legend>Pick, diff, sim</legend>
    <button type="submit" name="cmd" value="target-list">List caches</button>
    <button type="submit" name="cmd" value="target-show">Show target</button>
    <button type="submit" name="cmd" value="gate">Show Apple-submit gate</button>
    <label for="table">Table for diff</label>
    <select id="table" name="table">__TABLE_OPTIONS__</select>
    <button type="submit" name="cmd" value="diff">Diff target vs baseline</button>
    <label for="stub">Allowlisted stub</label>
    <select id="stub" name="id">__STUB_OPTIONS__</select>
    <button type="submit" name="cmd" value="sim">Sim stub</button>
  </fieldset>
  <fieldset>
    <legend>Decode a chosen pair</legend>
    <label for="cache">Cache</label>
    <select id="cache" name="cache">__CACHE_OPTIONS__</select>
    <label for="cache2">Against</label>
    <select id="cache2" name="cache2">__CACHE2_OPTIONS__</select>
    <button type="submit" name="cmd" value="tables">Decode tables</button>
    <button type="submit" name="cmd" value="diff-pair">Diff selected pair</button>
    <button type="submit" name="cmd" value="emu">Emu fill-writer (pinned entry only)</button>
  </fieldset>
</form>
<pre id="out" aria-live="polite">[ ready — pick a command above ]</pre>
<script>
const form = document.getElementById('lab');
const out = document.getElementById('out');
form.addEventListener('submit', async (ev) => {
  ev.preventDefault();
  const btn = ev.submitter;
  const q = new URLSearchParams(new FormData(form, btn));
  out.textContent = 'running…';
  try {
    const res = await fetch('/api?' + q.toString());
    const body = await res.text();
    out.textContent = body;
    if (btn && btn.value === 'target-set' && !body.startsWith('(kernellab exit')) {
      location.reload();
    }
  } catch (err) {
    out.textContent = String(err);
  }
});
</script>
</body>
</html>
"""


def kernellab_cmd():
    env = os.environ.get("KERNELLAB_BIN")
    if env:
        return [sys.executable, env]
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "kernellab.py"),
        os.path.join(here, "kernellab"),
        "/var/jb/usr/share/kernellab/kernellab.py",
        "/usr/share/kernellab/kernellab.py",
        "/var/jb/usr/bin/kernellab",
        "/usr/bin/kernellab",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return [sys.executable, path]
    return [sys.executable, os.path.join(here, "kernellab.py")]


def kl_run(args):
    """Shell out to kernellab. Returns (code, text)."""
    cmd = kernellab_cmd() + list(args)
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=180,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
    except subprocess.TimeoutExpired:
        return 124, "(timed out — bounded at 180s)"
    text = proc.stdout or ""
    if proc.stderr and proc.stderr.strip():
        text = text + (("\n" if text else "") + proc.stderr)
    if proc.returncode != 0:
        text = f"(kernellab exit {proc.returncode})\n" + (text or "(no output)")
    if not text.strip():
        text = "(no output)"
    return proc.returncode, text[-30000:]


def q1(query, key, default=""):
    vals = query.get(key) or [default]
    return vals[0] if vals else default


def option(value, label, selected=False):
    sel = " selected" if selected else ""
    return f'<option value="{html.escape(value, quote=True)}"{sel}>{html.escape(label)}</option>'


def load_inventory():
    code, text = kl_run(["target", "list", "--json"])
    if code != 0:
        return {"caches": [], "target": {}, "allowlist": ["ident"], "error": text}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"caches": [], "target": {}, "allowlist": ["ident"], "error": text}


def render_page():
    inv = load_inventory()
    caches = [c for c in inv.get("caches") or [] if c.get("build")]
    builds = []
    seen = set()
    for entry in caches:
        if entry["build"] not in seen:
            seen.add(entry["build"])
            builds.append(entry["build"])
    target = inv.get("target") or {}
    current_build = target.get("build") or ""
    current_base = target.get("baseline") or ""

    if builds:
        build_opts = "".join(
            option(b, b, selected=(b == current_build)) for b in builds
        )
        cache_opts = build_opts
        cache2_opts = "".join(
            option(b, b, selected=(b == current_base or (not current_base and i == len(builds) - 1 and b != current_build)))
            for i, b in enumerate(builds)
        )
    else:
        empty = option("", "no kernelcache discovered")
        build_opts = cache_opts = cache2_opts = empty

    baseline_opts = option("", "(none)", selected=not current_base)
    baseline_opts += "".join(
        option(b, b, selected=(b == current_base)) for b in builds
    )

    tables = []
    table_seen = set()
    for entry in caches:
        for name in entry.get("tables") or []:
            if name not in table_seen:
                table_seen.add(name)
                tables.append(name)
    table_opts = option("", "all pinned names", selected=True)
    table_opts += "".join(option(name, name) for name in tables)

    allow = inv.get("allowlist") or ["ident"]
    stub_opts = "".join(option(s, s, selected=(s == "ident")) for s in allow)

    if current_build:
        path = target.get("path") or "(none)"
        base = current_base or "(none)"
        role = ""
        for row in inv.get("fleet") or []:
            if row.get("build") == current_build:
                role = f"\nrole: {row.get('role')} machine: {row.get('machine')}"
                break
        current = f"APPLE-SUBMIT: closed\ncurrent target: {current_build}\npath: {path}\nbaseline: {base}{role}"
    else:
        current = "APPLE-SUBMIT: closed\ncurrent target: (none) — choose a build and press Set target"
    if inv.get("error"):
        current += "\n" + inv["error"]

    page = PAGE
    page = page.replace("__BUILD_OPTIONS__", build_opts)
    page = page.replace("__BASELINE_OPTIONS__", baseline_opts)
    page = page.replace("__CACHE_OPTIONS__", cache_opts)
    page = page.replace("__CACHE2_OPTIONS__", cache2_opts)
    page = page.replace("__TABLE_OPTIONS__", table_opts)
    page = page.replace("__STUB_OPTIONS__", stub_opts)
    page = page.replace("__CURRENT__", html.escape(current))
    return page


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def _send(self, body, ctype="text/plain; charset=utf-8", status=200):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send(render_page(), "text/html; charset=utf-8")
            return
        if not parsed.path.startswith("/api"):
            self._send("not found", status=404)
            return
        query = parse_qs(parsed.query)
        cmd = q1(query, "cmd")
        if cmd == "target-json":
            code, text = kl_run(["target", "list", "--json"])
            if code == 0:
                self._send(text, "application/json; charset=utf-8")
            else:
                self._send(text, status=500)
            return
        if cmd == "target-list":
            _code, text = kl_run(["target", "list"])
            self._send(text)
            return
        if cmd == "target-show":
            _code, text = kl_run(["target", "show"])
            self._send(text)
            return
        if cmd == "gate":
            _code, text = kl_run(["gate"])
            self._send(text)
            return
        if cmd == "target-set":
            build = q1(query, "build")
            if not BUILD_RE.match(build or ""):
                self._send("refusing build id")
                return
            args = ["target", "set", "--build", build]
            baseline = q1(query, "baseline")
            if baseline:
                if not BUILD_RE.match(baseline):
                    self._send("refusing baseline id")
                    return
                args += ["--baseline", baseline]
            _code, text = kl_run(args)
            self._send(text)
            return
        if cmd == "diff":
            args = ["diff"]
            table = q1(query, "table")
            if table:
                if not TABLE_RE.match(table):
                    self._send("refusing table name")
                    return
                args += ["--table", table]
            _code, text = kl_run(args)
            self._send(text)
            return
        if cmd == "sim":
            stub = q1(query, "id") or "ident"
            if not STUB_RE.match(stub):
                self._send("refusing stub id")
                return
            _code, text = kl_run(["sim", stub])
            self._send(text)
            return
        if cmd == "tables":
            cache = q1(query, "cache")
            if not BUILD_RE.match(cache or ""):
                self._send("refusing cache id")
                return
            args = ["tables", "--cache", cache]
            table = q1(query, "table")
            if table:
                if not TABLE_RE.match(table):
                    self._send("refusing table name")
                    return
                args += ["--table", table]
            _code, text = kl_run(args)
            self._send(text)
            return
        if cmd == "diff-pair":
            cache = q1(query, "cache")
            cache2 = q1(query, "cache2")
            if not BUILD_RE.match(cache or "") or not BUILD_RE.match(cache2 or ""):
                self._send("refusing cache id")
                return
            args = ["diff", "--cache", cache, "--cache2", cache2]
            table = q1(query, "table")
            if table:
                if not TABLE_RE.match(table):
                    self._send("refusing table name")
                    return
                args += ["--table", table]
            _code, text = kl_run(args)
            self._send(text)
            return
        if cmd == "emu":
            cache = q1(query, "cache")
            if not BUILD_RE.match(cache or ""):
                self._send("refusing cache id")
                return
            _code, text = kl_run(["emu43748", "--cache", cache])
            self._send(text)
            return
        self._send("unknown cmd")


def main():
    print(f"KernelLab Console -> http://127.0.0.1:{PORT} (localhost only)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()

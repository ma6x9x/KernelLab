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
# Keep in lockstep with packaging/control Version.
CONSOLE_BUILD = "0.3.2"
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
.banner {
  color: #d7e6ff;
  background: #131a28;
  border: 1px solid #2c3a55;
  border-radius: 8px;
  padding: 0.6rem 0.8rem;
  letter-spacing: 0.04em;
  margin: 0 0 0.75rem;
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
.lab-top {
  display: grid;
  grid-template-columns: minmax(16rem, 1.4fr) minmax(14rem, 22rem);
  gap: 1rem;
  align-items: start;
}
.ladder-panel {
  border: 1px solid #2c3a55;
  border-radius: 8px;
  padding: 0.75rem 1rem 1rem;
}
.ladder-panel h2 {
  font-size: 1rem;
  color: #8ab4ff;
  margin: 0 0 0.35rem;
}
.ladder { margin: 0.4rem 0 0; padding-inline-start: 1.4rem; }
.stage {
  margin-block: 0.35rem;
  padding: 0.35rem 0.6rem;
  border: 1px solid #2c3a55;
  border-radius: 6px;
  min-height: 48px;
}
.stage-name { font-weight: 700; }
.stage-color { opacity: 0.85; margin-inline-start: 0.5rem; }
.stage-green { color: #7dcea0; border-color: #1f6b45; }
.stage-amber { color: #e6b35a; border-color: #8a6a2f; }
.stage-red { color: #f07178; border-color: #8a3038; }
@media (max-width: 720px) {
  .lab-top { grid-template-columns: 1fr; }
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
<p class="banner" id="build-banner">__BUILD_BANNER__</p>
<p class="dims">__EVIDENCE__localhost only. Pick a saved kernelcache, diff it against the baseline, then dry-run the allowlisted ident stub. Unicorn is not EL1. A stock kernelcache is not the live jailbroken kernel. An EMU row is not a device receipt. A map row is not a device receipt. Set target writes the same target.json the CLI uses. APPLE-SUBMIT stays closed. JB-rig kernel testing is not a fileable finding.</p>
<div class="lab-top">
<div class="train-chips">
<form id="quick-26" action="/api" method="get" data-lab="1">
  <fieldset>
    <legend>26.5 and 27.0</legend>
    <input type="hidden" name="train" value="26.5">
    <input type="hidden" name="baseline_train" value="27.0">
    <button type="submit" name="cmd" value="target-set-train">Set 26.5 host vs 27.0</button>
  </fieldset>
</form>
<form id="quick-27" action="/api" method="get" data-lab="1">
  <fieldset>
    <legend>27.0 and 26.5</legend>
    <input type="hidden" name="train" value="27.0">
    <input type="hidden" name="baseline_train" value="26.5">
    <button type="submit" name="cmd" value="target-set-train">Set 27.0 host vs 26.5</button>
  </fieldset>
</form>
</div>
<section class="ladder-panel" aria-label="Stage ladder">
  <h2>Stage ladder</h2>
  <p class="dims">sandbox, leak, race, krw, sptm. Map and emu labels. Not a device receipt.</p>
  __LADDER__
</section>
</div>
<form id="lab" action="/api" method="get" data-lab="1">
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
  <fieldset>
    <legend>Probes workspace</legend>
    <p class="dims">List stub. New tests are files in this folder, not a new .deb. Names only. A later on-device tab can own this list. Codegen slot is empty.</p>
    <pre id="probes">__PROBES__</pre>
    <button type="submit" name="cmd" value="probes-list">List probes</button>
  </fieldset>
</form>
<pre id="out" aria-live="polite">[ ready — pick a command above ]</pre>
<script>
const out = document.getElementById('out');
for (const form of document.querySelectorAll('form[data-lab]')) {
  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const btn = ev.submitter;
    const q = new URLSearchParams(new FormData(form, btn));
    out.textContent = 'running…';
    try {
      const res = await fetch('/api?' + q.toString());
      const body = await res.text();
      out.textContent = body;
      const setsTarget = btn && (btn.value === 'target-set' || btn.value === 'target-set-train');
      if (setsTarget && !body.startsWith('(kernellab exit')) {
        location.reload();
      }
    } catch (err) {
      out.textContent = String(err);
    }
  });
}
</script>
</body>
</html>
"""


def bridge_cmd():
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "oracle_bridge.py"),
        os.path.join(here, "oracle_bridge"),
        "/var/jb/usr/share/kernellab/oracle_bridge.py",
        "/usr/share/kernellab/oracle_bridge.py",
        "/var/jb/usr/bin/oracle_bridge",
        "/usr/bin/oracle_bridge",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return [sys.executable, path]
    return [sys.executable, os.path.join(here, "oracle_bridge.py")]


def ladder_html():
    try:
        proc = subprocess.run(
            bridge_cmd() + ["stages"],
            capture_output=True, text=True, timeout=30,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        text = (proc.stdout or "") + (proc.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "<p>%s</p>" % html.escape(str(exc))
    items = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 3 or parts[0] != "stage" or not parts[2].startswith("color="):
            continue
        name = parts[1]
        color = parts[2].split("=", 1)[1]
        if color not in ("green", "amber", "red"):
            color = "green"
        items.append(
            '<li class="stage stage-%s"><span class="stage-name">%s</span>'
            '<span class="stage-color">%s</span></li>'
            % (color, html.escape(name), html.escape(color))
        )
    if not items:
        return "<p>stage ladder unavailable</p>"
    return '<ol class="ladder">' + "".join(items) + "</ol>"


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


def console_build():
    env = os.environ.get("KERNELLAB_BUILD", "")
    if env and re.fullmatch(r"[0-9A-Za-z._-]{1,32}", env):
        return env
    return CONSOLE_BUILD


def probes_root():
    """On-device operator workspace. Override with KERNELLAB_PROBES for tests."""
    env = os.environ.get("KERNELLAB_PROBES")
    if env:
        return env
    if os.path.isdir("/var/jb"):
        return "/var/jb/var/kernellab/probes"
    return "/var/jb/var/kernellab/probes"


def operator_codegen_slot(root):
    """Empty extension point for a future operator-owned codegen tool.

    This package does not generate, compile, or copy probe sources.
    The slot writes nothing and returns an empty record.
    """
    return {
        "status": "empty",
        "generates": False,
        "compiles": False,
        "copies_sources": False,
        "path": root,
    }


def list_probe_entries(root, limit=200):
    """Names under the probes workspace. Bodies are not read."""
    root = os.path.abspath(root)
    if os.path.islink(root) or not os.path.isdir(root):
        return []
    found = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        rel_dir = os.path.relpath(dirpath, root)
        for name in list(dirnames):
            if name.startswith("."):
                dirnames.remove(name)
                continue
            path = os.path.join(dirpath, name)
            rel = name if rel_dir == "." else os.path.join(rel_dir, name)
            rel = rel.replace(os.sep, "/")
            if os.path.islink(path):
                found.append(rel + " (symlink, not followed)")
                dirnames.remove(name)
            else:
                found.append(rel + "/")
            if len(found) >= limit:
                return found
        for name in filenames:
            if name.startswith("."):
                continue
            path = os.path.join(dirpath, name)
            rel = name if rel_dir == "." else os.path.join(rel_dir, name)
            rel = rel.replace(os.sep, "/")
            if os.path.islink(path):
                found.append(rel + " (symlink, not followed)")
            else:
                found.append(rel)
            if len(found) >= limit:
                return found
    found.sort()
    return found


def format_probes_listing():
    root = probes_root()
    slot = operator_codegen_slot(root)
    lines = [
        f"probes: {root}",
        "new tests are files in this folder, not a new .deb",
        "codegen: empty (not implemented; an operator-owned tool may write here later)",
        f"slot: {slot['status']}",
    ]
    if os.path.islink(root) or not os.path.isdir(root):
        lines.append("entries: (directory not created yet — postinst creates it on device)")
        return "\n".join(lines)
    entries = list_probe_entries(root)
    if not entries:
        lines.append("entries: (none — drop your own trees here)")
    else:
        lines.append("entries:")
        lines.extend("  " + entry for entry in entries)
    lines.append("listing only — names, not bodies; nothing here is compiled or generated")
    return "\n".join(lines)


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
                role = (
                    f"\nrole: {row.get('role')} machine: {row.get('machine')} "
                    f"train: {row.get('train') or '(none)'}"
                )
                break
        current = f"APPLE-SUBMIT: closed\ncurrent target: {current_build}\npath: {path}\nbaseline: {base}{role}"
    else:
        current = "APPLE-SUBMIT: closed\ncurrent target: (none) — choose a build and press Set target"
    if inv.get("error"):
        current += "\n" + inv["error"]

    page = PAGE
    page = page.replace(
        "__BUILD_BANNER__",
        html.escape(f"=== KERNELLAB session BUILD {console_build()} ==="),
    )
    page = page.replace(
        "__EVIDENCE__",
        html.escape(
            "evidence class: device (weight 1.0, device receipt) · "
            "emu (weight 0.5, not a device receipt) · "
            "map (weight 0.3, not a device receipt). "
        ),
    )
    page = page.replace("__PROBES__", html.escape(format_probes_listing()))
    page = page.replace("__BUILD_OPTIONS__", build_opts)
    page = page.replace("__BASELINE_OPTIONS__", baseline_opts)
    page = page.replace("__CACHE_OPTIONS__", cache_opts)
    page = page.replace("__CACHE2_OPTIONS__", cache2_opts)
    page = page.replace("__TABLE_OPTIONS__", table_opts)
    page = page.replace("__STUB_OPTIONS__", stub_opts)
    page = page.replace("__CURRENT__", html.escape(current))
    page = page.replace("__LADDER__", ladder_html())
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
        if cmd == "target-set-train":
            train = q1(query, "train")
            baseline_train = q1(query, "baseline_train")
            if not re.fullmatch(r"[0-9]{2}\.[0-9]", train or ""):
                self._send("refusing train")
                return
            args = ["target", "set", "--train", train]
            if baseline_train:
                if not re.fullmatch(r"[0-9]{2}\.[0-9]", baseline_train):
                    self._send("refusing baseline train")
                    return
                args += ["--baseline-train", baseline_train]
            _code, text = kl_run(args)
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
        if cmd == "probes-list":
            self._send(format_probes_listing())
            return
        self._send("unknown cmd")


def main():
    build = console_build()
    print(f"=== KERNELLAB session BUILD {build} ===")
    print(
        "evidence class: device (weight 1.0, device receipt) | "
        "emu (weight 0.5, not a device receipt) | "
        "map (weight 0.3, not a device receipt)"
    )
    print(f"probes: {probes_root()} (codegen slot empty)")
    print(f"KernelLab Console -> http://127.0.0.1:{PORT} (localhost only)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# klconsole.py — KernelLab Console BETA 0 (2026-10-29)
#
# The VM-UI's first beta: a single-file LOCAL web console over kernellab.py
# (tables / diff / emu43748) with the Lum1na-Mind triage on the side. Runs on
# 127.0.0.1 only — nothing listens off-host, no keys, no telemetry, all free.
#
#   python3 klconsole.py            -> http://127.0.0.1:8737
#
# OPSEC: this server never talks to the network beyond localhost; it shells
# out to python3 kernellab.py (the same repo) and renders the results.

import json
import os
import re
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("KL_PORT", "8737"))

PAGE = """<!doctype html><html><head><meta charset=utf-8>
<title>KernelLab Console</title><style>
body{background:#0b0e14;color:#c8d2e0;font:14px/1.5 ui-monospace,Menlo,monospace;margin:0;padding:20px}
h1{font-size:16px;color:#8ab4ff;letter-spacing:2px;margin:0 0 12px}
button{background:#1c2333;color:#8ab4ff;border:1px solid #2c3a55;border-radius:6px;
padding:8px 14px;margin:2px;cursor:pointer;font:inherit}
button:hover{background:#263049}
select,input{background:#131a28;color:#c8d2e0;border:1px solid #2c3a55;border-radius:6px;padding:8px;font:inherit}
#out{white-space:pre-wrap;background:#0d1220;border:1px solid #1c2540;border-radius:8px;
padding:14px;margin-top:12px;min-height:300px;max-height:60vh;overflow:auto}
.dims{opacity:.55;font-size:12px;margin-bottom:8px}
</style></head><body>
<h1>KERNELLAB CONSOLE — BETA 0</h1>
<div class=dims>local-only · stdlib python · the no-guess law: every byte shown came from the on-disk caches</div>
<div>
cache <select id=cach></select>
table <select id=tab></select>
against <select id=cach2></select>
</div>
<div>%s</div>
<pre id=out>[ ready — pick a command above ]</pre>
<script>
const K=[...document.querySelectorAll('#cach,#cach2')],T=document.getElementById('tab');
const outs=document.getElementById('out');
async function go(q){outs.textContent='… running (this shells out to kernellab.py — real bytes, no guessing)';const r=await fetch('/api?'+q);outs.textContent=await r.text()}
document.getElementById('b_tables').onclick=()=>go('cmd=tables&c='+K[0].value+'&t='+T.value);
document.getElementById('b_diff').onclick=()=>go('cmd=diff&a='+K[0].value+'&b='+K[1].value+'&t='+T.value);
document.getElementById('b_emu').onclick=()=>go('cmd=emu&c='+K[0].value);
</script></body></html>"""


def kl_run(args):
    """shell out to kernellab.py with a bounded timeout; return its text."""
    cmd = [sys.executable, os.path.join(ROOT, "kernellab.py")] + args
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=180,
                           cwd=ROOT)
        out = (p.stdout or "") + (p.stderr or "")
        return out[-30000:] if out.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        return "(timed out — bounded at 180s; the no-storm law)"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, ctype="text/html; charset=utf-8"):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            caches = ["23F77", "24A435"]
            if os.path.isdir("/Users/kolby/Documents/ios-xnu-hunt/kernels/21D50"):
                caches.append("21D50")
            caches = [c for c in caches if c != "21D50" or
                      os.path.isdir("/Users/kolby/Documents/ios-xnu-hunt/kernels/21D50")]
            tables = {
                "23F77": ["iogpu.deviceconn", "iosurf.smethods", "iomfb.smethods", "ave2.smethods"],
                "24A435": ["iogpu.smethodsA", "m2scaler.methods", "iosurf.smethods",
                           "iomfb.smethods", "ave2.smethods"],
                "21D50": [],
            }
            opt = lambda v, s: "".join('<option>%s</option>' % v for v in s)
            btns = ('<button id=b_tables>TABLES (decode)</button>'
                    '<button id=b_diff>SURVIVOR-DIFF</button>'
                    '<button id=b_emu43748>EMU (fill-writer)</button>')
            page = PAGE % (btns)
            page = page.replace("</select>\n</div>",
                                "</select></div>")
            # simple selects
            page = page.replace('<select id=cach></select>',
                                '<select id=cach>%s</select>' % opt(caches, caches))
            page = page.replace('<select id=cach2></select>',
                                '<select id=cach2>%s</select>' % opt(reversed(caches), caches))
            page = page.replace('<select id=tab></select>',
                                '<select id=tab>%s</select>' % "".join(
                                    f'<option>{t}</option>' for t in tables["23F77"] + tables["24A435"]))
            self._send(page)
            return
        if u.path.startswith("/api"):
            q = parse_qs(u.query)
            cmd = q.get("cmd", [""])[0]
            if cmd == "tables":
                self._send(kl_run(["tables", "--cache", q.get("c", ["23F77"])[0],
                                   "--table", q.get("t", ["iogpu.deviceconn"])[0]]),
                           "text/plain; charset=utf-8")
            elif cmd == "diff":
                self._send(kl_run(["diff", "--cache", q.get("a", ["23F77"])[0],
                                   "--cache2", q.get("b", ["24A435"])[0],
                                   "--table", q.get("t", ["iosurf.smethods"])[0]]),
                           "text/plain; charset=utf-8")
            elif cmd == "emu":
                self._send(kl_run(["emu43748", "--cache", q.get("c", ["24A435"])[0]]),
                           "text/plain; charset=utf-8")
            else:
                self._send("unknown cmd", "text/plain")
            return
        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    print("KernelLab Console BETA 0 -> http://127.0.0.1:%d (localhost only)" % PORT)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
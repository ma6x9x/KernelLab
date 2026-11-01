#!/usr/bin/env python3
# kernellab.py — KernelLab CLI
#
# Week-1 home loop (see NOTES/002_target_diff_sim.md):
#   target list|set|show  — pick a kernelcache the operator already extracted
#   diff                  — survivor-diff of pinned tables (default: target vs baseline)
#   sim <id>              — allowlisted userspace stub only (ident)
#   gate                  — Apple-submit stays closed until kread/KRW (not this tool)
#   tables / emu43748     — slice #1, unchanged in what they are willing to claim
#
# Fleet build tags come from the ios-xnu-hunt judgment pack (roles and
# machines only). No-guess law: a build with no pinned table entry produces
# a refusal, not a VA. Addresses are not copied across machines.
# Caches are never shipped; this file only reads paths the operator points at.
# sim ident does not load kernel bytes into Unicorn.
# Nothing in this file can open the Apple-submit gate.

import argparse
import json
import os
import re
import sys
import tempfile

try:
    import unicorn
except ImportError:
    unicorn = None

# Flat VA law verified for these builds only (23F77 / 24A435 / 24B119).
# Any other tag refuses. Do not extend this set without a byte-verified pin.
VERIFIED_VA = ("23F77", "24A435", "24B119")

BUILD_RE = re.compile(r"^[0-9]{2}[A-Z][0-9]{2,4}[a-z]?$")

# Fleet-verified table pins. Per-build gaps are the diff layer's job.
# Do not add a row here to "fill in" a build — that is a guess.
KNOWN_TABLES = {
    # tag: {name: (va, stride, nrows)}
    "23F77":  {
        "iogpu.deviceconn": (0x7EB9318, 0x18, 55),
        "iosurf.smethods":  (0x7F33888, 0x28, 126),
        "iomfb.smethods":   (0x7EF0C90, 0x18, 88),
        "ave2.smethods":    (0x7BFEC58, 0x18, 16),
        # m2scaler on 23F77 is not pinned. Do not invent the slot.
    },
    "24A435": {
        "iogpu.smethodsA":  (0x82F64B0, 0x18, 56),
        "m2scaler.methods": (0x80EFCE0, 0x30, 12),
        "iosurf.smethods":  (0x837FA10, 0x28, 126),
        "iomfb.smethods":   (0x832FD70, 0x28, 93),
        "ave2.smethods":    (0x7F902D0, 0x18, 16),
        "ane.directpath":   (0x7CBFA30, 0x28, 26),
    },
}

# Userspace stubs named in this repo's notes. ident is the only one.
# emu43748 is a separate pinned command, not a sim id.
ALLOWLIST = {
    "ident": (
        "contract stub: report target file and pinned-entry present-vs-missing, "
        "then dry-run a userspace Unicorn return (movz x0, #1; ret)"
    ),
}

# movz x0, #1; ret — a userspace contract, not kernel text.
IDENT_STUB = bytes.fromhex("200080d2c0035fd6")
STUB_BASE = 0x10000000

# Judgment-pack device table plus the trains already named in this repo.
# 23F77 is 26.5 on iPhone13,2. 24A435 is 27.0 on iPhone18,2. 24A437 is the
# unpinned 27.0-family cache on that same machine. Trains are labels only.
# 23F77 and 23G71 do not share addresses. 21D50 is a shape reference.
# 24B119 is the same machine as 23F77 in the pack cache map and is not 27.0.
FLEET = (
    # tag, role, machine, train, note
    ("23F77", "hunt", "iPhone13,2", "26.5", "26.5 hunt host"),
    ("23G71", "hunt-ipad", "iPad8,*", "", "addresses do not transfer from 23F77"),
    ("21D50", "shape-reference", "iPhone12-mini", "", "shape reference only, not the hunt device"),
    ("24A435", "diff-input", "iPhone18,2", "27.0",
     "27.0 on a different machine; do not paste addresses onto 23F77"),
    ("24A437", "diff-input", "iPhone18,2", "27.0",
     "27.0 family, same machine as 24A435; no pinned method table"),
    ("24B119", "diff-input", "iPhone13,2", "",
     "same machine as 23F77 in the pack cache map; VA band pinned; no method-table pin"),
)
FLEET_BY = {
    tag: {"role": role, "machine": machine, "train": train, "note": note}
    for tag, role, machine, train, note in FLEET
}
TRAIN_RE = re.compile(r"^[0-9]{2}\.[0-9]$")

# JB-rig testing is allowed. It is not an Apple submission.
# This lab cannot open the gate, and a complete hunt-SKU chain is still required.
GATE_LINES = (
    "APPLE-SUBMIT: closed",
    "JB-rig kernel testing is not a fileable finding.",
    "The gate stays closed until a complete hunt-SKU chain. This lab cannot open it.",
    "Do not submit to Apple.",
)

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".hg", ".svn"}


def print_gate():
    for line in GATE_LINES:
        print(line)


def fleet_public():
    rows = []
    for tag, role, machine, train, note in FLEET:
        rows.append({
            "build": tag,
            "role": role,
            "machine": machine,
            "train": train,
            "pinned_entry": tag in KNOWN_TABLES,
            "note": note,
        })
    return rows


def annotate_cache(entry):
    meta = FLEET_BY.get(entry.get("build") or "")
    out = dict(entry)
    out["fleet_role"] = meta["role"] if meta else None
    out["machine"] = meta["machine"] if meta else None
    return out


def pair_note(tag_a, tag_b):
    meta_a = FLEET_BY.get(tag_a)
    meta_b = FLEET_BY.get(tag_b)
    if not meta_a or not meta_b:
        missing = [tag for tag, meta in ((tag_a, meta_a), (tag_b, meta_b)) if not meta]
        return (
            "pair-note: machine unknown for "
            + ",".join(missing)
            + " — refusing to treat this pair as one SKU"
        )
    if meta_a["machine"] != meta_b["machine"]:
        return (
            f"pair-note: different machines ({tag_a} {meta_a['machine']} vs "
            f"{tag_b} {meta_b['machine']}). survivor labels are file comparisons only. "
            "do not paste addresses across these machines."
        )
    return (
        f"pair-note: same machine {meta_a['machine']} ({tag_a} vs {tag_b}). "
        "a file diff does not open the Apple-submit gate."
    )


def band(tag):
    if tag in ("24A435", "24B119"):
        return 0xFFFFFE0007004000
    if tag == "23F77":
        return 0xFFFFFFF007004000
    raise SystemExit(f"no pinned VA band for {tag} — refusing positive claim")


def repo_dir():
    return os.path.dirname(os.path.abspath(__file__))


def cache_roots():
    """Env root first, then the jailbreak default, the checkout, and Documents if it exists."""
    roots = []
    env = os.environ.get("KERNELLAB_CACHES", "")
    if env.strip():
        for part in env.split(os.pathsep):
            part = part.strip()
            if part:
                roots.append(os.path.abspath(os.path.expanduser(part)))
    roots.append("/var/jb/var/kernellab/caches")
    roots.append(os.path.join(repo_dir(), "caches"))
    docs = os.path.expanduser("~/Documents/ios-xnu-hunt/kernels")
    if os.path.isdir(docs):
        roots.append(os.path.abspath(docs))
    out, seen = [], set()
    for root in roots:
        if root not in seen:
            seen.add(root)
            out.append(root)
    return out


def state_file():
    override = os.environ.get("KERNELLAB_STATE")
    if override:
        return os.path.abspath(os.path.expanduser(override))
    jb_dir = "/var/jb/var/kernellab"
    if os.path.isdir("/var/jb"):
        try:
            os.makedirs(jb_dir, exist_ok=True)
            return os.path.join(jb_dir, "target.json")
        except OSError:
            pass
    xdg = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(xdg, "kernellab", "target.json")


def load_target():
    path = state_file()
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise SystemExit(f"target.json unreadable ({path}): {e}")
    if not isinstance(doc, dict):
        raise SystemExit(f"target.json is not an object: {path}")
    return doc


def save_target(doc):
    path = state_file()
    parent = os.path.dirname(path) or "."
    os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".target.", suffix=".tmp", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(doc, f, sort_keys=True, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return path


def build_token(component):
    head = component.split("__", 1)[0]
    if BUILD_RE.match(head):
        return head
    if BUILD_RE.match(component):
        return component
    return None


def build_id_from_path(path):
    parts = os.path.abspath(path).split(os.sep)
    for part in reversed(parts[:-1]):
        tok = build_token(part)
        if tok:
            return tok
    return build_token(os.path.basename(path).split(".", 1)[0])


def is_kc_name(name):
    if not name or name.startswith("."):
        return False
    low = name.lower()
    if low.endswith((
        ".md", ".txt", ".json", ".py", ".pyc", ".deb",
        ".html", ".css", ".js", ".ds_store",
    )):
        return False
    return "kernelcache" in low


def _rank_key(entry):
    name = os.path.basename(entry["path"]).lower()
    if "research" in name:
        tier = 0
    elif "release" in name:
        tier = 1
    else:
        tier = 2
    return (tier, len(entry["path"]), entry["path"])


def discover_caches():
    found = []
    for root in cache_roots():
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, names in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
            for name in names:
                if not is_kc_name(name):
                    continue
                path = os.path.join(dirpath, name)
                if not os.path.isfile(path):
                    continue
                build = build_id_from_path(path)
                tables = list(KNOWN_TABLES.get(build, {})) if build else []
                found.append({
                    "build": build,
                    "path": path,
                    "bytes": os.path.getsize(path),
                    "pinned_entry": bool(tables),
                    "tables": tables,
                    "unlabeled": not bool(build),
                })
    preferred = set()
    groups = {}
    for entry in found:
        if entry["build"]:
            groups.setdefault(entry["build"], []).append(entry)
    for group in groups.values():
        group.sort(key=_rank_key)
        preferred.add(group[0]["path"])
    for entry in found:
        entry["preferred"] = entry["path"] in preferred
    found.sort(key=lambda e: (e["build"] or "zzzz", not e["preferred"], e["path"]))
    return found


def preferred_path(build):
    group = [c for c in discover_caches() if c["build"] == build]
    if not group:
        return None
    group.sort(key=_rank_key)
    return group[0]["path"]


def _search_blurb(build):
    lines = [f"no kernelcache for {build}. searched:"]
    for root in cache_roots():
        mark = "present" if os.path.isdir(root) else "absent"
        lines.append(f"  {mark}  {root}")
    lines.append(
        f"drop a file whose name contains 'kernelcache' under <root>/{build}/ "
        "— refusing to invent a path"
    )
    return "\n".join(lines)


def resolve_named(build, explicit_path=None):
    if not build or not BUILD_RE.match(build):
        raise SystemExit(
            f"refusing build id {build!r} — expected an iOS build token like 23F77"
        )
    if explicit_path:
        path = os.path.abspath(os.path.expanduser(explicit_path))
        if not os.path.isfile(path):
            raise SystemExit(f"no such file: {path}")
        return path
    path = preferred_path(build)
    if not path:
        raise SystemExit(_search_blurb(build))
    return path


def resolve_for_tag(tag):
    doc = load_target()
    if doc.get("build") == tag and doc.get("path"):
        if os.path.isfile(doc["path"]):
            return doc["path"]
        raise SystemExit(
            f"target.json records {tag} at {doc['path']} but that file is gone "
            "— retarget; refusing a substitute"
        )
    if doc.get("baseline") == tag and doc.get("baseline_path"):
        if os.path.isfile(doc["baseline_path"]):
            return doc["baseline_path"]
        raise SystemExit(
            f"target.json baseline {tag} at {doc['baseline_path']} is gone "
            "— retarget; refusing a substitute"
        )
    return resolve_named(tag)


class Cache:
    def __init__(self, tag, path=None):
        self.tag = tag
        self.path = path or resolve_for_tag(tag)
        if not self.path or not os.path.isfile(self.path):
            raise SystemExit(f"no cache for {tag}")
        with open(self.path, "rb") as f:
            self.d = f.read()

    # fileoff = (va & 0xFFFFFFF) − 0x7004000, verified builds only.
    def fo(self, va):
        if self.tag not in VERIFIED_VA:
            raise SystemExit(f"no pinned VA law for {self.tag} — refusing positive claim")
        return (va & 0xFFFFFFF) - 0x7004000

    def va(self, fo):
        return band(self.tag) + fo

    def fixup_ptr(self, o):
        """decode a chained-fixup pointer slot at fileoff o → real VA"""
        if o < 0 or o + 8 > len(self.d):
            raise SystemExit("refusing fixup: slice outside file — no positive claim")
        raw = int.from_bytes(self.d[o:o + 8], "little")
        if not raw:
            return 0
        return band(self.tag) + (raw & 0xFFFFFFFF)

    def read(self, va, n):
        o = self.fo(va)
        if o < 0 or o + n > len(self.d):
            raise SystemExit(
                f"refusing read: slice outside {self.tag} ({len(self.d)} bytes) "
                "— no positive claim"
            )
        return self.d[o:o + n]


def _table_in_file(c, va, stride, nrows):
    if nrows <= 0:
        return False
    o = c.fo(va)
    # Signature decode reads 0x28 bytes even when the row stride is shorter.
    need = (nrows - 1) * stride + 0x28
    return o >= 0 and o + need <= len(c.d)


def decode_table(c: Cache, va, stride, nrows, label):
    base = band(c.tag)
    print(f"\n== {c.tag} {label} @ VA {va:#x} stride {stride:#x} rows {nrows}")
    if not _table_in_file(c, va, stride, nrows):
        print(
            f"  refusing row decode: table slice outside {c.tag} "
            f"({len(c.d)} bytes). no positive claim."
        )
        return []
    rows = []
    for r in range(nrows):
        o = c.fo(va) + r * stride
        raw = int.from_bytes(c.d[o:o + 8], "little")
        fva = (base + (raw & 0xFFFFFFFF)) if raw else 0
        # signature bytes depend on table shape:
        # 0x18 stride = {handler, counts 4×u32}; 0x28 = {fn, ci, sin, co, sout, pad/entitle}
        cnt = []
        for k in range(8, 0x28, 4):
            cnt.append(int.from_bytes(c.d[o + k:o + k + 4], "little"))
        sig = f"sIn={cnt[0]:#x} sOut={cnt[1]:#x} stIn={cnt[2]:#x} stOut={cnt[3]:#x}"
        rows.append((r, fva, sig))
        mark = ""
        body = "--------"
        if fva:
            fo = c.fo(fva)
            if 0 <= fo and fo + 8 <= len(c.d):
                body = c.d[fo:fo + 8].hex()
            else:
                body = "unread"
        print(f"  sel{r:3d} fn={fva:#x} {sig}  body={body}{mark}")
    return rows


def fn_bytes(c: Cache, va, n=64):
    if not va:
        return None
    o = c.fo(va)
    if o < 0 or o + n > len(c.d):
        return None
    return c.d[o:o + n]


def diff_tag(fnA, fnB, vaA, vaB):
    if not vaA and not vaB:
        return "RETIRED", 0.0
    if not vaA or not vaB:
        return "ADDED", 0.0
    if fnA is None or fnB is None:
        return "RETIRED", 0.0
    a, b = fnA[:16], fnB[:16]
    if a == b:
        if fnA == fnB:
            return "SURVIVED", 1.0
        return "SURVIVED(0.5)", 0.5
    return "SHIFTED", 0.25


def cmd_tables(c, name=None):
    tabs = KNOWN_TABLES.get(c.tag)
    if not tabs:
        raise SystemExit(f"no pinned table entry for {c.tag} — refusing positive claim")
    if name:
        if name not in tabs:
            raise SystemExit(
                f"no pinned table entry {name} for {c.tag} — refusing positive claim"
            )
        va, stride, n = tabs[name]
        decode_table(c, va, stride, n, name)
    else:
        for k, (va, stride, n) in tabs.items():
            decode_table(c, va, stride, n, k)


def cmd_diff(tagA, tagB, name):
    tabsA = KNOWN_TABLES.get(tagA, {})
    tabsB = KNOWN_TABLES.get(tagB, {})
    if name not in tabsA or name not in tabsB:
        pinned_for = [tag for tag, tabs in ((tagA, tabsA), (tagB, tabsB)) if name in tabs]
        where = ", ".join(pinned_for) if pinned_for else "neither build"
        print(f"== {name}: NO-PIN — entry exists for {where}. refusing survivor claim")
        return
    (vaA, stride, n) = tabsA[name]
    (vaB, strideB, nB) = tabsB[name]
    A, B = Cache(tagA), Cache(tagB)
    print(f"\n== LIVE DIFF {name}: {tagA} vs {tagB}")
    if stride != strideB:
        print("  row0: STRIDE DIFFERS — layouts drifted; refusing a row-by-row survivor claim")
        return
    if not _table_in_file(A, vaA, stride, n) or not _table_in_file(B, vaB, strideB, nB):
        print(
            f"  refusing row decode: table slice outside {tagA} ({len(A.d)} bytes) "
            f"or {tagB} ({len(B.d)} bytes). no survivor claim."
        )
        return
    tally = {}
    for r in range(min(n, nB)):
        oA = A.fo(vaA) + r * stride
        oB = B.fo(vaB) + r * stride
        ra = int.from_bytes(A.d[oA:oA + 8], "little")
        rb = int.from_bytes(B.d[oB:oB + 8], "little")
        vaA_ = (band(tagA) + (ra & 0xFFFFFFFF)) if ra else 0
        vaB_ = (band(tagB) + (rb & 0xFFFFFFFF)) if rb else 0
        fa = fn_bytes(A, vaA_) if vaA_ else None
        fb = fn_bytes(B, vaB_) if vaB_ else None
        if (vaA_ and fa is None) or (vaB_ and fb is None):
            tag, _conf = "UNREADABLE", 0.0
        else:
            tag, _conf = diff_tag(fa, fb, vaA_, vaB_)
        tally[tag] = tally.get(tag, 0) + 1
        flag = "" if tag == "SURVIVED" else "  <<<"
        print(f"  row{r:3d} {tag:14s} {tagA}={vaA_:#x} {tagB}={vaB_:#x}{flag}")
    print("  tally:", tally)


def cmd_emu43748(tag, count, fill):
    ents = {"23F77": 0x874C070, "24A435": 0x8C16A84}
    entry = ents.get(tag)
    if not entry:
        raise SystemExit("no pinned fill-writer entry for " + tag)
    if unicorn is None:
        print("[-] unicorn missing — pip install unicorn")
        return
    c = Cache(tag)
    lo = entry & 0xFFFFFFFFFFFF
    fo_entry = lo - 0x7004000
    print(f"== emu43748 {tag}: fill-writer entry VA {entry:#x} → fileoff {fo_entry:#x}")
    page = 0x40000
    code_lo = lo & ~0x3FFFF
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM64, unicorn.UC_MODE_ARM)
    uc.mem_map(code_lo, 0x40000)
    uc.mem_write(lo, c.d[fo_entry:fo_entry + 0x4000])
    print("[*] entry bytes:", c.d[fo_entry:fo_entry + 16].hex())
    # the store-loop is entry+0x1b8 on 24A435 (pinned 0x8c16c3c); use it as the
    # emulation unit (pure store loop, no kalloc/PAC):
    store_loop = entry + 0x1b8
    print(f"[*] store-loop VA {store_loop:#x} bytes:", c.read(store_loop, 12).hex())
    # map a fake record table + request
    req = 0x40000000
    table = 0x40100000
    uc.mem_map(req & ~0xFFF, 0x20000)
    uc.mem_map(table, 0x10000)
    reqdata = bytes(0xFF) * 0x100  # the ANE req shape is set by the caller in the real path
    uc.mem_write(req, reqdata)
    # the pinned grammar: records stride 0x10 from table, count = request in-count
    uc.reg_write(unicorn.arm64_const.UC_ARM64_REG_X24, table)
    uc.reg_write(unicorn.arm64_const.UC_ARM64_REG_X28, 0)  # loop var i
    uc.reg_write(unicorn.arm64_const.UC_ARM64_REG_LR, 0xDEAD0000)
    print("[*] CONTRACT UNVERIFIED — register roles guessed from the pinned row;")
    print("    the harness REFUSES a positive claim unless the run completes and")
    print("    the store-loop exit reg-check passes (see note 284). This unit is")
    print("    the kernellab lane's skeleton, not yet an oracle.")
    try:
        uc.emu_start(store_loop, store_loop + 0x400, count=2000)
        print("[*] emulated run ENDED (loop exit or stop); check the record space:")
        t = uc.mem_read(table, 0x100)
        nonzero = sum(1 for b in t if b)
        print(f"    table bytes nonzero = {nonzero}/256")
    except unicorn.UcError as e:
        print(f"[!] unicorn stop: {e} — honest halt (no claim)")


def inventory():
    roots = [{"path": r, "present": os.path.isdir(r)} for r in cache_roots()]
    doc = load_target()
    target = {
        "build": doc.get("build"),
        "path": doc.get("path"),
        "baseline": doc.get("baseline"),
        "baseline_path": doc.get("baseline_path"),
    }
    return {
        "state": state_file(),
        "roots": roots,
        "caches": [annotate_cache(c) for c in discover_caches()],
        "target": target,
        "fleet": fleet_public(),
        "allowlist": sorted(ALLOWLIST),
        "submit_gate": "closed",
    }


def cmd_target_list(as_json):
    inv = inventory()
    if as_json:
        json.dump(inv, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return
    print(f"state: {inv['state']}")
    for root in inv["roots"]:
        mark = "present" if root["present"] else "absent"
        print(f"root {mark} {root['path']}")
    if not inv["caches"]:
        print("caches: (none)")
    for entry in inv["caches"]:
        if entry.get("unlabeled") or not entry.get("build"):
            print(f"cache (unlabeled) bytes={entry['bytes']} {entry['path']}")
            print("  place this file under <caches-root>/<build>/ — refusing to guess a build id")
            continue
        pin = "yes" if entry["pinned_entry"] else "no"
        pref = "yes" if entry["preferred"] else "no"
        role = entry.get("fleet_role") or "unlisted"
        print(
            f"cache {entry['build']} preferred={pref} pinned-entry={pin} "
            f"fleet={role} bytes={entry['bytes']} {entry['path']}"
        )
    for row in inv["fleet"]:
        pin = "yes" if row["pinned_entry"] else "no"
        train = row["train"] or "(none)"
        print(
            f"fleet {row['build']} role={row['role']} machine={row['machine']} "
            f"train={train} pinned-entry={pin}"
        )
        print(f"  {row['note']}")
    target = inv["target"]
    if target.get("build"):
        print(f"target build={target['build']} path={target.get('path')}")
        base = target.get("baseline") or "(none)"
        base_path = target.get("baseline_path") or "(none)"
        print(f"baseline={base} baseline_path={base_path}")
    else:
        print("target: (none) — kernellab target set --build <id> [--baseline <id>]")
    print_gate()


def cmd_target_show(as_json):
    doc = load_target()
    meta = FLEET_BY.get(doc.get("build") or "")
    view = {
        "state": state_file(),
        "build": doc.get("build"),
        "path": doc.get("path"),
        "baseline": doc.get("baseline"),
        "baseline_path": doc.get("baseline_path"),
        "fleet_role": meta["role"] if meta else None,
        "machine": meta["machine"] if meta else None,
        "train": meta["train"] if meta else None,
        "submit_gate": "closed",
    }
    if as_json:
        json.dump(view, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return
    for key in ("state", "build", "path", "baseline", "baseline_path", "fleet_role", "machine", "train"):
        val = view[key]
        print(f"{key}: {val if val else '(none)'}")
    print_gate()


def resolve_train(train):
    """Pick one on-disk fleet build for a train label. Prefer a pinned entry."""
    if not train or not TRAIN_RE.match(train):
        raise SystemExit(f"refusing train {train!r} — expected a label like 26.5 or 27.0")
    rows = [row for row in fleet_public() if row["train"] == train]
    if not rows:
        known = sorted({row["train"] for row in fleet_public() if row["train"]})
        raise SystemExit(
            f"no fleet tag for train {train}. known trains: {' '.join(known)}"
        )
    present = []
    for row in rows:
        path = preferred_path(row["build"])
        if path:
            present.append((row, path))
    if not present:
        lines = [
            f"no kernelcache on disk for train {train}.",
            "drop a file whose name contains kernelcache under:",
        ]
        for row in rows:
            lines.append(f"  /var/jb/var/kernellab/caches/{row['build']}/")
        lines.append("off-device, the same <build> directory under a caches root works.")
        lines.append(_search_blurb(rows[0]["build"]))
        raise SystemExit("\n".join(lines))

    def sort_key(item):
        row, path = item
        return (
            0 if row["pinned_entry"] else 1,
            0 if row["role"] == "hunt" else 1,
            _rank_key({"path": path}),
        )

    present.sort(key=sort_key)
    chosen, path = present[0]
    also = [row["build"] for row, _path in present[1:]]
    return chosen["build"], path, also


def cmd_target_set(build, baseline, path, clear_baseline, train=None, baseline_train=None):
    if train and build:
        raise SystemExit("pass --build or --train, not both")
    if baseline_train and baseline:
        raise SystemExit("pass --baseline or --baseline-train, not both")
    if train and path:
        raise SystemExit("--path applies to --build, not --train")
    if not build and not train:
        raise SystemExit("pass --build <id> or --train 26.5|27.0")
    if train:
        build, _path, also = resolve_train(train)
        print(f"train {train} -> {build}")
        if also:
            print("also on disk, not selected: " + ", ".join(also))
    if baseline_train:
        baseline, _bpath, also_b = resolve_train(baseline_train)
        print(f"baseline-train {baseline_train} -> {baseline}")
        if also_b:
            print("baseline also on disk, not selected: " + ", ".join(also_b))
    cur = load_target()
    chosen = resolve_named(build, path)
    doc = {
        "build": build,
        "path": chosen,
        "baseline": cur.get("baseline"),
        "baseline_path": cur.get("baseline_path"),
    }
    if clear_baseline:
        doc["baseline"] = None
        doc["baseline_path"] = None
    elif baseline:
        if baseline == build:
            raise SystemExit("baseline must be a different build than the target")
        doc["baseline"] = baseline
        doc["baseline_path"] = resolve_named(baseline)
    where = save_target(doc)
    print(f"target set: build={doc['build']}")
    print(f"path: {doc['path']}")
    if doc.get("baseline"):
        print(f"baseline: {doc['baseline']}")
        print(f"baseline_path: {doc['baseline_path']}")
    else:
        print("baseline: (none)")
    print(f"wrote: {where}")
    if doc.get("baseline"):
        print(pair_note(doc["build"], doc["baseline"]))
    print_gate()


def diff_pair(cache, cache2):
    if cache is None and cache2 is None:
        doc = load_target()
        if not doc.get("build"):
            raise SystemExit(
                "diff: no target — kernellab target set --build <id> --baseline <id>"
            )
        if not doc.get("baseline"):
            raise SystemExit(
                f"diff: target {doc['build']} has no baseline — "
                f"kernellab target set --build {doc['build']} --baseline <id>"
            )
        return doc["build"], doc["baseline"]
    if cache and not cache2:
        doc = load_target()
        if doc.get("build") == cache and doc.get("baseline"):
            return cache, doc["baseline"]
        raise SystemExit("diff: pass --cache2, or set a baseline on the target")
    if cache2 and not cache:
        raise SystemExit("diff: --cache is required with --cache2")
    return cache, cache2


def load_bridge():
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        here,
        "/var/jb/usr/share/kernellab",
        "/usr/share/kernellab",
        "/var/jb/usr/bin",
        "/usr/bin",
    ]
    for directory in candidates:
        if os.path.isfile(os.path.join(directory, "oracle_bridge.py")):
            if directory not in sys.path:
                sys.path.insert(0, directory)
            import oracle_bridge
            return oracle_bridge
    raise SystemExit("oracle_bridge.py not found — cannot --feed")


def _maybe_feed(ledger, file_present, emu_outcome):
    if not ledger:
        return
    bridge = load_bridge()
    if not os.path.exists(ledger):
        parent = os.path.dirname(os.path.abspath(ledger)) or "."
        os.makedirs(parent, exist_ok=True)
        bridge.save_ledger(ledger, {"domains": {}})
        print(f"ledger created: {ledger}")
    print(
        "feed: map weight 0.3 and emu weight 0.5 are ledger evidence only — "
        "not a device receipt"
    )
    map_outcome = "ok" if file_present else "lost"
    bridge.cmd_feed(ledger, "map", "kernellab", "kernellab.sim.ident.map", map_outcome)
    if emu_outcome:
        bridge.cmd_feed(ledger, "emu", "kernellab", "kernellab.sim.ident.emu", emu_outcome)


def run_ident_stub():
    """Dry-run the userspace contract stub. Does not map kernelcache bytes."""
    if unicorn is None:
        print("EMU: skipped unicorn-missing — no positive emu claim")
        return "nofire"
    try:
        uc = unicorn.Uc(unicorn.UC_ARCH_ARM64, unicorn.UC_MODE_ARM)
        uc.mem_map(STUB_BASE, 0x1000)
        uc.mem_write(STUB_BASE, IDENT_STUB)
        uc.emu_start(STUB_BASE, STUB_BASE + len(IDENT_STUB), count=8)
        x0 = uc.reg_read(unicorn.arm64_const.UC_ARM64_REG_X0)
    except unicorn.UcError as e:
        print(f"EMU: halt {e} — no positive emu claim")
        return "abort"
    if x0 == 1:
        print("EMU: contract-return x0=1")
        print("note: contract-return means the userspace stub returned. not a device receipt.")
        return "ok"
    print(f"EMU: unexpected x0={x0} — no positive emu claim")
    return "nofire"


def cmd_sim(stub_id, feed):
    if stub_id not in ALLOWLIST:
        known = " ".join(sorted(ALLOWLIST))
        raise SystemExit(f"sim: {stub_id!r} is not allowlisted. allowlist: {known}")
    print(f"== sim {stub_id}")
    print_gate()
    print(
        "CONTRACT: userspace allowlisted stub. Unicorn is not EL1. "
        "A stock kernelcache is not the live jailbroken kernel. "
        "An EMU row is not a device receipt."
    )
    print(f"stub: {ALLOWLIST[stub_id]}")
    doc = load_target()
    build = doc.get("build")
    path = doc.get("path")
    present = bool(path and os.path.isfile(path))
    nbytes = os.path.getsize(path) if present else 0
    if not build:
        print("MAP file: missing")
        print("MAP pinned-entry: missing")
        print("EMU: skipped")
        print(
            "refusing positive claim — no target.json "
            "(kernellab target set --build <id>)"
        )
        _maybe_feed(feed, file_present=False, emu_outcome=None)
        return
    print(f"target-build: {build}")
    print(f"target-path: {path}")
    print(f"MAP file: {'present' if present else 'missing'} bytes={nbytes}")
    tables = list(KNOWN_TABLES.get(build, {}))
    if tables:
        print("MAP pinned-entry: present names=" + ",".join(tables))
        print(
            "note: pinned-entry means this build id is in the lab table list. "
            "it is not a byte proof from the cache file."
        )
    else:
        print("MAP pinned-entry: missing")
        print(f"note: no pinned table entry for {build} — refusing positive claim")
    baseline = doc.get("baseline")
    if baseline:
        baseline_path = doc.get("baseline_path")
        baseline_present = bool(baseline_path and os.path.isfile(baseline_path))
        print(f"baseline-build: {baseline}")
        print(f"MAP baseline-file: {'present' if baseline_present else 'missing'}")
    else:
        print("baseline-build: (none)")
    emu_outcome = run_ident_stub()
    _maybe_feed(feed, file_present=present, emu_outcome=emu_outcome)


def _active_build(explicit, fallback):
    if explicit:
        return explicit
    return load_target().get("build") or fallback


def main(argv=None):
    ap = argparse.ArgumentParser(prog="kernellab")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_tables = sub.add_parser("tables", help="decode pinned UC method tables")
    p_tables.add_argument("--cache", default=None)
    p_tables.add_argument("--table", default=None)

    p_diff = sub.add_parser(
        "diff",
        help="survivor-diff pinned tables (default: target.json vs its baseline)",
    )
    p_diff.add_argument("--cache", default=None)
    p_diff.add_argument("--cache2", default=None)
    p_diff.add_argument("--table", default=None)

    p_emu = sub.add_parser(
        "emu43748",
        help="pinned fill-writer skeleton; refuses a build with no pinned entry",
    )
    p_emu.add_argument("--cache", default=None)
    p_emu.add_argument("--count", type=int, default=300)

    p_target = sub.add_parser("target", help="list, set, or show the saved kernelcache")
    tsub = p_target.add_subparsers(dest="target_cmd", required=True)

    p_list = tsub.add_parser("list", help="walk caches roots and print discovered kernelcaches")
    p_list.add_argument("--json", action="store_true", help="print the inventory as JSON")

    p_set = tsub.add_parser("set", help="persist target.json (build, path, optional baseline)")
    p_set.add_argument("--build", default=None, help="build id directory under a caches root")
    p_set.add_argument(
        "--train",
        default=None,
        help="26.5 or 27.0; picks the on-disk fleet tag for that train",
    )
    p_set.add_argument("--baseline", default=None, help="second build for the default diff")
    p_set.add_argument(
        "--baseline-train",
        default=None,
        help="train label for the baseline (26.5 or 27.0)",
    )
    p_set.add_argument("--path", default=None, help="explicit kernelcache file for --build")
    p_set.add_argument("--clear-baseline", action="store_true", help="drop a stored baseline")

    p_show = tsub.add_parser("show", help="print the persisted target")
    p_show.add_argument("--json", action="store_true")

    sub.add_parser(
        "gate",
        help="print the Apple-submit gate (stays closed; this lab cannot open it)",
    )

    p_sim = sub.add_parser("sim", help="allowlisted userspace stub dry-run (ident)")
    p_sim.add_argument("id", help="allowlist id; week 1 ships ident")
    p_sim.add_argument(
        "--feed",
        metavar="LEDGER",
        default=None,
        help="append one map row and one emu row through oracle_bridge",
    )

    args = ap.parse_args(argv)
    if args.cmd == "tables":
        tag = _active_build(args.cache, "23F77")
        cmd_tables(Cache(tag), args.table)
    elif args.cmd == "diff":
        tag_a, tag_b = diff_pair(args.cache, args.cache2)
        print(f"diff pair: {tag_a} vs {tag_b}")
        print(pair_note(tag_a, tag_b))
        print_gate()
        if args.table:
            names = [args.table]
        else:
            names = sorted(
                set(KNOWN_TABLES.get(tag_a, {})) | set(KNOWN_TABLES.get(tag_b, {}))
            )
        if not names:
            raise SystemExit(
                f"no pinned table entry for {tag_a} or {tag_b} — refusing positive claim"
            )
        for name in names:
            cmd_diff(tag_a, tag_b, name)
    elif args.cmd == "emu43748":
        tag = _active_build(args.cache, "23F77")
        cmd_emu43748(tag, args.count, None)
    elif args.cmd == "target":
        if args.target_cmd == "list":
            cmd_target_list(args.json)
        elif args.target_cmd == "set":
            cmd_target_set(
                args.build,
                args.baseline,
                args.path,
                args.clear_baseline,
                args.train,
                args.baseline_train,
            )
        elif args.target_cmd == "show":
            cmd_target_show(args.json)
    elif args.cmd == "gate":
        print_gate()
    elif args.cmd == "sim":
        cmd_sim(args.id, args.feed)


if __name__ == "__main__":
    main()

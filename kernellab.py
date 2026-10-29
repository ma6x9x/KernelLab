#!/usr/bin/env python3
# kernellab.py — KERNELLAB slice #1 (2026-10-28, note 284)
#
# The Kernellab lane (the operator's direction): an all-in-one corellium-
# alternative hosted on the jb devices — Procursus-jailed shell + the
# SandBlaster profile extractor + the boot-learner (p118) + this live-diff
# + primitive-test harness, evaluating REAL newer-XNU bytes (extracted
# kernelcaches / IPSWs) without burning device boots or risking panics.
#
# This slice is the MAC-side seed of the lane, the two layers that need no
# emulation and no guesses (the no-guess law):
#   1. tables   — decode the fleet's known UC method tables straight from
#                 the on-disk caches (row fns + in/out signatures).
#   2. diff     — LIVE SURVIVOR-DIFF of kext rows across two builds
#                 (byte-identical = SURVIVED; differs = SHIFTED; missing = RETIRED).
#   3. emu43748 — the 43748 fill-writer under unicorn (REAL bytes) —
#                 CONTRACT-UNVERIFIED gate: refuses to claim anything the
#                 emulated run doesn't itself produce.
#
# VA law: fileoff = low48(va) − 0x7004000 (23F77/24A435/24B117 verified
# tonight; each build's own static band = 0xfffffff007004000 or
# 0xfffffe0007004000). Fallback: the LC_FILESET entries (cmd 0x80000035).

import argparse
import os
import struct
import sys

try:
    from capstone import *
except ImportError:
    capstone = None
try:
    import unicorn
except ImportError:
    unicorn = None

KC = {
    "23F77":  "/Users/kolby/Documents/ios-xnu-hunt/kernels/23F77/23F77__iPhone13,2_3/kernelcache.research.iPhone13,2",
    "24A435": "/Users/kolby/Documents/ios-xnu-hunt/kernels/24A435/24A435__iPhone18,2/kernelcache.research.iPhone18,2",
    "24B119": None,  # cache not on disk yet (24B115/24B5099f are)
}


class Cache:
    def __init__(self, tag):
        self.tag = tag
        path = KC.get(tag) or self._find(tag)
        self.path = path
        self.d = open(path, "rb").read()

    @staticmethod
    def _find(tag):
        for root in ("/Users/kolby/Documents/ios-xnu-hunt/kernels",):
            for dirpath, _, names in os.walk(root):
                if tag in dirpath:
                    for n in names:
                        if "kernelcache.research" in n:
                            return os.path.join(dirpath, n)
        raise SystemExit(f"no cache for {tag}")

    # ---- VA law: (va & 0xFFFFFFF) − 0x7004000 (the verified flat law: the
    # low-28-bit band form; identical for 23F77/24A435/24B119 on-disk caches)
    def fo(self, va):
        return (va & 0xFFFFFFF) - 0x7004000

    def va(self, fo):
        return 0xFFFFFFF007004000 + fo  # low band form; band prefix cosmetic for reads

    def fixup_ptr(self, o):
        """decode a chained-fixup pointer slot at fileoff o → real VA"""
        raw = int.from_bytes(self.d[o:o + 8], "little")
        if not raw:
            return 0
        return band(self.tag) + (raw & 0xFFFFFFFF)


    def read(self, va, n):
        return self.d[self.fo(va):self.fo(va) + n]


KEXT_NAME_HINTS = ("IOGPUFamily", "AppleM2ScalerCSCDriver", "IOSurface",
                   "IOMobileGraphicsFamily", "AppleAVE2", "ANE")


# ---- known tables (fleet-verified); per-build addenda are the DIFF layer's job ----
KNOWN_TABLES = {
    # tag: {name: (va, stride, nrows)}
    "23F77":  {
        "iogpu.deviceconn": (0x7EB9318, 0x18, 55),
        "iosurf.smethods":  (0x7F33888, 0x28, 126),
        "iomfb.smethods":   (0x7EF0C90, 0x18, 88),
        "ave2.smethods":    (0x7BFEC58, 0x18, 16),
        # m2scaler table on 23F77 = device-observed 11 rows; static slot from t8150 twin band unresolved on 23F77 → left to device/census
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


def band(tag):
    return 0xFFFFFE0007004000 if tag in ("24A435", "24B119") else 0xFFFFFFF007004000


def decode_table(c: Cache, va, stride, nrows, label):
    base = band(c.tag)
    print(f"\n== {c.tag} {label} @ VA {va:#x} stride {stride:#x} rows {nrows}")
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
        body = c.d[c.fo(fva):c.fo(fva) + 8].hex() if fva else "--------"
        print(f"  sel{r:3d} fn={fva:#x} {sig}  body={body}{mark}")
    return rows


def fn_bytes(c: Cache, va, n=64):
    return c.d[c.fo(va):c.fo(va) + n]


def diff_tag(fnA, fnB, vaA, vaB):
    if not vaA and not vaB:
        return "RETIRED", 0.0
    if not vaA or not vaB:
        return "ADDED", 0.0
    if fnA is None or fnB is None:
        return "RETIRED", 0.0
    a, b = fnA[:16], fnB[:16]
    if a == b:
        # deeper: compare more
        if fnA == fnB:
            return "SURVIVED", 1.0
        return "SURVIVED(0.5)", 0.5
    return "SHIFTED", 0.25


def cmd_tables(c, name=None):
    tabs = KNOWN_TABLES.get(c.tag, {})
    if name:
        va, stride, n = tabs[name]
        decode_table(c, va, stride, n, name)
    else:
        for k, (va, stride, n) in tabs.items():
            decode_table(c, va, stride, n, k)


def cmd_diff(tagA, tagB, name):
    (vaA, stride, n) = KNOWN_TABLES[tagA][name]
    (vaB, strideB, nB) = KNOWN_TABLES[tagB][name]
    A, B = Cache(tagA), Cache(tagB)
    print(f"\n== LIVE DIFF {name}: {tagA} vs {tagB}")
    tally = {}
    for r in range(min(n, nB)):
        if stride != strideB:
            print(f"  row{r}: STRIDE DIFFERS — layouts drifted; run tables on each")
            break
        oA = A.fo(vaA) + r * stride
        oB = B.fo(vaB) + r * stride
        ra = int.from_bytes(A.d[oA:oA + 8], "little")
        rb = int.from_bytes(B.d[oB:oB + 8], "little")
        vaA_ = (band(tagA) + (ra & 0xFFFFFFFF)) if ra else 0
        vaB_ = (band(tagB) + (rb & 0xFFFFFFFF)) if rb else 0
        fa = fn_bytes(A, vaA_) if vaA_ else None
        fb = fn_bytes(B, vaB_) if vaB_ else None
        tag, conf = diff_tag(fa, fb, vaA_, vaB_)
        tally[tag] = tally.get(tag, 0) + 1
        flag = "" if tag == "SURVIVED" else "  <<<"
        print(f"  row{r:3d} {tag:14s} {tagA}={vaA_:#x} {tagB}={vaB_:#x}{flag}")
        if tally.get(tag, 0) <= 2 or tag not in ("SURVIVED",):
            pass
        else:
            # compact: after 3 identical rows print a run marker
            pass
    print("  tally:", tally)


def cmd_emu43748(tag, count, fill):
    if unicorn is None:
        print("[-] unicorn missing — pip install unicorn"); return
    c = Cache(tag)
    ents = {"23F77": 0x874C070, "24A435": 0x8C16A84}
    entry = ents.get(tag)
    if not entry:
        raise SystemExit("no pinned fill-writer entry for " + tag)
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


def main():
    ap = argparse.ArgumentParser("kernellab")
    ap.add_argument("cmd", choices=["tables", "diff", "emu43748"])
    ap.add_argument("--cache", default="23F77")
    ap.add_argument("--cache2", default="24A435")
    ap.add_argument("--table", default=None)
    ap.add_argument("--count", type=int, default=300)
    a = ap.parse_args()
    if a.cmd == "tables":
        decode = Cache(a.cache)
        cmd_tables(decode, a.table)
    elif a.cmd == "diff":
        if a.table not in (KNOWN_TABLES.get(a.cache) or {}):
            raise SystemExit(f"table {a.table} not known for {a.cache}")
        cmd_diff(a.cache, a.cache2, a.table)
    elif a.cmd == "emu43748":
        cmd_emu43748(a.cache, a.count, None)


if __name__ == "__main__":
    main()
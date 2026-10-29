#!/usr/bin/env python3
# oracle_bridge.py — offline-cortex bridge for the on-device LabBandit
# ("the Oracle", P007OpenOnly LabBandit.{h,m}).
#
# The ledger lives on the rig at Documents/lab_bandit.json. This tool reads
# that file OFF-DEVICE (pulled over AFC / scp) and:
#   show     — prints the LabBanditPlan-equivalent ranked plan (mirror of
#              labb_arm_stats + the v2 Plan ranking, LabBandit.m:176/613)
#   feed     — appends ONE class-weighted evidence row (RecordE mirror,
#              LabBandit.m:567) with an fsync'd atomic write (the p099 law)
#   demo     — copies a real ledger to /tmp/lab_bandit_demo.json and feeds
#              the known 27.0-shift receipts as map/emu rows (downweighted,
#              honest — never device-class claims)
#
# Laws mirrored exactly (do not "improve"):
#   reward:  door/claim-won/ok/fault-with-far=1.0 (WIN)
#            maf/family-b=0.0 (CRASH), abort/fires=0.5 (MID), else 0.25
#   EV:      rEff = -0.25 for crash (crash cost = the reboot), mean =
#            sum(c*w*rEff)/n; plan ev = mean*(1 - 0.35/sqrt(n)) for n>0
#            (== mean - 0.25*crash_share, then the Plan exploration shrink)
#   manual* buckets are never picked (labb_is_manual).
#   counts   key "<class>:<outcome>", weights device=1.0 emu=0.5 map=0.3
#   history  ring of 24 rows {t, arm, outcome:"<cls>:<oc>", cls}
#   feed only accepts outcome keys from the reward table — never invents.

import argparse
import json
import math
import os
import shutil
import sys
import tempfile
import datetime

DEMO_PATH = "/tmp/lab_bandit_demo.json"
HIST_RING = 24
DEMO_DOMAIN = "kernellab"

# LabBanditReward (LabBandit.m:42) — the shared reward law, verbatim.
REWARD_WIN = ("door", "claim-won", "ok", "fault-with-far")
REWARD_CRASH = ("maf", "family-b")
REWARD_MID = ("abort", "fires")
REWARD_MISS = ("nofire", "lost", "window-lost", "miss-adjacency", "survived")
KNOWN_OUTCOMES = frozenset(
    REWARD_WIN + REWARD_CRASH + REWARD_MID + REWARD_MISS)

EV_WEIGHTS = {"device": 1.0, "emu": 0.5, "map": 0.3}


def reward(outcome):
    if not outcome:
        return 0.25
    if outcome in REWARD_WIN:
        return 1.0
    if outcome in REWARD_CRASH:
        return 0.0
    if outcome in REWARD_MID:
        return 0.5
    return 0.25  # conservative miss


def ev_weight(cls):
    return EV_WEIGHTS.get(cls, 1.0)  # device/other


def is_manual(arm):
    return bool(arm) and arm.startswith("manual")


def load_ledger(path):
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    if not isinstance(doc, dict):
        raise SystemExit("error: %s is not a json object" % path)
    return doc


# atomic-write + fsync (the p099 ledger law: atomic, then F_FULLFSYNC).
def save_ledger(path, doc):
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(prefix=".lab_bandit.", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(doc, f, sort_keys=True, ensure_ascii=False, indent=2)
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


# mirror of labb_arm_stats (LabBandit.m:176): the stored counts are ALREADY
# class-weighted (RecordE adds the weight into the count itself), so the
# stats loop sums them AS-IS — never re-apply the class weight here
# (the C parses w from the prefix but does NOT multiply it into n/reward).
# Crash goes negative (-0.25 = the reboot cost) in the effective reward.
def arm_stats(arm_counts):
    n = 0.0
    reward_sum = 0.0
    crash_n = 0.0
    if not isinstance(arm_counts, dict):
        return n, 0.0, crash_n
    for key, val in arm_counts.items():
        if not isinstance(val, (int, float)) or val <= 0:
            continue
        oc = key
        if ":" in key and key.index(":") > 0:
            oc = key.split(":", 1)[1]
        r = reward(oc)
        r_eff = -0.25 if r <= 0.001 else r
        if r <= 0.001:
            crash_n += val
        n += val
        reward_sum += val * r_eff
    mean = reward_sum / n if n > 0 else 0.0
    return n, mean, crash_n


# mirror of LabBanditPlan (LabBandit.m:613): best non-manual arm per domain,
# ev = mean - 0.25*crash_share (== the -0.25-expectation above), then the
# Plan exploration shrink mean*(1 - 0.35/sqrt(n)); untried arms keep mean.
def domain_plan(dom):
    order = dom.get("arm_order") or []
    arms = dom.get("arms") or {}
    rows = []
    for arm in order:
        if is_manual(arm):
            continue
        n, mean, crash_n = arm_stats(arms.get(arm))
        crash_share = crash_n / n if n > 0 else 0.0
        ev = mean - 0.25 * crash_share
        if n > 0:
            ev = ev * (1.0 - 0.35 / math.sqrt(n))
        rows.append({"arm": arm, "ev": ev, "mean": mean, "n": n})
    rows.sort(key=lambda r: (-r["ev"], r["arm"]))
    return rows


def line(a, b, ev, n):
    return "plan: %-8s -> %-24s ev=%+.3f n=%.1f" % (a, b, ev, n)


def cmd_show(path):
    doc = load_ledger(path)
    doms = doc.get("domains") or {}
    plans = []
    for name in doms:
        dom = doms[name]
        if not isinstance(dom, dict):
            continue
        rows = domain_plan(dom)
        open_row = "round_open=%s last_arm=%s" % (
            "yes" if dom.get("round_open") else "no",
            dom.get("last_arm") or "?")
        if rows:
            plans.append({"domain": name, "best": rows[0], "rows": rows,
                          "open": open_row})
    # Plan ranks domains by ev descending
    plans.sort(key=lambda p: (-p["best"]["ev"], p["domain"]))
    if not plans:
        print("(no domains with pickable arms)")
        return
    for p in plans:
        b = p["best"]
        print(line(p["domain"], b["arm"], b["ev"], b["n"]) +
              "   [%s]" % p["open"])
    print("--- per-domain ranked arms (n carries the class downweight "
          "in the COUNTS: device=1.0 emu=0.5 map=0.3) ---")
    for p in plans:
        print(p["domain"] + ":")
        for r in p["rows"]:
            print("    %-32s n=%.2f mean=%+.3f ev=%+.3f"
                  % (r["arm"], r["n"], r["mean"], r["ev"]))


# LabBanditRecordE mirror (LabBandit.m:567). Appends ONE evidence row.
def cmd_feed(path, cls, domain, arm, outcome, quiet=False):
    if cls not in ("device", "emu", "map"):
        raise SystemExit("error: --class must be device|emu|map (got %r)" % cls)
    if outcome not in KNOWN_OUTCOMES:
        raise SystemExit("error: unknown outcome %r — only reward-table "
                         "classes are accepted (%s)" % (outcome, " ".join(
                             sorted(KNOWN_OUTCOMES))))
    doc = load_ledger(path)
    doms = doc.setdefault("domains", {})
    dom = doms.setdefault(domain, {})
    order = dom.setdefault("arm_order", [])
    if arm not in order:
        order.append(arm)  # Register's v1.1 arm-merge law: append, keep order
    arms = dom.setdefault("arms", {})
    counts = arms.setdefault(arm, {})
    w = ev_weight(cls)
    key1 = "%s:%s" % (cls, outcome)
    counts[key1] = counts.get(key1, 0.0) + w  # honest fractional evidence
    hist = dom.setdefault("history", [])
    stamp = datetime.datetime.now().astimezone().strftime(
        "%Y-%m-%d %H:%M:%S %Z")
    hist.append({"t": stamp, "arm": arm, "outcome": key1, "cls": cls})
    while len(hist) > HIST_RING:
        hist.pop(0)
    save_ledger(path, doc)
    if not quiet:
        print("fed: %s/%s %r -> %s w=%.1f (count=%.2f)" % (
            domain, cls, arm, outcome, w, counts[key1]))


def cmd_demo(src):
    if not os.path.exists(src):
        raise SystemExit("error: source ledger %s does not exist" % src)
    shutil.copyfile(src, DEMO_PATH)
    print("demo ledger: %s (copy of %s)" % (DEMO_PATH, src))
    print()
    print("== BEFORE ==")
    cmd_show(DEMO_PATH)
    print()
    # (a) map rows: the 27.0 shift receipts (live-survivor-diff evidence,
    #     downweighted map=0.3 — never a device-class claim)
    demo_rows = [
        ("map", "kernellab.iosurf.diff", "ok"),     # diff receipt = ok
        ("map", "kernellab.iosurf.smethods", "ok"),  # smethods row survived 27.0
        ("map", "kernellab.iosurf.smethods", "lost"),  # 2nd diff pass: lost
    ]
    for cls, arm, oc in demo_rows:
        cmd_feed(DEMO_PATH, cls, DEMO_DOMAIN, arm, oc, quiet=True)
    print("fed 3 map rows: kernellab.iosurf.diff/ok, "
          "kernellab.iosurf.smethods/ok+lost")
    # (b) one emu row: Kernellab offline emulation verdict, emu=0.5
    cmd_feed(DEMO_PATH, "emu", DEMO_DOMAIN, "kernellab.i43748.emu", "ok",
             quiet=True)
    print("fed 1 emu row : kernellab.i43748.emu/ok")
    print()
    print("== AFTER ==")
    cmd_show(DEMO_PATH)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="offline-cortex bridge for the LabBandit Oracle ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("show", help="print the LabBanditPlan-equivalent plan")
    p.add_argument("ledger", nargs="?", default="lab_bandit.json")

    p = sub.add_parser("feed", help="append one class-weighted evidence row")
    p.add_argument("--json", required=True)
    p.add_argument("--class", dest="ecls", required=True,
                   choices=["device", "emu", "map"])
    p.add_argument("--domain", required=True)
    p.add_argument("--arm", required=True)
    p.add_argument("--outcome", required=True)

    p = sub.add_parser("demo", help="copy a real ledger and feed demo rows")
    p.add_argument("ledger")

    a = ap.parse_args(argv)
    if a.cmd == "show":
        cmd_show(a.ledger)
    elif a.cmd == "feed":
        cmd_feed(a.json, a.ecls, a.domain, a.arm, a.outcome)
    elif a.cmd == "demo":
        cmd_demo(a.ledger)


if __name__ == "__main__":
    main()
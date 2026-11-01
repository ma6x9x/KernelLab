#!/usr/bin/env python3
"""Week-1 target / diff / sim / gate. No kernelcache bytes required."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KL = ROOT / "kernellab.py"
CONSOLE = ROOT / "klconsole.py"
BRIDGE = ROOT / "oracle_bridge.py"
FLEET = ("23F77", "23G71", "21D50", "24A435", "24A437", "24B119")


def run(args, env, check=False):
    proc = subprocess.run(
        [sys.executable, str(KL), *args],
        capture_output=True,
        text=True,
        env=env,
    )
    if check and proc.returncode != 0:
        raise AssertionError(proc.stdout + proc.stderr)
    return proc


class Week1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.caches = self.root / "caches"
        self.home = self.root / "home"
        self.home.mkdir()
        self.state = self.root / "target.json"
        self.env = os.environ.copy()
        self.env["HOME"] = str(self.home)
        self.env["KERNELLAB_CACHES"] = str(self.caches)
        self.env["KERNELLAB_STATE"] = str(self.state)
        self.env.pop("XDG_DATA_HOME", None)

    def write_kc(self, build, payload=b"not-a-kernelcache"):
        directory = self.caches / build
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "kernelcache.research.stub"
        path.write_bytes(payload)
        return path

    def test_target_help(self):
        proc = run(["target", "--help"], self.env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("list", proc.stdout)
        self.assertIn("set", proc.stdout)
        self.assertIn("show", proc.stdout)

    def test_gate_stays_closed(self):
        proc = run(["gate"], self.env, check=True)
        self.assertIn("APPLE-SUBMIT: closed", proc.stdout)
        self.assertIn("not a fileable finding", proc.stdout)
        self.assertIn("hunt-SKU chain", proc.stdout)
        self.assertIn("Do not submit to Apple.", proc.stdout)
        self.assertNotIn("APPLE-SUBMIT: open", proc.stdout)
        self.assertNotIn("hasKread stays false", proc.stdout)

    def test_fleet_roster_and_pins(self):
        self.write_kc("23F77")
        self.write_kc("24A437")
        proc = run(["target", "list"], self.env, check=True)
        for tag in FLEET:
            self.assertIn(f"fleet {tag} ", proc.stdout)
        self.assertIn(
            "fleet 23F77 role=hunt machine=iPhone13,2 train=26.5 pinned-entry=yes",
            proc.stdout,
        )
        self.assertIn("fleet 23G71 role=hunt-ipad", proc.stdout)
        self.assertIn("pinned-entry=no", proc.stdout)
        self.assertIn(
            "fleet 24A437 role=diff-input machine=iPhone18,2 train=27.0 pinned-entry=no",
            proc.stdout,
        )
        self.assertIn("fleet 21D50 role=shape-reference", proc.stdout)
        self.assertIn("APPLE-SUBMIT: closed", proc.stdout)
        self.assertIn("cache 23F77 ", proc.stdout)
        self.assertIn("fleet=hunt", proc.stdout)
        self.assertIn("cache 24A437 ", proc.stdout)
        self.assertIn("pinned-entry=no", proc.stdout)

        raw = run(["target", "list", "--json"], self.env, check=True)
        inv = json.loads(raw.stdout)
        self.assertEqual(inv["submit_gate"], "closed")
        by_build = {row["build"]: row for row in inv["fleet"]}
        self.assertEqual(set(by_build), set(FLEET))
        self.assertEqual(by_build["23F77"]["train"], "26.5")
        self.assertEqual(by_build["24A435"]["train"], "27.0")
        self.assertEqual(by_build["24A437"]["train"], "27.0")
        self.assertEqual(by_build["24B119"]["train"], "")
        self.assertTrue(by_build["23F77"]["pinned_entry"])
        self.assertFalse(by_build["24A437"]["pinned_entry"])
        self.assertFalse(by_build["23G71"]["pinned_entry"])
        self.assertFalse(by_build["24B119"]["pinned_entry"])
        for row in inv["fleet"]:
            self.assertNotIn("va", row)
            self.assertNotIn("stride", row)

    def test_set_show_and_cross_machine_note(self):
        hunt = self.write_kc("23F77")
        other = self.write_kc("24A435")
        proc = run(
            ["target", "set", "--build", "23F77", "--baseline", "24A435"],
            self.env,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("different machines", proc.stdout)
        self.assertIn("APPLE-SUBMIT: closed", proc.stdout)
        doc = json.loads(self.state.read_text())
        self.assertEqual(doc["build"], "23F77")
        self.assertEqual(doc["path"], str(hunt))
        self.assertEqual(doc["baseline"], "24A435")
        self.assertEqual(doc["baseline_path"], str(other))

        show = run(["target", "show"], self.env, check=True)
        self.assertIn("build: 23F77", show.stdout)
        self.assertIn("fleet_role: hunt", show.stdout)
        self.assertIn("machine: iPhone13,2", show.stdout)
        self.assertIn("APPLE-SUBMIT: closed", show.stdout)

    def test_same_machine_pair_still_refuses_unpinned_rows(self):
        self.write_kc("23F77")
        self.write_kc("24B119")
        proc = run(
            ["target", "set", "--build", "23F77", "--baseline", "24B119"],
            self.env,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("same machine iPhone13,2", proc.stdout)
        diff = run(["diff"], self.env)
        text = diff.stdout + diff.stderr
        self.assertEqual(diff.returncode, 0, text)
        self.assertIn("same machine iPhone13,2", text)
        self.assertIn("NO-PIN", text)
        self.assertIn("APPLE-SUBMIT: closed", text)
        self.assertNotIn("SURVIVED", text)

    def test_short_file_diff_does_not_claim_survived(self):
        self.write_kc("23F77")
        self.write_kc("24A435")
        run(["target", "set", "--build", "23F77", "--baseline", "24A435"], self.env, check=True)
        diff = run(["diff"], self.env)
        text = diff.stdout + diff.stderr
        self.assertEqual(diff.returncode, 0, text)
        self.assertIn("different machines", text)
        self.assertIn("do not paste addresses", text)
        self.assertTrue("NO-PIN" in text or "refusing row decode" in text)
        self.assertNotIn("SURVIVED", text)

    def test_unknown_builds_refuse(self):
        self.write_kc("22A400")
        self.write_kc("22B100")
        run(["target", "set", "--build", "22A400", "--baseline", "22B100"], self.env, check=True)
        diff = run(["diff"], self.env)
        text = diff.stdout + diff.stderr
        self.assertNotEqual(diff.returncode, 0)
        self.assertIn("no pinned table entry", text)
        self.assertIn("machine unknown", text)
        self.assertIn("APPLE-SUBMIT: closed", text)
        self.assertNotIn("SURVIVED", text)

    def test_train_preset_prefers_pinned_27(self):
        self.write_kc("23F77")
        self.write_kc("24A435")
        self.write_kc("24A437")
        proc = run(
            ["target", "set", "--train", "26.5", "--baseline-train", "27.0"],
            self.env,
        )
        text = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, text)
        self.assertIn("train 26.5 -> 23F77", text)
        self.assertIn("baseline-train 27.0 -> 24A435", text)
        self.assertIn("not selected: 24A437", text)
        self.assertIn("different machines", text)
        self.assertIn("not a fileable finding", text)
        doc = json.loads(self.state.read_text())
        self.assertEqual(doc["build"], "23F77")
        self.assertEqual(doc["baseline"], "24A435")

        only = run(
            ["target", "set", "--train", "27.0", "--baseline-train", "26.5"],
            self.env,
        )
        swapped = only.stdout + only.stderr
        self.assertEqual(only.returncode, 0, swapped)
        self.assertIn("train 27.0 -> 24A435", swapped)
        self.assertIn("baseline-train 26.5 -> 23F77", swapped)

    def test_train_falls_back_to_unpinned_and_refuses_when_missing(self):
        self.write_kc("24A437")
        proc = run(["target", "set", "--train", "27.0"], self.env)
        text = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, text)
        self.assertIn("train 27.0 -> 24A437", text)
        missing = run(
            ["target", "set", "--train", "26.5", "--baseline-train", "27.0"],
            self.env,
        )
        err = missing.stdout + missing.stderr
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("/var/jb/var/kernellab/caches/23F77/", err)
        self.assertNotIn("SURVIVED", err)

    def test_allowlist_is_ident_only(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("kernellab_mod", KL)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(set(mod.ALLOWLIST), {"ident"})

    def test_sim_ident_missing_pin_and_reject_unknown(self):
        path = self.write_kc("24A437", b"stub-bytes")
        run(["target", "set", "--build", "24A437"], self.env, check=True)
        proc = run(["sim", "ident"], self.env, check=True)
        self.assertIn("CONTRACT:", proc.stdout)
        self.assertIn("Unicorn is not EL1", proc.stdout)
        self.assertIn("not a device receipt", proc.stdout)
        self.assertIn("APPLE-SUBMIT: closed", proc.stdout)
        self.assertIn("MAP file: present", proc.stdout)
        self.assertIn(str(path), proc.stdout)
        self.assertIn("MAP pinned-entry: missing", proc.stdout)
        self.assertIn("refusing positive claim", proc.stdout)
        self.assertIn("EMU:", proc.stdout)
        bad = run(["sim", "not-a-probe"], self.env)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("not allowlisted", bad.stdout + bad.stderr)
        self.assertIn("ident", bad.stdout + bad.stderr)

    def test_tables_and_emu_refuse_unpinned_build(self):
        self.write_kc("24A437")
        tables = run(["tables", "--cache", "24A437"], self.env)
        self.assertNotEqual(tables.returncode, 0)
        self.assertIn("no pinned table entry", tables.stdout + tables.stderr)
        emu = run(["emu43748", "--cache", "24A437"], self.env)
        self.assertNotEqual(emu.returncode, 0)
        self.assertIn("no pinned fill-writer entry", emu.stdout + emu.stderr)

    def test_short_pinned_build_does_not_decode_rows(self):
        self.write_kc("23F77")
        proc = run(["tables", "--cache", "23F77", "--table", "iosurf.smethods"], self.env)
        text = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, text)
        self.assertIn("refusing row decode", text)
        self.assertNotIn("sel  0", text)

    def test_unlabeled_cache_is_not_a_build(self):
        self.caches.mkdir()
        (self.caches / "kernelcache.loose").write_bytes(b"loose")
        proc = run(["target", "list"], self.env, check=True)
        self.assertIn("(unlabeled)", proc.stdout)
        self.assertIn("refusing to guess a build id", proc.stdout)
        denied = run(["target", "set", "--build", "23F77"], self.env)
        self.assertNotEqual(denied.returncode, 0)

    def test_feed_ledger_row(self):
        self.write_kc("24A437")
        run(["target", "set", "--build", "24A437"], self.env, check=True)
        ledger = self.root / "lab_bandit.json"
        proc = run(["sim", "ident", "--feed", str(ledger)], self.env, check=True)
        self.assertIn("not a device receipt", proc.stdout)
        self.assertTrue(ledger.is_file())
        doc = json.loads(ledger.read_text())
        arms = doc["domains"]["kernellab"]["arms"]
        self.assertIn("kernellab.sim.ident.map", arms)
        self.assertIn("kernellab.sim.ident.emu", arms)
        show = subprocess.run(
            [sys.executable, str(BRIDGE), "show", str(ledger)],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("kernellab", show.stdout)
        self.assertIn("kernellab.sim.ident.map", show.stdout)

    def test_diff_without_target_refuses(self):
        proc = run(["diff"], self.env)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("no target", proc.stdout + proc.stderr)

    def test_console_api(self):
        self.write_kc("23F77")
        self.write_kc("24A435")
        env = self.env.copy()
        env["KL_PORT"] = "8738"
        env["KERNELLAB_BIN"] = str(KL)
        env["KERNELLAB_PROBES"] = str(self.root / "probes")
        proc = subprocess.Popen(
            [sys.executable, str(CONSOLE)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        def stop_console():
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)

        self.addCleanup(stop_console)
        base = "http://127.0.0.1:8738"

        def get(path):
            last = None
            for _ in range(40):
                try:
                    with urllib.request.urlopen(base + path, timeout=2) as resp:
                        return resp.status, resp.read().decode()
                except Exception as exc:  # server still binding
                    last = exc
                    import time
                    time.sleep(0.1)
            self.fail(f"console did not answer {path}: {last}")

        status, page = get("/")
        self.assertEqual(status, 200)
        self.assertIn("Set target", page)
        self.assertIn("Set 26.5 host vs 27.0", page)
        self.assertIn("Set 27.0 host vs 26.5", page)
        self.assertIn("Sim stub", page)
        self.assertIn("Show Apple-submit gate", page)
        self.assertIn("not a fileable finding", page)
        self.assertIn("APPLE-SUBMIT: closed", page)
        self.assertIn(">23F77<", page)
        self.assertIn('value="ident"', page)
        self.assertIn("=== KERNELLAB session BUILD 0.3.0 ===", page)
        self.assertIn("evidence class:", page)
        self.assertIn("device (weight 1.0, device receipt)", page)
        self.assertIn("emu (weight 0.5, not a device receipt)", page)
        self.assertIn("map (weight 0.3, not a device receipt)", page)
        self.assertIn("Probes workspace", page)
        self.assertIn("codegen: empty", page)
        self.assertIn("not a new .deb", page)

        status, body = get("/api?cmd=gate")
        self.assertEqual(status, 200)
        self.assertIn("APPLE-SUBMIT: closed", body)
        self.assertNotIn("APPLE-SUBMIT: open", body)

        status, body = get("/api?cmd=target-set-train&train=26.5&baseline_train=27.0")
        self.assertEqual(status, 200)
        self.assertIn("train 26.5 -> 23F77", body)
        self.assertIn("baseline-train 27.0 -> 24A435", body)
        self.assertIn("not a fileable finding", body)
        self.assertNotIn("(kernellab exit", body)

        status, body = get("/api?cmd=target-set-train&train=26.5;rm")
        self.assertIn("refusing train", body)

        status, body = get("/api?cmd=target-set&build=23F77&baseline=24A435")
        self.assertEqual(status, 200)
        self.assertIn("different machines", body)
        self.assertNotIn("(kernellab exit", body)

        status, body = get("/api?cmd=diff")
        self.assertIn("APPLE-SUBMIT: closed", body)
        self.assertNotIn("SURVIVED", body)

        status, body = get("/api?cmd=sim&id=ident")
        self.assertIn("CONTRACT:", body)
        self.assertIn("MAP file: present", body)
        self.assertIn("MAP pinned-entry: present", body)

        status, body = get("/api?cmd=sim&id=../etc/passwd")
        self.assertIn("refusing stub id", body)

        status, body = get("/api?cmd=target-set&build=not-a-build")
        self.assertIn("refusing build id", body)

        tree = self.root / "probes" / "operator-tree"
        tree.mkdir(parents=True)
        (tree / "owned.m").write_text("OPERATOR-BODY-NOT-LISTED\n")
        status, body = get("/api?cmd=probes-list")
        self.assertEqual(status, 200)
        self.assertIn("operator-tree/owned.m", body)
        self.assertNotIn("OPERATOR-BODY-NOT-LISTED", body)
        self.assertIn("codegen: empty", body)
        self.assertIn("listing only", body)

    def test_codegen_slot_is_empty_and_lists_names_only(self):
        import importlib
        sys.path.insert(0, str(ROOT))
        kl = importlib.import_module("klconsole")
        probes = self.root / "probes"
        tree = probes / "operator-tree"
        tree.mkdir(parents=True)
        (tree / "owned.m").write_text("OPERATOR-BODY-NOT-LISTED\n")
        before = sorted(path.name for path in tree.iterdir())
        slot = kl.operator_codegen_slot(str(probes))
        self.assertEqual(slot["status"], "empty")
        self.assertFalse(slot["generates"])
        self.assertFalse(slot["compiles"])
        self.assertFalse(slot["copies_sources"])
        self.assertEqual(slot["path"], str(probes))
        self.assertEqual(sorted(path.name for path in tree.iterdir()), before)
        missing = self.root / "missing-probes"
        kl.operator_codegen_slot(str(missing))
        self.assertFalse(missing.exists())
        self.assertEqual(kl.CONSOLE_BUILD, "0.3.0")
        control = (ROOT / "packaging" / "control").read_text()
        version = next(
            line.split()[1] for line in control.splitlines() if line.startswith("Version:")
        )
        self.assertEqual(kl.CONSOLE_BUILD, version)
        saved = os.environ.get("KERNELLAB_PROBES")
        os.environ["KERNELLAB_PROBES"] = str(probes)
        try:
            text = kl.format_probes_listing()
        finally:
            if saved is None:
                os.environ.pop("KERNELLAB_PROBES", None)
            else:
                os.environ["KERNELLAB_PROBES"] = saved
        self.assertIn("operator-tree/owned.m", text)
        self.assertNotIn("OPERATOR-BODY-NOT-LISTED", text)
        self.assertIn("codegen: empty", text)
        self.assertIn("not a new .deb", text)
        self.assertIn("slot: empty", text)

    def test_deb_ships_tools_and_not_a_kernelcache(self):
        if shutil.which("dpkg-deb") is None:
            self.skipTest("dpkg-deb missing")
        control = (ROOT / "packaging" / "control").read_text()
        version = next(
            line.split()[1] for line in control.splitlines() if line.startswith("Version:")
        )
        out = self.root / "deb"
        out.mkdir()
        proc = subprocess.run(
            ["sh", str(ROOT / "packaging" / "build.sh"), version, str(out)],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        deb = out / f"kernellab_{version}_iphoneos-arm64.deb"
        self.assertTrue(deb.is_file())
        contents = subprocess.check_output(["dpkg-deb", "--contents", str(deb)], text=True)
        for needle in (
            "./usr/bin/kernellab",
            "./usr/bin/klconsole",
            "./usr/bin/oracle_bridge",
            "./usr/share/kernellab/NOTES/002_target_diff_sim.md",
            "./usr/share/kernellab/NOTES/003_jb_rig_day_one.md",
            "./usr/share/kernellab/NOTES/004_springboard_and_probes.md",
            "./Applications/KernelLab.app/Info.plist",
            "./Applications/KernelLab.app/KernelLab",
            "./Applications/KernelLab.app/icon.png",
            "./Applications/KernelLab.app/icon@2x.png",
            "./Applications/KernelLab.app/icon@3x.png",
        ):
            self.assertIn(needle, contents)
        self.assertNotIn("kernelcache", contents.lower())
        for line in contents.splitlines():
            path = line.split()[-1]
            self.assertFalse(path.endswith(".m") or path.endswith(".h"), path)
        info = subprocess.check_output(["dpkg-deb", "--info", str(deb)], text=True)
        self.assertIn(f"Version: {version}", info)
        self.assertIn("postinst", info)
        control = self.root / "control"
        control.mkdir()
        subprocess.check_call(["dpkg-deb", "-e", str(deb), str(control)])
        postinst = (control / "postinst").read_text()
        self.assertIn("mkdir -p /var/jb/var/kernellab/caches", postinst)
        self.assertIn("mkdir -p /var/jb/var/kernellab/probes", postinst)
        self.assertIn("uicache -p /var/jb/Applications/KernelLab.app", postinst)
        self.assertIn("kernellab sim ident", postinst)
        self.assertIn("target set --train 26.5 --baseline-train 27.0", postinst)
        self.assertIn("not a fileable finding", postinst)
        self.assertIn("APPLE-SUBMIT stays closed", postinst)
        self.assertIn("not a new .deb", postinst)

        import plistlib
        rootfs = self.root / "rootfs"
        subprocess.check_call(["dpkg-deb", "-x", str(deb), str(rootfs)])
        app = rootfs / "Applications" / "KernelLab.app"
        info = plistlib.loads((app / "Info.plist").read_bytes())
        self.assertEqual(info["CFBundleDisplayName"], "KernelLab")
        self.assertEqual(info["CFBundleExecutable"], "KernelLab")
        self.assertEqual(info["CFBundleShortVersionString"], version)
        launcher = (app / "KernelLab").read_text()
        self.assertNotIn("__KERNELLAB_BUILD__", launcher)
        self.assertIn(f"KERNELLAB_BUILD:-{version}", launcher)
        self.assertIn("klconsole", launcher)
        self.assertIn("127.0.0.1", launcher)
        self.assertIn("codegen slot empty", launcher)
        self.assertTrue(os.access(app / "KernelLab", os.X_OK))
        for icon in ("icon.png", "icon@2x.png", "icon@3x.png"):
            self.assertGreater((app / icon).stat().st_size, 32)


if __name__ == "__main__":
    unittest.main()

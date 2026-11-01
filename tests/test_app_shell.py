"""Guards for the SpringBoard Mach-O: layout, no probe bodies, no shell launcher."""

import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"

BANNED = (
    "task_for_pid",
    "IOConnectCall",
    "kalloc",
    "mach_vm",
    "kread",
    "kwrite",
    "popen(",
    "dlopen",
    "/bin/sh",
)


class AppShellTests(unittest.TestCase):
    def test_version_and_identity(self):
        control = (ROOT / "packaging" / "control").read_text()
        self.assertIn("Version: 0.3.1", control)
        plist = (APP / "Info.plist").read_text()
        self.assertIn("<string>0.3.1</string>", plist)
        self.assertIn("com.ma6x9x.kernellab", plist)
        self.assertIn("<string>KernelLab</string>", plist)

    def test_makefile_is_rootless_application(self):
        text = (APP / "Makefile").read_text()
        self.assertIn("THEOS_PACKAGE_SCHEME := rootless", text)
        self.assertIn("APPLICATION_NAME := KernelLab", text)
        self.assertIn("Sources/*.swift", text)
        self.assertNotIn("TOOL_NAME", text)

    def test_prebuilt_is_macho_not_a_shell(self):
        binary = APP / "prebuilt" / "KernelLab.app" / "KernelLab"
        blob = binary.read_bytes()
        self.assertEqual(blob[:4], b"\xcf\xfa\xed\xfe")
        self.assertFalse(blob.startswith(b"#!"))
        self.assertIn(b"/var/jb/usr/bin/kernellab", blob)
        self.assertIn(b"Kolby pastes", blob)
        described = subprocess.check_output(["file", "-b", str(binary)], text=True)
        self.assertIn("Mach-O", described)
        self.assertIn("arm64", described)
        ok = subprocess.run(
            ["sh", str(ROOT / "packaging" / "postinst"), "--is-macho", str(binary)],
        )
        self.assertEqual(ok.returncode, 0)
        shell = Path(tempfile.mkdtemp()) / "KernelLab"
        shell.write_text("#!/bin/sh\necho no\n")
        shell.chmod(0o755)
        denied = subprocess.run(
            ["sh", str(ROOT / "packaging" / "postinst"), "--is-macho", str(shell)],
        )
        self.assertNotEqual(denied.returncode, 0)

    def test_no_objective_c_bodies_in_the_app_tree(self):
        banned_suffixes = {".m", ".mm", ".h", ".metal"}
        for path in APP.rglob("*"):
            if path.is_file() and path.suffix.lower() in banned_suffixes:
                self.fail(f"source body is not part of the app: {path}")

    def test_sources_stay_on_the_lab_shell(self):
        files = list((APP / "Sources").glob("*.swift")) + [APP / "stub" / "main.c"]
        self.assertGreater(len(files), 8)
        for path in files:
            text = path.read_text()
            for word in BANNED:
                self.assertNotIn(word, text, f"{path.name} contains {word}")
        scanner = (APP / "Sources" / "ProbeScanner.swift").read_text()
        self.assertNotIn("contents(atPath", scanner)
        self.assertNotIn("func preview", scanner)
        runner = (APP / "Sources" / "LabRunner.swift").read_text()
        self.assertIn("/var/jb/usr/bin/kernellab", runner)
        self.assertIn("posix_spawn", runner)
        stub = (APP / "stub" / "main.c").read_text()
        self.assertIn("posix_spawn", stub)
        self.assertIn("Kolby pastes", stub)

    def test_extension_point_is_empty(self):
        registry = (APP / "Sources" / "ProbePlugInRegistry.swift").read_text()
        self.assertIn("authored by Kolby, not shipped", registry)
        self.assertIn("static let plugs: [any ProbeWorkspacePlugIn] = []", registry)
        protocol = (APP / "Sources" / "ProbeWorkspacePlugIn.swift").read_text()
        self.assertIn("protocol ProbeWorkspacePlugIn", protocol)
        self.assertNotIn("func run", protocol)
        self.assertNotIn("func generate", protocol)

    def test_springboard_shell_launcher_is_gone(self):
        self.assertFalse((ROOT / "packaging" / "springboard" / "KernelLab").exists())


if __name__ == "__main__":
    unittest.main()

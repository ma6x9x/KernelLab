"""Guards for the SpringBoard shell: layout files, no probe bodies."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"

BANNED = (
    "task_for_pid",
    "IOConnectCall",
    "kalloc",
    "unicorn",
    "emu43748",
    "mach_vm",
    "kread",
    "kwrite",
    "popen(",
    "dlopen",
)


class AppShellTests(unittest.TestCase):
    def test_version_bump(self):
        control = (ROOT / "packaging" / "control").read_text()
        self.assertIn("Version: 0.3.0", control)
        plist = (APP / "Info.plist").read_text()
        self.assertIn("<string>0.3.0</string>", plist)
        self.assertIn("com.ma6x9x.kernellab", plist)
        self.assertIn("<string>15.0</string>", plist)

    def test_makefile_is_rootless_application(self):
        text = (APP / "Makefile").read_text()
        self.assertIn("THEOS_PACKAGE_SCHEME := rootless", text)
        self.assertIn("APPLICATION_NAME := KernelLab", text)
        self.assertIn("Sources/*.swift", text)

    def test_no_objective_c_bodies(self):
        banned_suffixes = {".m", ".mm", ".c", ".h", ".metal"}
        for path in APP.rglob("*"):
            if path.is_file() and path.suffix.lower() in banned_suffixes:
                self.fail(f"source body is not part of the app shell: {path}")

    def test_swift_sources_stay_on_the_lab_shell(self):
        swift = list((APP / "Sources").glob("*.swift"))
        self.assertGreater(len(swift), 10)
        for path in swift:
            text = path.read_text()
            for word in BANNED:
                self.assertNotIn(word, text, f"{path.name} contains {word}")

    def test_commands_are_the_lab_cli(self):
        actions = (APP / "Sources" / "LabAction.swift").read_text()
        for needle in ('"diff"', '"sim", "ident"', '"gate"', '"target", "list"', '"tables"'):
            self.assertIn(needle, actions)
        runner = (APP / "Sources" / "LabRunner.swift").read_text()
        self.assertIn("/var/jb/usr/bin/kernellab", runner)
        self.assertIn("posix_spawn", runner)
        self.assertNotIn("/bin/sh", runner)

    def test_extension_point_is_empty(self):
        registry = (APP / "Sources" / "ProbePlugInRegistry.swift").read_text()
        self.assertIn("authored by Kolby, not shipped", registry)
        self.assertIn("static let plugs: [any ProbeWorkspacePlugIn] = []", registry)
        protocol = (APP / "Sources" / "ProbeWorkspacePlugIn.swift").read_text()
        self.assertIn("protocol ProbeWorkspacePlugIn", protocol)
        self.assertNotIn("func run", protocol)
        self.assertNotIn("func generate", protocol)

    def test_stub_is_comment_only(self):
        text = (APP / "Sources" / "ProbeNames.swift").read_text()
        self.assertIn("// Kolby pastes", text)
        self.assertIn("user-owned sources only", text)
        self.assertNotIn("@implementation", text)
        self.assertNotIn("@interface", text)


if __name__ == "__main__":
    unittest.main()

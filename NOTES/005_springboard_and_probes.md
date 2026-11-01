# 005 — SpringBoard app and the probes workspace (0.3.0)

The `.deb` still installs the CLI (`kernellab`, `klconsole`, `oracle_bridge`).
It also installs a rootless SpringBoard app:

```
/var/jb/Applications/KernelLab.app
```

`CFBundleDisplayName` is `KernelLab`. `postinst` runs:

```
uicache -p /var/jb/Applications/KernelLab.app
```

The home-screen icon opens that bundle. The bundle's executable is a
packaging launcher: it prints the BUILD banner, starts the existing
`klconsole` on `127.0.0.1:8737`, and opens that page on device (`uiopen`
when the jailbreak provides it). The on-device UI is the console that
already ships here. CI has no iOS SDK, so the package does not build a
Theos binary and does not add new `.m` or `.h` sources.

## Install, then the day-one loop

1. Install `kernellab_0.3.0_iphoneos-arm64.deb` with Sileo, Zebra, or dpkg.
2. The KernelLab icon appears on the home screen after `uicache`.
3. Drop your own extracted kernelcaches under:

```
/var/jb/var/kernellab/caches/<build>/kernelcache…
```

4. Run the day-one loop (CLI or the console the icon opened):

```
kernellab target set --train 26.5 --baseline-train 27.0
kernellab diff
kernellab sim ident --feed /var/jb/var/kernellab/lab_bandit.json
kernellab gate
```

`kernellab gate` still prints `APPLE-SUBMIT: closed`. The icon does not
change that.

The console header prints a BUILD banner and the evidence classes already
used by this lab: `device` (weight 1.0, a device receipt), `emu` (weight
0.5, not a device receipt), `map` (weight 0.3, not a device receipt).
What counts as a complete port-work run stays in `NOTES/004_lum1na_parity.md`.

## Probes workspace

`postinst` creates:

```
/var/jb/var/kernellab/probes/
```

Put your own `.m` / `.h` trees in that directory when you want a new test.
Those files stay on the device. They are not in this repository, and they
are not inside the `.deb`. Installing a newer KernelLab package does not
require you to sideload a new binary for each test: the app lists whatever
is already in the folder.

The console has a list stub for that path (names only). A later on-device
tab can own the same directory. This package does not read probe bodies,
compile them, or generate them.

## Empty codegen slot

`packaging/probes/SLOT.md` and `operator_codegen_slot()` in `klconsole.py`
are the extension point for a future tool that you run yourself. That tool
is not implemented here. The slot returns empty and writes nothing.

# 004 — SpringBoard app shell (0.3.0)

`KernelLab.app` is a home-screen shell over the lab harness. Tapping the
icon runs `/var/jb/usr/bin/kernellab` and shows that process's output. The
app does not reimplement Unicorn, tables, diff, or `sim ident`.

APPLE-SUBMIT stays closed. This package does not ship kernelcaches. It does
not ship probe sources. It does not compile or run files in the probes folder.

## Install

1. Install `kernellab_0.3.0_iphoneos-arm64.deb` with Sileo, Zebra, or dpkg.
2. `postinst` creates `/var/jb/var/kernellab/caches`, `.../probes`, and
   `.../receipts`, then runs `uicache -p /var/jb/Applications/KernelLab.app`
   when `uicache` is on PATH.
3. Tap the KernelLab icon.

The CLI, `klconsole`, and `oracle_bridge` stay on disk. The icon does not
replace them.

Ubuntu CI stages the bundle layout without a Mach-O. A phone build that
should actually launch needs Theos first (`make -C app clean all`, then
`./packaging/build.sh`). Details are in the README.

## Console

Train chips:

- 26.5 host, baseline 27.0 → `kernellab target set --train 26.5 --baseline-train 27.0`
- 27.0 host, baseline 26.5 → `kernellab target set --train 27.0 --baseline-train 26.5`

Buttons: Diff, Sim ident (`sim ident`), Show gate, List caches (`target list`),
Tables. Export writes `sim ident`, the on-screen console, and copies of `.ips`
files into `/var/jb/var/kernellab/receipts/`. That transcript is not an Apple
submission.

## Probes

Default folder: `/var/jb/var/kernellab/probes`. Change it in the tab, or point
it at the app's Documents directory. Refresh lists `.m` and `.h` names you
dropped with Filza. No reinstall is required to see a new file.

Paste slots start empty. The words on the slot are "Kolby pastes". Saving
writes the text you typed. "Create empty stub" writes only:

```
// Kolby pastes
// user-owned sources only
// KernelLab does not compile or run this file.
```

The extension point is an empty protocol and an empty registry. The note on
screen is: future: operator-supplied runner / codegen plugs here — authored
by Kolby, not shipped.

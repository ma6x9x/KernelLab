# 004 — Lum1na / Lum1na-Debug parity (lab discipline, not attack bodies)

Use this when a JB-rig run should count as complete for Lum1na port work.
Fill every line. A blank line means the run is not complete.

Apple submit stays closed. This note does not cover a submission.

## Complete means all of these are written down

1. **Ident.** Output of `kernellab sim ident` for this run: `CONTRACT`, `MAP file`, `MAP pinned-entry`, and the `EMU` line.
2. **Console.** The target `klconsole` is showing, or the same `target show` text: train and build id.
3. **iPanic .ips path.** The path of the `.ips` file iPanic already shows for this run. If the rig produced no panic log, write `none`. This checklist records the path. It does not open the file.
4. **Train and build id.** From `kernellab target show`. Example: train `26.5`, build `23F77`, or train `27.0`, build `24A435`.
5. **Stage under test.** One ladder label, in this order: `sandbox`, `leak`, `race`, `krw`, `sptm`.
6. **Receipt label.** One of `map`, `emu`, or `device`.

## Receipt labels

| Label | What it is | Weight in oracle_bridge |
| --- | --- | --- |
| map | A file or diff observation | 0.3 |
| emu | A userspace Unicorn dry-run | 0.5 |
| device | A receipt that came from the rig itself | 1.0 |

Map is not a device receipt. Emu is not a device receipt. Unicorn is not EL1. A stock kernelcache is not the live kernel.

The existing ident keys stay `kernellab.sim.ident.map` and `kernellab.sim.ident.emu`. A stage label adds `kernellab.stage.<name>` as map and emu rows only. This tool refuses `class=device` on a stage arm, so a ladder name is never stored here as a device KRW claim.

```
oracle_bridge stages
kernellab sim ident --feed /var/jb/var/kernellab/lab_bandit.json --stage leak
oracle_bridge show /var/jb/var/kernellab/lab_bandit.json
```

Replace `leak` with the stage you actually exercised. The stage word is a label on the receipt. It does not create the receipt.

## Copy block

```
ident:        (paste sim ident)
console:      (train and build from target show)
ips:          (path or none)
train:        
build:        
stage:        sandbox | leak | race | krw | sptm
receipt:      map | emu | device
```

`klconsole` shows the same five stage names beside the 26.5 and 27.0 chips. Green is sandbox, leak, and krw. Amber is race. Red is sptm. The color is a label. It is not a result.

## Honesty / Lum1na parity

KernelLab adopts Lum1na lab discipline. Evidence weights stay the table
above: `device` = 1.0, `emu` = 0.5, `map` = 0.3. An emu verdict can kill a
lane or rank arms. It does not replace a device receipt.

`CONTRACT-UNVERIFIED`, an honest `SKIP`, and `NO-PIN` mean there is no
corroborated oracle. Refuse the positive claim.

`kernellab gate` prints `APPLE-SUBMIT: closed`. JB-rig kernel testing is
not a fileable finding.

A device export for iPanic is Ident, then the full console from the tap or
command under test, then the `.ips` when the run panics (the path, or
`none`). Handoff is panic type → faulting frame → stage. The stage is one
name from the ladder above.

Pair Lum1na Mind by the build id from `kernellab target show` (`26.5` /
`23F77`, `27.0` / `24A435`). Mind is not in this deb.

## VA law

`fileoff = (va & 0xFFFFFFF) − 0x7004000` on the builds that law was verified:
23F77, 24A435, and 24B119. Any other build id refuses the VA read. Do not
extend that set without a byte-verified pin.

Non-goals: no attack `.m` authorship, no probe codegen, and no copying
`Exploit` bodies into KernelLab.

## SpringBoard app and probes workspace

Package `0.3.0` installs the CLI and a rootless app:

```
/var/jb/Applications/KernelLab.app
```

`CFBundleDisplayName` is `KernelLab`. `postinst` runs
`uicache -p /var/jb/Applications/KernelLab.app`. The icon starts the
existing `klconsole` on `127.0.0.1:8737` and opens that page. The
executable is a packaging launcher. This repo does not build a Theos
binary and does not add `.m` or `.h` sources.

Install `kernellab_0.3.0_iphoneos-arm64.deb` with Sileo, drop extracted
kernelcaches under `/var/jb/var/kernellab/caches/<build>/`, then the
day-one loop in `NOTES/003_jb_rig_day_one.md`. The console header prints
`BUILD 0.3.0`. Evidence classes stay the table above. `APPLE-SUBMIT`
stays closed.

`postinst` creates `/var/jb/var/kernellab/probes/` and leaves it empty.
New tests are files the operator drops there, not a new `.deb`. The
console lists names only. `packaging/probes/SLOT.md` and
`operator_codegen_slot()` are an empty slot. They write nothing.

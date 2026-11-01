# 003 — JB-rig day one (26.5 and 27.0)

This is the loop for a jailbroken rig that already has kernel read/write and
is used to test 26.5 and 27.0 caches. It is lab work. It is not an Apple
submission.

`kernellab gate` prints `APPLE-SUBMIT: closed`. A target pick, a survivor
diff, or `sim ident` does not open that gate. JB-rig kernel testing is not
a fileable finding. The gate stays closed until a complete hunt-SKU chain.
This repository does not submit to Apple and does not describe that chain.

## 1. Install

Install `kernellab_0.3.0_iphoneos-arm64.deb` with Sileo, Zebra, or dpkg.
`postinst` creates `/var/jb/var/kernellab/caches` and
`/var/jb/var/kernellab/probes`, registers the SpringBoard icon with
`uicache -p /var/jb/Applications/KernelLab.app`, and prints this loop.
The package contains the CLI, `klconsole`, `oracle_bridge`, and
`KernelLab.app`. It does not contain a kernelcache. Confirm with
`dpkg-deb --contents` before you copy one on. The icon opens the same
localhost console as `klconsole`. The probes workspace, the stage ladder,
and receipt honesty are `NOTES/004_lum1na_parity.md`. New tests are files
in `/var/jb/var/kernellab/probes/`, not a new deb.

## 2. Drop kernelcaches

The build id is the directory name. The file name must contain `kernelcache`.

```
/var/jb/var/kernellab/caches/23F77/kernelcache.research.iPhone13,2
/var/jb/var/kernellab/caches/24A435/kernelcache.research.iPhone18,2
/var/jb/var/kernellab/caches/24A437/kernelcache.research.iPhone18,2
```

Those filenames are examples. A name like `23F77__iPhone13,2_3` as the
directory also works, because the build token is the part before `__`.

| Build | Train | Machine | Pinned method tables |
| --- | --- | --- | --- |
| 23F77 | 26.5 | iPhone13,2 | yes — hunt host |
| 24A435 | 27.0 | iPhone18,2 | yes |
| 24A437 | 27.0 | iPhone18,2 | no |

`23F77` and `24A435` are different machines. A diff of that pair says so.
Addresses are not copied from one onto the other. `24A437` is the unpinned
27.0-family cache on the same machine as `24A435`. If both 27.0 files are
on disk, `--train 27.0` selects `24A435` and names `24A437` as not selected.
`24B119`, `23G71`, and `21D50` stay on `target list` and are not 26.5 or 27.0.

Off the phone, the same directories work under `./caches` or
`KERNELLAB_CACHES`.

## 3. Set host against the other train

26.5 host, 27.0 baseline:

```
kernellab target list
kernellab target set --train 26.5 --baseline-train 27.0
kernellab target show
```

That resolves to `23F77` against `24A435` when those files are present.
The explicit form is the same choice:

```
kernellab target set --build 23F77 --baseline 24A435
```

Swap the trains when the rig under test is the 27.0 machine:

```
kernellab target set --train 27.0 --baseline-train 26.5
```

`klconsole` on `http://127.0.0.1:8737` has the same two buttons. They write
`/var/jb/var/kernellab/target.json` and nothing else.

If a train has no file, the command refuses and prints the directory to
fill. It does not invent a path.

## 4. Diff

```
kernellab diff
```

No arguments means target versus baseline. Honesty labels on a real row
compare stay `SURVIVED`, `SHIFTED`, `RETIRED`, and `ADDED`. `NO-PIN` and a
slice refusal are refusals. A short file must not come back `SURVIVED`.

The 26.5 host against 27.0 is a different-machine file comparison. Expect
that note. It is the lab comparison. It is not a same-SKU port and it is
not a submission.

## 5. Sim

```
kernellab sim ident
```

The allowlist is `ident` only. The notes in this repo do not name another
userspace stub, so none was added. `ident` prints whether the target file
is present or missing, and whether this build id has a pinned table entry.
Then it dry-runs a userspace Unicorn return (`movz x0, #1; ret`) when
Unicorn is installed. It does not load kernel bytes. `emu43748` stays its
own command for builds that already have that pinned entry. It is not a
`sim` id.

## 6. Ledger feed

```
kernellab sim ident --feed /var/jb/var/kernellab/lab_bandit.json
oracle_bridge show /var/jb/var/kernellab/lab_bandit.json
```

That appends one `map` row and one `emu` row on domain `kernellab`
(`kernellab.sim.ident.map`, `kernellab.sim.ident.emu`). The bridge weights
are map 0.3 and emu 0.5. Neither row is a device receipt, and neither row
is a fileable finding. Add `--stage sandbox|leak|race|krw|sptm` to also
label `kernellab.stage.<name>` as map and emu. What counts as a complete
port-work run is `NOTES/004_lum1na_parity.md`.

## 7. Mind

Mind is not in this deb. KernelLab does not launch it and does not accept a
Mind flag. When you point Mind at a build, use the build id from
`kernellab target show`.

https://github.com/ma6x9x/Lum1na

## 8. Gate check

```
kernellab gate
```

Expect `APPLE-SUBMIT: closed` and `JB-rig kernel testing is not a fileable
finding.` Stop there for Apple. Keep using the rig for the lab loop above.

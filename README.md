# Kernellab

A userspace micro-lab for iOS/XNU kernel research. It reads kernelcaches the
operator has already extracted and answers map / diff / stub questions from
those files. It is not a jailbreak and it does not ship kernelcaches.

The `.deb` is the lab home. Mind is a separate repo. Lumina / P007 is the hands.

## Week-1 loop: pick → diff → sim

```
kernellab target list
kernellab target set --build 23F77 --baseline 24A435
kernellab target show
kernellab diff
kernellab sim ident
klconsole
```

`diff` with no arguments compares the build in `target.json` to its baseline.
If those builds are different machines (for example hunt `23F77` /
`iPhone13,2` against `24A435` / `iPhone18,2`), the diff says so and does not
treat the pair as one SKU. `23G71`, `21D50`, and `24A437` are fleet tags with
no pinned method table: the lab lists them and refuses a positive claim.
`24B119` shares the hunt machine in the pack's cache map and still has no
method-table pin.

`sim ident` is the only allowlisted stub: it prints whether the target file
and the pinned table entry are present or missing, then dry-runs a userspace
Unicorn snippet (`movz x0, #1; ret`). It does not load kernel bytes.

`kernellab gate` prints `APPLE-SUBMIT: closed`. Kernel read/write is not
obtained. A pick, a diff, or a stub dry-run does not open that gate, and this
lab does not submit to Apple.

Optional: `kernellab sim ident --feed ledger.json` appends one map row and one
emu row through `oracle_bridge`. Those weights stay map=0.3 and emu=0.5.

## Where to put caches

The lab walks these roots (a root that is missing is reported, not invented):

1. `KERNELLAB_CACHES` (OS path separator for more than one)
2. `/var/jb/var/kernellab/caches` on a rootless jailbreak
3. `./caches` next to the checkout
4. `~/Documents/ios-xnu-hunt/kernels` when that directory exists

Place files as `<root>/<build>/kernelcache…`. The build id is the directory
name. The saved choice is `/var/jb/var/kernellab/target.json` on device, or
`$XDG_DATA_HOME/kernellab/target.json` off-device. `KERNELLAB_STATE` overrides
that path.

## What the other commands do

1. **tables** — decode a build's pinned user-client method tables from the
   on-disk kernelcache.
2. **diff** — survivor-diff of a pinned method table across two builds:
   `SURVIVED` (byte-identical code), `SHIFTED` (same slot, changed body),
   `RETIRED` / `ADDED` (row missing on one side). A name that is not pinned
   on both builds is `NO-PIN`. A file that does not contain the slice is not
   decoded. The lab does not guess offsets.
3. **emu43748** — the existing per-function skeleton. It runs only when that
   build already has a pinned entry, and it still refuses a claim the run
   does not produce.

## Honesty

- Unicorn is not EL1.
- A stock kernelcache is not the live jailbroken kernel.
- An EMU or map ledger row is not a device receipt.
- A build with no pinned table entry gets a refusal, not a filled-in table.
- `APPLE-SUBMIT` stays closed until a kread has passed on a device you own.
  This tool does not perform that check and cannot flip the gate.

## VA law

`fileoff = (va & 0xFFFFFFF) − 0x7004000` for the builds that law was verified
on: 23F77, 24A435, and 24B119. Other build ids refuse the VA read.

## Layout

- `kernellab.py` — the CLI.
- `klconsole.py` — localhost console. `http://127.0.0.1:8737`.
- `oracle_bridge.py` — offline LabBandit ledger mirror.
- `NOTES/` — design notes. Start with `NOTES/002_target_diff_sim.md`.
- `packaging/` — rootless Procursus `.deb`. See `DEBIAN-STYLE.md`.

## Console

`python3 klconsole.py` binds `127.0.0.1` only. The Target panel lists caches
the CLI discovered. Set target, List caches, Show target, Diff, and Sim stub
shell out to `kernellab` and persist through `target.json`.

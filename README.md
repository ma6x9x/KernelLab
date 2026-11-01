# Kernellab

A userspace micro-lab for iOS/XNU kernel research. It reads kernelcaches the
operator has already extracted and answers map / diff / stub questions from
those files. It is not a jailbreak and it does not ship kernelcaches.

The `.deb` is the lab home. Mind is a separate repo. Lumina / P007 is the hands.

## JB-rig day one: 26.5 host vs 27.0

The full runbook is `NOTES/003_jb_rig_day_one.md`. Short form, after the deb
is installed and the caches are dropped:

```
/var/jb/var/kernellab/caches/23F77/kernelcache…
/var/jb/var/kernellab/caches/24A435/kernelcache…
/var/jb/var/kernellab/caches/24A437/kernelcache…

kernellab target set --train 26.5 --baseline-train 27.0
kernellab diff
kernellab sim ident --feed /var/jb/var/kernellab/lab_bandit.json
oracle_bridge show /var/jb/var/kernellab/lab_bandit.json
kernellab gate
```

`26.5` is `23F77` (iPhone13,2). `27.0` prefers `24A435` (iPhone18,2) when
that file is present, and otherwise can select `24A437` on the same machine,
which has no pinned method table. Those two trains are different machines.
The diff says so. Swap with `--train 27.0 --baseline-train 26.5` when the
rig under test is the 27.0 machine. `klconsole` has both buttons.

`sim ident` is the only allowlisted stub. It prints present versus missing,
then dry-runs a userspace Unicorn return. It does not load kernel bytes.
The feed writes one map row and one emu row. Those weights stay map=0.3 and
emu=0.5. They are not a device receipt and not a fileable finding.
`oracle_bridge stages` prints the ladder `sandbox → leak → race → krw → sptm`.
`sim ident --feed … --stage leak` keeps the ident keys and adds
`kernellab.stage.leak` as map and emu only. A stage name is not a device
claim. The port checklist is `NOTES/004_lab_receipt_checklist.md`.

`kernellab gate` prints `APPLE-SUBMIT: closed`. JB-rig kernel testing is not
a fileable finding. The gate stays closed until a complete hunt-SKU chain.
This lab does not open it and does not submit to Apple.

Mind is separate. Pair it by the build id from `target show`:
https://github.com/ma6x9x/Lum1na

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
- `APPLE-SUBMIT` stays closed. JB-rig kernel testing is not a fileable
  finding. This tool cannot open the gate.

## VA law

`fileoff = (va & 0xFFFFFFF) − 0x7004000` for the builds that law was verified
on: 23F77, 24A435, and 24B119. Other build ids refuse the VA read.

## Layout

- `kernellab.py` — the CLI.
- `klconsole.py` — localhost console. `http://127.0.0.1:8737`.
- `oracle_bridge.py` — offline LabBandit ledger mirror.
- `NOTES/` — design notes. Day one is `NOTES/003_jb_rig_day_one.md`.
- `packaging/` — rootless Procursus `.deb`. See `DEBIAN-STYLE.md`.

## Console

`python3 klconsole.py` binds `127.0.0.1` only. The Target panel lists caches
the CLI discovered. Set target, List caches, Show target, Diff, and Sim stub
shell out to `kernellab` and persist through `target.json`.

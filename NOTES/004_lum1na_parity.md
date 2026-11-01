# 004 — Lum1na / Lum1na-Debug parity (lab discipline, not attack bodies)

KernelLab adopts Lum1na *lab discipline*. It never copies `Exploit/*.m`, and
it never copies KRW, PPL, or race probe bodies. This note is the honesty
contract for that parity. It does not describe a probe.

## Evidence classes

The weights already in `oracle_bridge` are the classes. Only `device` moves
the plan at full strength.

| Class | Weight | What counts |
| --- | --- | --- |
| device | 1.0 | a real probe tap, a panic, or a MAF |
| emu | 0.5 | a Kernellab Unicorn or `sim` verdict |
| map | 0.3 | a static or Ghidra decode receipt |

An emulated verdict can kill a lane or rank arms. It never replaces a
device receipt.

## Honesty gates

`CONTRACT-UNVERIFIED`, an honest `SKIP`, `NO-PIN`, and `GUARD` mean there
is no corroborated oracle. Refuse the positive claim.

`kernellab gate` prints `APPLE-SUBMIT: closed`. The gate stays closed until
a complete, actionable hunt-SKU chain on the latest public iOS. JB-rig
kernel testing is not a fileable finding. Picking a cache, diffing two
files, or running `sim ident` does not open it. See
`NOTES/003_jb_rig_day_one.md`.

## Receipt dump shape (for iPanic)

Every device run the SpringBoard app or the CLI exports includes these
three parts, in this order:

1. Ident. Device model, iOS build id, and the train tag. Use the same tags
   Mind and Lum1na already use: `26.5` → `23F77`, `27.0` → `24A435`.
2. The full console from the tap or command that was under test.
3. The `.ips` if it panics. Attach the path in-app when the shell exists.

Handoff to iPanic is panic type → faulting frame → ladder stage map.
Ladder language is `sandbox` → `leak` → `race` → `krw` → `sptm` (LabBandit
arms).

Ownership:

- Research owns the honesty and evidence-class wording.
- iPanic owns classification.
- ASR owns ledger schema notes.
- iXPl0it and Build Fixer own the SpringBoard `.app` and the `.deb`.

## Build-id pairing

Train chips and `kernellab target show` use the same tags Mind and Lum1na
use: `26.5`, `27.0`, `23F77`, `24A435`. Pair Mind by build id. Mind is not
in the KernelLab deb. KernelLab does not launch it and does not accept a
Mind flag. When you point Mind at a build, use the build id from
`target show`.

## Explicit non-goals

- No Logos tweak hooks.
- No copying Lum1na `Exploit` sources into this repo.
- No probe recipes in this note.

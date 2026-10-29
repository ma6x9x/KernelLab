# Kernellab

A userspace micro-lab for iOS/XNU kernel research — a Corellium-*inspired*
alternative for researchers who already hold decrypted kernel images
(kernelcaches extracted from IPSWs). Not a VM and not a jailbreak: it runs
**real, byte-exact kernel code** from captured builds in an offline harness
(Unicorn) and answers port/diff/grammar questions without device boots or
panic risk.

## What it is

1. **tables** — decode a build's user-client method tables straight from the
   on-disk kernelcache (row handlers + in/out signatures over the chained
   dyld fixups).
2. **diff** — live **survivor-diff** of a method table across two iOS
   builds: `SURVIVED` (byte-identical code), `SHIFTED` (same slot, changed
   body), `RETIRED` (row gone). The static half of every port decision,
   automated.
3. **emu43748** — per-function emulation of real kernel bytes (first unit =
   the CVE-2026-43748 ANE record fill-writer). Runs the REAL bytes under
   Unicorn; the harness refuses to claim a result its run doesn't produce.

## Why not a true VM

Corellium-class virtualization needs EL2; on every SPTM/TXM train (iOS 17+)
the secure monitor holds EL2 and never hands it to XNU, and no modern
iOS jailbreak obtains it. What a jailbreak *does* give (root, kernel RW on
some trains, physRW, entitlement control) is exactly enough to host an
**emulator** of the kernels you already hold decrypted. Kernellab is that
pattern: the guest is a real kernel image, the host is an emulator, the
oracle is byte comparison.

## VA law

`fileoff = (va & 0xFFFFFFF) − 0x7004000` — the flat-delta law verified on
23F77 (xnu-12377, iPhone13,2 26.5), 24A435 (xnu-13432-class, iPhone18,2
27.0) and 24B119; one delta covers the kernel and all kext filesets.

## Status / honesty

- Slice #1 (this repo): tables + diff + the emulation skeleton.
- The planned device-side layers (profile extraction à la SandBlaster,
  boot-learner-driven per-per-boot pinning, primitive probes) are tracked
  in the repo notes as they land; every claim in output is labeled with its
  evidence class.

## Layout

- `kernellab.py` — the CLI harness.
- `NOTES/` — design notes as they land.
- Caches are NOT in the repo (Apple content) — point `KC` at your own
  extracted kernelcache paths.
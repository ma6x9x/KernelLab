# 001 — the KERNELLAB lane (2026-10-28)

Direction: an all-in-one corellium-alternative for the iPhone that already
sits in the fleet — not a VM (EL2 is held by the secure monitor on every
SPTM/TXM train 17+; no modern jailbreak obtains it), a **userspace micro-lab
hosted on the jailbroken device**:

1. Host: the 12 mini (17.3 / Dopamine) — physRW + big allocations + the
   Procursus-jailed shell = the emulator host.
2. Images: real extracted kernelcaches (23F77/24A435/24B119 + whatever the
   operator captures next) — no device boot needed to load them.
3. Engine: Unicorn-class per-function emulation of REAL kernel bytes.
   Full-xnu boot under TCG is not the unit (too slow) — the unit is
   per-function / per-dispatch-row emulation with a stubbed environment.
4. Layers in this lane:
   - **tables** — UC method tables decoded from the caches (done, slice #1).
   - **diff** — live survivor-diff across builds (done, slice #1).
   - **emu43748** — the 43748 fill-writer store-loop under unicorn
     (skeleton; CONTRACT-UNVERIFIED until the register roles are
     byte-derived — the harness refuses positive claims).
   - **profiles** — SandBlaster-class profile extraction from the emulated
     sandbox kext (the 23F77 extraction is running as of this note; the
     decompiled exception.* answers feed the sandbox round-4).
   - **boot-learner** (p118 + LabBandit) — the per-boot pin layer; every
     real device boot trains the pin table the lab's emulation consumes.
5. Fusion law: an emulated verdict is EVIDENCE-CLASS "EMU" — it can kill a
   lane cheaply or rank arms, never replace a device receipt (panic/MAF).
   The bandit treats EMU outcomes as a separate arm class until a port shows
   device-parity.

Rules kept: no guessed struct sizes fired on-device; byte-verify before any
pin; panic-class evidence only from real devices; no Apple content in the
repo (caches live outside, path-configured).
# 002 — pick a kernelcache, diff, sim (week 1)

The KernelLab `.deb` is the lab home. Mind stays a separate repo. Lumina / P007
stays the hands. This note is the operator loop for a kernelcache that is
already extracted and sitting on disk. It is lab tooling. It is not a bounty
report, and it does not describe an exploit.

## Where caches live

The package does not contain kernelcaches. Drop your own extracted files here:

- `KERNELLAB_CACHES` — extra root (use the OS path separator for more than one)
- `/var/jb/var/kernellab/caches` — rootless jailbreak default (`postinst` creates it)
- `./caches` — checkout fallback
- `~/Documents/ios-xnu-hunt/kernels` — included only when that directory exists

Layout:

```
<caches-root>/<build>/kernelcache…
```

The build id is the directory name (`23F77`, `24A435`, or a name like
`23F77__iPhone13,2_3`). A file left loose in the caches root is listed as
unlabeled. The lab will not guess a build id for it.

## Fleet tags

These are the build ids named by the judgment pack. `target list` prints
them even when the file is not on disk yet. A tag with no pinned method
table stays a refusal. Addresses are not copied from one machine to another.

| Build | Train | Role | Machine | Pinned method tables |
| --- | --- | --- | --- | --- |
| 23F77 | 26.5 | hunt | iPhone13,2 | yes |
| 23G71 |  | hunt iPad | iPad8,* | no — addresses do not transfer from 23F77 |
| 21D50 |  | shape reference | iPhone 12 mini | no — not the hunt device |
| 24A435 | 27.0 | diff input | iPhone18,2 | yes — do not paste onto 23F77 |
| 24A437 | 27.0 | diff input | iPhone18,2 | no |
| 24B119 |  | diff input | iPhone13,2 | no method table (VA band only) |

The pack's own `kernellab.py` still points `24B119` at a Mac home path.
This tree does not. Discovery walks the caches roots above. The comparison
took that path generalization and left the slice-1 table pins as they were.
No new offset row was added.

## Apple-submit gate

`kernellab gate` prints `APPLE-SUBMIT: closed`. Target, diff, and sim print
the same line. JB-rig kernel testing is not a fileable finding. The gate
stays closed until a complete hunt-SKU chain. Picking a cache, diffing two
files, or dry-running `ident` does not open it. Do not submit to Apple from
this lab. The day-one rig loop is `NOTES/003_jb_rig_day_one.md`.

## State

On a rootless jailbreak the saved choice is `/var/jb/var/kernellab/target.json`.
Off-device it is `$XDG_DATA_HOME/kernellab/target.json` (that is
`~/.local/share/kernellab/target.json` when `XDG_DATA_HOME` is unset).
`KERNELLAB_STATE` overrides the file path.

Fields: `build`, `path`, `baseline`, `baseline_path`.

## Loop

```
kernellab target list
kernellab target set --build <saved> --baseline <other>
kernellab target show
kernellab diff
kernellab sim ident
```

`diff` with no arguments reads `target.json` and compares the saved build to
its baseline. `--cache` and `--cache2` still select an explicit pair. With no
`--table`, every pinned name on either build is reported.

Honesty labels on a real row compare stay `SURVIVED`, `SHIFTED`, `RETIRED`,
and `ADDED`. Two other results are refusals, not port decisions:

- `NO-PIN` — that table name is not pinned on both builds. No offset is invented.
- a slice refusal / `UNREADABLE` — the file does not contain the pinned slice.
  No survivor claim is made from a short or empty read.

`sim` accepts allowlisted ids only. Week 1 ships `ident`. It prints:

- `MAP file: present` or `missing`
- `MAP pinned-entry: present` or `missing` (present means the build id is in
  the lab's pinned list — it is not a byte proof that this file contains the table)
- `EMU:` a userspace Unicorn dry-run of `movz x0, #1; ret`

`ident` does not load kernelcache bytes into the emulator. If Unicorn is not
installed, the emu line is `skipped unicorn-missing` and there is no positive
emu claim.

Optional ledger mirror, same classes `oracle_bridge` already accepts:

```
kernellab sim ident --feed /path/to/lab_bandit.json
```

That appends one `map` row and one `emu` row on domain `kernellab`. Map weight
is 0.3 and emu weight is 0.5 inside the existing bridge. Neither row is a
device receipt.

## Honesty

- Unicorn is not EL1. The ident stub runs in a userspace emulator.
- A stock kernelcache is not the live jailbroken kernel. `diff` compares files
  on disk. It does not read the kernel that is running on the phone.
- An EMU or map ledger row is not a device receipt. Device-class evidence still
  has to come from the device.
- No pinned table entry means no positive claim. The lab will not invent a VA,
  a stride, or a row count for a build that is not already pinned.

## Console

`klconsole` listens on `127.0.0.1:8737` only. The Target form and the
list / show / diff / sim buttons shell out to the commands above. Set target
persists `target.json` and nothing else.

## JB host check

1. Install the deb. `postinst` creates `/var/jb/var/kernellab/caches` and prints
   the same loop.
2. Copy extracted kernelcaches into `/var/jb/var/kernellab/caches/<build>/`.
   Confirm `dpkg -c` of the deb has no kernelcache file.
3. `kernellab target list`, then `target set`, then `diff`, then `sim ident`.
4. Run `klconsole` and open `http://127.0.0.1:8737` (an SSH tunnel if you are
   not on the phone).
5. Expect `sim ident` to print `CONTRACT`, `APPLE-SUBMIT: closed`, and
   present-vs-missing. Expect `diff` to refuse any build that has no pinned
   table entry, and to say when the two builds are different machines
   (23F77 vs 24A435 is one of those pairs). `kernellab gate` stays closed.

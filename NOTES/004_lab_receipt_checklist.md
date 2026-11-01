# 004 — lab receipt checklist

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

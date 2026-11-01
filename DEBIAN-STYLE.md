# Packaging: kernellab deb

Rootless Procursus-layout deb (the fleet's jailbroken phone is the hosting
device): everything lives under `<prefix>/usr/...`, no `Root` ownership of
system paths, installed via Sileo/Zebra/dpkg like any other repo package.

- `/usr/bin/kernellab` — the CLI (`target`, `diff`, `sim`, `tables`, `emu43748`)
- `/usr/bin/klconsole` — localhost console (127.0.0.1:8737)
- `/usr/bin/oracle_bridge` — LabBandit ledger mirror
- `/usr/share/kernellab/` — the same three sources, README, and `NOTES/`
- `/Applications/KernelLab.app` — SpringBoard bundle (`CFBundleDisplayName`
  KernelLab, `CFBundleIdentifier` `com.ma6x9x.kernellab`). On a rootless
  device this is `/var/jb/Applications/KernelLab.app`. The executable is an
  arm64 Mach-O (`MH_EXECUTE`) with one `LC_LOAD_DYLINKER` (`/usr/lib/dyld`)
  and `LC_LOAD_DYLIB` entries for libSystem, libobjc, and UIKit. `postinst`
  accepts either install path, prepends `/var/jb/usr/bin` to `PATH`, and
  runs `uicache -p <app> -s`. A reported registration failure falls back
  to `uicache -a`. A missing binary or a `#!/bin/sh` launcher skips
  `uicache`.
- Caches are NOT packaged (Apple content). `postinst` creates
  `/var/jb/var/kernellab/caches` and prints the pick → diff → sim hint.
  The operator drops extracted kernelcaches under `<caches>/<build>/`.
- `/var/jb/var/kernellab/probes` is created by `postinst` and left empty.
  Operator trees dropped there are not in the `.deb`. The build refuses
  to package a `.m` or `.h` file. `packaging/probes/SLOT.md` is the empty
  codegen slot in the repo; it is not installed into the probes directory.

## Rebuild

`./packaging/build.sh` from a macOS/Linux checkout (needs `dpkg-deb`),
or the `📦 Package kernellab (.deb)` GitHub Actions job — artifact
`kernellab_<version>_iphoneos-arm64.deb` on every push. The build refuses
to package a file whose name contains `kernelcache`.

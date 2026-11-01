# Packaging: kernellab deb

Rootless Procursus-layout deb (the fleet's jailbroken phone is the hosting
device): everything lives under `<prefix>/usr/...`, no `Root` ownership of
system paths, installed via Sileo/Zebra/dpkg like any other repo package.

- `/usr/bin/kernellab` — the CLI (`target`, `diff`, `sim`, `tables`, `emu43748`)
- `/usr/bin/klconsole` — localhost console (127.0.0.1:8737)
- `/usr/bin/oracle_bridge` — LabBandit ledger mirror
- `/usr/share/kernellab/` — the same three sources, README, and `NOTES/`
- Caches are NOT packaged (Apple content). `postinst` creates
  `/var/jb/var/kernellab/caches` and prints the pick → diff → sim hint.
  The operator drops extracted kernelcaches under `<caches>/<build>/`.

## Rebuild

`./packaging/build.sh` from a macOS/Linux checkout (needs `dpkg-deb`),
or the `📦 Package kernellab (.deb)` GitHub Actions job — artifact
`kernellab_<version>_iphoneos-arm64.deb` on every push. The build refuses
to package a file whose name contains `kernelcache`.

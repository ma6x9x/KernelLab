# Packaging: kernellab deb

Rootless Procursus-layout deb (the fleet's jailbroken phone is the hosting
device): paths in the archive are under `/usr/...` and `/Applications/...`.
On a rootless jailbreak, dpkg's root is `/var/jb`, so they land at
`/var/jb/usr/...` and `/var/jb/Applications/...`.

- `/usr/bin/kernellab` — the CLI (`target`, `diff`, `sim`, `tables`, `gate`)
- `/usr/bin/klconsole` — localhost console (127.0.0.1:8737)
- `/usr/bin/oracle_bridge` — LabBandit ledger mirror
- `/usr/share/kernellab/` — the same three sources, README, and `NOTES/`
- `/Applications/KernelLab.app` — SpringBoard shell. Bundle id
  `com.ma6x9x.kernellab`. It execs the CLI. It does not reimplement it.
- Caches are NOT packaged (Apple content). `postinst` creates
  `/var/jb/var/kernellab/caches` and prints the pick → diff → sim hint.
  The operator drops extracted kernelcaches under `<caches>/<build>/`.
- `postinst` also creates `/var/jb/var/kernellab/probes` and
  `/var/jb/var/kernellab/receipts` (owned by `mobile` when that user exists)
  and runs `uicache` so the icon appears. Probe sources are not in the deb.

## Rebuild

`./packaging/build.sh` from a macOS/Linux checkout (needs `dpkg-deb`),
or the `📦 Package kernellab (.deb)` GitHub Actions job — artifact
`kernellab_<version>_iphoneos-arm64.deb`. The build refuses to package a
file whose name contains `kernelcache`, and it refuses to package a `.m`
or `.mm` file.

Ubuntu CI does not run Theos. The job still embeds
`Applications/KernelLab.app` (Info.plist, icons, and `THEOS-BUILD.txt` when
no Mach-O was produced). To put a launchable executable in the deb, build
the app first:

```
export THEOS=~/theos
make -C app clean all
./packaging/build.sh
```

The script prefers `app/prebuilt/KernelLab.app`, then a bundle under
`app/.theos`, then the source layout.

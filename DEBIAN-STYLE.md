# Packaging: kernellab deb

Rootless Procursus-layout deb (the fleet's 21D50 12 mini is the hosting
device): everything lives under `<prefix>/usr/...`, no `Root` ownership of
system paths, installed via Sileo/Zebra/dpkg like any other repo package.

- `/usr/bin/kernellab`          — the CLI harness (kernellab.py)
- `/usr/share/kernellab/README.md`
- `/usr/share/kernellab/NOTES/` — the lane notes as they land
- Caches are NOT packaged (Apple content) — the operator points KC at
  their own extracted kernelcaches.

## Rebuild

`./packaging/build.sh` from a macOS/Linux checkout (needs `dpkg-deb`),
or the `📦 Package kernellab (.deb)` GitHub Actions job — artifact
`kernellab_<version>_iphoneos-arm64.deb` on every push.
#!/bin/sh
# build.sh — package the kernellab deb (rootless Procursus layout).
# Usage: ./packaging/build.sh [version] [outdir]
# Kernelcaches are operator-supplied. This script refuses to ship one.
set -eu
cd "$(dirname "$0")/.."
VER="${1:-$(grep -m1 '^Version:' packaging/control | cut -d' ' -f2)}"
OUTDIR="${2:-build}"
STAGE="$(mktemp -d)"
cleanup() { rm -rf "$STAGE"; }
trap cleanup EXIT

mkdir -p "$STAGE/DEBIAN" \
         "$STAGE/usr/bin" \
         "$STAGE/usr/share/kernellab/NOTES" \
         "$STAGE/Applications/KernelLab.app"

cp kernellab.py "$STAGE/usr/bin/kernellab"
cp klconsole.py "$STAGE/usr/bin/klconsole"
cp oracle_bridge.py "$STAGE/usr/bin/oracle_bridge"
chmod 755 "$STAGE/usr/bin/kernellab" \
          "$STAGE/usr/bin/klconsole" \
          "$STAGE/usr/bin/oracle_bridge"

cp kernellab.py klconsole.py oracle_bridge.py "$STAGE/usr/share/kernellab/"

[ -f README.md ] && cp README.md "$STAGE/usr/share/kernellab/" || true
[ -f DEBIAN-STYLE.md ] && cp DEBIAN-STYLE.md "$STAGE/usr/share/kernellab/" || true
cp NOTES/*.md "$STAGE/usr/share/kernellab/NOTES/" 2>/dev/null || true

# SpringBoard bundle. The executable is the sh launcher in this repo
# (CI has no iOS SDK / Theos). Version tokens come from packaging/control.
APP="$STAGE/Applications/KernelLab.app"
sed "s/__KERNELLAB_BUILD__/${VER}/g" packaging/springboard/Info.plist > "$APP/Info.plist"
sed "s/__KERNELLAB_BUILD__/${VER}/g" packaging/springboard/KernelLab > "$APP/KernelLab"
chmod 755 "$APP/KernelLab"
printf 'APPL????' > "$APP/PkgInfo"
python3 packaging/springboard/make_icon.py "$APP"
python3 -c '
import plistlib, sys
path, version = sys.argv[1], sys.argv[2]
with open(path, "rb") as handle:
    info = plistlib.load(handle)
assert info["CFBundleDisplayName"] == "KernelLab", info.get("CFBundleDisplayName")
assert info["CFBundleExecutable"] == "KernelLab"
assert info["CFBundleShortVersionString"] == version
assert info["CFBundleIdentifier"] == "com.ma6x9x.kernellab"
' "$APP/Info.plist" "$VER"

if find "$STAGE" -iname '*kernelcache*' -print | grep -q .; then
  echo "refusing to package a kernelcache" >&2
  find "$STAGE" -iname '*kernelcache*' -print >&2
  exit 1
fi

# Probe and exploit sources stay on the device, under the operator's
# probes workspace. The package refuses to ship .m/.h files.
if find "$STAGE" \( -name '*.m' -o -name '*.h' \) -print | grep -q .; then
  echo "refusing to package .m/.h sources" >&2
  find "$STAGE" \( -name '*.m' -o -name '*.h' \) -print >&2
  exit 1
fi

cp packaging/control "$STAGE/DEBIAN/control"
for script in postinst postrm prerm; do
  if [ -f "packaging/$script" ]; then
    cp "packaging/$script" "$STAGE/DEBIAN/$script"
    chmod 755 "$STAGE/DEBIAN/$script"
  fi
done

mkdir -p "$OUTDIR"
dpkg-deb --root-owner-group --build "$STAGE" "$OUTDIR/kernellab_${VER}_iphoneos-arm64.deb"
echo "built: $OUTDIR/kernellab_${VER}_iphoneos-arm64.deb"
dpkg-deb --info "$OUTDIR/kernellab_${VER}_iphoneos-arm64.deb" | head -20
dpkg-deb --contents "$OUTDIR/kernellab_${VER}_iphoneos-arm64.deb"

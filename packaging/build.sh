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
         "$STAGE/usr/share/kernellab/NOTES"

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

if find "$STAGE" -iname '*kernelcache*' -print | grep -q .; then
  echo "refusing to package a kernelcache" >&2
  find "$STAGE" -iname '*kernelcache*' -print >&2
  exit 1
fi

cp packaging/control "$STAGE/DEBIAN/control"
if [ -f packaging/postinst ]; then
  cp packaging/postinst "$STAGE/DEBIAN/postinst"
  chmod 755 "$STAGE/DEBIAN/postinst"
fi

mkdir -p "$OUTDIR"
dpkg-deb --root-owner-group --build "$STAGE" "$OUTDIR/kernellab_${VER}_iphoneos-arm64.deb"
echo "built: $OUTDIR/kernellab_${VER}_iphoneos-arm64.deb"
dpkg-deb --info "$OUTDIR/kernellab_${VER}_iphoneos-arm64.deb" | head -20
dpkg-deb --contents "$OUTDIR/kernellab_${VER}_iphoneos-arm64.deb"

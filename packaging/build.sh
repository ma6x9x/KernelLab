#!/bin/sh
# build.sh — package the kernellab deb (rootless Procursus layout).
# Usage: ./packaging/build.sh [version]   (version from packaging/control or arg)
set -eu
cd "$(dirname "$0")/.."
VER="${1:-$(grep -m1 '^Version:' packaging/control | cut -d' ' -f2)}"
OUTDIR="${2:-build}"
STAGE="$(mktemp -d)"

mkdir -p "$STAGE/DEBIAN" \
         "$STAGE/usr/bin" \
         "$STAGE/usr/share/kernellab/NOTES"

cp kernellab.py "$STAGE/usr/bin/kernellab"
chmod 755 "$STAGE/usr/bin/kernellab"

[ -f README.md ] && cp README.md "$STAGE/usr/share/kernellab/" || true
[ -f DEBIAN-STYLE.md ] && cp DEBIAN-STYLE.md "$STAGE/usr/share/kernellab/" || true
cp NOTES/*.md "$STAGE/usr/share/kernellab/NOTES/" 2>/dev/null || true

cp packaging/control "$STAGE/DEBIAN/control"
[ -f packaging/postinst ] && cp packaging/postinst "$STAGE/DEBIAN/postinst" && chmod 755 "$STAGE/DEBIAN/postinst"

mkdir -p "$OUTDIR"
dpkg-deb --root-owner-group --build "$STAGE" "$OUTDIR/kernellab_${VER}_iphoneos-arm64.deb"
echo "built: $OUTDIR/kernellab_${VER}_iphoneos-arm64.deb"
dpkg-deb --info "$OUTDIR/kernellab_${VER}_iphoneos-arm64.deb" | head -20
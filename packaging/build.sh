#!/bin/sh
# build.sh — package the kernellab deb (rootless Procursus layout).
# Usage: ./packaging/build.sh [version] [outdir]
# Kernelcaches are operator-supplied. This script refuses to ship one.
# The SpringBoard bundle is staged from a Theos/prebuilt .app when present.
# Ubuntu CI has no Theos, so it stages Info.plist + icons and says so.
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
         "$STAGE/Applications"

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

stage_springboard_app() {
  dest="$STAGE/Applications/KernelLab.app"
  mkdir -p "$dest"
  if [ -f app/prebuilt/KernelLab.app/Info.plist ]; then
    cp -R app/prebuilt/KernelLab.app/. "$dest/"
    echo "app: using app/prebuilt/KernelLab.app"
  else
    found=""
    if [ -d app/.theos ]; then
      found=$(find app/.theos -type d -name KernelLab.app -print 2>/dev/null | head -n 1 || true)
    fi
    if [ -n "$found" ] && [ -f "$found/Info.plist" ]; then
      cp -R "$found"/. "$dest/"
      echo "app: using Theos bundle $found"
    else
      cp app/Info.plist "$dest/Info.plist"
      cp app/entitlements.plist "$dest/entitlements.plist"
      cp app/Resources/icon.png "$dest/icon.png"
      cp app/Resources/icon@2x.png "$dest/icon@2x.png"
      cp app/Resources/icon@3x.png "$dest/icon@3x.png"
      cp app/THEOS-BUILD.txt "$dest/THEOS-BUILD.txt"
      echo "app: staged KernelLab.app layout only (no Theos executable on this machine)"
      echo "app: SpringBoard launches after: make -C app clean all && ./packaging/build.sh"
    fi
  fi
  if [ -f "$dest/KernelLab" ]; then
    chmod 755 "$dest/KernelLab"
  fi
}

stage_springboard_app

if [ ! -f "$STAGE/Applications/KernelLab.app/Info.plist" ]; then
  echo "KernelLab.app Info.plist missing" >&2
  exit 1
fi
if [ ! -f "$STAGE/Applications/KernelLab.app/KernelLab" ]; then
  echo "note: KernelLab.app has no compiled executable in this deb."
  echo "note: Ubuntu CI cannot run Theos. See README (SpringBoard app)."
fi

if find "$STAGE" -iname '*kernelcache*' -print | grep -q .; then
  echo "refusing to package a kernelcache" >&2
  find "$STAGE" -iname '*kernelcache*' -print >&2
  exit 1
fi
if find "$STAGE" \( -name '*.m' -o -name '*.mm' \) -print | grep -q .; then
  echo "refusing to package Objective-C source bodies" >&2
  find "$STAGE" \( -name '*.m' -o -name '*.mm' \) -print >&2
  exit 1
fi

cp packaging/control "$STAGE/DEBIAN/control"
if [ -f packaging/postinst ]; then
  cp packaging/postinst "$STAGE/DEBIAN/postinst"
  chmod 755 "$STAGE/DEBIAN/postinst"
fi
if [ -f packaging/postrm ]; then
  cp packaging/postrm "$STAGE/DEBIAN/postrm"
  chmod 755 "$STAGE/DEBIAN/postrm"
fi

mkdir -p "$OUTDIR"
dpkg-deb --root-owner-group --build "$STAGE" "$OUTDIR/kernellab_${VER}_iphoneos-arm64.deb"
echo "built: $OUTDIR/kernellab_${VER}_iphoneos-arm64.deb"
dpkg-deb --info "$OUTDIR/kernellab_${VER}_iphoneos-arm64.deb" | head -20
dpkg-deb --contents "$OUTDIR/kernellab_${VER}_iphoneos-arm64.deb"

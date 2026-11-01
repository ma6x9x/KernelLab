#!/bin/sh
# build.sh — package the kernellab deb (rootless Procursus layout).
# Usage: ./packaging/build.sh [version] [outdir]
# Kernelcaches are operator-supplied. This script refuses to ship one.
# The SpringBoard executable must be a Mach-O. A /bin/sh launcher is refused.
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
  found=""
  if [ -d app/.theos ]; then
    found=$(find app/.theos -type d -name 'KernelLab.app' -print 2>/dev/null | head -n 1 || true)
  fi
  # A fresh Theos bundle wins when it is a real Mach-O. Otherwise ship the
  # signed prebuilt soft UI (app/prebuilt/KernelLab.app).
  if [ -n "$found" ] && sh packaging/postinst --is-macho "$found/KernelLab"; then
    cp -R "$found"/. "$dest/"
    echo "app: using Theos bundle $found"
  elif [ -f app/prebuilt/KernelLab.app/Info.plist ] && sh packaging/postinst --is-macho app/prebuilt/KernelLab.app/KernelLab; then
    cp -R app/prebuilt/KernelLab.app/. "$dest/"
    echo "app: using signed prebuilt app/prebuilt/KernelLab.app"
  else
    cp app/Info.plist "$dest/Info.plist"
    cp app/entitlements.plist "$dest/entitlements.plist"
    cp app/Resources/icon.png "$dest/icon.png"
    cp app/Resources/icon@2x.png "$dest/icon@2x.png"
    cp app/Resources/icon@3x.png "$dest/icon@3x.png"
    cp app/THEOS-BUILD.txt "$dest/THEOS-BUILD.txt"
    echo "app: staged layout only (no Mach-O). SpringBoard will not show an icon." >&2
    echo "app: build with app/stub/build-stub.sh or: make -C app" >&2
  fi
  if [ -f "$dest/KernelLab" ]; then
    if ! sh packaging/postinst --is-macho "$dest/KernelLab"; then
      echo "refusing to package a KernelLab executable that is not Mach-O" >&2
      exit 1
    fi
    chmod 755 "$dest/KernelLab"
  fi
  python3 - "$dest/Info.plist" "$VER" << 'PY'
import plistlib, sys
path, version = sys.argv[1], sys.argv[2]
with open(path, "rb") as handle:
    info = plistlib.load(handle)
info["CFBundleDisplayName"] = "KernelLab"
info["CFBundleExecutable"] = "KernelLab"
info["CFBundleIdentifier"] = "com.ma6x9x.kernellab"
info["CFBundleShortVersionString"] = version
info["CFBundleVersion"] = version
info["CFBundlePackageType"] = "APPL"
info["MinimumOSVersion"] = info.get("MinimumOSVersion") or "15.0"
with open(path, "wb") as handle:
    plistlib.dump(info, handle)
PY
}

stage_springboard_app

if [ ! -f "$STAGE/Applications/KernelLab.app/Info.plist" ]; then
  echo "KernelLab.app Info.plist missing" >&2
  exit 1
fi

if find "$STAGE" -iname '*kernelcache*' -print | grep -q .; then
  echo "refusing to package a kernelcache" >&2
  find "$STAGE" -iname '*kernelcache*' -print >&2
  exit 1
fi

if find "$STAGE" \( -name '*.m' -o -name '*.h' -o -name '*.mm' \) -print | grep -q .; then
  echo "refusing to package .m/.h sources" >&2
  find "$STAGE" \( -name '*.m' -o -name '*.h' -o -name '*.mm' \) -print >&2
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
# Checkout keeps older kernellab_*.deb files (0.3.0 next to 0.3.1).
# dpkg-deb refuses a glob that expands to more than one package.
rm -f "$OUTDIR"/kernellab_*.deb
dpkg-deb --root-owner-group --build "$STAGE" "$OUTDIR/kernellab_${VER}_iphoneos-arm64.deb"
echo "built: $OUTDIR/kernellab_${VER}_iphoneos-arm64.deb"
dpkg-deb --info "$OUTDIR/kernellab_${VER}_iphoneos-arm64.deb" | head -20
dpkg-deb --contents "$OUTDIR/kernellab_${VER}_iphoneos-arm64.deb"

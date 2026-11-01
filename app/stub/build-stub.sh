#!/bin/sh
# Build the arm64 soft-UI Mach-O without the iOS SDK.
# Needs clang with an Apple arm64 target and ld64.lld (LLVM's Mach-O linker).
# Output: app/prebuilt/KernelLab.app/KernelLab plus Info.plist and icons.
set -eu
cd "$(dirname "$0")/../.."
ROOT="$PWD"
STUB="$ROOT/app/stub"
WORK="$(mktemp -d)"
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

LLD="${LD64:-}"
if [ -z "$LLD" ]; then
  for c in ld64.lld /usr/bin/ld64.lld /usr/lib/llvm-18/bin/ld64.lld; do
    if command -v "$c" >/dev/null 2>&1; then
      LLD="$c"
      break
    fi
  done
fi
if [ -z "$LLD" ]; then
  echo "ld64.lld not found. Set LD64 to the Mach-O linker." >&2
  exit 1
fi
LDID="${LDID:-}"
if [ -z "$LDID" ]; then
  for c in ldid /tmp/ldid/ldid; do
    if [ -x "$c" ] || command -v "$c" >/dev/null 2>&1; then
      LDID="$c"
      break
    fi
  done
fi

clang -target arm64-apple-ios15.0 -ffreestanding -fno-stack-protector -fno-builtin \
  -c "$STUB/main.c" -o "$WORK/main.o"

python3 - "$WORK" << 'PY'
import pathlib, struct, subprocess, sys
work = pathlib.Path(sys.argv[1])
data = (work / "main.o").read_bytes()
_, _, _, _, ncmds, _, _, _ = struct.unpack_from("<IIIIIIII", data, 0)
off = 32
symoff = nsyms = stroff = 0
for _ in range(ncmds):
    cmd, cmdsize = struct.unpack_from("<II", data, off)
    if cmd == 2:
        symoff, nsyms, stroff, _strsize = struct.unpack_from("<IIII", data, off + 8)
    off += cmdsize
undef = []
for i in range(nsyms):
    n_strx, n_type, _sect, _desc, n_value = struct.unpack_from("<IBBHQ", data, symoff + i * 16)
    if (n_type & 0x01) and (n_type & 0x0e) == 0 and n_value == 0:
        name = data[stroff + n_strx:data.find(b"\0", stroff + n_strx)].decode()
        undef.append(name)

objc = []
uikit = []
system = []
for name in undef:
    if name in {"_UIApplicationMain"}:
        uikit.append(name)
    elif name.startswith("_objc_") or name.startswith("_class_") or name.startswith("_sel_") or name.startswith("_object_"):
        objc.append(name)
    else:
        system.append(name)

def emit(path, names):
    lines = ["/* link-time stubs. runtime binds the real device libraries. */"]
    for name in names:
        c_name = name[1:]
        if c_name == "environ":
            lines.append("char **environ;")
        else:
            lines.append(f"void {c_name}() {{}}")
    path.write_text("\n".join(lines) + "\n")

emit(work / "libSystem.c", system)
emit(work / "libobjc.c", objc)
emit(work / "UIKit.c", uikit)
print(f"symbols system={len(system)} objc={len(objc)} uikit={len(uikit)}")
PY

clang -target arm64-apple-ios15.0 -ffreestanding -fno-stack-protector -c "$WORK/libSystem.c" -o "$WORK/libSystem.o"
clang -target arm64-apple-ios15.0 -ffreestanding -fno-stack-protector -c "$WORK/libobjc.c" -o "$WORK/libobjc.o"
clang -target arm64-apple-ios15.0 -ffreestanding -fno-stack-protector -c "$WORK/UIKit.c" -o "$WORK/UIKit.o"

"$LLD" -dylib -arch arm64 -platform_version ios 15.0.0 15.0.0 \
  -install_name /usr/lib/libSystem.B.dylib -o "$WORK/libSystem.B.dylib" "$WORK/libSystem.o"
"$LLD" -dylib -arch arm64 -platform_version ios 15.0.0 15.0.0 \
  -install_name /usr/lib/libobjc.A.dylib -o "$WORK/libobjc.A.dylib" "$WORK/libobjc.o"
"$LLD" -dylib -arch arm64 -platform_version ios 15.0.0 15.0.0 \
  -install_name /System/Library/Frameworks/UIKit.framework/UIKit -o "$WORK/UIKit" "$WORK/UIKit.o"

"$LLD" -arch arm64 -platform_version ios 15.0.0 15.0.0 \
  -o "$WORK/KernelLab" "$WORK/main.o" \
  "$WORK/libSystem.B.dylib" "$WORK/libobjc.A.dylib" "$WORK/UIKit" \
  -adhoc_codesign

if [ -n "$LDID" ]; then
  "$LDID" -Cadhoc -S"$ROOT/app/entitlements.plist" "$WORK/KernelLab"
else
  echo "ldid not found; left the linker ad-hoc signature in place" >&2
fi

DEST="$ROOT/app/prebuilt/KernelLab.app"
rm -rf "$DEST"
mkdir -p "$DEST"
cp "$WORK/KernelLab" "$DEST/KernelLab"
cp "$ROOT/app/Info.plist" "$DEST/Info.plist"
cp "$ROOT/app/entitlements.plist" "$DEST/entitlements.plist"
cp "$ROOT/app/Resources/icon.png" "$ROOT/app/Resources/icon@2x.png" "$ROOT/app/Resources/icon@3x.png" "$DEST/"
chmod 755 "$DEST/KernelLab"
file "$DEST/KernelLab"
echo "built $DEST/KernelLab"

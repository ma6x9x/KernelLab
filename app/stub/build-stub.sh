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
  for c in ld64.lld ld64.lld-18 ld64.lld-19 ld64.lld-20 ld64.lld-21 \
    /usr/bin/ld64.lld /usr/bin/ld64.lld-18 \
    /usr/lib/llvm-18/bin/ld64.lld /usr/lib/llvm-19/bin/ld64.lld \
    /usr/lib/llvm-20/bin/ld64.lld /usr/lib/llvm-21/bin/ld64.lld; do
    if [ -x "$c" ]; then
      LLD="$c"
      break
    fi
    if command -v "$c" >/dev/null 2>&1; then
      LLD=$(command -v "$c")
      break
    fi
  done
fi
if [ -z "$LLD" ]; then
  LLD=$(find /usr/lib /usr/bin -name 'ld64.lld*' -type f -executable 2>/dev/null | head -n 1 || true)
fi
if [ -z "$LLD" ]; then
  echo "ld64.lld not found. Set LD64 to the Mach-O linker." >&2
  exit 1
fi
LDID="${LDID:-}"
if [ -z "$LDID" ]; then
  for c in ldid /tmp/ldid/ldid /usr/bin/ldid /var/jb/usr/bin/ldid; do
    if [ -x "$c" ]; then
      LDID="$c"
      break
    fi
    if command -v "$c" >/dev/null 2>&1; then
      LDID=$(command -v "$c")
      break
    fi
  done
fi
if [ -z "$LDID" ]; then
  echo "ldid not found. The SpringBoard binary must be signed with entitlements." >&2
  echo "Build https://github.com/ProcursusTeam/ldid and set LDID." >&2
  exit 1
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
# ld64.lld references this from lazy binding. It is not in main.o.
# The empty body is link-only; dyld binds the real libSystem copy.
if "_dyld_stub_binder" not in system:
    system.append("_dyld_stub_binder")

def emit(path, names):
    lines = ["/* link-time stubs. runtime binds the real device libraries. */"]
    for name in names:
        c_name = name[1:]
        if c_name == "environ":
            lines.append("char **environ;")
        elif c_name == "dyld_stub_binder":
            # ld64.lld's lazy-bind stub looks up this symbol without the
            # usual Mach-O underscore prefix.
            lines.append('__asm__(".globl dyld_stub_binder\\ndyld_stub_binder:\\nret\\n");')
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

# Classic dyld opcodes load on every iOS arm64 dyld. Chained fixups from
# ld64.lld are DYLD_CHAINED_PTR_64 (macOS absolute targets). Prefer opcodes.
# If that link fails, chained fixups are still checked for command types.
link_kernel_lab() {
  mode=$1
  "$LLD" -arch arm64 -platform_version ios 15.0.0 15.0.0 \
    "-${mode}" \
    -o "$WORK/KernelLab" "$WORK/main.o" \
    "$WORK/libSystem.B.dylib" "$WORK/libobjc.A.dylib" "$WORK/UIKit" \
    -adhoc_codesign
}
rm -f "$WORK/KernelLab"
if ! link_kernel_lab no_fixup_chains; then
  rm -f "$WORK/KernelLab"
  echo "classic dyld opcodes failed; retrying with chained fixups" >&2
  link_kernel_lab fixup_chains
fi

# Repair LC_LOAD_DYLINKER / LC_LOAD_DYLIB swaps before ldid hashes the file.
python3 "$ROOT/packaging/check-macho.py" --normalize "$WORK/KernelLab"
"$LDID" -Cadhoc -Hsha256 -S"$ROOT/app/entitlements.plist" "$WORK/KernelLab"
python3 "$ROOT/packaging/check-macho.py" "$WORK/KernelLab"

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

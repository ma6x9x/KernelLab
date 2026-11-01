#!/usr/bin/env python3
"""Check a KernelLab SpringBoard executable.

The home-screen bundle is unloadable when ld64.lld records libSystem,
libobjc, or UIKit as LC_LOAD_DYLINKER, or records /usr/lib/dyld as a
dylib. --normalize repairs that swap when the command layout is already
a dylib_command (name offset 24) or a dylinker_command (name offset 12).
Signing happens after normalize; the default mode also requires the ldid
entitlements blob.
"""

import struct
import sys
from pathlib import Path

MH_MAGIC_64 = 0xFEEDFACF
MH_EXECUTE = 2
CPU_TYPE_ARM64 = 0x0100000C
MH_DYLDLINK = 0x4

LC_LOAD_DYLIB = 0xC
LC_ID_DYLIB = 0xD
LC_LOAD_DYLINKER = 0xE
LC_ID_DYLINKER = 0xF
LC_LOAD_WEAK_DYLIB = 0x80000018
LC_REEXPORT_DYLIB = 0x8000001F
LC_DYLD_INFO = 0x22
LC_DYLD_INFO_ONLY = 0x80000022
LC_CODE_SIGNATURE = 0x1D
LC_MAIN = 0x80000028
LC_BUILD_VERSION = 0x32
LC_DYLD_CHAINED_FIXUPS = 0x80000034

DYLIB_LOADS = {LC_LOAD_DYLIB, LC_LOAD_WEAK_DYLIB, LC_REEXPORT_DYLIB}
NAME_COMMANDS = DYLIB_LOADS | {LC_ID_DYLIB, LC_LOAD_DYLINKER, LC_ID_DYLINKER}
FIXUP_COMMANDS = {LC_DYLD_INFO, LC_DYLD_INFO_ONLY, LC_DYLD_CHAINED_FIXUPS}

REQUIRED_DYLIBS = (
    "/usr/lib/libSystem.B.dylib",
    "/usr/lib/libobjc.A.dylib",
    "/System/Library/Frameworks/UIKit.framework/UIKit",
)
DYLINKER = "/usr/lib/dyld"
ENTITLEMENT_MARKERS = (
    b"platform-application",
    b"com.apple.private.security.no-container",
    b"com.apple.private.security.no-sandbox",
)
CSMAGIC_EMBEDDED_SIGNATURE = 0xFADE0CC0
CSMAGIC_EMBEDDED_ENTITLEMENTS = 0xFADE7171


class MachOError(Exception):
    pass


def _name_at(blob, off, cmdsize):
    nameoff = struct.unpack_from("<I", blob, off + 8)[0]
    if nameoff <= 0 or nameoff >= cmdsize:
        raise MachOError(f"load command name offset {nameoff} is outside the command")
    end = blob.find(b"\0", off + nameoff, off + cmdsize)
    if end < 0:
        raise MachOError("load command name is not NUL-terminated")
    return blob[off + nameoff : end].decode("utf-8", "replace"), nameoff


def commands(blob):
    if len(blob) < 32 or struct.unpack_from("<I", blob, 0)[0] != MH_MAGIC_64:
        raise MachOError("not a little-endian 64-bit Mach-O")
    _, cputype, _, filetype, ncmds, sizeofcmds, flags, _ = struct.unpack_from(
        "<IIIIIIII", blob, 0
    )
    off = 32
    found = []
    for _ in range(ncmds):
        if off + 8 > len(blob):
            raise MachOError("load commands run past the file")
        cmd, cmdsize = struct.unpack_from("<II", blob, off)
        if cmdsize < 8 or off + cmdsize > len(blob):
            raise MachOError(f"bad load command size at {off:#x}")
        found.append((off, cmd, cmdsize))
        off += cmdsize
    if off != 32 + sizeofcmds:
        raise MachOError("sizeofcmds does not match the parsed load commands")
    return cputype, filetype, flags, found


def normalize(path):
    """Rewrite swapped dylib/dylinker command ids. Returns the number of edits."""
    blob = bytearray(Path(path).read_bytes())
    if blob.startswith(b"#!"):
        raise MachOError("refusing a shell launcher")
    _, _, _, found = commands(blob)
    edits = 0
    for off, cmd, cmdsize in found:
        if cmd not in NAME_COMMANDS:
            continue
        name, nameoff = _name_at(blob, off, cmdsize)
        if name == DYLINKER and cmd != LC_LOAD_DYLINKER:
            if nameoff != 12:
                raise MachOError(
                    f"{DYLINKER} is a {cmd:#x} command with name offset {nameoff}, not a dylinker_command"
                )
            struct.pack_into("<I", blob, off, LC_LOAD_DYLINKER)
            edits += 1
            print(f"normalized {name} to LC_LOAD_DYLINKER", file=sys.stderr)
        elif name != DYLINKER and cmd == LC_LOAD_DYLINKER:
            if nameoff != 24:
                raise MachOError(
                    f"{name} is LC_LOAD_DYLINKER with name offset {nameoff}; "
                    "the linker did not emit a dylib_command"
                )
            struct.pack_into("<I", blob, off, LC_LOAD_DYLIB)
            edits += 1
            print(f"normalized {name} to LC_LOAD_DYLIB", file=sys.stderr)
    if edits:
        Path(path).write_bytes(blob)
    return edits


def _signature_entitlements(blob, found):
    sig_off = None
    for off, cmd, cmdsize in found:
        if cmd == LC_CODE_SIGNATURE:
            sig_off, sig_size = struct.unpack_from("<II", blob, off + 8)
            if sig_off + sig_size > len(blob):
                raise MachOError("LC_CODE_SIGNATURE points outside the file")
            superblob = blob[sig_off : sig_off + sig_size]
            if len(superblob) < 12:
                raise MachOError("code signature is truncated")
            magic, length, count = struct.unpack_from(">III", superblob, 0)
            if magic != CSMAGIC_EMBEDDED_SIGNATURE:
                raise MachOError(f"code signature magic is {magic:#x}")
            if length > len(superblob) or count > 64:
                raise MachOError("code signature superblob is corrupt")
            entitlements = b""
            for index in range(count):
                base = 12 + index * 8
                if base + 8 > len(superblob):
                    raise MachOError("code signature index is truncated")
                slot_type, slot_off = struct.unpack_from(">II", superblob, base)
                if slot_off + 8 > len(superblob):
                    continue
                slot_magic, slot_len = struct.unpack_from(">II", superblob, slot_off)
                if slot_magic == CSMAGIC_EMBEDDED_ENTITLEMENTS and slot_off + slot_len <= len(superblob):
                    entitlements = superblob[slot_off : slot_off + slot_len]
            return entitlements
    raise MachOError("LC_CODE_SIGNATURE is missing")


def check(path, require_signature=True):
    blob = Path(path).read_bytes()
    if blob.startswith(b"#!"):
        raise MachOError("refusing a /bin/sh launcher")
    cputype, filetype, flags, found = commands(blob)
    if cputype != CPU_TYPE_ARM64:
        raise MachOError(f"cputype is {cputype:#x}, expected arm64")
    if filetype != MH_EXECUTE:
        raise MachOError(f"filetype is {filetype}, expected MH_EXECUTE")
    if not flags & MH_DYLDLINK:
        raise MachOError("executable is not dynamically linked")

    dylinkers = []
    dylibs = []
    has_main = False
    has_fixups = False
    has_ios_build = False
    for off, cmd, cmdsize in found:
        if cmd == LC_MAIN:
            has_main = True
        elif cmd in FIXUP_COMMANDS:
            has_fixups = True
        elif cmd == LC_BUILD_VERSION and cmdsize >= 24:
            platform = struct.unpack_from("<I", blob, off + 8)[0]
            has_ios_build = platform == 2
        elif cmd in NAME_COMMANDS:
            name, _nameoff = _name_at(blob, off, cmdsize)
            if cmd == LC_LOAD_DYLINKER:
                dylinkers.append(name)
            elif cmd in DYLIB_LOADS:
                dylibs.append(name)

    if dylinkers != [DYLINKER]:
        raise MachOError(f"expected one LC_LOAD_DYLINKER {DYLINKER}, found {dylinkers}")
    missing = [name for name in REQUIRED_DYLIBS if name not in dylibs]
    if missing:
        raise MachOError("missing LC_LOAD_DYLIB for " + ", ".join(missing))
    swapped = [name for name in dylinkers if name in REQUIRED_DYLIBS]
    if swapped:
        raise MachOError("libraries recorded as LC_LOAD_DYLINKER: " + ", ".join(swapped))
    if not has_main:
        raise MachOError("LC_MAIN is missing")
    if not has_fixups:
        raise MachOError("no LC_DYLD_INFO_ONLY or LC_DYLD_CHAINED_FIXUPS")
    if not has_ios_build:
        raise MachOError("LC_BUILD_VERSION platform is not iOS")
    if require_signature:
        entitlements = _signature_entitlements(blob, found)
        for marker in ENTITLEMENT_MARKERS:
            if marker not in entitlements:
                raise MachOError(f"code signature is missing entitlement {marker.decode()}")
    return dylibs


def main(argv):
    normalize_first = False
    args = []
    for arg in argv[1:]:
        if arg == "--normalize":
            normalize_first = True
        elif arg in ("-h", "--help"):
            print("usage: check-macho.py [--normalize] KernelLab", file=sys.stderr)
            return 2
        else:
            args.append(arg)
    if len(args) != 1:
        print("usage: check-macho.py [--normalize] KernelLab", file=sys.stderr)
        return 2
    path = args[0]
    try:
        if normalize_first:
            edits = normalize(path)
            dylibs = check(path, require_signature=False)
            print(f"normalized {path}: {edits} load command(s); dylibs={len(dylibs)}")
        else:
            dylibs = check(path, require_signature=True)
            print(f"mach-o ok: {path} ({len(dylibs)} dylibs, signed)")
    except MachOError as exc:
        print(f"mach-o rejected: {path}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
"""
POSS (Property Object Serialization Stream) Parser
===================================================
Dead Star (Steam AppID 366400) - Armature Engine (BPE)

Parses .poss / .cgpr / .sgpr files from gamedata.ara.
These are serialized CGameObjectPropertiesPackage containers holding
game object hierarchies with components, transforms, and properties.

Usage:
    python3 parse_poss.py <file.poss> [--json] [--hex-dump] [--verbose]
    python3 parse_poss.py --batch <directory> [--output <dir>]
"""

import struct
import sys
import os
import json
import argparse
from pathlib import Path


# ============================================================================
# Low-level readers (matching CInputStream API in Engine_Steam_Release.dll)
# ============================================================================

def read_varint(data, pos):
    """Read7BitEncodedInt: LEB128 unsigned varint (.NET style)."""
    result = 0
    shift = 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            break
        shift += 7
    return result, pos


def read_string(data, pos):
    """ReadString: varint length + UTF-8 bytes."""
    slen, pos = read_varint(data, pos)
    if slen == 0:
        return "", pos
    raw = data[pos:pos + slen]
    try:
        s = raw.decode('utf-8')
    except UnicodeDecodeError:
        s = raw.decode('latin-1')
    return s, pos + slen


def read_guid(data, pos):
    """Read 16-byte Microsoft GUID (LE u32 + LE u16 + LE u16 + 8 bytes)."""
    if pos + 16 > len(data):
        return "????????-????-????-????-????????????", pos + 16
    g = data[pos:pos + 16]
    a = struct.unpack_from('<I', g, 0)[0]
    b = struct.unpack_from('<H', g, 4)[0]
    c = struct.unpack_from('<H', g, 6)[0]
    s = (f"{a:08x}-{b:04x}-{c:04x}-"
         f"{g[8]:02x}{g[9]:02x}-"
         f"{g[10]:02x}{g[11]:02x}{g[12]:02x}{g[13]:02x}{g[14]:02x}{g[15]:02x}")
    return s, pos + 16


def read_u32(data, pos):
    """ReadUint32: LE u32."""
    return struct.unpack_from('<I', data, pos)[0], pos + 4


def read_u16(data, pos):
    """ReadUint16: LE u16."""
    return struct.unpack_from('<H', data, pos)[0], pos + 2


def read_u8(data, pos):
    """ReadUint8."""
    return data[pos], pos + 1


def read_float(data, pos):
    """ReadReal32: LE float32."""
    return struct.unpack_from('<f', data, pos)[0], pos + 4


def read_float64(data, pos):
    """ReadReal64: LE float64."""
    return struct.unpack_from('<d', data, pos)[0], pos + 8


# ============================================================================
# POSS Format Constants
# ============================================================================

MAGIC = b'POSS30RV'
COMPONENT_MARKER = 0xC029451E  # Appears before every component's TComponentEditorId
FORMAT_VERSION = 6              # Current version seen in all files


# ============================================================================
# High-level structures
# ============================================================================

class PossFile:
    """Top-level POSS file container."""
    def __init__(self):
        self.magic = ""
        self.string_count = 0
        self.strings = []
        self.root_object = None
        self.all_objects = []  # flat list for convenience

    def to_dict(self):
        d = {
            'magic': self.magic,
            'string_count': self.string_count,
            'strings': self.strings,
        }
        if self.root_object:
            d['root_object'] = self.root_object.to_dict()
        return d


class GameObject:
    """A CGameObjectProperties node in the hierarchy."""
    def __init__(self):
        self.offset = 0
        self.reserved = 0       # u32, always 0
        self.total_components = 0  # u32, total across entire tree (root only)
        self.version = 0        # u32, always 6
        self.guid = ""          # TGameObjectEditorId (16-byte GUID)
        self.name = ""          # object name
        self.field_a = 0        # u32 after name (purpose uncertain)
        self.field_b = 0        # u32 after name (purpose uncertain)
        self.components = []    # list of Component
        self.children = []      # list of child GameObject
        self.raw_body = b""     # unparsed body bytes (for hex dump)

    def to_dict(self):
        d = {
            'guid': self.guid,
            'name': self.name,
            'version': self.version,
            'total_components_in_tree': self.total_components,
            'field_a': self.field_a,
            'field_b': self.field_b,
            'components': [c.to_dict() for c in self.components],
            'children': [ch.to_dict() for ch in self.children],
        }
        return d


class Component:
    """A CGameObjectComponentProperties within a game object."""
    def __init__(self):
        self.offset = 0
        self.type_hash = 0      # u32, component type marker (usually 0xC029451E)
        self.editor_id_bytes = b""  # 9 bytes after type hash
        self.guid = ""          # TComponentEditorId GUID
        self.body_bytes = b""   # raw body data
        self.transform = None   # 3x4 float matrix if detected
        self.properties = {}    # decoded properties (if possible)

    def to_dict(self):
        d = {
            'type_hash': f"0x{self.type_hash:08x}",
            'guid': self.guid,
        }
        if self.transform:
            d['transform'] = {
                'matrix_3x4': self.transform,
            }
        if self.properties:
            d['properties'] = self.properties
        d['body_size'] = len(self.body_bytes)
        return d


# ============================================================================
# Transform matrix detection
# ============================================================================

TRANSFORM_PREFIX = bytes.fromhex('5f7a4afb')  # Common hash before transform data

def try_decode_transform(body):
    """Try to extract 12 floats (transform data) from the component body.

    The 12 floats appear after the common prefix hash 0xFB4A7A5F.
    Layout appears to be 3 groups of 4 floats. For identity transforms,
    each group is [1.0, 0.0, 0.0, 0.0]. The exact geometric interpretation
    (rotation, scale, position decomposition) is uncertain.
    """
    idx = body.find(TRANSFORM_PREFIX)
    if idx < 0:
        return None, {}

    # After the prefix, skip fixed bytes to reach float data
    # Pattern: 5f7a4afb 3800 0100 0e0343f5 3000
    # = 4 + 2 + 2 + 4 + 2 = 14 bytes
    float_start = idx + 14

    if float_start + 48 > len(body):
        return None, {}

    # Read 12 floats in 3 groups of 4
    matrix = []
    pos = float_start
    for group in range(3):
        r = []
        for i in range(4):
            f, pos = read_float(body, pos)
            r.append(round(f, 6))
        matrix.append(r)

    return matrix, {'transform_offset_in_body': idx}


# ============================================================================
# String reference detection
# ============================================================================

def find_string_references(body, string_table):
    """Find references to string table entries in component body data."""
    refs = {}
    for i, s in enumerate(string_table):
        if s and len(s) >= 4:
            encoded = s.encode('utf-8')
            if encoded in body:
                refs[i] = s
    return refs


# ============================================================================
# Parser
# ============================================================================

def parse_poss(filepath, verbose=False):
    """Parse a POSS file and return a PossFile object."""
    with open(filepath, 'rb') as f:
        data = f.read()

    poss = PossFile()

    # -- Header --
    if len(data) < 12:
        raise ValueError(f"File too small: {len(data)} bytes")

    poss.magic = data[0:8].decode('ascii', errors='replace')
    if data[0:8] != MAGIC:
        raise ValueError(f"Invalid magic: {poss.magic!r} (expected POSS30RV)")

    poss.string_count, _ = read_u32(data, 8)

    # -- String Table --
    pos = 12
    for _ in range(poss.string_count):
        s, pos = read_string(data, pos)
        poss.strings.append(s)

    if verbose:
        print(f"  String table: {poss.string_count} entries, ends at offset {pos}")

    # -- Check for empty/minimal file (e.g. 20-byte files with 0 strings) --
    if pos + 28 > len(data):
        return poss

    # -- Root Game Object --
    root, pos = parse_game_object(data, pos, poss.strings, verbose, depth=0)
    poss.root_object = root
    poss.all_objects.append(root)

    # -- Child Game Objects (siblings after root's components) --
    while pos + 28 < len(data):
        # Check if there's another object header: [0, X, 6, GUID]
        if not looks_like_object_header(data, pos):
            break
        child, pos = parse_game_object(data, pos, poss.strings, verbose, depth=1)
        root.children.append(child)
        poss.all_objects.append(child)

    return poss


def looks_like_object_header(data, pos):
    """Check if data at pos looks like a game object header [0, X, 6]."""
    if pos + 28 > len(data):
        return False
    v1 = struct.unpack_from('<I', data, pos)[0]
    v3 = struct.unpack_from('<I', data, pos + 8)[0]
    v2 = struct.unpack_from('<I', data, pos + 4)[0]
    if v1 != 0:
        return False
    if v3 != FORMAT_VERSION:
        return False
    if v2 > 10000:
        return False
    # Verify GUID at +12 has valid version nibble
    g = data[pos + 12:pos + 28]
    if len(g) < 16:
        return False
    c = struct.unpack_from('<H', g, 6)[0]
    ver = (c >> 12) & 0xF
    return ver in (4, 5)


def parse_game_object(data, pos, string_table, verbose, depth=0):
    """Parse a CGameObjectProperties from data at pos."""
    obj = GameObject()
    obj.offset = pos

    indent = "  " * (depth + 1)

    # Header: 3 x u32
    obj.reserved, pos = read_u32(data, pos)
    obj.total_components, pos = read_u32(data, pos)
    obj.version, pos = read_u32(data, pos)

    # GUID
    obj.guid, pos = read_guid(data, pos)

    # Name
    obj.name, pos = read_string(data, pos)

    if verbose:
        print(f"{indent}Object: '{obj.name}' GUID={obj.guid} "
              f"[res={obj.reserved}, comp={obj.total_components}, ver={obj.version}]")

    # Two u32 fields after name (purpose uncertain - may relate to
    # message/link counts or component property counts)
    if pos + 8 <= len(data):
        obj.field_a, pos = read_u32(data, pos)
        obj.field_b, pos = read_u32(data, pos)

    # Parse components: look for COMPONENT_MARKER
    while pos + 4 <= len(data):
        marker = struct.unpack_from('<I', data, pos)[0]
        if marker != COMPONENT_MARKER:
            break

        comp, pos = parse_component(data, pos, string_table, verbose, depth)
        obj.components.append(comp)

    return obj, pos


def parse_component(data, pos, string_table, verbose, depth=0):
    """Parse a CGameObjectComponentProperties from data at pos."""
    comp = Component()
    comp.offset = pos
    indent = "  " * (depth + 2)

    # Type hash (4 bytes) = COMPONENT_MARKER
    comp.type_hash, pos = read_u32(data, pos)

    # Editor ID bytes (9 bytes: appears to be part of TComponentEditorId)
    comp.editor_id_bytes = data[pos:pos + 9]
    pos += 9

    # Component GUID
    comp.guid, pos = read_guid(data, pos)

    if verbose:
        print(f"{indent}Component: GUID={comp.guid} type=0x{comp.type_hash:08x}")

    # Read the component body until the next marker or object header
    body_start = pos
    body_end = find_body_end(data, pos)
    comp.body_bytes = data[body_start:body_end]
    pos = body_end

    # Try to decode transform matrix
    comp.transform, extra = try_decode_transform(comp.body_bytes)

    if verbose and comp.transform:
        m = comp.transform
        is_identity = all(
            abs(m[i][j] - (1.0 if i == j else 0.0)) < 0.001
            for i in range(3) for j in range(3)
        )
        tx, ty, tz = m[0][3], m[1][3], m[2][3]
        if is_identity and tx == 0 and ty == 0 and tz == 0:
            print(f"{indent}  Transform: identity")
        else:
            print(f"{indent}  Transform: pos=({tx}, {ty}, {tz})")

    return comp, pos


def find_body_end(data, pos):
    """Find where the component body ends (next marker or object header)."""
    i = pos
    while i + 4 <= len(data):
        u32 = struct.unpack_from('<I', data, i)[0]
        if u32 == COMPONENT_MARKER:
            return i
        # Check for object header pattern
        if (u32 == 0 and i + 12 <= len(data) and
            struct.unpack_from('<I', data, i + 8)[0] == FORMAT_VERSION):
            v2 = struct.unpack_from('<I', data, i + 4)[0]
            if v2 < 10000 and i + 28 <= len(data):
                g = data[i + 12:i + 28]
                c = struct.unpack_from('<H', g, 6)[0]
                ver = (c >> 12) & 0xF
                if ver in (4, 5):
                    return i
        i += 1
    return len(data)


# ============================================================================
# Output formatting
# ============================================================================

def format_text(poss, filepath="", show_hex=False):
    """Format PossFile as human-readable text."""
    lines = []
    fname = os.path.basename(filepath)
    lines.append(f"{'=' * 70}")
    lines.append(f"POSS File: {fname}")
    lines.append(f"{'=' * 70}")
    lines.append(f"Magic:        {poss.magic}")
    lines.append(f"String Count: {poss.string_count}")
    lines.append("")

    if poss.strings:
        # Categorize strings
        paths = [s for s in poss.strings if s.startswith('$/')]
        events = [s for s in poss.strings if s and not s.startswith('$/') and not s.startswith('~')]
        loc_keys = [s for s in poss.strings if s.startswith('~')]
        empty = [s for s in poss.strings if s == ""]

        if paths:
            lines.append(f"--- Resource Paths ({len(paths)}) ---")
            for s in paths[:50]:
                ext = s.rsplit('.', 1)[-1] if '.' in s else '?'
                lines.append(f"  [{ext:4s}] {s}")
            if len(paths) > 50:
                lines.append(f"  ... ({len(paths) - 50} more)")
            lines.append("")

        if events:
            lines.append(f"--- Events/Names ({len(events)}) ---")
            for s in events[:50]:
                lines.append(f"  {s}")
            if len(events) > 50:
                lines.append(f"  ... ({len(events) - 50} more)")
            lines.append("")

        if loc_keys:
            lines.append(f"--- Localization Keys ({len(loc_keys)}) ---")
            for s in loc_keys[:20]:
                lines.append(f"  {s}")
            if len(loc_keys) > 20:
                lines.append(f"  ... ({len(loc_keys) - 20} more)")
            lines.append("")

    if poss.root_object:
        lines.append(f"--- Object Hierarchy ---")
        format_object(poss.root_object, lines, indent=0, show_hex=show_hex)

    return "\n".join(lines)


def format_object(obj, lines, indent=0, show_hex=False):
    """Recursively format a game object."""
    prefix = "  " * indent
    lines.append(f"{prefix}Object: '{obj.name}'")
    lines.append(f"{prefix}  GUID: {obj.guid}")
    lines.append(f"{prefix}  Version: {obj.version}, "
                 f"Total Components in Tree: {obj.total_components}")
    lines.append(f"{prefix}  Field A: {obj.field_a}, Field B: {obj.field_b}")

    for comp in obj.components:
        format_component(comp, lines, indent + 1, show_hex)

    for child in obj.children:
        format_object(child, lines, indent + 1, show_hex)


def format_component(comp, lines, indent=0, show_hex=False):
    """Format a component."""
    prefix = "  " * indent
    lines.append(f"{prefix}Component:")
    lines.append(f"{prefix}  Type Hash: 0x{comp.type_hash:08x}")
    lines.append(f"{prefix}  GUID: {comp.guid}")
    lines.append(f"{prefix}  Editor ID: {comp.editor_id_bytes.hex()}")
    lines.append(f"{prefix}  Body Size: {len(comp.body_bytes)} bytes")

    if comp.transform:
        m = comp.transform
        is_identity = all(
            abs(m[i][j] - (1.0 if i == j else 0.0)) < 0.001
            for i in range(3) for j in range(3)
        )
        tx, ty, tz = m[0][3], m[1][3], m[2][3]
        if is_identity and abs(tx) < 0.001 and abs(ty) < 0.001 and abs(tz) < 0.001:
            lines.append(f"{prefix}  Transform: identity (no translation)")
        else:
            lines.append(f"{prefix}  Transform:")
            for row in m:
                lines.append(f"{prefix}    [{row[0]:10.4f} {row[1]:10.4f} "
                             f"{row[2]:10.4f} {row[3]:10.4f}]")

    if show_hex and comp.body_bytes:
        lines.append(f"{prefix}  Body Hex (first 128 bytes):")
        for i in range(0, min(128, len(comp.body_bytes)), 16):
            chunk = comp.body_bytes[i:i + 16]
            hex_str = ' '.join(f'{b:02x}' for b in chunk)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            lines.append(f"{prefix}    {i:04x}: {hex_str:48s}  {ascii_str}")


# ============================================================================
# Batch processing
# ============================================================================

def batch_process(input_dir, output_dir=None, extensions=('.poss', '.cgpr', '.sgpr')):
    """Process all POSS files in a directory."""
    from collections import Counter

    input_path = Path(input_dir)
    files = []
    for ext in extensions:
        files.extend(input_path.rglob(f'*{ext}'))

    print(f"Found {len(files)} files to process")

    success = 0
    failed = 0
    object_names = Counter()
    string_stats = Counter()

    for filepath in sorted(files):
        try:
            poss = parse_poss(str(filepath))
            success += 1

            if poss.root_object:
                object_names[poss.root_object.name] += 1

            for s in poss.strings:
                if s.startswith('$/'):
                    ext = s.rsplit('.', 1)[-1] if '.' in s else '?'
                    string_stats[f'path.{ext}'] += 1
                elif s.startswith('~'):
                    string_stats['loc_key'] += 1
                elif s:
                    string_stats['event/name'] += 1

            if output_dir:
                out_path = Path(output_dir) / filepath.relative_to(input_path).with_suffix('.txt')
                out_path.parent.mkdir(parents=True, exist_ok=True)
                text = format_text(poss, str(filepath))
                out_path.write_text(text)

        except Exception as e:
            failed += 1
            if failed <= 10:
                print(f"  FAILED: {filepath.name}: {e}")

    print(f"\nResults: {success} success, {failed} failed out of {len(files)} files")
    print(f"\nTop 20 object names:")
    for name, count in object_names.most_common(20):
        print(f"  {count:5d}x  {name}")
    print(f"\nString type distribution:")
    for key, count in string_stats.most_common(20):
        print(f"  {count:6d}x  {key}")


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='POSS format parser for Dead Star')
    parser.add_argument('file', nargs='?', help='POSS file to parse')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--hex-dump', action='store_true', help='Include hex dumps')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose parsing')
    parser.add_argument('--batch', metavar='DIR', help='Batch process directory')
    parser.add_argument('--output', '-o', metavar='DIR', help='Output directory for batch')

    args = parser.parse_args()

    if args.batch:
        batch_process(args.batch, args.output)
        return

    if not args.file:
        parser.print_help()
        return

    try:
        poss = parse_poss(args.file, verbose=args.verbose)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(poss.to_dict(), indent=2))
    else:
        print(format_text(poss, args.file, show_hex=args.hex_dump))


if __name__ == '__main__':
    main()

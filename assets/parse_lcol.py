#!/usr/bin/env python3
"""
LCOL (CLocalizationTable) parser for Dead Star.
Extracts localization key-value pairs from .lcol files.

Usage:
    python parse_lcol.py <file.lcol> [--json] [--lang <index>] [--dump-all]
"""

import struct
import sys
import json
import os

LANGUAGES = ["English", "French", "German", "Italian", "Portuguese", "Spanish", "Russian"]


def read_varint(data, pos):
    """Read unsigned LEB128 varint."""
    result = 0
    shift = 0
    while True:
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            break
        shift += 7
    return result, pos


def parse_lcol(data):
    """Parse an LCOL file from bytes. Returns dict with all parsed data."""
    magic = data[:4]
    if magic != b'LCOL':
        raise ValueError(f"Invalid magic: {magic!r}, expected b'LCOL'")

    version, num_lang_slots = struct.unpack_from('<II', data, 4)
    lang_map = list(struct.unpack_from(f'<{num_lang_slots}I', data, 12))

    pos = 12 + num_lang_slots * 4
    num_string_blocks = struct.unpack_from('<I', data, pos)[0]
    pos += 4

    strings = []
    for _ in range(num_string_blocks):
        prefix = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        slen, pos = read_varint(data, pos)
        s = data[pos:pos + slen].decode('utf-8', errors='replace')
        pos += slen + 8  # string + 8-byte null padding
        strings.append(s)

    # Footer: key lookup table
    num_languages = struct.unpack_from('<I', data, pos)[0]
    pos += 4
    num_keys = struct.unpack_from('<I', data, pos)[0]
    pos += 4

    keys = []
    for _ in range(num_keys):
        lang_entries = []
        for _ in range(num_languages):
            key_idx = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            val_idx = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            lang_entries.append((key_idx, val_idx))
        keys.append(lang_entries)

    return {
        'version': version,
        'lang_slots': num_lang_slots,
        'lang_map': lang_map,
        'num_languages': num_languages,
        'num_keys': num_keys,
        'strings': strings,
        'keys': keys,
    }


def lcol_to_dict(parsed, lang_index=0):
    """Convert parsed LCOL to a simple {key: value} dict for one language."""
    result = {}
    for lang_entries in parsed['keys']:
        if lang_index < len(lang_entries):
            key_idx, val_idx = lang_entries[lang_index]
            key = parsed['strings'][key_idx] if key_idx < len(parsed['strings']) else f'?{key_idx}'
            val = parsed['strings'][val_idx] if val_idx < len(parsed['strings']) else f'?{val_idx}'
            result[key] = val
    return result


def lcol_to_multilang(parsed):
    """Convert parsed LCOL to {key: {lang: value}} dict."""
    result = {}
    for lang_entries in parsed['keys']:
        # Use the first language's key as the canonical key
        if lang_entries:
            canonical_key = parsed['strings'][lang_entries[0][0]]
        else:
            continue
        translations = {}
        for lang_idx, (key_idx, val_idx) in enumerate(lang_entries):
            lang_name = LANGUAGES[lang_idx] if lang_idx < len(LANGUAGES) else f'lang_{lang_idx}'
            val = parsed['strings'][val_idx] if val_idx < len(parsed['strings']) else None
            translations[lang_name] = val
        result[canonical_key] = translations
    return result


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    filepath = sys.argv[1]
    output_json = '--json' in sys.argv
    dump_all = '--dump-all' in sys.argv
    lang_index = 0

    if '--lang' in sys.argv:
        idx = sys.argv.index('--lang')
        if idx + 1 < len(sys.argv):
            lang_index = int(sys.argv[idx + 1])

    with open(filepath, 'rb') as f:
        data = f.read()

    parsed = parse_lcol(data)

    if output_json:
        if dump_all:
            result = lcol_to_multilang(parsed)
        else:
            result = lcol_to_dict(parsed, lang_index)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"LCOL v{parsed['version']}: {parsed['num_keys']} keys, "
              f"{parsed['num_languages']} languages, {len(parsed['strings'])} strings")
        print(f"Languages: {', '.join(LANGUAGES[:parsed['num_languages']])}")
        print()

        if dump_all:
            multilang = lcol_to_multilang(parsed)
            for key, translations in multilang.items():
                print(f"[{key}]")
                for lang, val in translations.items():
                    preview = val[:80].replace('\n', '\\n') if val else '(none)'
                    print(f"  {lang}: {preview}")
                print()
        else:
            lang_name = LANGUAGES[lang_index] if lang_index < len(LANGUAGES) else f'lang_{lang_index}'
            print(f"Showing {lang_name} (index {lang_index}):\n")
            kv = lcol_to_dict(parsed, lang_index)
            for key, val in kv.items():
                preview = val[:80].replace('\n', '\\n')
                print(f"  {key} = {preview}")


if __name__ == '__main__':
    main()

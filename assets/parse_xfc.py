#!/usr/bin/env python3
"""
XFC (compiled shader effect) parser for Dead Star.
Extracts shader combinations, DXBC blobs, and render state from .xfc files.

Usage:
    python parse_xfc.py <file.xfc> [--extract-shaders <outdir>] [--json]
"""

import struct
import sys
import json
import os


def parse_xfc(data):
    """Parse an XFC file from bytes."""
    magic = data[:4]
    if magic != b'!XFC':
        raise ValueError(f"Invalid magic: {magic!r}, expected b'!XFC'")

    version, num_combinations = struct.unpack_from('<II', data, 4)
    section_offsets = list(struct.unpack_from('<9I', data, 12))

    # Section sizes
    section_sizes = []
    for i in range(9):
        end = section_offsets[i + 1] if i < 8 else len(data)
        section_sizes.append(end - section_offsets[i])

    # Section 1: combination hash table (8 bytes per combo)
    combinations = []
    s1_start = section_offsets[1]
    for i in range(num_combinations):
        combo_hash, state_offset = struct.unpack_from('<II', data, s1_start + i * 8)
        combinations.append({
            'index': i,
            'hash': f'0x{combo_hash:08x}',
            'state_offset': state_offset,
        })

    # Section 2: shader blob descriptors (pairs of offset, size)
    s2_start = section_offsets[2]
    s2_size = section_sizes[2]
    num_shader_pairs = s2_size // 8
    shader_blobs = []
    for i in range(num_shader_pairs):
        blob_offset, blob_size = struct.unpack_from('<II', data, s2_start + i * 8)
        shader_blobs.append({
            'offset_in_section7': blob_offset,
            'size': blob_size,
        })

    # Section 7: DXBC shader data - identify shader types
    s7_start = section_offsets[7]
    s7_end = section_offsets[8] if 8 < 9 else len(data)
    s7_data = data[s7_start:s7_end]

    dxbc_blobs = []
    pos = 0
    while pos < len(s7_data):
        idx = s7_data.find(b'DXBC', pos)
        if idx == -1:
            break
        if idx + 28 > len(s7_data):
            break
        dxbc_size = struct.unpack_from('<I', s7_data, idx + 24)[0]
        blob_data = s7_data[idx:idx + dxbc_size]

        # Determine shader type
        shader_type = 'unknown'
        has_shex = b'SHEX' in blob_data or b'SHDR' in blob_data
        if not has_shex:
            shader_type = 'input_signature'
        else:
            shex_pos = blob_data.find(b'SHEX')
            if shex_pos == -1:
                shex_pos = blob_data.find(b'SHDR')
            if shex_pos > 0:
                # Version token is 4 bytes after chunk header (tag + size)
                chunk_data_offset = shex_pos + 8
                if chunk_data_offset + 4 <= len(blob_data):
                    ver_token = struct.unpack_from('<I', blob_data, chunk_data_offset)[0]
                    st = (ver_token >> 16) & 0xF
                    type_map = {0: 'pixel', 1: 'vertex', 2: 'geometry',
                                3: 'hull', 4: 'domain', 5: 'compute'}
                    shader_type = type_map.get(st, f'type_{st}')

        dxbc_blobs.append({
            'offset': idx,
            'size': dxbc_size,
            'type': shader_type,
        })
        pos = idx + max(dxbc_size, 4)

    # Section 8: metadata footer (20 bytes)
    s8_start = section_offsets[8]
    s8_data = data[s8_start:]
    metadata = {
        'num_vs_blobs': s8_data[0] if len(s8_data) > 0 else 0,
        'num_dxbc_blobs': s8_data[2] if len(s8_data) > 2 else 0,
        'has_input_sig': bool(s8_data[12]) if len(s8_data) > 12 else False,
        'num_ps_variants': s8_data[13] if len(s8_data) > 13 else 0,
        'has_vs': bool(s8_data[14]) if len(s8_data) > 14 else False,
        'max_texture_slot': s8_data[15] if len(s8_data) > 15 else 0,
        'has_ps': bool(s8_data[16]) if len(s8_data) > 16 else False,
    }

    return {
        'version': version,
        'num_combinations': num_combinations,
        'section_offsets': [f'0x{o:x}' for o in section_offsets],
        'section_sizes': section_sizes,
        'combinations': combinations,
        'shader_blob_descriptors': shader_blobs,
        'dxbc_blobs': dxbc_blobs,
        'metadata': metadata,
        '_raw_s7_data': s7_data,
    }


def extract_shaders(parsed, outdir):
    """Extract DXBC shader blobs to individual files."""
    os.makedirs(outdir, exist_ok=True)
    s7_data = parsed['_raw_s7_data']

    for i, blob in enumerate(parsed['dxbc_blobs']):
        blob_data = s7_data[blob['offset']:blob['offset'] + blob['size']]
        ext = blob['type']
        filename = f'shader_{i:02d}_{ext}.dxbc'
        filepath = os.path.join(outdir, filename)
        with open(filepath, 'wb') as f:
            f.write(blob_data)
        print(f"  Extracted: {filename} ({blob['size']} bytes)")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    filepath = sys.argv[1]
    output_json = '--json' in sys.argv
    extract_dir = None

    if '--extract-shaders' in sys.argv:
        idx = sys.argv.index('--extract-shaders')
        if idx + 1 < len(sys.argv):
            extract_dir = sys.argv[idx + 1]

    with open(filepath, 'rb') as f:
        data = f.read()

    parsed = parse_xfc(data)

    if extract_dir:
        print(f"Extracting {len(parsed['dxbc_blobs'])} DXBC blobs to {extract_dir}/")
        extract_shaders(parsed, extract_dir)

    # Remove raw data before JSON output
    output = {k: v for k, v in parsed.items() if not k.startswith('_')}

    if output_json:
        print(json.dumps(output, indent=2))
    else:
        print(f"XFC v{parsed['version']}: {parsed['num_combinations']} combinations, "
              f"{len(parsed['dxbc_blobs'])} DXBC blobs")
        print(f"File size: {len(data)} bytes")
        print()

        print("Sections:")
        for i, (off, sz) in enumerate(zip(parsed['section_offsets'], parsed['section_sizes'])):
            names = ['BlendState', 'HashTable', 'ShaderDesc', 'DepthStencil',
                     'DepthTest', 'StencilCfg', 'SamplerState', 'DXBC_Data', 'Footer']
            print(f"  [{i}] {names[i]:14s} offset={off} size={sz}")
        print()

        print("DXBC Shaders:")
        for blob in parsed['dxbc_blobs']:
            print(f"  @0x{blob['offset']:04x}: {blob['type']:16s} {blob['size']} bytes")
        print()

        meta = parsed['metadata']
        print(f"Metadata: VS={meta['num_vs_blobs']}, PS_variants={meta['num_ps_variants']}, "
              f"textures={meta['max_texture_slot']}, total_blobs={meta['num_dxbc_blobs']}")

        if parsed['combinations'][:5]:
            print(f"\nFirst 5 combinations (of {parsed['num_combinations']}):")
            for c in parsed['combinations'][:5]:
                print(f"  [{c['index']}] hash={c['hash']} state_offset={c['state_offset']}")


if __name__ == '__main__':
    main()

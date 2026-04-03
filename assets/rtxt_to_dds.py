#!/usr/bin/env python3
"""
RTXT to DDS Converter for Dead Star (BPE Engine)

Converts proprietary .rtxt texture files to standard .dds format.
Supports BC1/DXT1, BC2/DXT3, BC3/DXT5, BC5/ATI2, and RGBA8 formats.
Handles 2D textures and cubemaps.

Usage:
    python3 rtxt_to_dds.py input.rtxt [output.dds]
    python3 rtxt_to_dds.py --batch input_dir/ output_dir/
"""

import struct
import sys
import os
import glob
import argparse


# RTXT format IDs -> (name, bytes_per_block, is_block_compressed)
RTXT_FORMATS = {
    0: ("RGBA8",    4, False),   # 4 bytes per pixel
    6: ("BC1/DXT1", 8, True),    # 8 bytes per 4x4 block
    7: ("BC2/DXT3", 16, True),   # 16 bytes per 4x4 block
    8: ("BC3/DXT5", 16, True),   # 16 bytes per 4x4 block
    9: ("BC5/ATI2", 16, True),   # 16 bytes per 4x4 block
}

# DDS constants
DDS_MAGIC = 0x20534444  # 'DDS '
DDSD_CAPS = 0x1
DDSD_HEIGHT = 0x2
DDSD_WIDTH = 0x4
DDSD_PITCH = 0x8
DDSD_PIXELFORMAT = 0x1000
DDSD_MIPMAPCOUNT = 0x20000
DDSD_LINEARSIZE = 0x80000
DDSD_DEPTH = 0x800000

DDPF_ALPHAPIXELS = 0x1
DDPF_FOURCC = 0x4
DDPF_RGB = 0x40

DDSCAPS_COMPLEX = 0x8
DDSCAPS_TEXTURE = 0x1000
DDSCAPS_MIPMAP = 0x400000

DDSCAPS2_CUBEMAP = 0x200
DDSCAPS2_CUBEMAP_ALL_FACES = 0xFC00


def align32(n):
    return (n + 31) & ~31


def mip_raw_size(w, h, fmt_id):
    """Calculate raw pixel data size for one mip level."""
    _, bpb, is_bc = RTXT_FORMATS[fmt_id]
    if is_bc:
        blocks_w = max(1, (w + 3) // 4)
        blocks_h = max(1, (h + 3) // 4)
        return blocks_w * blocks_h * bpb
    else:
        return w * h * bpb


def parse_rtxt_header(data):
    """Parse RTXT header from first 128 bytes. Returns dict of fields."""
    if len(data) < 128:
        raise ValueError("File too small for RTXT header")

    magic = data[0:4]
    if magic != b'RTXT':
        raise ValueError(f"Not an RTXT file (magic: {magic!r})")

    version = struct.unpack_from('<I', data, 4)[0]
    header_size = struct.unpack_from('<I', data, 8)[0]
    width = struct.unpack_from('<H', data, 12)[0]
    height = struct.unpack_from('<H', data, 14)[0]
    depth = struct.unpack_from('<H', data, 16)[0]
    fmt_id = struct.unpack_from('<H', data, 18)[0]
    has_alpha = data[0x16]
    is_srgb = data[0x17]
    is_cubemap = data[0x18]
    mip_count = data[0x1D]

    if fmt_id not in RTXT_FORMATS:
        raise ValueError(f"Unknown RTXT format ID: {fmt_id}")

    return {
        'version': version,
        'header_size': header_size,
        'width': width,
        'height': height,
        'depth': depth,
        'format_id': fmt_id,
        'format_name': RTXT_FORMATS[fmt_id][0],
        'has_alpha': has_alpha,
        'is_srgb': is_srgb,
        'is_cubemap': is_cubemap,
        'mip_count': mip_count,
        'face_count': 6 if is_cubemap else 1,
    }


def extract_mip_data(file_data, header):
    """Extract raw pixel data for all faces and mip levels from RTXT file.
    Returns list of (face_idx, mip_idx, raw_bytes) tuples."""
    w = header['width']
    h = header['height']
    fmt_id = header['format_id']
    mip_count = header['mip_count']
    face_count = header['face_count']

    offset = header['header_size']  # 128
    results = []

    for face in range(face_count):
        for mip in range(mip_count):
            mw = max(1, w >> mip)
            mh = max(1, h >> mip)
            raw_size = mip_raw_size(mw, mh, fmt_id)

            # Read the 4-byte size prefix
            if offset + 4 > len(file_data):
                raise ValueError(f"Unexpected EOF reading mip size at offset 0x{offset:X}")
            stored_size = struct.unpack_from('<I', file_data, offset)[0]
            if stored_size != raw_size:
                raise ValueError(
                    f"Mip size mismatch at face={face} mip={mip}: "
                    f"stored={stored_size} expected={raw_size}"
                )

            # Read pixel data
            data_offset = offset + 4
            if data_offset + raw_size > len(file_data):
                raise ValueError(f"Unexpected EOF reading mip data at offset 0x{data_offset:X}")
            raw_data = file_data[data_offset:data_offset + raw_size]
            results.append((face, mip, raw_data))

            # Advance past aligned entry
            entry_size = align32(4 + raw_size)
            offset += entry_size

    return results


def build_dds_header(header):
    """Build a 128-byte DDS file header (or 148 for DX10 extended)."""
    w = header['width']
    h = header['height']
    fmt_id = header['format_id']
    mip_count = header['mip_count']
    is_cubemap = header['is_cubemap']

    flags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT
    caps1 = DDSCAPS_TEXTURE
    caps2 = 0

    if mip_count > 1:
        flags |= DDSD_MIPMAPCOUNT
        caps1 |= DDSCAPS_COMPLEX | DDSCAPS_MIPMAP

    if is_cubemap:
        caps1 |= DDSCAPS_COMPLEX
        caps2 |= DDSCAPS2_CUBEMAP | DDSCAPS2_CUBEMAP_ALL_FACES

    # Pixel format
    pf_size = 32
    pf_flags = 0
    pf_fourcc = 0
    pf_rgbbits = 0
    pf_rmask = 0
    pf_gmask = 0
    pf_bmask = 0
    pf_amask = 0

    pitch_or_linear = 0
    use_dx10 = False

    if fmt_id == 0:
        # RGBA8 uncompressed
        pf_flags = DDPF_RGB | DDPF_ALPHAPIXELS
        pf_rgbbits = 32
        pf_rmask = 0x000000FF
        pf_gmask = 0x0000FF00
        pf_bmask = 0x00FF0000
        pf_amask = 0xFF000000
        flags |= DDSD_PITCH
        pitch_or_linear = w * 4
    elif fmt_id == 6:
        pf_flags = DDPF_FOURCC
        pf_fourcc = 0x31545844  # 'DXT1'
        flags |= DDSD_LINEARSIZE
        pitch_or_linear = mip_raw_size(w, h, fmt_id)
    elif fmt_id == 7:
        pf_flags = DDPF_FOURCC
        pf_fourcc = 0x33545844  # 'DXT3'
        flags |= DDSD_LINEARSIZE
        pitch_or_linear = mip_raw_size(w, h, fmt_id)
    elif fmt_id == 8:
        pf_flags = DDPF_FOURCC
        pf_fourcc = 0x35545844  # 'DXT5'
        flags |= DDSD_LINEARSIZE
        pitch_or_linear = mip_raw_size(w, h, fmt_id)
    elif fmt_id == 9:
        # BC5 -- use ATI2 FourCC (widely supported)
        pf_flags = DDPF_FOURCC
        pf_fourcc = 0x32495441  # 'ATI2'
        flags |= DDSD_LINEARSIZE
        pitch_or_linear = mip_raw_size(w, h, fmt_id)

    # Build 128-byte DDS header
    dds = bytearray(128)
    struct.pack_into('<I', dds, 0, DDS_MAGIC)        # 'DDS '
    struct.pack_into('<I', dds, 4, 124)               # header size (after magic)
    struct.pack_into('<I', dds, 8, flags)
    struct.pack_into('<I', dds, 12, h)
    struct.pack_into('<I', dds, 16, w)
    struct.pack_into('<I', dds, 20, pitch_or_linear)
    struct.pack_into('<I', dds, 24, 0)                # depth
    struct.pack_into('<I', dds, 28, mip_count)
    # reserved1[11] at 32-75 = zeros
    # Pixel format at offset 76
    struct.pack_into('<I', dds, 76, pf_size)
    struct.pack_into('<I', dds, 80, pf_flags)
    struct.pack_into('<I', dds, 84, pf_fourcc)
    struct.pack_into('<I', dds, 88, pf_rgbbits)
    struct.pack_into('<I', dds, 92, pf_rmask)
    struct.pack_into('<I', dds, 96, pf_gmask)
    struct.pack_into('<I', dds, 100, pf_bmask)
    struct.pack_into('<I', dds, 104, pf_amask)
    # Caps
    struct.pack_into('<I', dds, 108, caps1)
    struct.pack_into('<I', dds, 112, caps2)
    # caps3, caps4, reserved2 at 116-127 = zeros

    return bytes(dds)


def convert_rtxt_to_dds(input_path, output_path=None):
    """Convert a single RTXT file to DDS. Returns output path."""
    if output_path is None:
        output_path = os.path.splitext(input_path)[0] + '.dds'

    with open(input_path, 'rb') as f:
        file_data = f.read()

    header = parse_rtxt_header(file_data)
    mip_entries = extract_mip_data(file_data, header)
    dds_header = build_dds_header(header)

    # DDS stores data as: for each face, all mips in order
    # (Same order as RTXT, so just concatenate raw data)
    with open(output_path, 'wb') as f:
        f.write(dds_header)
        for face, mip, raw_data in mip_entries:
            f.write(raw_data)

    return output_path, header


def main():
    parser = argparse.ArgumentParser(
        description='Convert Dead Star RTXT textures to DDS format'
    )
    parser.add_argument('input', help='Input .rtxt file or directory (with --batch)')
    parser.add_argument('output', nargs='?', help='Output .dds file or directory (with --batch)')
    parser.add_argument('--batch', action='store_true', help='Convert all .rtxt files in input directory')
    parser.add_argument('--info', action='store_true', help='Print header info only, do not convert')
    args = parser.parse_args()

    if args.info:
        with open(args.input, 'rb') as f:
            data = f.read(128)
        hdr = parse_rtxt_header(data)
        print(f"File: {args.input}")
        print(f"  Size: {os.path.getsize(args.input)} bytes")
        print(f"  Version: {hdr['version']}")
        print(f"  Dimensions: {hdr['width']}x{hdr['height']}")
        print(f"  Format: {hdr['format_name']} (id={hdr['format_id']})")
        print(f"  Mip Levels: {hdr['mip_count']}")
        print(f"  Has Alpha: {bool(hdr['has_alpha'])}")
        print(f"  sRGB: {bool(hdr['is_srgb'])}")
        print(f"  Cubemap: {bool(hdr['is_cubemap'])}")
        return

    if args.batch:
        input_dir = args.input
        output_dir = args.output or input_dir
        os.makedirs(output_dir, exist_ok=True)

        files = sorted(glob.glob(os.path.join(input_dir, '*.rtxt')))
        if not files:
            print(f"No .rtxt files found in {input_dir}")
            return

        success = 0
        failed = 0
        for fp in files:
            bn = os.path.splitext(os.path.basename(fp))[0] + '.dds'
            out_fp = os.path.join(output_dir, bn)
            try:
                _, hdr = convert_rtxt_to_dds(fp, out_fp)
                success += 1
            except Exception as e:
                print(f"FAILED: {os.path.basename(fp)}: {e}")
                failed += 1

        print(f"Converted {success} files ({failed} failed) to {output_dir}")
    else:
        try:
            out_path, hdr = convert_rtxt_to_dds(args.input, args.output)
            print(f"Converted: {args.input}")
            print(f"  -> {out_path}")
            print(f"  {hdr['width']}x{hdr['height']} {hdr['format_name']} "
                  f"({hdr['mip_count']} mips"
                  f"{', cubemap' if hdr['is_cubemap'] else ''})")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()

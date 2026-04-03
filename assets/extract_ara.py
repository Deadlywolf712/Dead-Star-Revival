#!/usr/bin/env python3
"""
ARMA v2 Archive Extractor for Dead Star (gamedata.ara)

Extracts all 9,500 files from the archive. Files are organized into:
  - _named/  : Files with known paths (special entries 0-3)
  - _by_entry/ : ALL files by entry index with detected extensions

The SPED path table lists 11,986 resource paths but the internal mapping
uses an undecoded dependency graph, not a simple index-to-entry lookup.
The complete path list is saved for reference.
"""

import struct
import os
import time

ARA_PATH = '/home/john-tran/Desktop/Dead Star Revival/DepotDownloaderMod/build_output/depots/366401/1234898/GameData/gamedata.ara'
OUTPUT_DIR = '/home/john-tran/Desktop/Dead Star Revival/Revival Assets/RAW ORIGINAL'

CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks


def read_uleb128(f):
    """Read unsigned LEB128 from file."""
    result = 0
    shift = 0
    while True:
        b = f.read(1)[0]
        result |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            break
        shift += 7
    return result


def detect_extension(magic_bytes):
    """Detect file extension from 4-byte magic."""
    magic_map = {
        b'POSS': '.poss',
        b'RTXT': '.rtxt',
        b'LCOL': '.lcol',
        b'LDOM': '.ldom',
        b'!XFC': '.xfc',
        b'TNOF': '.tnof',
        b'SPED': '.sped',
        b'BKHD': '.bnk',
    }
    for m, ext in magic_map.items():
        if magic_bytes[:len(m)] == m:
            return ext
    if magic_bytes[:1] == b'<':
        return '.xml'
    # Check if text
    text_count = sum(1 for b in magic_bytes if 32 <= b < 127 or b in (9, 10, 13))
    if len(magic_bytes) > 0 and text_count / len(magic_bytes) > 0.85:
        return '.txt'
    return '.bin'


def extract_all():
    file_size = os.path.getsize(ARA_PATH)
    print(f"Archive: {ARA_PATH}")
    print(f"Size: {file_size:,} bytes ({file_size / (1024**3):.2f} GB)")
    print(f"Output: {OUTPUT_DIR}")
    print()

    with open(ARA_PATH, 'rb') as f:
        # Verify magic
        if f.read(4) != b'ARMA':
            print("ERROR: Not an ARMA archive")
            return

        # Read file entry table (9500 entries at 0x20174)
        print("Reading file entry table...")
        f.seek(0x20174)
        entries = []
        for _ in range(9500):
            data = f.read(20)
            entries.append((
                struct.unpack_from('<Q', data, 0)[0],   # offset
                struct.unpack_from('<I', data, 8)[0],    # compressed_size
                struct.unpack_from('<I', data, 12)[0],   # uncompressed_size
                struct.unpack_from('<I', data, 16)[0],   # flags
            ))
        print(f"  {len(entries)} entries")

        # Read SPED path table for reference
        print("Reading SPED path table...")
        f.seek(0x4e8f0)
        path_count = struct.unpack('<I', f.read(4))[0]
        paths = []
        for _ in range(path_count):
            length = read_uleb128(f)
            path = f.read(length).decode('ascii', errors='replace')
            paths.append(path)
        print(f"  {path_count} paths")

        # Known named files (confirmed through DLL analysis and content verification)
        known_names = {
            0: 'commandlineargs.txt',
            1: 'buildversion.txt',
            2: 'SPED_manifest.bin',
            3: 'gamescriptvars.txt',
        }

        # Create output directories
        by_entry_dir = os.path.join(OUTPUT_DIR, '_by_entry')
        named_dir = os.path.join(OUTPUT_DIR, '_named')
        os.makedirs(by_entry_dir, exist_ok=True)
        os.makedirs(named_dir, exist_ok=True)

        # Extract all files
        print(f"\nExtracting {len(entries)} files...")
        start_time = time.time()
        extracted = 0
        skipped = 0
        errors = 0
        total_bytes = 0

        for i, (offset, comp_size, uncomp_size, flags) in enumerate(entries):
            if uncomp_size == 0:
                skipped += 1
                continue
            if offset + uncomp_size > file_size:
                skipped += 1
                continue

            # Read magic bytes for extension detection
            f.seek(offset)
            magic_sample = f.read(min(64, uncomp_size))
            ext = detect_extension(magic_sample)

            # Create by-entry file
            entry_filename = f'entry_{i:05d}{ext}'
            entry_path = os.path.join(by_entry_dir, entry_filename)

            try:
                f.seek(offset)
                remaining = uncomp_size
                with open(entry_path, 'wb') as out:
                    while remaining > 0:
                        chunk = min(CHUNK_SIZE, remaining)
                        data = f.read(chunk)
                        if not data:
                            break
                        out.write(data)
                        remaining -= len(data)

                # Also save known named files
                if i in known_names:
                    named_path = os.path.join(named_dir, known_names[i])
                    # Copy from the entry file (already written)
                    import shutil
                    shutil.copy2(entry_path, named_path)

                extracted += 1
                total_bytes += uncomp_size
            except Exception as e:
                print(f"  ERROR entry {i}: {e}")
                errors += 1

            if (i + 1) % 1000 == 0 or i == len(entries) - 1:
                elapsed = time.time() - start_time
                pct = (i + 1) / len(entries) * 100
                speed = total_bytes / (1024**2) / max(elapsed, 0.001)
                print(f"  [{pct:5.1f}%] {extracted}/{len(entries)} files, "
                      f"{total_bytes / (1024**3):.2f} GB, {speed:.0f} MB/s")

        elapsed = time.time() - start_time
        print(f"\nDone in {elapsed:.1f}s")
        print(f"  Extracted: {extracted}")
        print(f"  Skipped (empty/invalid): {skipped}")
        print(f"  Errors: {errors}")
        print(f"  Total: {total_bytes:,} bytes ({total_bytes / (1024**3):.2f} GB)")

        # Write manifest
        manifest_path = os.path.join(OUTPUT_DIR, '_manifest.txt')
        with open(manifest_path, 'w') as mf:
            mf.write(f"# ARMA v2 Extraction Manifest\n")
            mf.write(f"# Archive: {ARA_PATH}\n")
            mf.write(f"# Total entries: {len(entries)}\n")
            mf.write(f"# Extracted: {extracted} files, {total_bytes:,} bytes\n")
            mf.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            mf.write(f"# Format: entry_index | offset | size | detected_ext | known_name\n\n")
            for i, (off, cs, us, fl) in enumerate(entries):
                name = known_names.get(i, '')
                if us == 0 or us < 4 or off + us > file_size:
                    ext = ''
                else:
                    try:
                        f.seek(off)
                        ext = detect_extension(f.read(min(64, us)))
                    except:
                        ext = ''
                mf.write(f"{i:5d} | 0x{off:012x} | {us:10d} | {ext:6s} | {name}\n")
        print(f"Manifest: {manifest_path}")

        # Write SPED path list
        paths_file = os.path.join(OUTPUT_DIR, '_sped_paths.txt')
        with open(paths_file, 'w') as pf:
            pf.write(f"# SPED Path Table ({path_count} entries)\n")
            pf.write(f"# These are resource paths from the SPED loading manifest.\n")
            pf.write(f"# The mapping to file entry indices requires the hash table.\n\n")
            for i, p in enumerate(paths):
                pf.write(f"{p}\n")
        print(f"SPED paths: {paths_file}")

        # Write file type summary
        type_counts = {}
        for i, (off, cs, us, fl) in enumerate(entries):
            if us < 4 or off + us > file_size:
                continue
            try:
                f.seek(off)
                ext = detect_extension(f.read(min(64, us)))
                type_counts[ext] = type_counts.get(ext, 0) + 1
            except:
                continue

        summary_path = os.path.join(OUTPUT_DIR, '_file_types.txt')
        with open(summary_path, 'w') as sf:
            sf.write("# File Type Summary\n\n")
            for ext, count in sorted(type_counts.items(), key=lambda x: -x[1]):
                sf.write(f"{count:6d}  {ext}\n")
        print(f"Type summary: {summary_path}")


if __name__ == '__main__':
    extract_all()

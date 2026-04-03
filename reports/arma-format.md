# ARMA v2 Archive Format Specification

**Source:** `gamedata.ara` (3,431,406,624 bytes / ~3.2 GB)  
**Game:** Dead Star (Steam AppID 366400)  
**Engine DLL:** `Engine_Steam_Release.dll` (`System\CArmatureArchive.cpp`)  
**Date:** 2026-04-03

---

## Overview

The ARMA v2 format is a flat archive used by the Armature Engine (BPE / Armature Game Studios).
Files are stored **uncompressed** with a hash-based directory for O(1) lookups by path.
Path lookup uses **FNV-1a** hashing of the **uppercase** path string (`CalculateAsUpperCaseStringFNV1a`).

---

## File Layout

```
Offset 0x00000000  Header (32 bytes)
Offset 0x00000020  Directory Hash Table (bucket pointer array)
Offset 0x00002000  Hash Bucket Data (variable-length chain entries) [CONFIRMED]
Offset 0x00020174  File Entry Table (9500 x 20 bytes = 190,000 bytes) [CONFIRMED]
Offset 0x0004E7A4  12-byte zero padding [CONFIRMED]
Offset 0x0004E7B0  File Data Region (to end of file) [CONFIRMED]
```

---

## Header (32 bytes at offset 0x00)

| Offset | Size | Type   | Value         | Description |
|--------|------|--------|---------------|-------------|
| 0x00   | 4    | char[] | `ARMA`        | [CONFIRMED] Magic bytes |
| 0x04   | 2    | uint16 | `0x0002`      | [CONFIRMED] Archive version (2) |
| 0x06   | 2    | uint16 | `0x696E`      | [UNCERTAIN] Unknown/padding ("ni" in ASCII) |
| 0x08   | 4    | uint32 | `9500`        | [CONFIRMED] Total file entry count |
| 0x0C   | 4    | uint32 | `0x00002000`  | [CONFIRMED] Offset to hash bucket data region |
| 0x10   | 4    | uint32 | `0x00020174`  | [CONFIRMED] Offset to file entry table |
| 0x14   | 4    | uint32 | `0x0004E7B0`  | [CONFIRMED] Offset to file data region |
| 0x18   | 4    | uint32 | `0x00000000`  | Reserved/zero |
| 0x1C   | 4    | uint32 | `0x00000000`  | Reserved/zero |

---

## Directory Hash Table (offset 0x20 to 0x2000)

**Size:** 8,160 bytes = 2,040 uint32 entries  
**Structure:** Array of absolute file offsets pointing into the Hash Bucket Data region.  
**Zero entries:** 622 (empty hash slots)  
**Non-zero entries:** 1,418

Each non-zero value is an **absolute file offset** to a hash bucket chain in the bucket data region (0x2000-0x20174).

### Hash Bucket Format

Each bucket is variable-length:

```
uint32  count           // Number of entries in this bucket
struct[count] {
    uint32  path_hash   // FNV-1a hash of uppercase full path (e.g., "$/GAMESCRIPTVARS.TXT")
    uint32  file_index  // Index into the File Entry Table
}
```

**Bucket sizes observed:** 4+8=12 bytes (1 entry), 4+16=20 bytes (2 entries), 4+24=28 bytes (3 entries)

[CONFIRMED] Buckets are packed contiguously. The gaps between consecutive offset values in the hash table match the expected bucket sizes (12, 20, 28 bytes = 1, 2, 3 entries respectively).

### Hash Algorithm

- **Algorithm:** FNV-1a (Fowler-Noll-Vo 1a)
- **Seed:** `0x811C9DC5` (standard FNV offset basis) [CONFIRMED in SPED header at 0x4E868]
- **Multiplier:** `0x01000193` (standard FNV prime)
- **Input:** Path string converted to **uppercase** before hashing
- **DLL function:** `CalculateAsUpperCaseStringFNV1a@HashUtils`

### Hash Table Slot Resolution [UNCERTAIN]

The slot index for a given hash is computed by some modulo or masking operation against the 2,040-slot table. The exact slot selection algorithm has not been fully determined from static analysis. The table size (2040) is not a power of 2.

**Open question:** The first-level hash table yields 2,312 file entries from 1,418 buckets. The remaining ~7,188 entries are accessible through a mechanism not yet fully decoded (possibly a second-level directory or tree structure within the bucket data region).

---

## File Entry Table (offset 0x20174)

**Entry count:** 9,500 (from header offset 0x08)  
**Entry size:** 20 bytes  
**Total size:** 190,000 bytes

| Offset | Size | Type   | Description |
|--------|------|--------|-------------|
| 0x00   | 8    | uint64 | Absolute file offset in archive |
| 0x08   | 4    | uint32 | Compressed size (bytes) |
| 0x0C   | 4    | uint32 | Uncompressed size (bytes) |
| 0x10   | 4    | uint32 | Flags (always 0x00000000 observed) |

**[CONFIRMED] All files are uncompressed.** Every entry has compressed_size == uncompressed_size and flags == 0. No zlib, gzip, lz4, or zstd magic bytes were found at file data boundaries.

### Special Entries

| Index | Offset     | Size      | Content | Path |
|-------|------------|-----------|---------|------|
| 0     | 0x0004E7B0 | 147       | [TEXT] Command line args | `$/commandlineargs.txt` |
| 1     | 0x0004E850 | 12        | [TEXT] Build version "REL-147994\r\n" | (version string) |
| 2     | 0x0004E860 | 2,167,328 | [BINARY] SPED load manifest + path table | (internal metadata) |
| 3     | 0x0025FA80 | 243       | [TEXT] Game script variables | `$/gamescriptvars.txt` |

---

## SPED Section (Entry 2)

The SPED (Speed/Preload) section contains the resource loading manifest.

### SPED Header (16 bytes at entry 2 data offset)

| Offset | Size | Type   | Value         | Description |
|--------|------|--------|---------------|-------------|
| 0x00   | 4    | char[] | `SPED`        | [CONFIRMED] Magic |
| 0x04   | 4    | uint32 | `6`           | [CONFIRMED] Version |
| 0x08   | 4    | uint32 | `0x811C9DC5`  | [CONFIRMED] FNV-1a seed (confirms hash algorithm) |
| 0x0C   | 4    | uint32 | `2`           | [UNCERTAIN] Unknown |

### Load Groups (14 groups)

After the SPED header, 14 load groups define the progressive loading order:

| Group | File Count | Cumulative Offset | Description |
|-------|-----------|-------------------|-------------|
| 0     | 14        | 0x0600            | Initial boot files |
| 1     | 48        | 0x1200            | Core engine support |
| 2     | 3         | 0x3700            | Fonts/console |
| 3     | 10        | 0x6980            | Loading screen |
| 4     | 5         | 0xC380            | Master lists |
| 5     | 6         | 0x11180           | Sound banks |
| 6     | 1         | 0x1D500           | Wreckage assets |
| 7     | 4         | 0x35B80           | Ship assets |
| 8     | 6         | 0x50980           | Effects |
| 9     | 8         | 0x6DE00           | More effects |
| 10    | 2         | 0x88B80           | Sound |
| 11    | 1         | 0xC6400           | Large asset |
| 12    | 3         | 0x13D680          | Region data |
| 13    | 0         | 0x262600          | (empty group, marks end) |

### Path Table

After the load groups and 8 bytes of zero padding:

| Offset (in file) | Size | Description |
|-------------------|------|-------------|
| 0x0004E8F0        | 4    | uint32 path_count = 11,986 |
| 0x0004E8F4        | var  | Length-prefixed path strings |

Each path entry:
```
uint8   length      // String length (1-255)
char[]  path        // ASCII path string (length bytes, no null terminator)
```

**Path format:** `$/directory/subdirectory/_win/filename.extension`  
- `$/` prefix = archive root
- `_win/` = Windows platform-specific variant
- Extensions: .cgpr (6004), .ctxr (3077), .cmat (1813), .cmdl (654), .cfpr (132), etc.

---

## File Lookup Process (Reconstructed)

1. Convert path to uppercase: `$/GAMESCRIPTVARS.TXT`
2. Compute FNV-1a hash with seed `0x811C9DC5`
3. Find hash table slot (algorithm TBD, likely hash % table_size)
4. Read bucket at the slot's offset
5. Linear search bucket entries for matching hash
6. Use file_index to read the File Entry Table
7. Seek to the entry's absolute offset and read uncompressed_size bytes

---

## Compression Detection Results

[CONFIRMED] **No compression is used.**

- All 9,500 entries have `compressed_size == uncompressed_size`
- All flags are `0x00000000`
- No zlib headers (0x78xx) found at file boundaries
- No gzip headers (0x1F8B) found
- No LZ4 frame headers (0x04224D18) found
- No Zstandard headers (0x28B52FFD) found
- The DLL references to "deflate" and "gzip" come from embedded libcurl/OpenSSL, not the archive system

---

## File Type Distribution (by 4-byte magic)

| Count | Magic | Description |
|-------|-------|-------------|
| 3,424 | POSS  | Game object property/script containers |
| 3,077 | RTXT  | Texture resources (.ctxr) |
| 1,813 | LCOL  | Collection/localization data |
| 654   | LDOM  | Model data (.cmdl) |
| 184   | !XFC  | Font/config data (.cfon, .cfpr) |
| 162   | XML   | XML-based metadata (.cmat) |
| 39    | SPED  | Speed/preload manifests |
| ~100  | (text)| Plain text configs |

---

## Key Config Files

### $/commandlineargs.txt (Entry 0, 147 bytes)
```
-vf $/GameScriptVars.txt -d $/needle_win.bpdeps -i $/needle/loaders/startup.sgpr -l $/needle/ui/loadingscreen/scripts/initial_loading_screen.sgpr
```

Flags:
- `-vf` : Variables file (GameScriptVars.txt)
- `-d`  : Dependencies file (needle_win.bpdeps)
- `-i`  : Initial loader script
- `-l`  : Loading screen script

### $/gamescriptvars.txt (Entry 3, 243 bytes)
```
r_renderer="needle";
renderConsoleOutput=0;
renderConsoleMessages=0;
needle_useMatchmaker=true;
needle_DemoMode=0;
needle_EnableClientReadyMatchStartClient=false;
needle_EnableClientReadyMatchStartServer=false;
capitalShipEnable=true;
```

**Note:** This file only contains **overrides** of default values. The full set of 483 `needle_*` variables have defaults hardcoded in `GameComponentsNeedle_Steam_Release.dll`. See `configs/needle_variables_all.txt` for the complete list.

### $/KeyboardControlDefaults.txt
**[NOT FOUND]** This file is not present in the archive. The DLL (`GameCore_Steam_Release.dll`) handles its absence gracefully with the message: "KeyboardControlDefaults.txt not found."

---

## Build Information

- **Build version:** REL-147994 (entry 1)
- **Compiler:** MSVC (cl) with /MD /Ox
- **Build path:** `E:\rel\Needle_Release\`
- **Engine:** Armature Engine (BPE - Armature Game Studios)
- **OpenSSL:** 1.0.2 (embedded)
- **Sound:** Wwise (Audiokinetic)
- **Archive implementation:** `System\CArmatureArchive.cpp`

---

## API Surface (from DLL exports)

```
CArmatureArchive::MountArchives()
CArmatureArchive::UnmountArchives()
CArmatureArchive::OpenFileFromArchives(const char* path)
CArmatureArchive::GetFileSize(const char* path)
CArmatureArchive::GetSplitFileSize(const char* path, uint32& comp, uint32& uncomp)
CArmatureArchive::GetMountedArchiveCount()
CArmatureArchiveFile::Read(void* buffer, uint32 size)
CArmatureArchiveFileBase::Seek(int64 offset, EArcSeek origin)
CArmatureArchiveFileBase::Tell()
CArmatureArchiveFileBase::GetSize()
CArmatureArchiveFileBase::Close()
```

---

## Open Questions

1. **Hash table slot selection:** The exact modulo/masking for mapping FNV-1a hash to the 2,040-slot directory table is unknown. Not a simple `hash % 2040`.
2. **Two-level directory:** Only 2,312 of 9,500 file entries are reachable through the first-level hash table. The second level (or an alternative lookup path for resource files vs. config files) needs further reverse engineering.
3. **SPED load group offsets:** The exact meaning of the cumulative offset values in load groups (whether byte offsets, entry indices, or something else) is uncertain.
4. **Bytes 6-7 of header:** Value `0x696E` ("ni") is unidentified. Could be a sub-version, flags, or part of a larger field.

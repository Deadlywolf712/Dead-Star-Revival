# RTXT Texture Format Specification

**Date:** 2026-04-03
**Analyst:** Binary Analyst Agent
**Source:** Dead Star (Steam AppID 366400), gamedata.ara archive
**Total Files Analyzed:** 3,220 .rtxt files (100% success rate on format decode)

---

## 1. Overview

RTXT is a proprietary GPU texture container format used by the BPE (Armature) engine in Dead Star. It wraps standard block-compressed (DXT/BC) and uncompressed (RGBA8) texture data with a fixed-size header and per-mip-level size metadata.

---

## 2. File Structure

```
[128-byte header]
[mip level 0: 4-byte size + pixel data, padded to 32 bytes]
[mip level 1: 4-byte size + pixel data, padded to 32 bytes]
...
[mip level N-1: 4-byte size + pixel data, padded to 32 bytes]
```

For cubemap textures (6 faces), all mip levels for face 0 come first, then face 1, etc.

---

## 3. Header Format (128 bytes, all little-endian)

| Offset | Size | Type | Field | Description |
|--------|------|------|-------|-------------|
| 0x00 | 4 | char[4] | magic | Always `RTXT` (0x52 0x54 0x58 0x54) |
| 0x04 | 4 | uint32 | version | Always 8 |
| 0x08 | 4 | uint32 | header_size | Always 128 (0x80) |
| 0x0C | 2 | uint16 | width | Texture width in pixels |
| 0x0E | 2 | uint16 | height | Texture height in pixels |
| 0x10 | 2 | uint16 | depth | Always 1 (2D textures) |
| 0x12 | 2 | uint16 | format | Pixel format ID (see table below) |
| 0x14 | 2 | uint16 | reserved1 | Always 0 |
| 0x16 | 1 | uint8 | has_alpha | 0 = no alpha channel, 1 = has alpha |
| 0x17 | 1 | uint8 | is_srgb | 0 = linear, 1 = sRGB color space |
| 0x18 | 1 | uint8 | is_cubemap | 0 = 2D texture, 1 = cubemap (6 faces) |
| 0x19 | 1 | uint8 | array_flag | 0 or 1 (related to texture arrays) |
| 0x1A | 2 | uint16 | reserved2 | Always 0 |
| 0x1C | 1 | uint8 | reserved3 | Always 0 |
| 0x1D | 1 | uint8 | mip_count | Number of mipmap levels (1-12) |
| 0x1E | 2 | uint16 | reserved4 | Always 0 |
| 0x20 | 96 | byte[96] | padding | Always zero-filled |

---

## 4. Pixel Format Table

| ID | Name | Block Size | Bytes/Block | DDS FourCC | DXGI_FORMAT |
|----|------|-----------|-------------|------------|-------------|
| 0 | RGBA8 | 1x1 pixel | 4 bytes/px | (none) | R8G8B8A8_UNORM / _SRGB |
| 6 | BC1/DXT1 | 4x4 block | 8 | `DXT1` | BC1_UNORM / _SRGB |
| 7 | BC2/DXT3 | 4x4 block | 16 | `DXT3` | BC2_UNORM / _SRGB |
| 8 | BC3/DXT5 | 4x4 block | 16 | `DXT5` | BC3_UNORM / _SRGB |
| 9 | BC5/ATI2 | 4x4 block | 16 | `ATI2` | BC5_UNORM |

### Format Distribution (3,220 files)

| Format | Count | Percentage |
|--------|-------|------------|
| BC1/DXT1 (fmt=6) | 1,828 | 56.8% |
| RGBA8 (fmt=0) | 836 | 26.0% |
| BC3/DXT5 (fmt=8) | 288 | 8.9% |
| BC2/DXT3 (fmt=7) | 142 | 4.4% |
| BC5/ATI2 (fmt=9) | 126 | 3.9% |

### sRGB Flag Distribution

- fmt=9 is always linear (is_srgb=0) -- these are normal maps
- fmt=0,6,7,8 are mostly sRGB (is_srgb=1)

---

## 5. Mip Level Data Structure

Each mip level is stored as:

```
[4 bytes] uint32 LE: raw pixel data size for this mip level
[N bytes] raw pixel data
[P bytes] zero padding to align total (4 + N + P) to 32-byte boundary
```

The formula for total bytes per mip entry:
```
entry_size = align32(4 + raw_data_size)
where align32(x) = (x + 31) & ~31
```

### Raw Data Size Calculation

For **block-compressed** formats (BC1-BC5):
```
blocks_w = max(1, ceil(width / 4))
blocks_h = max(1, ceil(height / 4))
raw_size = blocks_w * blocks_h * bytes_per_block
```

For **uncompressed** RGBA8:
```
raw_size = width * height * 4
```

### Mip Dimensions

Each subsequent mip level halves both dimensions (minimum 1):
```
mip_width  = max(1, width >> mip_level)
mip_height = max(1, height >> mip_level)
```

---

## 6. Cubemap Layout

When `is_cubemap = 1`, the file contains 6 faces in standard cubemap order:
1. +X (right)
2. -X (left)
3. +Y (top)
4. -Y (bottom)
5. +Z (front)
6. -Z (back)

Each face contains all mip levels in sequence, then the next face follows.

Only 5 files in the dataset are cubemaps (all BC1/DXT1 format).

---

## 7. Conversion to DDS

To convert RTXT to DDS:

1. Read the 128-byte RTXT header
2. Write a standard 128-byte DDS header (or 148 bytes with DX10 extension for BC5)
3. For each mip level, read the 4-byte size prefix, then copy the raw pixel data (skip padding)
4. Concatenate all mip pixel data after the DDS header

The key difference is that DDS stores mip data contiguously without per-mip size prefixes or alignment padding.

---

## 8. Validation

The format was validated against all 3,220 .rtxt files:
- **3,215 files** (99.84%): exact byte-perfect match with computed sizes
- **5 files** (0.16%): cubemaps -- also match when accounting for 6 faces

Zero unknown or malformed files were encountered.

# POSS (Property Object Serialization Stream) Format Specification

**Date:** 2026-04-03
**Source:** Dead Star (Steam AppID 366400), gamedata.ara archive
**Engine:** Armature Engine (BPE / Armature Game Studios)
**DLL:** `Engine_Steam_Release.dll` (`Script\CScriptVar.cpp`, `CGameObjectPropertiesPackage`)
**Total Files:** 3,331 .poss files + 3,178 .cgpr files (100% parse success rate)

---

## 1. Overview

POSS is a binary serialization format used by the BPE engine to store **CGameObjectPropertiesPackage** containers. Each file represents a hierarchical tree of game objects, where each game object has a unique GUID, a name, and one or more components. Components contain transform data, property values, messages, and links.

File extensions using this format:
- `.poss` (compiled property object, generic)
- `.cgpr` (compiled game property resource)
- `.sgpr` (compiled script game property resource)

The POSS format is the **single largest file type** in Dead Star's archive (3,424 files by magic, ~36% of all files). It contains all game object definitions: ships, weapons, UI screens, cameras, effects, drones, structures, resource generators, and more.

---

## 2. File Structure Overview

```
[File Header]           12 bytes
[Shared String Table]   variable (varint-prefixed strings)
[Root Game Object]      variable
  [Components...]       variable (one per component)
[Child Game Objects...] variable (recursive, same structure as root)
```

All multi-byte integers are **little-endian** unless noted.
Strings use **.NET-style 7-bit encoded integer** length prefix (LEB128 varint).

---

## 3. File Header (12 bytes)

| Offset | Size | Type    | Value       | Description |
|--------|------|---------|-------------|-------------|
| 0x00   | 8    | char[8] | `POSS30RV`  | [CONFIRMED] Magic bytes (ASCII) |
| 0x08   | 4    | uint32  | varies      | [CONFIRMED] String table entry count |

- **Magic:** Always the 8-byte ASCII string `POSS30RV`. The "30RV" likely encodes a format version.
- **String Count:** Number of entries in the shared string table that follows immediately.

---

## 4. Shared String Table (offset 0x0C)

Immediately after the header, `string_count` strings are stored sequentially. Each string is encoded as:

```
[varint: byte_length] [UTF-8 bytes: byte_length]
```

The varint uses .NET's `Read7BitEncodedInt` encoding (LEB128):
- Bytes 0x00-0x7F: single byte, value = byte
- Bytes 0x80+: continuation bit in bit 7, value bits in bits 0-6, next byte continues

Empty strings have `byte_length = 0` (single 0x00 byte, no data bytes).

### String Types Observed

| Category | Count | Description |
|----------|-------|-------------|
| Resource paths | ~55,000 | `$/needle/.../*.ctxr`, `.cmdl`, `.cgpr`, etc. |
| Event/signal names | ~12,000 | `Needle_ShowLobby`, `play_turret_base_turning`, etc. |
| Localization keys | ~4,000 | `~LOBBY_NEEDLE_NEXT_MATCH~`, `~PLAYER_LEVEL~`, etc. |
| Script snippets | ~500 | `restartGame=true;`, `(%d / %d)`, etc. |
| Empty strings | ~3,300 | Zero-length placeholder at index 0 |

The string table serves as a **deduplication pool** -- strings referenced by components point into this table by index (via shared_string in the engine).

---

## 5. Game Object Structure

After the string table, the root game object and its children are serialized. Each game object has the following layout:

### Object Header

| Offset | Size | Type   | Description |
|--------|------|--------|-------------|
| +0x00  | 4    | uint32 | Reserved (always 0) |
| +0x04  | 4    | uint32 | Total component count across entire object tree (root only; 0 for children) |
| +0x08  | 4    | uint32 | Format version (always 6) |
| +0x0C  | 16   | GUID   | TGameObjectEditorId (Microsoft GUID, LE u32+u16+u16+8bytes) |
| +0x1C  | var  | string | Object name (varint-prefixed UTF-8) |

After the name, two additional uint32 fields follow:

| Offset     | Size | Type   | Description |
|------------|------|--------|-------------|
| after_name | 4    | uint32 | Field A (purpose uncertain; often 0, sometimes small integer) |
| +4         | 4    | uint32 | Field B (purpose uncertain; correlates loosely with component complexity) |

### GUID Format

GUIDs are stored in Microsoft's mixed-endian format:
```
bytes 0-3:  uint32 LE  (data1)
bytes 4-5:  uint16 LE  (data2)
bytes 6-7:  uint16 LE  (data3)
bytes 8-15: 8 bytes    (data4, big-endian)
```

All observed GUIDs are UUID version 4 (random) or version 5 (SHA-1 name-based).

### Object Hierarchy

Children are serialized **after** the parent's components, as siblings in the byte stream. The parser detects child objects by looking for the `[0, X, 6]` header pattern followed by a valid version-4/5 GUID.

---

## 6. Component Structure

Each game object contains one or more **CGameObjectComponentProperties** entries.

### Component Header

| Offset | Size | Type   | Value         | Description |
|--------|------|--------|---------------|-------------|
| +0x00  | 4    | uint32 | `0xC029451E`  | [CONFIRMED] Component type marker (constant across all files) |
| +0x04  | 9    | bytes  | varies        | TComponentEditorId supplementary bytes |
| +0x0D  | 16   | GUID   | varies        | Component instance GUID |

The 9-byte `editor_id_bytes` field has a mostly constant pattern:
```
XX 00 77 e7 6d e0 YY 00 01
```
Where `XX` varies (0x61, 0x68, 0x88, 0xE0) and `YY` varies (0x51, 0x58, 0x5B).

### Component Body

After the header, the component body is a variable-length binary blob containing:

1. **Transform data** (when present, identified by hash `0xFB4A7A5F`)
2. **Property values** (typed data: floats, ints, bools, string indices)
3. **Message handlers** (event routing between components)
4. **Links** (references to other components by TComponentId)

#### Transform Data Layout

Most components begin their body with a fixed prefix:

```
XX 00                           # 2 bytes (XX varies: 0x01, 0x02)
5F 7A 4A FB                     # 4 bytes: hash identifier (0xFB4A7A5F)
38 00                           # 2 bytes: u16 = 56 (sub-type or flags)
01 00                           # 2 bytes: u16 = 1 (version)
0E 03 43 F5                     # 4 bytes: hash identifier (0xF543030E)
30 00                           # 2 bytes: u16 = 48 (float data size = 12 * 4)
[12 x float32]                  # 48 bytes: transform data
```

The 12 floats are arranged in 3 groups of 4. For identity transforms:
```
Group 0: [1.0, 0.0, 0.0, 0.0]
Group 1: [1.0, 0.0, 0.0, 0.0]
Group 2: [1.0, 0.0, 0.0, 0.0]
```

For non-identity transforms, the groups contain rotation/scale/translation data. [UNCERTAIN] The exact decomposition (row-major, column-major, quaternion, Euler, etc.) has not been fully determined. The last float in each group may represent translation (x, y, z) when rotation is present.

---

## 7. CInputStream API (from DLL exports)

The serialization uses these read methods from `CInputStream`:

| Method | Bytes | Description |
|--------|-------|-------------|
| `Read7BitEncodedInt` | 1-5 | LEB128 unsigned varint |
| `ReadString` | varint + N | Varint length + UTF-8 bytes |
| `ReadBool` | 1 | Boolean (0/1) |
| `ReadInt8` / `ReadUint8` | 1 | Signed/unsigned byte |
| `ReadInt16` / `ReadUint16` | 2 | LE int16/uint16 |
| `ReadInt32` / `ReadUint32` | 4 | LE int32/uint32 |
| `ReadInt64` / `ReadUint64` | 8 | LE int64/uint64 |
| `ReadReal32` | 4 | LE float32 (IEEE 754) |
| `ReadReal64` | 8 | LE float64 (IEEE 754) |
| `ReadCStyleString` | N+1 | Null-terminated string |
| `AlignReadPosition` | 0-7 | Align stream to boundary |

---

## 8. Key Classes (from DLL symbol analysis)

```
CGameObjectPropertiesPackage       # Top-level container (= POSS file)
  CGameObjectPropertiesPackageEntry  # One entry per game object
    CGameObjectProperties            # Object header (GUID, name, version)
    CGameObjectComponentProperties   # Per-component data
      TComponentEditorId             # Component type + instance GUID
      StaticProperties               # Fixed property values
      AddMessagesAndLinks()          # Event handlers and component links
    FChildGameObjectProperties()     # Recursive children
  CGameObjectApplyPropertiesData     # Property application context
CScriptVar                          # Runtime script variable system
  CScriptVarCachedBool/Int/Real/String  # Typed cached variables
```

---

## 9. Content Distribution

### Object Types (top 20 from 3,331 files)

| Count | Object Name | Description |
|-------|-------------|-------------|
| 2,520 | ShipResources | Ship paint/skin resource packages |
| 137 | MergedNode | Merged scene graph nodes |
| 66 | Sector Border (Editor Visual) | Sector boundary visualizations |
| 64 | PortraitResources | Player portrait textures |
| 49 | Ship (Base) | Ship base definitions |
| 43 | Sector Generator | Procedural sector generators |
| 30 | Turret (Base) | Weapon turret definitions |
| 29 | Nebula - Visual Archetype Mappings | Nebula visual configs |
| 27 | Destruction - Ship (Base) | Ship destruction sequences |
| 21 | Structure (Base) | Space structure definitions |
| 19 | Asteroid (Base) | Asteroid object definitions |
| 19 | Region Event - CometStorm | Comet storm event controllers |
| 19 | Resource Generator (Base) | Resource node generators |
| 16 | CameraGroup_Manager | Camera system managers |
| 13 | Structure Node (Base) | Structure component nodes |
| 11 | RegionEventPiratesSpawners | Pirate wave spawners |
| 10 | Asteroid Loader | Asteroid streaming loaders |
| 10 | Hangar - Ship Model | Hangar ship display models |

### Referenced Resource Types

| Count | Extension | Description |
|-------|-----------|-------------|
| 13,860 | .ctxr | Texture resources (RTXT format) |
| 9,627 | .cmdl | 3D model data (LDOM format) |
| 8,563 | .cgpr | Nested game property files (POSS format) |
| 3,515 | .cmat | Material definitions (XML format) |
| 1,926 | .cloc | Localization string tables (LCOL format) |
| 1,807 | .cskn | Skinned mesh data |
| 1,734 | .cfpr | Font/config property files (!XFC format) |
| 1,692 | .csif | Scene instance files |
| 1,092 | .ccol | Collision mesh data |
| 922 | .cfon | Font files |
| 876 | .cani | Animation data |
| 679 | .cwwu | Wwise sound bank references |
| 72 | .cesm | Engineer scripting modules (AI) |

---

## 10. Parser

A Python parser is available at:
```
Revival Assets/assets/parse_poss.py
```

Usage:
```bash
# Parse single file
python3 parse_poss.py file.poss
python3 parse_poss.py file.poss --json
python3 parse_poss.py file.poss --hex-dump --verbose

# Batch process
python3 parse_poss.py --batch directory/ --output output_dir/
```

**Validation:** Parser successfully reads 100% of POSS files (3,331 .poss + 3,178 .cgpr = 6,509 files, 0 failures).

---

## 11. Open Questions

1. **Transform matrix decomposition:** The 12 floats after the transform hash prefix have an uncertain geometric interpretation. They are NOT a standard row-major or column-major 3x3+translation matrix. May be a custom scale/rotation/position encoding specific to the BPE engine.

2. **Component body property decoding:** After the transform data, components contain additional binary data (property values, message handlers, links) whose exact field-by-field layout is type-dependent. The component type hash `0xC029451E` is constant, suggesting the differentiation comes from the property data itself rather than the component header.

3. **Field A and Field B after object name:** Two uint32 values follow each object's name. Field A is almost always 0 (occasionally 1). Field B varies and seems to correlate with the complexity of the object's component data, but does not directly map to component count.

4. **Editor ID supplementary bytes:** The 9 bytes between the component type marker and the GUID have a mostly-constant pattern. The varying bytes (positions 0 and 6) may encode component sub-type information or version flags.

5. **String table referencing:** While the string table is a deduplication pool, the exact mechanism by which component bodies reference strings (by index, by hash, or by inline embedding) needs further investigation.

6. **Child object count:** There is no explicit field storing the number of child objects. The parser discovers children by pattern-matching the `[0, X, 6, GUID]` header signature. The root object's `total_components` field counts components across the entire tree.

# XFC Format Specification (!XFC)

## Overview

XFC is a **compiled shader effect** format used by the Dead Star engine (Armature Studio's custom engine). The magic bytes `!XFC` stand for "compiled effect" (eXternal/eFFect Compiled). Each XFC file contains:

- Blend/render state descriptors per shader combination (permutation)
- Depth/stencil state configuration
- Compiled DXBC (DirectX Bytecode) shader blobs (vertex + pixel shaders)
- Shader combination hash lookup table

The engine class is `Effect_Win32` with `EffectCombination_Win32` per permutation, loaded via `FEffectFactory`. The "count" field is the number of shader **combinations** -- permutations of compile-time defines like `BLENDMODE`, `DEPTHCHECK`, `DEPTHWRITE`, `SKINNED`, `INSTANCED`, etc.

## File Statistics

- **39 files** in the Dead Star archive (entries 10-48)
- Sizes range from **1,220 bytes** (1 combination) to **518,036 bytes** (3,200 combinations)
- All version 2
- No named paths in archive (loaded by index)

## Referenced Shader Sources (from DLL strings)

```
$/enginesupport/shaders/Default.fx
$/enginesupport/shaders/NeedleCharacter.fx
$/enginesupport/shaders/NeedleEffect.fx
$/enginesupport/shaders/NeedleEnvironment.fx
$/enginesupport/shaders/NeedleEnvironmentBlended.fx
$/enginesupport/shaders/NeedleEnvironmentLayered.fx
$/enginesupport/shaders/NeedleMask.fx
$/enginesupport/shaders/NeedleUI.fx
$/enginesupport/shaders/NeedleUIInternal.fx
$/enginesupport/shaders/OzzyTransparent.fx
$/enginesupport/shaders/PostProcess.fx
$/enginesupport/shaders/UnlitGeneric.fx
$/enginesupport/shaders/VertexLitGeneric.fx
$/enginesupport/shaders/FullScreen.fx
$/enginesupport/shaders/EditorBillboard.fx
```

## Header (48 bytes)

| Offset | Size | Type   | Field                |
|--------|------|--------|----------------------|
| 0x00   | 4    | char[] | Magic: `!XFC`        |
| 0x04   | 4    | uint32 | Version (always 2)   |
| 0x08   | 4    | uint32 | Combination count    |
| 0x0C   | 4    | uint32 | Section 0 offset     |
| 0x10   | 4    | uint32 | Section 1 offset     |
| 0x14   | 4    | uint32 | Section 2 offset     |
| 0x18   | 4    | uint32 | Section 3 offset     |
| 0x1C   | 4    | uint32 | Section 4 offset     |
| 0x20   | 4    | uint32 | Section 5 offset     |
| 0x24   | 4    | uint32 | Section 6 offset     |
| 0x28   | 4    | uint32 | Section 7 offset     |
| 0x2C   | 4    | uint32 | Section 8 offset     |

All offsets are absolute from file start. The header itself occupies bytes 0x00-0x2F (48 bytes), so Section 0 always starts at offset 0x30.

## Section 0: Blend/Render State Array (variable size)

Contains per-combination blend state descriptors. Each combination has a variable-length record of byte-level render state enums. The byte values observed are limited to 0-8 and 0xFF, consistent with D3D11 blend mode / render state enumerations:

- **0** = disabled/zero/opaque
- **1-8** = various blend factors / operations
- **0xFF** = unset/default sentinel
- **0xFFFF** = section separator within record
- **0xFFFFFFFF** = record terminator

Record size varies per file (typically 48-52 bytes per combination). Records contain:
- Blend enable flags
- Source/destination blend factors
- Blend operations
- Color write masks
- Alpha blend configuration

The combination hash table (Section 1) provides byte offsets into this section.

## Section 1: Combination Hash Table (8 bytes per combination)

| Offset | Size | Type   | Field                          |
|--------|------|--------|--------------------------------|
| 0      | 4    | uint32 | Combination hash               |
| 4      | 4    | uint32 | Byte offset into Section 0     |

The hash is used by `GetCombinationByHash()` for runtime lookup. The engine computes a hash from the current shader define permutation string (e.g., `"DEPTHCHECK=1;DEPTHWRITE=1;BLENDMODE=0"`) and looks up the matching combination.

## Section 2: Shader Blob Descriptor Table (variable size)

Array of (offset, size) pairs describing DXBC shader blobs within Section 7:

| Offset | Size | Type   | Field                              |
|--------|------|--------|------------------------------------|
| 0      | 4    | uint32 | DXBC blob offset in Section 7      |
| 4      | 4    | uint32 | DXBC blob size in bytes            |

Repeated for each unique shader blob. The last pair typically describes the shared input signature blob (at offset 0 in Section 7). Shader types include:

- **Input Signature** (ISGN only, no SHEX) -- shared vertex input layout
- **Vertex Shader** (ISGN + OSGN + SHEX, shader model 5.0)
- **Pixel Shader** (ISGN + OSGN + SHEX, shader model 5.0)

## Section 3: Depth/Stencil State (variable, 0-64 bytes)

Per-effect depth and stencil test configuration. Contains uint32 values for depth compare function, stencil operations, and float values for depth range:

- `0xFF7FFFFF` = `-FLT_MAX` (depth range min)
- `0x7F7FFFFF` = `+FLT_MAX` (depth range max)
- `0xFFFFFFFF` = sentinel/terminator

May be empty (0 bytes) for effects that don't use depth testing.

## Section 4: Depth Test Configuration (always 48 bytes)

Fixed-size depth test parameters:

| Index | Typical Values | Meaning                |
|-------|----------------|------------------------|
| 0-1   | 3, 3           | Depth compare func     |
| 2-5   | 0              | Reserved               |
| 6     | 1              | Depth write enable     |
| 7-9   | 0              | Reserved               |
| 10-11 | 0xFFFFFFFF     | Terminator             |

## Section 5: Stencil Configuration (typically 64 bytes)

Stencil test parameters including front/back face operations:

- Stencil reference value
- Stencil read/write masks
- Front face: compare func, pass op, fail op, depth fail op
- Back face: same
- `0xFFFF` = stencil mask sentinel

## Section 6: Sampler/Texture State Table (typically 272 bytes)

Repeating 36-byte records describing texture sampler states for up to 8 texture slots. Each record contains:

| Index | Meaning                           |
|-------|-----------------------------------|
| 0     | Padding/separator (0)             |
| 1     | Sampler type/dimension            |
| 2     | Min filter                        |
| 3     | Mag filter                        |
| 4     | Mip filter                        |
| 5     | Address mode U                    |
| 6     | Address mode V                    |
| 7     | Max anisotropy or mip levels      |
| 8     | Terminator (0 or 0xF)             |

Terminated by `0xFFFFFFFF 0xFFFFFFFF`.

## Section 7: DXBC Shader Blob Data (variable, largest section)

Raw concatenated DXBC (DirectX Bytecode) shader blobs. Each blob starts with `DXBC` magic and is a standard compiled HLSL shader. Blob positions are described by Section 2.

Typical blob layout:
1. Shared input signature blob (ISGN only)
2. Vertex shader blob(s) (ISGN + OSGN + SHEX)
3. Pixel shader blob(s) (ISGN + OSGN + SHEX)

All shaders are Shader Model 5.0 (`_5_0`). The SHEX chunks contain standard DXBC instruction opcodes.

## Section 8: Effect Metadata Footer (always 20 bytes)

| Offset | Size | Type  | Field                          |
|--------|------|-------|--------------------------------|
| 0      | 1    | uint8 | Number of VS blobs             |
| 1      | 1    | uint8 | Padding (always 0)             |
| 2      | 1    | uint8 | Number of unique DXBC blobs    |
| 3      | 1    | uint8 | Padding (always 0)             |
| 4-11   | 8    | -     | Reserved (zeros)               |
| 12     | 1    | uint8 | Has input signature            |
| 13     | 1    | uint8 | Number of PS blob variants     |
| 14     | 1    | uint8 | Has vertex shader              |
| 15     | 1    | uint8 | Max texture slot used          |
| 16     | 1    | uint8 | Has pixel shader               |
| 17-19  | 3    | -     | Reserved (zeros)               |

## Relationship to Renderer

The `Effect_Win32` class in `Renderer_Steam_Release.dll` loads XFC files through `FEffectFactory`. Each effect corresponds to one `.fx` shader source file. The combination system allows runtime selection of the correct shader permutation based on material properties (`CMaterialFlags`) without recompiling shaders.

The `CShader` base class uses `GetBlendMode()` to select the appropriate `EffectCombination_Win32` from the loaded effect. The combination hash encodes the current set of shader defines.

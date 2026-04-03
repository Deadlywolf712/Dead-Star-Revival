# LCOL Format Specification (Localization Collection)

## Overview

LCOL is the **localization table** format used by the Dead Star engine. The magic bytes `LCOL` correspond to the engine class `CLocalizationTable` (found in `Engine_Steam_Release.dll`, source: `Mechanics\CLocalizationTable.cpp`).

Each LCOL file stores a collection of key-value string pairs across multiple languages. The engine supports up to 27 locale slots mapped to 7 unique language indices. Keys can differ per language (enabling region-specific content), though most files share the same key across all languages.

## File Statistics

- **33 files** in the Dead Star archive
- Sizes range from **583 bytes** (1 key, 8 strings) to **518,604 bytes** (115 keys, 874 strings)
- All version 8
- Languages: English (0), French (1), German (2), Italian (3), Portuguese (4), Spanish (5), Russian (6)
- Some files are English-only (1 language), most have all 7

## Engine API

```cpp
class CLocalizationTable {
    static void FLocFactory(SFactoryResourceBuildData&, SFactoryReturnResource&);
    const shared_string& GetLocTableEntry(bool*, ESystemRegion, ELanguage, const shared_string& key);
    const vector<STimedString>* GetLocTableTimingListOrNull(ESystemRegion, ELanguage, const shared_string& key);
};
```

Components: `CComponentLocalization`, `CComponentLocalizationArray` provide game object access.

## File Layout

```
[Header]                    12 bytes
[Language Map]              num_lang_slots * 4 bytes
[String Count]              4 bytes
[String Blocks]             variable (repeated)
[Key Lookup Footer]         variable
```

## Header (12 bytes)

| Offset | Size | Type   | Field                          |
|--------|------|--------|--------------------------------|
| 0x00   | 4    | char[] | Magic: `LCOL`                  |
| 0x04   | 4    | uint32 | Version (always 8)             |
| 0x08   | 4    | uint32 | Number of locale slots (always 27) |

## Language Map (108 bytes)

27 uint32 values mapping each locale slot to a language index (0-6).

Observed mapping pattern (repeats 3 times for 3 system regions):
```
Slot  0: lang 0 (English)     Slot  9: lang 0 (English)    Slot 18: lang 0 (English)
Slot  1: lang 0 (English)     Slot 10: lang 0 (English)    Slot 19: lang 0 (English)
Slot  2: lang 1 (French)      Slot 11: lang 1 (French)     Slot 20: lang 1 (French)
Slot  3: lang 2 (German)      Slot 12: lang 2 (German)     Slot 21: lang 2 (German)
Slot  4: lang 3 (Italian)     Slot 13: lang 3 (Italian)    Slot 22: lang 3 (Italian)
Slot  5: lang 4 (Portuguese)  Slot 14: lang 4 (Portuguese) Slot 23: lang 0 (English)*
Slot  6: lang 5 (Spanish)     Slot 15: lang 5 (Spanish)    Slot 24: lang 5 (Spanish)
Slot  7: lang 0 (English)     Slot 16: lang 0 (English)    Slot 25: lang 0 (English)
Slot  8: lang 6 (Russian)     Slot 17: lang 6 (Russian)    Slot 26: lang 6 (Russian)
```

*Slot 23 maps to English instead of Portuguese in some region configurations.

The 3 groups of 9 correspond to `ESystemRegion` values (NA, EU, Asia or similar). The engine resolves `(ESystemRegion, ELanguage)` -> language index via this map.

## String Count (4 bytes)

| Offset | Size | Type   | Field                          |
|--------|------|--------|--------------------------------|
| 0x78   | 4    | uint32 | Total number of string blocks  |

This is the total count of ALL strings (keys + values across all languages).

## String Blocks (repeated)

Each string block:

| Field   | Size     | Type    | Description                        |
|---------|----------|---------|------------------------------------|
| Prefix  | 4        | uint32  | Always 1 (reserved/type marker)    |
| Length  | 1-2      | varint  | String byte length (LEB128)        |
| Data    | (length) | utf-8   | String content                     |
| Padding | 8        | zeros   | Fixed 8-byte null terminator pad   |

### String Length Encoding (LEB128 Varint)

The string length uses unsigned LEB128 variable-length integer encoding:

- If the first byte has bit 7 clear (< 128): length = that byte (1 byte consumed)
- If the first byte has bit 7 set (>= 128): length = (byte0 & 0x7F) | (byte1 << 7) (2 bytes consumed)
- Theoretically extends to more bytes, but in practice max observed is 2 bytes (max length ~16383)

Examples:
- `0x17` = 23 bytes (single byte, bit 7 clear)
- `0xE5 0x02` = (0x65) | (0x02 << 7) = 101 + 256 = 357 bytes

### String Content

Strings are UTF-8 encoded. Content includes:
- Localization keys: `AUGMENT_BUTTON_TEXT`, `SHIP_RACEA_FRIGATE_NAME`, etc.
- Localized values: plain text, color markup (`%BLUE_TEXT_COLOR%`), button refs (`%BUTTON_CONFIRM%`), newlines
- Color codes: `#r255#` prefix format
- Variable references: `%VARIABLE_NAME%` substitution markers

## Key Lookup Footer

Located after all string blocks:

| Field          | Size | Type   | Description                        |
|----------------|------|--------|------------------------------------|
| num_languages  | 4    | uint32 | Number of language columns stored  |
| num_keys       | 4    | uint32 | Number of key entries              |

Followed by `num_keys` key records, each containing `num_languages` pairs:

| Field          | Size | Type   | Description                        |
|----------------|------|--------|------------------------------------|
| key_string_idx | 4    | uint32 | Index into string block array (key)|
| val_string_idx | 4    | uint32 | Index into string block array (val)|

Each key record has `num_languages` such pairs. The pair at position `i` corresponds to language index `i`. Different languages CAN have different key strings (the key_string_idx may differ per language), though in practice most share the same key.

### Footer Size Formula

```
footer_bytes = 8 + num_keys * num_languages * 8
```

### Example (7 languages, 1 key)

```
Footer: [7, 1, 0, 1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0, 7]
  num_languages = 7
  num_keys = 1
  key[0]:
    lang 0 (English):    key=string[0], val=string[1]
    lang 1 (French):     key=string[0], val=string[2]
    lang 2 (German):     key=string[0], val=string[3]
    lang 3 (Italian):    key=string[0], val=string[4]
    lang 4 (Portuguese): key=string[0], val=string[5]
    lang 5 (Spanish):    key=string[0], val=string[6]
    lang 6 (Russian):    key=string[0], val=string[7]
```

## Language Enum (ELanguage)

Based on DLL strings and LCOL data:

| Index | Language   | Code |
|-------|------------|------|
| 0     | English    | en   |
| 1     | French     | fr   |
| 2     | German     | de   |
| 3     | Italian    | it   |
| 4     | Portuguese | pt   |
| 5     | Spanish    | es   |
| 6     | Russian    | ru   |

The DLL also references Dutch and Japanese, but these do not appear in the shipped LCOL data (likely cut before release).

## Content Categories

Based on parsed key names:

- **UI Text**: AUGMENT_*, CONTRACT_*, CAREER_*, CONQUEST_*
- **Ship Names**: SHIP_RACEA_FRIGATE_NAME (VINDICATOR), SHIP_RACEB_RAIDER_NAME (STALKER), etc.
- **Game Systems**: SYSTEM_0_NAME (Core), SYSTEM_1_NAME (weapons), rank descriptions
- **DLC Content**: DLC_DEC_RACEAA (Ordo Robots Pack), DLC_SHIP_RACED (Kurg Ship Expansion)
- **Credits**: CREDITS_ARMATURE_HEADING_*, CREDITS_ARMATURE_PEOPLE_* (with full staff lists)
- **HUD/Controls**: SYS0_ANALOG_LEFT_DESC, button mappings
- **Level Data**: Per-level localization in entries 05308-07542 (ship stats, ability descriptions)

## Validation

All 33 LCOL files parse to exact byte completion with the varint + 8-byte padding format. No orphan bytes, no truncation.

# New .Z File Format Knowledge from Zorkie

Notes compiled from reviewing zorkie (ZILF to .z compiler) changes since zwalker was last updated (December 19, 2025). Zorkie has 50+ commits with significant .z format insights.

## 1. Header Extension Table (V5+)

**Header byte $36-37**: Points to extension table address.

The extension table format:
- Word 0: Number of extension words following (N)
- Word 1: Mouse X coordinate after click (runtime, init to 0)
- Word 2: Mouse Y coordinate after click (runtime, init to 0)
- Word 3: Unicode translation table address (if present)

The extension table lives in **dynamic memory** (writable at runtime) because mouse coordinates are written by the interpreter.

Zorkie builds minimal extension tables (2 bytes with count=0) even when not using extended features, because some interpreters (bocfel) read the entry count even when address=0.

## 2. Unicode Translation Table (V5+)

For V5+, characters outside basic ZSCII (codes > 154) use a Unicode extension table. The table maps ZSCII codes 155-251 to Unicode code points.

**Table format**:
- Located at address stored in extension table word 3
- Contains Unicode code points (2 bytes each) for ZSCII 155+
- Maximum 97 entries (ZSCII 155-251)

**Encoding flow**:
1. When encoding text with extended characters (ä, ö, ü, ß, etc.)
2. Assign each unique Unicode code point to next available ZSCII code (starting at 155)
3. Use ZSCII escape sequence (shift-to-A2, z-char 6, 10-bit ZSCII) to encode
4. Interpreter uses Unicode table to decode ZSCII → display character

**Validation**: V1-V4 cannot represent characters > ZSCII 154. Zorkie raises error ZIL0414.

## 3. Custom Alphabet Tables (V5+)

**Header byte $34-35**: Points to custom alphabet table (78 bytes, 3×26 characters).

CHRSET directive (`<CHRSET n "alphabet">`) allows custom character sets:
- CHRSET 0: Custom A0 alphabet (lowercase)
- CHRSET 1: Custom A1 alphabet (uppercase)
- CHRSET 2: Custom A2 alphabet (punctuation)

Each alphabet is 26 characters. The interpreter uses this table for Z-text decoding.

## 4. German Language Support

LANGUAGE directive (`<LANGUAGE GERMAN>`) enables:
- German escape sequences in strings: `%o` → ö, `%a` → ä, `%u` → ü, `%s` → ß
- German custom alphabets with umlauts in A0/A1
- Unicode to ZSCII mapping for alphabet characters

The compiler processes `%X` escape sequences before text encoding.

## 5. V7 vs V8 Packed Address Details

**V6-7 packed addressing** (more complex than V5/V8):
- Routine: `4P + 8×R_O` where R_O is from header $28-29
- String: `4P + 8×S_O` where S_O is from header $2A-2B

**V8 packed addressing** (simpler):
- Both routines and strings: `8P`

V7 requires 4-byte padding before first routine (so packed address 0 is never valid). V8 doesn't need this.

**String alignment by version**:
- V1-5: 2-byte alignment
- V6-7: 4-byte alignment
- V8: **8-byte alignment** (important for packed address calculation)

## 6. V7 Initial PC Handling

V7 differs from V6 and V8 in the initial PC:
- V1-5: Header $06-07 contains byte address of first instruction
- V6: Header $06-07 contains packed address of main routine
- V7: Same as V6 but with offset-based packed addressing
- V8: Header $06-07 contains packed address (8P formula)

## 7. Dictionary Location in Memory

Critical discovery: **Dictionary MUST be in static memory** for strict interpreters like bocfel.

Memory layout:
```
Dynamic Memory:
  - Header (64 bytes)
  - Globals
  - Objects
  - Impure tables (writable tables)
  - Extension table (V5+)
Static Memory (starts at header $0E-0F):
  - Pure tables (read-only)
  - Alphabet table (V5+)
  - Dictionary
High Memory (starts at header $04-05):
  - Routines
  - Strings
```

## 8. Property Table Improvements

### Property Routine Placeholders

When object properties reference routines (like ACTION handlers):
- Compiler detects routine names in property values
- Creates `0xFA00 | idx` placeholders in property data
- Assembler resolves to packed routine addresses after high_mem_base is known

### PROPDEF/PROPSPEC Pattern Types

Property definition patterns support:
- WORD: 2-byte value
- BYTE: 1-byte value
- ROOM: Object number (1 byte in V3, 2 bytes V4+)
- OBJECT: Object number
- VOC: Dictionary word address (requires placeholder resolution)

The MANY modifier allows repeating pattern elements.

## 9. Vocabulary Word Placeholders

For resolving W?* (vocabulary word) references:
- `0xFB00 | idx` placeholders in routine bytecode
- `0xFA00` (VOCAB) placeholder for dictionary base address in globals
- Assembler resolves these to actual dictionary word addresses

NEW-PARSER? mode generates VWORD tables (14 bytes per word):
- lexical-word, classification, flags, semantic-stuff, verb-stuff, adj-id, dir-id

## 10. String Placeholder Ranges

Zorkie uses different placeholder ranges to avoid collision:
- **TELL strings**: `0xE000-0xFFFD` (8190 slots)
- **String operands**: `0xFC00-0xFCFF` (256 slots)
- **Routine calls**: `0xFD00-0xFDFF` (256 slots, deduplicated)
- **Vocab words**: `0xFB00-0xFBFF` (256 slots)
- **Table addresses**: `0xFF00-0xFFFF` (256 slots)

## 11. LOWCORE-TABLE Header Field Iteration

`LOWCORE-TABLE` is a builtin for iterating over header bytes. This reveals which header fields are commonly accessed:

Common header fields:
- Byte $00: Version
- Bytes $04-05: High memory base
- Bytes $06-07: Initial PC / Main routine
- Bytes $08-09: Dictionary address
- Bytes $0A-0B: Object table address
- Bytes $0C-0D: Globals table address
- Bytes $0E-0F: Static memory base
- Bytes $18-19: Abbreviations table
- Bytes $34-35: Alphabet table (V5+)
- Bytes $36-37: Extension table (V5+)

## 12. Version-Specific Opcode Details

### COLOR Opcode (V5+)
- Extended opcode: `0xBE 0x1B` (EXT:27)
- NOT VAR:27 as might be expected

### V6-7 Routines Padding
- 4-byte padding before first routine required
- Ensures packed address 0 is never a valid routine
- `packed = (4 + routine_offset) / 4`

## 13. SENTENCE-ENDS? Text Feature

When SENTENCE-ENDS? is enabled:
- Punctuation (`.`, `!`, `?`) followed by two spaces gets special handling
- The second space becomes ZSCII 0x0B (sentence space)
- Exception: Punctuation before newline gets normal spaces

## 14. Checksum Calculation Reminder

```python
def calculate_checksum(data: bytes) -> int:
    return sum(data[0x40:]) & 0xFFFF  # Sum bytes after 64-byte header
```

Header byte $1C-1D stores this checksum.

## 15. File Size Divisor Table (Complete)

| Version | Divisor | Max File Size | Formula |
|---------|---------|---------------|---------|
| V1-3    | 2       | 128 KB        | header[$1A] × 2 |
| V4-5    | 4       | 256 KB        | header[$1A] × 4 |
| V6-7    | 4       | 512 KB        | header[$1A] × 4 |
| V8      | 8       | 512 KB        | header[$1A] × 8 |

## Summary of Key New Knowledge

1. **Extension table** (V5+) at header $36 - required for mouse coords and Unicode
2. **Unicode table** in extension word 3 - maps ZSCII 155-251 to Unicode
3. **Custom alphabets** at header $34 - 78 bytes for custom A0/A1/A2
4. **V8 requires 8-byte string alignment** - critical for packed addresses
5. **Dictionary MUST be in static memory** - bocfel and strict interpreters require this
6. **Property routine placeholders** - 0xFA00 pattern for deferred resolution
7. **Vocabulary word placeholders** - 0xFB00 pattern for dictionary references
8. **V6-7 need 4-byte routine padding** - packed address 0 must be invalid
9. **SENTENCE-ENDS? uses ZSCII 0x0B** - special sentence-ending space character

---
*Compiled 2026-01-26 from zorkie commits Dec 19-31, 2025*

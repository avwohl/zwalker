# Changelog

## 2025-12-06 - Z-Machine Bug Fixes

### Summary
Fixed 5 critical bugs in the Z-machine interpreter, achieving 100% compliance with the CZECH test suite (425 tests, 0 failures, down from 46 failures).

### Bug Fixes

#### 1. Version-Dependent Opcode Handling
Fixed incorrect opcode implementations that varied between Z-machine versions:
- **1OP:0F**: In v5+, this is `call_1n` (no store), not `not` (has store)
- **0OP:09**: In v5+, this is `catch` (has store), not `pop`
- **VAR:04**: In v5+, `aread` has a store byte

**Impact**: Games compiled for v5+ Z-machines were experiencing incorrect opcode behavior.

#### 2. check_arg_count Fix
Fixed argument count checking in routine calls:
- Added `num_args` field to `CallFrame` to track actual arguments passed
- Changed handler to compare with `num_args` instead of `num_locals`

**Impact**: Routines were incorrectly reporting argument availability, causing conditional logic errors.

#### 3. call_vs2/call_vn2 Decoder Fix
Fixed operand type byte decoding for extended VAR-form opcodes:
- `call_vs2` and `call_vn2` ALWAYS have two type bytes, regardless of how many operands the first byte specifies
- Previous implementation only read second type byte if first byte used all 4 operand slots

**Impact**: Calls with 5-8 operands were being decoded incorrectly.

#### 4. Indirect Variable Reference Semantics (Major Fix)
Fixed stack semantics for the 7 opcodes with indirect variable references (`inc`, `dec`, `inc_chk`, `dec_chk`, `load`, `store`, `pull`):

**Previous (incorrect) behavior**:
- First operand read would pop the stack if it was variable 0
- Operations on variable 0 would push to stack

**New (correct) behavior**:
- First operand (the variable reference) is READ normally (including popping if it's the stack)
- When the TARGET variable is 0 (stack), operations use peek/modify semantics:
  - `load` from var 0: peek stack (not pop)
  - `store` to var 0: modify stack top (not push)
  - `pull` to var 0: modify stack top after pop (not push)
  - `inc`/`dec` on var 0: modify in place

**Impact**: This was the most significant bug, causing incorrect stack behavior throughout game execution.

#### 5. Robustness Improvements
Enhanced error handling and bounds checking:
- `pop()` returns 0 on empty stack instead of raising an error
- Added bounds checking for routine addresses
- Added bounds checking for object addresses

**Impact**: Games with edge cases or unusual code patterns are now more stable.

### Test Results

**Before fixes**: CZECH compliance test had 46 failures
**After fixes**: CZECH compliance test has 0 failures (425/425 passing)

All 43 test games now pass successfully:
- Z-machine v3 games: 5 passing
- Z-machine v4 games: 2 passing
- Z-machine v5 games: 28 passing
- Z-machine v8 games: 8 passing

### Files Modified
- `zwalker/zmachine.py`: Core interpreter implementation (~169 lines changed)
- Multiple walkthrough result files updated with improved exploration data

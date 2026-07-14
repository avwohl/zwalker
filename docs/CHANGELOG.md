# Changelog

## 2026-07-13 - Verified Complete Solve: Zork III (Trilogy Complete)

- **Zork III solved 7/7** (won, 241 turns, 216 commands, RNG seed 1) —
  `solutions/zork3_verified.json`, `walkthroughs/zork3_verified_7.txt`. The full
  ending plays out: the Dungeon Master transformation in the Treasury of Zork.
- New `scripts/solve_zork3_adaptive.py`: adaptive recorder that plays the
  classic lake-first route under a pinned RNG seed, handling the random gates
  (earthquake window, hooded-figure mercy fight, once-only Viking ship, 50%
  amulet grab, old-man presence) and records a deterministic command list.
  Mechanics cross-checked against the official ZIL source
  (historicalsource/zork3).
- New `scripts/debug_replay.py`: transcript-printing replayer for diagnosing
  where a walkthrough goes wrong (companion to `replay_solve.py`).
- `replay_solve.py` fix: "eaten by a grue" death marker false-positived on the
  darkness *warning* text ("You are likely to be eaten by a grue"); now matches
  the actual kill text. Zork I/II verifications unaffected (re-verified).

## 2026-06-08 - Verified Complete Solves: Zork I & Zork II

### Summary
First fully verified end-to-end game solves, plus the replay harness that makes them
reproducible.

- **Zork I solved 350/350** (won, 499 turns, 431 commands) — `solutions/zork1_verified.json`,
  `walkthroughs/zork1_verified_350.txt`
- **Zork II solved 400/400** (won, 416 turns, 386 commands) — `solutions/zork2_verified.json`,
  `walkthroughs/zork2_verified_400.txt`
- **Replay harness** `scripts/replay_solve.py`: deterministic walkthrough replay with RNG
  seed search — pins `vm.rng.seed` and searches seeds until random events (thief, combat,
  wizard) line up, then records a full score timeline. Zork I verifies at seed 3, Zork II
  at seed 2.
- **Walker fix**: rollback false-positive in the exploration engine.

## 2026-06-08 - Agentic Solver (Plan B) & Interpreter Fixes

- New `zwalker/agentic_solver.py`: perceive→decide→act→verify loop with BFS navigation
  via a world model, checkpoint/backtracking stack, and a pluggable decider (free local
  heuristics or Claude via API).
- Tuning: configurable wall-clock budget, plan caching, zero-move navigation consumes a
  turn, dead navigation targets filtered (fixes agentic spin).
- Solver hardening: score-driven and dictionary-constrained command selection, real exit
  detection, undo support; fixed a Zork III crash and hardened the LLM planner.
- Implemented `output_stream 3` (memory redirection) and the default Unicode table.
- Auto-load `.env` (`ANTHROPIC_API_KEY`) on import.

## 2026-03-16 - Save/Restore Fix

- Fixed save/restore crash on V1-3 games (issue #2).

## 2025-12-06 - Z-Machine Bug Fixes

### Summary
Fixed 5 critical bugs in the Z-machine interpreter, achieving 100% compliance with the CZECH test suite (czech.z5: 425 tests, 0 failures, down from 46 failures).

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
**After fixes**: CZECH compliance test has 0 failures (czech.z5: 425/425 passing; the
full v3/v4/v5/v8 suite totals 1,604 tests — see the 2026 entries above)

All 43 test games now pass successfully:
- Z-machine v3 games: 5 passing
- Z-machine v4 games: 2 passing
- Z-machine v5 games: 28 passing
- Z-machine v8 games: 8 passing

### Files Modified
- `zwalker/zmachine.py`: Core interpreter implementation (~169 lines changed)
- Multiple walkthrough result files updated with improved exploration data

# WIP — zorkie ↔ zwalker: compile & solve real Infocom games

Session handoff / resume state. Primary repos:
- **zwalker** `/home/wohl/src/zwalker` (interpreter + verifier + L2 harness)
- **zorkie**  `/home/wohl/src/zorkie` (the ZIL compiler being fixed)

Scratch dir used for builds:
`/tmp/claude-1000/-home-wohl-src-zwalker/a6eff8c9-94e6-43c5-a647-a0cdd68c8526/scratchpad/zktest`

## Goal

Fix zorkie to compile the ZIL **sources** of the games zwalker solved, then solve
the zorkie-compiled builds. Sources don't exactly match the released `.z`, so each
build needs its own re-derived walkthrough.

## Scope reality (important)

- Of the 50 zwalker-verified games, **only 28 are Infocom ZIL** (`.z3`/`.z4`) —
  the only candidates for zorkie. **22 are Inform** (`.z5`/`.z8` comp games:
  Photopia, Shade, Lost Pig, 9:05, …) and **can never be zorkie inputs** (zorkie
  compiles ZIL, not Inform). ~26 of the 28 have ZIL source vendored in
  `~/src/zorkie/tests/test-games/` (zork1/2/3, enchanter, sorcerer, spellbreaker,
  planetfall, stationfall, cutthroats, deadline, suspect, suspended, witness,
  moonmist, wishbringer, lurkinghorror, ballyhoo, hollywoodhijinx, infidel,
  plunderedhearts, leathergoddesses, hitchhikersguide, starcross, amfv, trinity, …).
- Getting even ONE full Infocom game to compile+solve is finishing a large part of
  zorkie's back end (object/property/string codegen + the parser + the compile-time
  macro evaluator). This is a multi-week effort, NOT a session.

## What works now (committed + pushed)

**zwalker** (HEAD ~`b74d6e8` + WIP.md): the L2 integration harness
`scripts/test_zorkie_game.py` runs `compile ZIL → run in zwalker → replay to a win`.
Green suite of 3 self-contained games (source in `games/zil/`):
`microquest`, `mazekey`, `reactor` — all `zorkie [L2] PASS`. `cloak` is a tracked
frontier (not counted). Also fixed a zwalker robustness bug: `decode_zstring`
recursion guard (`zwalker/zmachine.py`). All 50 verified solves still pass.

**zorkie** fixes this session (all pushed; suite 692 passed, 3 pre-existing
unrelated failures: test_color, test_read_v5, two-space TELL):
- `b5384e2` parser: suppress special-form dispatch inside quasiquote templates
- `f3d6e10` lexer/preprocess: fix `!<form>` splice bracket miscount in `%<…>` skippers
- `f9b8fa3` codegen: fix `JE`/`EQUAL?` with large-constant comparands (dict words)
- `97424a5` codegen: evaluate nested-form operands in `G?`/`L?` (fixed the
  `<G? <SET CNT <+ .CNT 1>> N>` infinite loop)
- `557c40a` objects: don't let an `IN`-direction exit clobber the `IN` container
- `3d4514f` README rewrite

## Zork 1 status (the lead real game — shared library helps the whole Zork family)

Compile (from `~/src/zorkie/tests/test-games/zork1/`):
```
cd ~/src/zorkie/tests/test-games/zork1
PYTHONPATH=~/src/zorkie python3 ~/src/zorkie/zorkie zork1.zil -o /tmp/.../zktest/zork1_zk.z3 -v 3
```
It **compiles** (~107 KB) and boots through the banner + serial, and now (after
`557c40a`) prints the room name **"West of House"**. Then it goes wrong:

1. **Room description = "echo echo …"** — `DESCRIBE-ROOM` (gverbs.zil:1635) does
   `<APPLY <GETP ,HERE ,P?ACTION> ,M-LOOK>`; WEST-OF-HOUSE has no LDESC, so its
   description comes from its ACTION routine `WEST-HOUSE`. The **ACTION property
   (prop 9 = 0x61dc packed) resolves to the WRONG routine** (it lands in `V-ECHO`,
   gverbs.zil:546, whose body is the literal "echo echo …"). → routine-address /
   property-value codegen bug. **NEXT BUG TO FIX.**
2. **Crash: "Write to static memory at 0x57AC"** after ~685 instructions at
   pc 0x5d48 (zwalker `set_variable`→`write_word`). Reached during
   `DESCRIBE-OBJECTS` / main-loop setup. Likely a global-var index out of range or
   a bad `PUT`/`STOREW`. (My `557c40a` fix advanced execution INTO this; it's a
   real next bug, not a regression — the game was never playable.)
3. **Parser** — `gparser.zil` `PARSER` doesn't dispatch typed commands (before
   `557c40a`, boot reached the READ prompt and commands returned just `>`). Biggest
   single subsystem.

WEST-OF-HOUSE is object **180**, parent now **82** (ROOMS) — verified fixed.

## How to diagnose (reusable recipes)

Boot + drive (stops at READ prompt):
```python
from zwalker.walker import GameWalker
w=GameWalker(open(Z,'rb').read()); print(w.start()); print(w.try_command('open mailbox').output)
```
Instruction trace to find a hang/crash (tail shows the failing loop):
```python
from zwalker.zmachine import ZMachine
vm=ZMachine(open(Z,'rb').read()); vm.debug=True   # prints every [n] opcode
# or step manually: for i in range(N): 
#   if vm.waiting_for_input or vm.finished: break
#   if not vm.step(): break
```
Trace routine calls: monkeypatch `vm._call_routine`. Inspect objects:
`vm.get_object_name(n)`, `vm.get_object_parent(n)`, `vm.get_object_prop_addr(n)`.
Per-top-level-form parse scan (find which forms fail): split flattened source on
balanced `<…>` and parse each with a fresh `Parser`.

## Next steps (in order)

1. Fix the **ACTION property routine-address** so WEST-OF-HOUSE's action resolves
   to `WEST-HOUSE` (not `V-ECHO`). Confirm prop 9 is P?ACTION and that packed
   `0x61dc` should be `WEST-HOUSE`'s address. Check how zorkie emits a routine name
   as a property value (packed-address resolution / fixup).
2. Fix the **static-memory write** crash (find what global/index at pc 0x5d48).
3. Then the **parser** dispatch (gparser).
4. Re-derive a Zork 1 source-build walkthrough, register in `test_zorkie_game.py`.
5. Repeat for the shared-library siblings (Zork 2/3, Enchanter, …), then the
   standalone Infocom games.

## Key files

- zorkie codegen: `~/src/zorkie/zilc/codegen/codegen_improved.py`
  (`generate_condition_test` ~15903, `_resolve_two_cmp_operands`, `gen_equal` ~14196)
- zorkie parser: `~/src/zorkie/zilc/parser/parser.py` (`parse_room`/`parse_properties` ~927)
- zorkie object/parent build: `~/src/zorkie/zilc/compiler.py` (`get_parent_num` ~4094,
  parent loop ~4125; directions ~2104; property table ~3900-4060)
- zwalker interpreter: `~/src/zwalker/zwalker/zmachine.py`
- harness/docs: `~/src/zwalker/scripts/test_zorkie_game.py`, `docs/ZORKIE_TESTING.md`
- zorkie's own status: `~/src/zorkie/WIP.md`, `docs/KNOWN_ISSUES.md`

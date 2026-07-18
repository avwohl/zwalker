# WIP — zorkie ↔ zwalker: compile & solve real Infocom games

Session handoff / resume state. Primary repos:
- **zwalker** `/home/wohl/src/zwalker` (interpreter + verifier + L2 harness)
- **zorkie**  `/home/wohl/src/zorkie` (the ZIL compiler being fixed)

## Goal

Build the ZIL **sources** of the games zwalker solved with zorkie, then solve the
zorkie-compiled builds. Sources don't exactly match the released `.z`, so each build
needs its own re-derived walkthrough.

## State after session 7 (2026-07-18): FOUR GAMES WIN — L2 suite 7/7

- **ZORK I WINS 350/350** (Master Adventurer): route re-derived for this build's
  RNG stream by `scripts/solve_zork1_zorkie_adaptive.py` (seed 3, 402 cmds) →
  `walkthroughs/zork1_zorkie_350.txt`. Counted L2 game.
- **ZORK III WINS 7/7**: the OFFICIAL verified route (`zork3_verified_7.txt`,
  seed 1) replays LOCKSTEP-IDENTICAL — rooms AND scores — to the official
  Release-25 binary over all 216 commands, into the Treasury of Zork. Counted.
- **Starcross WINS 400/400**: OFFICIAL route (`starcross_verified_400.txt`,
  seed 1) lockstep-identical to Release 18 over all 240 commands. Counted.
- minizork stays 350/350. `python3 scripts/test_zorkie_game.py` → **7/7**
  (microquest, mazekey, reactor, minizork, zork1, zork3, starcross).
- zorkie pytest: 692 pass / 3 pre-existing fails (test_color, test_read_v5,
  TELL two-space). ~30 general fixes this session — full catalog in
  `~/src/zorkie/STATUS.md` ("Landed sessions 6-7").

## How this session's bugs were found (reuse this)

Four PARALLEL diagnosis agents (Workflow tool), each with the debug recipes
below, each verifying proposed fixes by monkeypatch + the regression gates
before reporting; then one serial integration pass in the repo from their
verified patch files. The two zork1 agents independently cross-confirmed each
other's root causes. Integration deltas that the gates caught: the table-vocab
index filter needs the prepositions/long-word tables registered too, and
preposition synonyms need explicit registration when the head is also a
direction ('inside').

## Adaptive route harness (for future zorkie builds of solved games)

`scripts/solve_zork1_zorkie_adaptive.py` + `walkthroughs/zork1_zorkie_route.txt`:
the official route with RNG-sensitive spots as @-steps (@killtroll @killthief
@heal @buoy), replayed per seed, recording the actual command stream with
`#% MAX_SCORE:` / `#% WIN_TEXT:` directives (NOTE the colon — replay_solve's
directive parser requires it). Pattern copied from solve_minizork_adaptive.py.
zork3/starcross needed NO adaptation (official routes replay clean).

## Next frontier (in order)

1. **Compile blockers** (13 games): zork2, deadline, suspect, witness, sorcerer,
   planetfall, suspended (CLEAR V4), hollywoodhijinx (51>32 attrs), cutthroats,
   infidel, enchanter (entry-file pick), lurkinghorror, spellbreaker. The old
   PRSO?/PRSI?/PRSA? macro note may be stale — re-measure which still fail and
   why; several may have been cured by the session-6/7 macro + dialect fixes.
2. **Size bucket** (9 games code-generate but exceed the limit): abbreviation
   selection/packing — ballyhoo 198KB, moonmist, wishbringer, leathergoddesses,
   plunderedhearts, stationfall, hitchhikersguide (V3 >128KB); trinity, amfv
   (V4 >256KB).
3. cloak frontier: stdlib ISAVE-requires-V5 in a V3 build.
4. Durable cleanups recommended by the agents: positional prop_routine_fixups
   (mirror prop_dict_fixups) to remove the 256-distinct-routine cap; positional
   recording for table vocab words; retire the legacy 0xFF00 outer-table scan
   by converting the global-table nested-ptr offsets to table_addr_fixups; the
   TELL 0x8D scan is still byte-blind (no observed failure).

## Diagnosis recipes (unchanged, proven again this session)

- Lockstep differ: `python3 scripts/lockstep.py <official.z3> <zorkie.z3>
  <walkthrough> <seed>` — first room/score divergence = next bug.
- PC-trace by wrapping `vm.step` (monkeypatching `vm._call_routine` misses some
  call opcodes). Static disassembly: reuse zwalker's opcode tables; routine
  code = high_mem + `comp._last_codegen.routines[name]` + 1 + 2*nlocals.
- Pass audit: wrap each assembler `_resolve_*`, diff pre/post bytes in the
  suspect routine's range.
- dfrotz (`/usr/games/dfrotz`) is the cross-check oracle.
- Bug families to suspect FIRST: (1) in-band marker scans matching legal data —
  fix by positions recorded at emission, never by widening a scan; (2) 8/12-bit
  capacity limits; (3) ZILCH dialect value semantics (truthiness of void ops,
  SET-literal, ACT? vs V? numbering); (4) macro/compile-time evaluation gaps.

## Key files

- zorkie codegen: `~/src/zorkie/zilc/codegen/codegen_improved.py`
- zorkie assembler: `~/src/zorkie/zilc/zmachine/assembler.py`
- zorkie compiler / dictionary / macros: `~/src/zorkie/zilc/compiler.py`,
  `zilc/zmachine/dictionary.py`, `zilc/parser/macro_expander.py`
- lockstep differ: `~/src/zwalker/scripts/lockstep.py`
- harness/status: `~/src/zwalker/scripts/test_zorkie_game.py`, `~/src/zorkie/STATUS.md`

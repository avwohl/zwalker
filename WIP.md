# WIP — zorkie ↔ zwalker: compile & solve real Infocom games

Session handoff / resume state. Primary repos:
- **zwalker** `/home/wohl/src/zwalker` (interpreter + verifier + L2 harness)
- **zorkie**  `/home/wohl/src/zorkie` (the ZIL compiler being fixed)

## Goal

Build the ZIL **sources** of the games zwalker solved with zorkie, then solve the
zorkie-compiled builds. Sources don't exactly match the released `.z`, so each build
needs its own re-derived walkthrough.

## State after session 6 (2026-07-18)

- **minizork still WINS 350/350** (L2 suite 4/4; regression during the session was
  caught by the suite and fixed — see the false-positive story below).
- **zork1 plays 34 commands lockstep-identical** to the official Release-119 binary
  (rooms AND scores) at seed 3 over `walkthroughs/zork1_verified_350.txt`:
  mailbox/leaflet, window entry, lamp/sword/rug/trap door, tree/egg, cellar,
  troll fight through the kill. Reproduce:
  `python3 scripts/lockstep.py games/zcode/zork1.z3 ~/src/zorkie/builds/zork1_zorkie.z3 walkthroughs/zork1_verified_350.txt 3`
  (scripts/lockstep.py is now COMMITTED, not session-scratch.)
- **zork3 unblocked**: ITABLE compile-time-form-size fix ended the write-to-static
  crash; boots and takes commands. Next: stray "(lamp)" in look output.
- **starcross unblocked**: ITABLE BYTE length-prefix fix ended the empty-parse;
  next is its 1982-dialect syntax dispatch ("I don't understand that sentence.").

## zork1 frontier (pick up here)

At cmd[34] 'west' the official build enters the Maze; zorkie's troll room stays
blocked. Two issues, probably related, both in the combat layer:
1. First blow prints garbled z-text before the real melee message
   ("fbi the herebs the fcgfpe…"). Melee tables are LTABLE-of-LTABLE-of-strings —
   suspect string pointers inside nested tables resolve against the wrong base.
2. The troll dies (black-fog text prints, object removed) but
   `<APPLY <GETP .VILLAIN ,P?ACTION> ,F-DEAD>` (1actions.zil:3575) doesn't take
   effect: TROLL-FLAG stays 0, so the west exit refuses. A minimal APPLY repro
   passes — the failure is context-specific; disassemble VILLAIN-RESULT next
   (method below). After these: expect RNG-stream route adaptation like
   minizork's (heal-waits, combat repeats baked into the command stream).

## Session-6 fixes (all general-purpose, in zorkie)

1. Vocab/vword scanners: match on PRISTINE input, never rescan own writes
   (dict '"' at 0x3EFB clobbered a je branch in zork1's PARSER).
2. String pass and routine/vocab passes now share one patched-positions set.
3. JUMP-offset guard: 0xFC/0xFB as either byte of a `jump` offset is not a
   placeholder (`8c 02 fc 0d` in MAIN-LOOP-1 became a string address and NUM
   stayed 0 → "There's nothing here you can take." on every verb).
4. ITABLE size as compile-time form (`<ITABLE NONE <* 8 2 36>>`) folds via
   `_eval_compile_time_value` (+, -, *, /, MOD) — zork3 CPOBJS/CELLOBJS.
5. Bare `<ITABLE BYTE n>` = length-PREFIXED table (starcross P-INBUF).
6. Syntax-table dialects: games declaring `P-SYNLEN 8` (zork1 + most of the
   fleet) get fixed 8-byte records (SBITS,PREP1,PREP2,FWIM1,FWIM2,LOC1,LOC2,
   ACTION); minizork's compact 2/4/7 records stay for the P-SYNLEN-0 dialect.
   All per-verb structures now live in ONE `_SYNTAX_ENTRIES` blob (table count
   was 325 and the 8-bit `0xFF00|idx` placeholder aliased); VERBS pointers are
   patched positionally via `table_addr_fixups`.
7. `%<COND …>` compile-time predicates now evaluate `<OR …>`/`<AND …>` —
   zork1's `%<COND (<OR <==? ,ZORK-NUMBER 1> …>` had compiled treasure scoring
   out of ITAKE.
8. Nested `<TABLE …>` inside a global table (VILLAINS) registers the enclosing
   table for pointer resolution (`_tables_with_nested_ptrs`).
9. SYNONYM/PSEUDO/ADJ dict-word references in properties are patched
   POSITIONALLY (`prop_dict_fixups`: obj-idx 0-based, prop, byte-off,
   word-offset). The old in-band `0x8000|offset` scan both truncated large
   dictionaries (zork1 'window' at offset 0x15FE) and, when widened,
   false-matched minizork's GLOBAL prop bytes `9a 8f` — that was the L2
   regression. Scanning is skipped whenever fixups are supplied.

## The method that wins (unchanged)

**Lockstep differ** (`scripts/lockstep.py`): official binary vs zorkie build,
compare room+score after every command; first divergence = next compiler bug.
For codegen bugs: PC-trace the region in zwalker (wrap `vm.step`, record PCs),
then disassemble with the session pattern (see zdis.py approach: reuse
zwalker's opcode tables; routine addr = high_mem + cg.routines[name], code
starts at addr+1+2*nlocals). `comp._last_codegen` gives routines/objects/
globals/constants maps. Beware: monkeypatching `vm._call_routine` after
construction misses some call opcodes — PC-tracing via `vm.step` is reliable.

## Known capacity limits still latent

- `0xFF00|table_idx` placeholders (globals, code operands) are 8-bit; zork1
  ducked under via the syntax blob, but a game with >255 tables breaks again.
- Adjective fallback marker `0xFE00|offset` is 8-bit (non-classic path only).
- The `_process_compile_arithmetic` %-form evaluator is text/regex-based.

## Next steps (in order)

1. zork1 combat frontier (above), then continue lockstep to 350/350 and
   register a source-matched walkthrough as L2 game 5.
2. zork3 "(lamp)" quirk, then lockstep it (zork3_verified_7.txt route).
3. starcross 1982 syntax dispatch.
4. PRSO?/PRSI?/PRSA? macro expansion (zork2, spellbreaker, lurkinghorror).
5. Abbreviation selection/packing — 9 games exceed the size limit.
6. Single-game blockers: planetfall (parse), suspended (CLEAR V4), hollywood
   (51>32 attrs), cutthroats/infidel (silent exit), enchanter (entry-file pick).

## Diagnosis recipes (reusable)

Boot + drive:
```python
from zwalker.walker import GameWalker
w=GameWalker(open(Z,'rb').read()); print(w.start()); print(w.try_command('open mailbox').output)
```
- dfrotz (`/usr/games/dfrotz`) is the cross-check oracle:
  `printf 'cmd\nquit\ny\n' | dfrotz -p game.z3`. Both misbehave => zorkie bug.
- Score in a zorkie V3 build: gtab = word at 0x0C; score = word at gtab+2.
- Compile: `cd ~/src/zorkie && PYTHONPATH=. python3 zorkie <src.zil> -o out.z3 -v 3`.

## Key files

- zorkie codegen: `~/src/zorkie/zilc/codegen/codegen_improved.py`
- zorkie assembler (all resolution passes): `~/src/zorkie/zilc/zmachine/assembler.py`
- zorkie compiler pipeline (prop/dict fixups, %COND eval): `~/src/zorkie/zilc/compiler.py`
- zwalker interpreter: `~/src/zwalker/zwalker/zmachine.py`
- lockstep differ: `~/src/zwalker/scripts/lockstep.py`
- harness/status: `~/src/zwalker/scripts/test_zorkie_game.py`, `~/src/zorkie/STATUS.md`

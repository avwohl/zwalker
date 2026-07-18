# WIP — zorkie ↔ zwalker: compile & solve real Infocom games

Session handoff / resume state. Primary repos:
- **zwalker** `/home/wohl/src/zwalker` (interpreter + verifier + L2 harness)
- **zorkie**  `/home/wohl/src/zorkie` (the ZIL compiler being fixed)

## Goal

Build the ZIL **sources** of the games zwalker solved with zorkie, then solve the
zorkie-compiled builds. Sources don't exactly match the released `.z`, so each build
needs its own re-derived walkthrough.

## MILESTONE REACHED (2026-07-18): minizork WINS 350/350

The zorkie build of the real 1987 `mini.zil` (Release 0) plays the **complete
game** to the Stone Barrow victory in zwalker: 420 commands, score 350/350,
room/score progression lockstep-identical to the official binary over the whole
route. It took ~50 general compiler fixes across 5 sessions (full catalogs:
`~/src/zorkie/STATUS.md` + memory `zorkie-parser-frontier`).

- Verified replay: `walkthroughs/minizork_zorkie_350.txt` (RNG seed 1; `#%
  MAX_SCORE`/`#% WIN_TEXT` directives included so replay_solve asserts the win).
- Registered as a **counted** game in the L2 harness: `python3
  scripts/test_zorkie_game.py` → `zorkie L2 suite: 4/4 games play-and-win
  (microquest, mazekey, reactor, minizork)`; cloak remains the uncounted frontier.
- Reference build kept at `~/src/zorkie/builds/minizork_zorkie.z3` (gitignored;
  the harness recompiles from source every run).
- Route note: the published Release-34 route was adapted for this build's RNG
  stream — no Troll-Room heal; heal-waits in SACRED rooms (Living Room before
  each 'open trap door', Altar after the torch swap, Temple/Egyptian Room before
  take bell/coffin). Combat repeats are baked into the command stream.

## The method that won (reuse for every next game)

**Lockstep differ**: run the OFFICIAL binary and the zorkie build side by side
through a verified route, comparing ROOM-NAME (global 16's short name) and SCORE
(global 17) after every command — the first divergence IS the next compiler bug.
Then minimal-repro it, fix, re-run. (lockstep.py / solve_zorkie_minizork.py were
session-scratch scripts — re-create from this description; ~80 lines each.)

Watch for the recurring bug class: **position-blind byte scanners** in
`zilc/zmachine/assembler.py` misreading already-resolved bytes 0xF0/0xFA-0xFC as
placeholders. Every new "impossible" corruption has been one of these; fix by
position-tracking (record placeholder offsets at encode time) — never by scanning.

## Next steps (in order)

1. **zork1 by lockstep** — it already boots, reaches READ, and dispatches
   commands on the same parser pipeline as minizork. Drive it with
   `walkthroughs/zork1_verified_350.txt`'s route against the official Release-119
   binary (`~/src/zorkie/tests/test-games/zork1/COMPILED/zork1.z3`), fix the
   first divergence, repeat. Then register a source-matched walkthrough here.
2. **zork3** (write-to-static crash at 0x2826) — likely another scanner/store bug.
3. **starcross** vocabulary lookup ("I beg your pardon?" on every command).
4. PRSO?/PRSI?/PRSA? macro expansion (unblocks zork2, spellbreaker, lurkinghorror).
5. Abbreviation selection / packing — 9 games code-generate but exceed the size
   limit (ballyhoo, moonmist, wishbringer, leathergoddesses, plunderedhearts,
   stationfall, hitchhikersguide; V4: trinity, amfv).
6. Single-game blockers: planetfall (parse), suspended (CLEAR V4), hollywood
   (51>32 attrs), cutthroats/infidel (silent exit), enchanter (entry-file pick).

## State of the repos (after this session's commits)

- zwalker: L2 harness green 4/4 + cloak frontier; all 50 released-binary solves
  unaffected (no interpreter changes this session).
- zorkie: suite baseline 692 pass / 3 pre-existing fails (test_color,
  test_read_v5, TELL two-space). All session fixes are general-purpose codegen /
  assembler / dictionary corrections — no minizork-specific hacks.

## Diagnosis recipes (reusable)

Boot + drive to READ prompt:
```python
from zwalker.walker import GameWalker
w=GameWalker(open(Z,'rb').read()); print(w.start()); print(w.try_command('open mailbox').output)
```
- `codegen.routines[name]` values are OFFSETS from `high_mem_base` (= len(story)
  when routines are appended), NOT absolute addresses.
- dfrotz (`/usr/games/dfrotz`) is the cross-check oracle:
  `printf 'cmd\nquit\ny\n' | dfrotz -p game.z3`. If both interpreters misbehave,
  it's a zorkie bug, not a zwalker quirk.
- Score in a zorkie V3 build: globals table at `story[0x0C]<<8|story[0x0D]`;
  globals number from 16, so score = global 17 = the word at gtab+2.

## Key files

- zorkie codegen: `~/src/zorkie/zilc/codegen/codegen_improved.py`
- zorkie assembler (scanner classes): `~/src/zorkie/zilc/zmachine/assembler.py`
- zorkie dictionary: `~/src/zorkie/zilc/zmachine/dictionary.py`
- zorkie compiler pipeline: `~/src/zorkie/zilc/compiler.py`
- zwalker interpreter: `~/src/zwalker/zwalker/zmachine.py`
- harness/status: `~/src/zwalker/scripts/test_zorkie_game.py`, `~/src/zorkie/STATUS.md`

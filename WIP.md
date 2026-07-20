# WIP — zorkie ↔ zwalker: compile & solve real Infocom games

Session handoff / resume state. Primary repos:
- **zwalker** `~/src/zwalker` (interpreter + verifier + L2 harness)
- **zorkie**  `~/src/zorkie` (the ZIL compiler being fixed)

## Goal

Build the ZIL **sources** of the games zwalker solved, compile them with zorkie,
and drive the zorkie-compiled builds to verified wins in zwalker.

## State after session 9 (2026-07-19/20): L2 suite 27/27 — V3 corpus done, V4 arrived

`python3 scripts/test_zorkie_game.py` → **27/27** games compile from ZIL source
and play to a replay_solve-verified win: microquest, mazekey, reactor,
minizork 350/350, zork1 350/350, zork3 7/7, starcross 400/400, zork2 400/400,
deadline, suspended, infidel, witness, cutthroats 250/250, sorcerer 400/400,
enchanter 400/400, hitchhikersguide 400/400, suspect, ballyhoo 200/200,
hollywoodhijinx 150/150, wishbringer 100/100, spellbreaker 600/600,
stationfall 80/80, plunderedhearts 25/25, leathergoddesses (321,
self-randomized), lurkinghorror 100/100, **trinity 100/100 (V4)**,
**amfv (V4, scoreless)**. zorkie pytest: 696 pass / 3 pre-existing fails.

Every Infocom V3 corpus game with a verified route now wins from source. The
compiler-fix catalog lives in `~/src/zorkie/STATUS.md` (sessions 8-9) and the
git log of both repos.

### Route-provenance rule (learned the hard way)
When a compiler CORRECTNESS fix "breaks" a game, the route is usually stale:
routes recorded against a buggy build (SIZE=0 PROPDEF defaults, corrupted
tables) can only win ON that bug. Lockstep the fixed build vs the OFFICIAL
binary first — if clean, re-derive the route (suspect, minizork, zork2 all
went this way). And always acceptance-test with `replay_solve` itself: it
seeds the RNG AFTER `GameWalker.start()`; drivers that seed before explore a
different stream (trinity/amfv were mis-"verified" that way once).

### Verifier conveniences
- `#% WIN_TEXT_SUFFICIENT: 1` — the WIN_TEXT match alone decides the win, for
  games whose real score var zwalker can't read on a zorkie build (wishbringer
  V3 time-game clock; trinity V4 layout). The WIN_TEXT should quote the game's
  own score line ("100 points out of 100") so the match itself proves the score.
- `scripts/rederive_route.py` — adaptive @-routes; note it seeds BEFORE start
  (recordings replay fine because they bake retries in, but verify the
  recording with replay_solve afterward).

## Remaining frontier

1. **moonmist** — fits the V3 cap (130196) and replays its 86-cmd route to
   completion, but ask/tell topic resolution fails pre-existing ("Bolitho looks
   confused"; 'examine ghost' prints raw dict memory). Needs a parser-table /
   GENERIC-property lockstep investigation, then it should win.
2. **planetfall** — SOURCE truncated (`comptwo.zil` physically ends mid-object
   at TRIFFID). Provenance problem; check upstream historicalsource for a
   complete revision. Do NOT "fix" by accepting unbalanced input.
3. **cloak** — ZILF stdlib uses ISAVE (V5+) in a V3 build; the real frontier is
   a V5 target (the V4 opcode work + call_vs2 are a head start).
4. Cosmetics: stray \x01 on some V4 CRLFs, TELL two-space, amfv tubecar
   departure-message timing (2/14 occurrences).

## Diagnosis recipes (proven across 9 sessions)

- Lockstep differ: `python3 scripts/lockstep.py <official.z> <zorkie.z>
  <walkthrough> <seed>` — first room/score divergence = next bug. Text-level
  probing catches what room+score can't (failed takes, fumbles): replay with
  GameWalker + replay_solve.load_commands and print outputs around suspects.
- dfrotz cross-check oracle: `~/esrc/frotz-src/dfrotz` (macOS symlink).
- Bug families, in order of prior: (1) in-band marker/placeholder scans
  matching legal data — resolve by positions recorded at emission, NEVER
  widen a scan; (2) 8/12/16-bit capacity limits (vocab indices, object>255
  operands, call args); (3) ZILCH dialect value semantics; (4) macro /
  compile-time evaluation gaps; (5) V4-specific layouts (properties, exits,
  adjectives are all different from V3).
- Agent hygiene: verify deliverables from worktrees (rebuild+replay), not
  reports; commit verified integrations immediately; `git checkout -- zilc`
  during bisects destroys staged work.

## Key files

- zorkie codegen: `~/src/zorkie/zilc/codegen/codegen_improved.py`
- zorkie assembler / dictionary / abbreviations / object table:
  `zilc/zmachine/{assembler,dictionary,abbreviations,object_table}.py`
- zorkie compiler / parser / macros: `zilc/compiler.py`, `zilc/parser/*`
- harness: `~/src/zwalker/scripts/test_zorkie_game.py` (L2 suite, 27 games),
  `scripts/sweep_zorkie_corpus.py`, `scripts/replay_solve.py`,
  `scripts/lockstep.py`, `scripts/rederive_route.py`
- status: `~/src/zorkie/STATUS.md`

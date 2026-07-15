# Changelog

## 2026-07-14 - Verified Complete Solves: 26-game batch — corpus now 35 games across V1/V3/V4/V5/V8

- **26 new verified complete solves** join the 9 already in the repo, taking the
  corpus to **35 games, every one played start to finish and reproducibly won**
  under a pinned RNG seed (`scripts/replay_solve.py`; JSON + documented
  walkthrough per game). The batch spans every Z-machine story-file version
  the interpreter plays: V1, V3, V4, V5, V8.
  - Infocom: The Lurking Horror 100/100, Trinity 100/100 (V4),
    A Mind Forever Voyaging (V4, ending-text win), Infidel 400/400,
    Cutthroats 250/250, Moonmist (ending-text win), Plundered Hearts 25/25,
    The Witness (ending-text win), and Zork I Release 5 350/350 — a 1980
    **V1** story file, the first V1 verified solve.
  - Classics and comp games: Adventure/Colossal Cave 350/350 (V3 port),
    Adventureland 100/100, Detective 360/360, 9:05, Photopia, Shade,
    All Roads, Balances 51/51, The Edifice, The Acorn Court 30/30,
    Suveh Nux, Cloak of Darkness, Theatre 50/50, Lost Pig 7/7,
    The Dreamhold, Castle Adventure!, Cold Iron (V8).
- **The Lurking Horror 100/100** (won, 310 turns, 306 commands, RNG seed 1,
  r221/s870918 from eblong.com): all 19 five-point ZIL scoring events plus the
  endgame's `SETG SCORE 100` on killing the horror; the win text is the
  "President of the Institute" ending. Only two RNG sources matter — the
  urchin's 10-turn wander and a 25% random elevator call — and the recorded
  route rides them deterministically at seed 1; the adaptive recorder
  (`scripts/solve_lurking_adaptive.py`) also carries urchin-hunt and
  elevator-recall recoveries, winning 6 of seeds 1-8. Research synthesis with
  ZIL file:line citations in `logs/lurking_notes.md`.
- **Unscored games are now verifiable**: walkthrough headers can carry
  machine directives — `#% WIN_TEXT: <regex>` (the win is asserted by the
  game's true ending text) and `#% MAX_SCORE: <N>` (for games whose max the
  interpreter's banner/serial map doesn't know). The win criterion requires
  the declared ending text and/or the max score, and the verified JSON
  records `win_text_seen`.
- **Interpreter fixes** shaken out by the batch (all 35 games re-verified
  against the final code):
  - V4+ games get the interpreter-supplied header bytes (screen size,
    interpreter number) filled in at boot and on restart — Theatre and
    Trinity refuse to run without them.
  - Score-variable overrides for Cutthroats r23 (its RATING global; the
    turn slot maps to its minutes-since-midnight clock) and Trinity r15
    (V4+ has no status-line convention; its SCORE/MOVES globals are mapped
    per build), plus max-score map entries for The Lurking Horror.
  - `read char` accepts the literal words "enter"/"return" as the RETURN
    key so raw-keypress menus (Theatre's journal) can be driven from a
    plain command list.
  - Out-of-range property pointers in small object tables read as nameless
    instead of crashing (cloak.z3).
  - `replay_solve` death detection: bare "you are dead" replaced with the
    Zork-family kill phrasing — Plundered Hearts' mandatory pre-duel taunt
    ("You will have no need of her when you are dead.") false-positived.
- Docs overhauled for the batch: README and docs/index.html verified tables
  now carry a Z-version column and are generated from the verified JSONs;
  WALKTHROUGHS.html regenerated.

## 2026-07-14 - Verified Complete Solve: Stationfall (Planetfall Series Complete)

- **Stationfall solved 80/80** (won, GST 5700 on day 2, 375 commands, RNG
  seed 1) — `solutions/stationfall_verified.json`,
  `walkthroughs/stationfall_verified_80.txt`. Full ending: the corrupted
  Floyd shot in the replica factory (a hero's death), the alien pyramid
  destroyed with the reflective foil, Oliver toddling over to ask for a
  game — "Intergalactic Mega-Hero." All 18 scoring events on the timeline.
  With Planetfall 80/80, the Planetfall series is replay-verified complete.
- **The determinism discovery**: Stationfall rolls its day-1 start clock
  from RANDOM(1220) *during boot*, before any seed can be pinned, so no
  fixed command list could ever replay — until the recording opens with
  `restart`/`yes`, which reloads memory but keeps the seeded RNG and
  re-rolls the clock on the pinned stream. After that prelude the whole
  game is a pure function of the seed, including the feelie copy-protection
  spacetruck course, which the recorder computes from the live clock.
- New `scripts/solve_stationfall_adaptive.py`: a two-day route with
  floating hazard handlers on every turn — hull welders hunted down
  4%/turn (fourth turn in their room is death; the route bounces
  out-and-back to despawn them), Plato's one-time stun ambush ("floyd,
  help" each stun turn, then re-collecting the scattered inventory),
  Floyd's floor-pilfering (nothing stealable is ever floor-stashed), the
  frezone explosive's 210-unit melt clock, and hunger/sleep timers.
  Mechanics verified against the official ZIL source
  (historicalsource/stationfall) and machine-validated at 80/80 across 23
  seeds during research; synthesis in `logs/stationfall_notes.md`.

## 2026-07-14 - Verified Complete Solve: Wishbringer

- **Wishbringer solved 100/100** (won, 162 moves, 179 commands, RNG seed 1,
  zero of the Stone's 7 Wishes used) — `solutions/wishbringer_verified.json`,
  `walkthroughs/wishbringer_verified_100.txt`. The full ending: the Magick
  Stone surrendered to the sculpture, Festeron restored, and the post-office
  door knock answered. All 34 scoring events on the timeline.
- **Time-game score support in the interpreter**: Wishbringer is a V3 "time"
  game — the status-line globals (vars 17/18) hold the clock (15:00 start,
  1 turn = 1 minute), so the standard V3 score read returned the *hour*.
  `zmachine.py` now carries a per-build score-variable override map;
  for Wishbringer r68 `get_score()`/`get_turns()` read the game's own
  GSCORE/GMOVES globals (vars 152/151), found by tracing which globals the
  SCORE verb prints and confirmed against the ZIL source. All seven prior
  solves re-verified after the change.
- New `scripts/solve_wishbringer_adaptive.py`: a no-wish route that parses
  the seed-rolled magic word (KALUZE/FRATTO/SORKIN, revealed only in the
  pelican's cloud-writing) at runtime, crosses the trail/fog maze with zero
  wrong turns (each mistake adds a cumulative 10% death roll), dashes the
  Witchville cemetery in two turns (a third scatters your inventory), and
  dodges the deterministic 19-room Boot Patrol loop by entering the jail
  from the tunnels below. Mechanics verified against the official ZIL
  source (historicalsource/wishbringer) and machine-validated at 100/100
  across 92 seeds during research; synthesis in `logs/wishbringer_notes.md`.
- `games/zcode/wishbringer.z3` (r68/850501 freeware from eblong.com) added
  to the corpus; `get_max_score` banner/serial map covers it.

## 2026-07-14 - Verified Complete Solve: Planetfall

- **Planetfall solved 80/80** (won, 444 commands, RNG seed 1, best ending) —
  `solutions/planetfall_verified.json`, `walkthroughs/planetfall_verified_80.txt`.
  The full rescue: Veldina awakened, the cure administered, promotion to
  Lieutenant First Class, Blather demoted to toilet attendant, Floyd rebuilt.
  Rank: Galactic Overlord. All 23 scoring events on the timeline.
- New `scripts/solve_planetfall_adaptive.py`: a two-in-game-day route
  navigating the disease/hunger/sleep clocks with a hunger watchdog and a
  scheduled Dorm-B night, Floyd's chatter (1-3 RNG draws per turn, 6%
  wander-off with order retries), the comm-panel repair (2-or-3 pours with
  the color sequence parsed from text), the shuttle speed curfew, Floyd's
  bio-lab sacrifice, the miniaturization booth (TYPE 384), the speck
  marksmanship ledger feeding the microbe disposal window, and the
  fungicide-flood escape. Mechanics verified against the official ZIL
  source (historicalsource/planetfall) and machine-validated at 80/80
  across 65 seeds during research; synthesis in `logs/planetfall_notes.md`.
- `get_max_score` banner/serial map covers Planetfall r37 (and Stationfall's
  banner for the future). Planetfall's "turns" are Galactic Standard Time.

## 2026-07-14 - Verified Complete Solve: Spellbreaker (Both Trilogies Complete)

- **Spellbreaker solved 600/600** (won, 531 turns, 422 commands, RNG seed 1) —
  `solutions/spellbreaker_verified.json`, `walkthroughs/spellbreaker_verified_600.txt`.
  Full ending: the shadow destroyed inside its own hypercube, the age of
  magic ended — "class of Scientist." All 31 scoring events on the timeline.
  With this, both classic Infocom trilogies (Zork I-III, Enchanter saga) are
  replay-verified complete.
- New `scripts/solve_spellbreaker_adaptive.py` executing the directive route
  `logs/spellbreaker_route.txt`: spell-fizzle retry loops (any cast can fail
  until the magic cube is held), the sliding-rock chase solved by expectimax
  over the brown rock's exact ZIL pursuit automaton, Belboz's identity quiz
  answered from the guild-lore table, and the endgame vault weighing — twelve
  shuffled cubes with random positional labels and a 50/50 glow bias,
  identified in exactly three jindak comparisons (the classic 12-coin puzzle
  with unknown bias); the found label is captured and reused downstream.
  Route mechanics verified against the official ZIL source
  (historicalsource/spellbreaker) and machine-validated at 600/600 across 20
  seeds during research; synthesis in `logs/spellbreaker_notes.md`.
- `games/zcode/spellbreaker.z3` (r87/860904 freeware from eblong.com) added
  to the corpus; `get_max_score` serial map covers it.

## 2026-07-13 - Verified Complete Solve: Sorcerer

- **Sorcerer solved 400/400** (won, 390 turns, 234 commands, RNG seed 2) —
  `solutions/sorcerer_verified.json`, `walkthroughs/sorcerer_verified_400.txt`.
  Full ending: Jeearr destroyed against the vardik shield; "Leader of the
  Circle of Enchanters." All 23 scoring events match the official ZIL table.
- New `scripts/solve_sorcerer_adaptive.py`: parses the two seed-rolled values
  from game text at runtime — the journal's monster code (mapped through the
  infotater wheel to the five trunk buttons, where one wrong press is
  permanently unwinnable) and the coal-mine combination (echoed on the dial
  and back to your younger self to close the golmac time loop). Route
  handles the matchbook mail window (turn 24), the berzio clock retirement,
  the 3-fweep glass-maze crossing with the dorn-beast lure into the
  floorless cell, and the 8-turn Belboz endgame window. Mechanics verified
  against the official ZIL source (historicalsource/sorcerer); notes in
  `logs/sorcerer_notes.md`.
- `games/zcode/sorcerer.z3` (r18/860904, freeware from eblong.com) added to
  the corpus; `get_max_score` serial map covers it (banner prints only after
  the opening dream).

## 2026-07-13 - Verified Complete Solve: Enchanter

- **Enchanter solved 400/400** (won, 300 turns, 206 commands, RNG seed 1) —
  `solutions/enchanter_verified.json`, `walkthroughs/enchanter_verified_400.txt`.
  Full ending: "you have joined the Circle of Enchanters." All 18 scoring
  events match the official ZIL point table.
- New `scripts/solve_enchanter_adaptive.py`: 3-game-day route with adaptive
  handling of the hunger/thirst/sleep survival clocks, the mirror-hall
  adventurer (15%/turn appearance), map/pencil pilfering, the Unseen Terror
  map-and-pencil maze, the hasted-turtle kulcad errand, and the one-command-
  per-turn Krill endgame. Mechanics verified against the official ZIL source
  (historicalsource/enchanter); route notes in `logs/enchanter_notes.md`.
- `zmachine.get_max_score`: added Enchanter-series detection
  (Enchanter 400, Sorcerer 400, Spellbreaker 600).
- `replay_solve.py`: second death-marker false positive fixed — "fills your
  lungs" matched Enchanter's west-gate text ("a blast of cold air fills your
  lungs"); now requires the drowning phrasing. All four solves re-verified.

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

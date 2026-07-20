# Roadmap: solve every `.z`, compile every ZIL/ZILF, verify both builds

Three interlocking goals:

1. **Solve every known published `.z`** — a verified zwalker walkthrough (replay to
   won=True at a fixed RNG seed) for each released story file.
2. **Compile every ZIL and ZILF source** with zorkie and drive the compiled build
   to a verified win in zwalker (the from-source / L2 track).
3. **Keep both** — because the preserved source almost never matches the published
   binary, each game has **two** builds that need **two** walkthroughs.

## The central principle: two builds, two walkthroughs

For a game with both a published binary (**PUB**) and compilable source (**SRC**):

- PUB and SRC differ in release/serial, object numbering, the RNG stream, item
  sizes/weights, scoring globals, and ending text. A route that wins on one often
  loses on the other (proven repeatedly: minizork, zork2, suspect all needed
  re-derived SRC routes; the PROPDEF-defaults fix made SRC *match* PUB and broke
  the old SRC route).
- Therefore every such game carries up to two verified walkthroughs:
  - `<game>_verified_*.txt` — wins on the PUB binary (the binary-solve track).
  - `<game>_zorkie_*.txt` / source-build route — wins on the SRC build (L2 track).
- **SRC-from-PUB derivation SOP** (already the working method):
  1. `zorkie` compile SRC.
  2. `scripts/lockstep.py PUB.z SRC.z <PUB route> <seed>` → first room/score divergence.
  3. If the divergence is a **miscompile** → fix zorkie (general fix).
     If it's a **legitimate build difference** (RNG/item size/object #) → adapt the
     route: `scripts/rederive_route.py` with `@repeat`/`@until` steps for the
     RNG-sensitive spots, seed search.
  4. Verify with `scripts/replay_solve.py` (seeds AFTER `start()` — the acceptance
     convention). Record the exact winning stream with `#% MAX_SCORE`/`#% WIN_TEXT`
     directives (`#% WIN_TEXT_SUFFICIENT: 1` for time-games whose score var a SRC
     build doesn't expose).

## Current state (2026-07-20)

- **zwalker interpreter**: CZECH-clean on v1/v3/v4/v5/v8. **No v6** (the graphical
  Infocom line) — a hard prerequisite for anything V6, in this repo.
- **zorkie compiler**: full v3, full v4 (Trinity/AMFV). **No v5, no v6.**
- **From-source (L2)**: 28/28 — 26 v3 + 2 v4 (`scripts/test_zorkie_game.py`).
- **Binary-solve**: ~50 verified solves; 51 PUB + 13 SRC walkthroughs on file;
  ~147 `.z` binaries present in `games/zcode/` (mostly Inform v5/v8, not all solved).
- Source universe: 40 Infocom ZIL + ~7 ZILF (see `GAME_SOURCE_MATRIX.md`).

The two ceilings that gate the biggest expansions: **zorkie has no V5/V6 target**,
and **zwalker cannot interpret V6**.

---

## Phase 0 — Manifest + harness (foundation, do first)

Everything downstream needs one source of truth and a two-track runner.

- **Manifest** `corpus_manifest.json`: one row per game with
  `{pub_path, pub_version, pub_walkthrough, pub_status, src_dir, src_entry,
  src_version, src_walkthrough, src_status, notes}`. Seed it from
  `GAME_SOURCE_MATRIX.md`, the `sweep_zorkie_corpus.py` CORPUS dict, and a scan of
  `games/zcode/` (version = header byte 0) + `walkthroughs/`.
- **Two-track verifier** `scripts/verify_corpus.py`: for each manifest row, run the
  PUB replay and (if source compiles) the SRC compile+replay; emit an updated
  matrix and a per-version scoreboard. Supersedes the ad-hoc suite + sweep.
- **Naming convention**: settle `<game>.pub.txt` vs `<game>.src.txt` (or keep the
  existing `_verified_`/`_zorkie_`); document it once so both tracks are unambiguous.
- **Acquisition list**: decide the scope of "all known `.z`" (see Scope below) and a
  `scripts/fetch_corpus.py` that pulls the target set from the IF Archive
  `if-archive/games/zcode` index into `games/zcode/` with provenance recorded.

Effort: S–M. Risk: low. Unblocks measurement for every later phase.

## Phase 1 — Close the from-source V3/V4 gap (near-done)

Attemptable Infocom sources still un-won (all v3/v4, no new compiler target needed):

- **seastalker** (v3), **minizork-1982** (v3), **infocom-sampler** (v3),
  **bureaucracy** (v4), **nordandbert** (v4).
- Method: compile, lockstep vs the PUB binary, derive the SRC route (Phase-0 SOP),
  register in the L2 suite. Bureaucracy/Nord&Bert exercise more V4 paths — expect a
  few general V4 fixes (feeds Phase 3).
- **planetfall** (v3) is **source-blocked**: `comptwo.zil` is a truncated
  historicalsource checkout (ends mid-object at TRIFFID). Subtask: locate a complete
  upstream revision (other historicalsource branches / IF Archive source drops); do
  not "repair" by accepting unbalanced input.

Effort: M (5 games). Risk: low–med. Target: L2 → ~33 from-source wins.

## Phase 2 — Binary-solve track: solve the published corpus

Goal: a verified PUB walkthrough for every `.z` in scope.

- **Tier A — Infocom PUB binaries** (v1/v3/v4/v5): we already have human
  walkthroughs and, for source games, a derived route; fill the rest.
- **Tier B — the broad IF corpus** in `games/zcode/` (Inform v5/v8, ~97 unsolved):
  drive with the agentic solver (`zwalker/agentic_solver.py`,
  `scripts/solve_with_opus.py`) seeded by human walkthroughs where they exist,
  then `replay_solve` to pin a deterministic winning route.
- **Tier C — acquire + solve more** from the IF Archive up to the chosen scope.
- Parallelizable: fan out solver agents per game; each returns a verified route or a
  "stuck" report (menu/Y-N prompts, timing puzzles, mazes — the known hard cases).

Effort: L (scales with corpus scope). Risk: med (some games need human hints / are
not winnable headless). Milestone the count, not "all", and log what's dropped.

## Phase 3 — zorkie V5 target (biggest from-source unlock)

Unblocks Infocom **Beyond Zork, Border Zone, Sherlock, checkpoint** + ZILF
**cloak_plus** + any ZILF v5 game. zwalker already interprets v5 (CZECH-clean).

- V5 codegen: extended (VAR/EXT) opcodes, the v5 header/flags, v5 dictionary + object
  format (63 props, 14-bit object numbers already handled for V4>255), colour/sound/
  mouse/`set_font` ops, `save_undo`/`restore_undo` (already have `gen_save_undo`),
  `check_arg_count`, `print_table`, etc. Much of the hard V4 work (call_vs2,
  scan_table, EZIP layouts, 16-bit operands) transfers.
- Gate each addition against the CZECH v5 harness and the L2 suite; derive SRC routes
  for the four V5 Infocom games (Phase-0 SOP).

Effort: XL (new version target). Risk: high. Target: L2 + ~4–5 v5 wins.

## Phase 4 — ZILF-library parser-table emission

cloak already compiles as v3 but no ZILF-**library** game wins: the library parser
(`_is_classic_parser=False`, first exercised by cloak) reads a VERBS/syntax-table
byte layout zorkie does not emit, so `MATCH-SYNTAX` never sets `,PRSA`.

- Implement the ZILF-dialect VERBS/syntax/action-table emission (distinct from the
  classic-Infocom table zorkie already builds). Root cause is isolated in zorkie
  (commit 2989b3a NOTES): table sizing, constructor eval, library-message/pronoun/
  DEFSTRUCT are all correct — only the syntax-table format remains.
- Unlocks **cloak, advent (ZILF port), Milliways, zil_test**, and the whole
  ZILF-library game class in one shot — the highest game-count-per-fix lever.

Effort: L. Risk: med. Independent of Phase 3 (can run in parallel).

## Phase 5 — V6 support (both repos; the graphical line)

The hardest, and blocked on **two** prerequisites:

- **zwalker V6 interpreter** first: v6 routine-calling, windows/graphics/menus, the
  v6 opcode set. Validate against a CZECH-v6 / the published Zork Zero etc. Without
  this, no V6 story file — PUB or SRC — can even run.
- Then **zorkie V6 target**: YZIP codegen, v6 headers/packed addresses, the graphics
  primitives. Unblocks Zork Zero, Journey, Arthur, Shogun (source not local),
  Restaurant, Abyss (source) and the V6 PUB binaries.

Effort: XXL, two-repo. Risk: high. Sequence last; consider "runs/parses" milestones
short of pixel-perfect graphics.

## Phase 6 — Dual-walkthrough reconciliation & regression

- For every game with both builds, keep PUB and SRC walkthroughs, document the
  divergence class (RNG / item-size / object-# / ending-text), and cover both in the
  regression suite so a compiler change that re-aligns SRC to PUB (like PROPDEF) is
  caught and the stale route is re-derived, not silently lost.
- Fold the whole matrix into `verify_corpus.py` output so `GAME_SOURCE_MATRIX.md`
  regenerates from data.

---

## Scope decision for "all known `.z`"

"All known" is unbounded (the IF Archive is thousands of files). Recommended tiers,
finish each before widening:

- **T0**: everything already in `games/zcode/` (~147) + all 40 Infocom sources.
- **T1**: the full Infocom published catalog (all versions/releases) + all ZILF
  sample/community games.
- **T2**: the IF Archive `games/zcode` index, prioritized by notability (IFDB
  ratings), with a hard "unsolvable-headless" drop list (menu/graphics/multiplayer).

## Recommended execution order & milestones

1. **Phase 0** (manifest + two-track verifier) — 1 pass, unblocks measurement.
2. **Phase 1** (finish v3/v4 from-source) → L2 ~33; and **Phase 2 Tier A/B** in
   parallel (fan-out solver on the present binary corpus) → binary solves ~2×.
3. **Phase 4** (ZILF parser table) — high game-count/fix; parallel with the above.
4. **Phase 3** (zorkie V5) — the big from-source expansion.
5. **Phase 2 Tier C** (acquire + solve to the chosen scope).
6. **Phase 5** (V6, both repos) — last, largest.

## Cross-cutting risks

- **Route provenance drift**: any general compiler fix can re-align SRC toward PUB
  (or away) and invalidate a recorded SRC route — the full L2 suite must run after
  every codegen change (learned when a moonmist fix crashed cutthroats), and SRC
  routes get re-derived, never hand-patched to the old bytes.
- **Headless-unsolvable games**: menu/Y-N/timing/graphics games need solver support
  or are out of scope — enumerate, don't silently skip.
- **Compile time**: the CELF abbreviation selector made big-game compiles minutes
  long; the corpus verifier must parallelize and use generous timeouts.
- **V6 is a genuine two-repo project**; don't let it block the v3/v4/v5 wins.

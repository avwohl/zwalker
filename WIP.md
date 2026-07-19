# WIP — zorkie ↔ zwalker: compile & solve real Infocom games

Session handoff / resume state. Primary repos:
- **zwalker** `~/src/zwalker` (interpreter + verifier + L2 harness)
- **zorkie**  `~/src/zorkie` (the ZIL compiler being fixed)

## Goal

Build the ZIL **sources** of the games zwalker solved, compile them with zorkie,
and drive the zorkie-compiled builds to verified wins in zwalker. Sources don't
exactly match the released `.z`, so each build may need its own re-derived
walkthrough.

## State after session 8 (2026-07-19): L2 suite 20/20

`python3 scripts/test_zorkie_game.py` → **20/20** games compile from ZIL source
and play to a verified win: microquest, mazekey, reactor, minizork 350/350,
zork1 350/350, zork3 7/7, starcross 400/400, zork2 400/400, deadline, suspended,
infidel, witness, cutthroats 250/250, sorcerer 400/400, enchanter 400/400,
hitchhikersguide 400/400, **suspect**, **ballyhoo 200/200**,
**hollywoodhijinx 150/150**, **wishbringer 100/100** (last four new this session).
zorkie pytest: 696 pass / 3 pre-existing fails (test_color, test_read_v5, TELL
two-space).

### This session's wins (see zorkie STATUS.md for the compiler-fix catalog)
- **suspect** — 3 miscompile fixes (MDL NTH/REST, %<DEBUG-CODE> selector defines,
  gen_call); re-derived 109-cmd route (`walkthroughs/suspect_zorkie_win.txt`).
- **ballyhoo** — unblocked purely by zorkie's round-5 size fixes; the OFFICIAL
  route `walkthroughs/ballyhoo_verified_200.txt` wins with no adaptation.
- **hollywoodhijinx** — tipped-room + vocab-placeholder-overflow fixes; official
  route recorded as `walkthroughs/hollywood_zorkie_150.txt`.
- **wishbringer** — the build genuinely wins; verified by endgame WIN_TEXT via a
  new opt-in `replay_solve` directive **WIN_TEXT_SUFFICIENT** (V3 time-game whose
  score var a zorkie build doesn't expose). Route `walkthroughs/wishbringer_zorkie_100.txt`.

### Machine migration (Linux /home/wohl → macOS /Users/wohl) — RESOLVED
- zorkie's `tests/test-games/` sources were bare gitlinks with **no .gitmodules**.
  Fixed durably in zorkie (`.gitmodules` maps all 51 to historicalsource/*,
  taradinoc/zilf for the zilf pair); `git submodule update --init` restores them.
- dfrotz for zorkie's zilf pytest: `~/esrc/frotz-src/dfrotz` → Homebrew
  `/opt/homebrew/bin/dfrotz` (`brew install frotz`). `ZORKIE_INTERPRETER` overrides.

## Frontier (next session, in priority order)

1. **General size-reduction pass on zorkie** — the single highest-leverage step.
   zorkie output is ~4KB bloated vs the official ZILCH builds, which is the ONLY
   thing blocking the two nearly-won games and the size bucket:
   - `wip/spellbreaker-v3-8fixes` (zorkie branch): 8 general V3 fixes → 440/600,
     lockstep-clean through cmd 330; stalls at 'answer dimithio' (THINGS/PSEUDO
     table, +1.8KB over the V3 cap). Merge once size drops.
   - `wip/trinity-v4-8fixes` (zorkie branch): 8 general V4 fixes → plays through
     cmd 7; stalls at 'buy bag' (HERE? MULTIFROB DEFMAC, +7KB over the V4 cap).
   - Still over the V3 cap: stationfall (~+420), leathergoddesses (x1.zil, ~+1446),
     plunderedhearts, moonmist, lurkinghorror.
   Both WIP branches are gate-green (pytest 696/3, minizork/zork1 350/350).
   NOTE: round-6's THINGS restoration (needed by hollywood) pushed spellbreaker —
   same PSEUDO macro — back over the cap; the size pass re-fits it.
2. **amfv** (V4) — behavioral death mid-route; a prior fix was incomplete and grew
   the build over the V4 cap. Needs a fresh V4 lockstep pass off current main.
3. **planetfall** — BLOCKED ON SOURCE, not zorkie: `comptwo.zil` is a truncated
   historical checkout (ends mid-object at TRIFFID). Do not "repair" by accepting
   unbalanced input. Re-check upstream for a complete revision.
4. cloak frontier: stdlib ISAVE-requires-V5 in a V3 build.

## Adaptive route harness

- `scripts/rederive_route.py GAME.z route.txt --seeds 1-24 [--max-score N]
  [--win-text 'regex'] --out out.txt` — @-steps (@repeat/@until) retried until a
  success condition holds; records the exact stream with `#% MAX_SCORE:` /
  `#% WIN_TEXT:` directives (colon required; win-text/max-score are CLI flags).
- `scripts/draft_adaptive_route.py walkthroughs/x_verified_N.txt --out
  routes/x_zorkie_route.txt` — drafts @-routes. WARNING: the drafter guesses a
  success substring from the verb (push/pull → 'moves') that is often wrong; fix
  each @-step's condition to the game's ACTUAL message before trusting a stall.
- `scripts/sweep_zorkie_corpus.py [games…]` — compile+boot+replay the whole
  corpus, worst-first status table (leathergoddesses entry is x1.zil).

## Diagnosis recipes (proven; unchanged)

- Lockstep differ: `python3 scripts/lockstep.py <official.z> <zorkie.z>
  <walkthrough> <seed>` — first room/score divergence = next bug. Reads V3 status
  globals; for V4 (trinity) adapt a private copy (score/turns via different
  globals / the header).
- PC-trace by wrapping `vm.step` (monkeypatching `vm._call_routine` misses some
  call opcodes). Static disasm: reuse zwalker's opcode tables; routine code =
  high_mem + `comp._last_codegen.routines[name]` + 1 + 2*nlocals.
- dfrotz cross-check oracle: `~/esrc/frotz-src/dfrotz`.
- Bug families to suspect FIRST: (1) in-band marker scans matching legal data —
  fix by positions recorded at emission, never by widening a scan; (2) 8/12-bit
  capacity limits (vocab placeholders, object>255 in V4); (3) ZILCH dialect value
  semantics (void-op truthiness, SET-literal, ACT? vs V? numbering, bare-atom
  values); (4) macro/compile-time evaluation gaps; (5) V4-specific codegen.

## Key files

- zorkie codegen: `~/src/zorkie/zilc/codegen/codegen_improved.py`
- zorkie assembler: `~/src/zorkie/zilc/zmachine/assembler.py`
- zorkie compiler / dictionary / macros / abbrev: `~/src/zorkie/zilc/compiler.py`,
  `zilc/zmachine/dictionary.py`, `zilc/parser/macro_expander.py`,
  `zilc/zmachine/abbreviations.py`
- lockstep differ: `~/src/zwalker/scripts/lockstep.py`
- harness/status: `~/src/zwalker/scripts/test_zorkie_game.py` (L2 suite, 20 games),
  `~/src/zwalker/scripts/sweep_zorkie_corpus.py`, `~/src/zorkie/STATUS.md`

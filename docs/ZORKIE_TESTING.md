# Testing Zorkie with ZWalker's Verified Solves

## Why this note

[Zorkie](https://github.com/avwohl/zorkie) is a from-scratch Python compiler for
Infocom's ZIL/ZILF language that emits Z-machine story files (`.z3`–`.z8`). One of
the original reasons ZWalker exists is to give zorkie a *behavioral* end-to-end
test: not just "does the compiler emit a structurally valid `.z`?" but "does the
game it produced actually **play and win**?" ZWalker already has that oracle — 50
walkthroughs replayed to a verified win under a pinned RNG seed
(`scripts/replay_solve.py`, see [WALKTHROUGHS.html](WALKTHROUGHS.html)).

There is a catch that anyone wiring the two together needs to understand first,
and it is the subject of this note.

**Every one of our 50 verified solves targets a *released* Infocom binary. Zorkie
compiles *historicalsource* ZIL. Those are not the same game, so the walkthroughs
cannot be assumed to verify against zorkie's output — they have to be re-derived
per compiled build.**

Where zorkie is today (2025-12, `~/src/zorkie/WIP.md`, `docs/COMPILATION_*.md`):
it compiles the small test games cleanly (`cloak.zil → cloak.z3` is a real
golden pair) and it *structurally* compiles the big real games — `tests/test-games/infocom-zil/`
vendors ~40 real source trees (zork1/2/3, enchanter, planetfall, sorcerer,
spellbreaker, trinity, …) and Zork 1 emits a ~103 KB story file — but those large
games are at 30–65 % of official byte size and still **hang at runtime** (parser /
`SYNTAX` gaps), and zorkie's current self-test is a byte/structure hexdiff against
a golden binary (`tests/test-games/compare-zcode.sh`), not gameplay. A
walkthrough-to-win test is the natural next rung above that hexdiff.

## The provenance gap: `compile(historicalsource ZIL)` ≠ released `.z`

Two independent reasons, and both apply at once.

**1. The source is a snapshot, not the shipping revision.** The historicalsource
repos are "a snapshot of the Infocom development system at time of shutdown …
canonical, but not necessarily the exact source code arrangement for production"
(the repos' own READMEs). The tree sits at whatever revision existed when the
company folded, which is generally **not** the exact revision that produced any
given commercial release. So it carries a different **release number and serial
date** (Infocom serials are the compile-date stamp), later or in-progress
**bugfixes**, sometimes debug/test verbs or altered response strings, and in some
cases it is an unreleased "final-dev" build that never passed QA. eblong states
outright there is "no guarantee that the 'most current' source corresponds to a
final release." Zork I alone shipped as r2 … r119 with distinct serials; the
snapshot matches at most one of them, if any.

We have already hit this in our own corpus:
[`logs/wishbringer_notes.md`](../logs/wishbringer_notes.md) records that the only
surviving Wishbringer ZIL is **r69 / serial 850920**, but the **shipped binary we
solved is r68 / serial 850501** — every mechanic had to be re-verified empirically
against r68. Compile that source and you get r69, a different game than our
walkthrough targets.

**2. The compiler is a reimplementation, and byte-identity is a non-goal.**
Infocom built with ZILCH (on TOPS-20); ZILCH is lost. ZILF (Jesse/Tara McGrew's
clean-room C# reimplementation) and zorkie both make their own codegen choices,
and ZILF's own docs say producing byte-identical output is an explicit non-goal
(reserved for the ZAPF assembler given identical assembly). So **even feeding
byte-for-byte identical ZIL** yields a different story file: object-table and
property/attribute ordering (hence different internal object **numbers**),
dictionary word ordering and packing, routine/string layout with their packed
addresses and alignment padding, abbreviation-table ("frequent words")
optimization, ZSCII text packing, header fields (version, release, serial,
checksum, length, flags), and the linked parser/verb **runtime library**. The
community describes ZILF builds of historicalsource as "functionally close but not
identical" to the shipped games — playable and (for well-preserved titles)
winnable, but not the same bytes and not always the same behavior. The ongoing
[Infocom Files](https://github.com/the-infocom-files) rebuild effort documents
real per-game divergences on the road to winnability (e.g. a build of The Witness
that doesn't accept `all`; a broken robot status line in Suspended).

## Why our 50 walkthroughs don't transfer as-is

A ZWalker walkthrough is a **fixed command list replayed under a pinned seed** and
checked for a numeric max score or a `#% WIN_TEXT` ending regex. The provenance
gap breaks that in ways we can enumerate — and, tellingly, most of these are
things we **already had to special-case just to handle differences between
released builds**, which is the strongest evidence that a source-compiled build
will need the same treatment:

- **Score globals move per build.** `zwalker/zmachine.py` carries a
  `_SCORE_VAR_OVERRIDES` map keyed to the exact `(serial, release)` because each
  binary stashes the real score in a different global — Wishbringer → vars
  152/151, Cutthroats → var 132 (RATING) + var 215 (clock), Trinity → vars
  170/149. A recompiled build reshuffles globals; `get_score()` reads garbage
  until a new entry is added.
- **Max-score / banner detection is keyed to exact `(serial, release)`.**
  `get_max_score` even distinguishes Zork II from Zork III (both serial 860811,
  different release). Change the release number — which a recompile always does —
  and the game falls out of the map.
- **Which action awards which point is keyed to ZIL line offsets.** e.g.
  [`logs/ballyhoo_notes.md`](../logs/ballyhoo_notes.md) pins all 20 scoring
  milestones to specific `bigtop.zil` / `way.zil` / `outside.zil` offsets; a
  different source revision can shift point values or triggers.
- **Object names and parser vocabulary drift.** The memory notes castle_adventure
  renamed an object `torch` → `flashlight` between releases ("the binary is the
  authority"); a typed command or an `it`/pronoun reference that worked on one
  build fails on another.
- **RNG stream diverges under the pinned seed.** Different codegen + a different
  runtime library change how many times, and in what order, `RANDOM` is drawn.
  Our seed is pinned *after* `start()` for exactly this reason; once the draw
  count/order differs, combat/thief/random-message outcomes differ and a scripted
  win path desyncs. (Boot-time draws matter too — Stationfall rolls its day-1
  clock from `RANDOM 1220` during `GO`; see `logs/stationfall_notes.md`.)
- **Ending text and timing shift.** A different revision emits different
  victory/death wording, so a `#% WIN_TEXT` regex keyed to the shipped string
  misses; and clock/daemon games (Deadline, Cutthroats) fire events on turn
  counters, so any change in per-turn cost lands timed puzzles on the wrong turn.
- **Header/boot expectations.** V4+ binaries read interpreter-supplied screen
  bytes at boot (`_init_interpreter_header`; Theatre/Trinity quit with
  "[Screen too narrow.]" otherwise) — behavior tied to the specific build.

## The plan: a parallel "source-build" verification track

Do **not** hand-edit the released-binary command lists, and do **not** overwrite
them — they are the oracle for the *shipped* games and should stay pinned to those
binaries. Instead, add a parallel track that verifies the *source-compiled* game,
and use ZILF as a reference compiler so you can tell "the source doesn't win" apart
from "zorkie miscompiled it":

    released .z      → walkthroughs/<game>_verified_*.txt      (existing; the shipped-game oracle)
    ZILF(source ZIL) → walkthroughs/<game>_zilf_win.txt        (new; the source-provenance baseline)
    zorkie(source ZIL) — replay the ZILF walkthrough against it (the differential test of zorkie)

The key mechanism is that **we don't rewrite walkthroughs by hand — we re-run the
adaptive recorder.** The 24 `scripts/solve_*_adaptive.py` recorders are
milestone-driven: they drive the game through `GameWalker` segment by segment,
assert score/text milestones, retry alternate phrasings, sweep seeds, and *record
the exact command stream that won*. That is precisely the machinery that already
absorbs build-to-build variation, so pointing a recorder at a freshly compiled
binary and re-recording produces a command list matched to **that** build.

### Step by step (per game)

1. **Compile the source two ways.** Build the game's historicalsource ZIL with
   **ZILF** (the reference/golden compiler) and with **zorkie**. Keep both `.z`
   files and note each build's `serial`/`release` from the header. ZILF is the
   authoritative second compiler here; `tests/test-games/compare-zcode.sh` in
   zorkie already diffs zorkie output against a ZILF/official golden.
2. **Establish the source baseline with ZILF first.** Run the game's adaptive
   recorder against the *ZILF-compiled* binary. Let it re-derive the route: it
   will re-pin the seed, re-key any score milestones, and re-record the winning
   command list for this build. Ship `walkthroughs/<game>_zilf_win.txt` +
   `solutions/<game>_zilf_verified.json`. This proves the *source* is winnable and
   is independent of zorkie.
3. **Re-map what moved.** Where the compiled build's `(serial, release)` differs
   (it will), add it to `get_max_score`, and add a `_SCORE_VAR_OVERRIDES` entry if
   `get_score()` no longer tracks the game's own SCORE verb (find the true score
   global by diffing all 240 globals across two runs that bracket a known score
   change — the method used for Trinity). Re-key `#% WIN_TEXT` to the source
   build's actual ending line, and re-pin the seed to whatever the recorder found.
4. **Differentially test zorkie.** Compile the *same* ZIL with zorkie and replay
   the *same* baseline walkthrough (from step 2) against the zorkie binary with
   `replay_solve.py`. If it also wins, zorkie's codegen is behaviorally correct
   for every path that route exercises. If it desyncs, the `score_timeline` step
   where it diverges — or the first turn whose output differs from the ZILF run —
   localizes the compiler bug; hand that turn to `compare-zcode.sh` /
   `inspect-zcode.sh`.
5. **Record the delta.** Write a short `logs/<game>_provenance.md`: released
   serial/release vs source serial/release, which overrides / vocab / WIN_TEXT /
   seed changed, and any source-build bugs found (the Infocom Files project has
   already catalogued several, e.g. The Witness `all`). This is what keeps the two
   tracks from being confused later.

### Strength gradient (each rung strictly stronger than the last)

- **L0 — structural:** hexdiff zorkie output against a ZILF/official golden
  (`compare-zcode.sh`). This is zorkie's test today.
- **L1 — boots:** load the zorkie `.z` in ZWalker's interpreter and run without
  crashing. `scripts/test_zorkie_compilation.py` already does exactly this for
  `~/src/zorkie/examples/*.zil` — extend it to the compiled real games.
- **L2 — plays and wins:** replay a source-matched walkthrough to a verified win
  (this note). The strongest, semantic, end-to-end signal.

### Where to start

Start where zorkie already round-trips, not with Zork 1 (which still hangs):

- **Cloak of Darkness** is the ideal first target. It is tiny, zorkie ships
  `tests/test-pairs/cloak.zil` with a committed **ZILF 0.8** golden `cloak.z3`
  (the reference build), and we have a source-matched
  [`walkthroughs/cloak_zilf_win.txt`](../walkthroughs/cloak_zilf_win.txt) that
  wins against that golden. The L2 harness (`scripts/test_zorkie_game.py cloak`)
  already drives this. Getting `cloak` to L2 through *zorkie* (it currently fails
  to compile the source — see status below) is the first concrete milestone and
  shrinks the whole pipeline to a game you can debug by hand.
- **Adventure / Colossal Cave** next: zorkie vendors `games/advent_source/advent.zil`,
  and we have `advent_verified_350.txt`. (Note the golden `advent.z3` in
  `tests/test-pairs/` is currently a 14-byte "404" stub — re-fetch it before using
  it as a reference.)
- Then the comp-scale games, then work up toward the full Infocom titles as
  zorkie's routine-codegen coverage (currently ~26 % of official routine bytes for
  Zork 1) closes.

## Current status: cloak through zorkie (2026-07-15)

`scripts/test_zorkie_game.py cloak` today reports: **reference (ZILF golden) L2
PASS** (plays and wins, 5 commands) and **zorkie COMPILE-FAIL**. The
win-verification path and the source-matched walkthrough are therefore proven
correct; the red is entirely in zorkie's compilation of the ZILF standard
library that `cloak.zil` pulls in via `<INSERT-FILE "parser">`.

**`cloak.zil` now parses fully** — three parser/lexer bugs found here were fixed
upstream, and the compile has moved past the whole front end into codegen:

1. zorkie `b5384e2` — special-form dispatch (`CONSTANT`/`ROUTINE`/`OBJECT`/…) was
   firing *inside* quasiquote templates, so `` `<CONSTANT ~.NAME <ITABLE …>> ``
   (pervasive in the library, e.g. `FINISH-PRONOUNS`) failed with "Expected
   RANGLE, got LANGLE". A `quasiquote_depth` counter suppresses that dispatch
   inside templates. (Advanced the parse from `cloak.zil:964` to `:2318`.)
2. zorkie `f3d6e10` — the two `%<…>` compile-time-eval bracket-matchers (in the
   lexer and in `preprocess_zilf_directives`) treated every `!` as a character
   literal and skipped the next char, so a `!<form>` splice had its `<` swallowed
   while its `>` still counted, ending the match one `>` short and leaking a stray
   `>` ("Unexpected closing parenthesis" at `MAP-SCOPE-INIT-STAGES-FROM-BITS`).
   Only `!\X` is a character literal; `!<form>`/`!.var`/`!,var` are splices.

With those, cloak clears **every** parse error and the blocker is now **codegen**:
the first stop is `ZIL0402: Call to LIBRARY-MESSAGE has 4 arguments, but V3 only
supports up to 3 call arguments` (plus `Unknown identifier` warnings for
`NO-OBJECT` / `ENTER`). That is the boundary between "parse the library" (done)
and "compile and run it," which is the larger remaining work:

1. **Codegen / semantics** — the V3 3-argument call limit (the library calls
   `LIBRARY-MESSAGE` with 4 args; ZILF lowers this, zorkie rejects it), unresolved
   identifiers, and zorkie emitting ~26 % of the official routine bytes for a full
   game today.
2. **Compile-time macro evaluation** — actually *running* `%<…>` / `DEFINE` /
   `MAPF` / PROPSPEC to build the tables and routines the library generates
   (zorkie parses these but does not yet evaluate them — its "PROPSPEC routine
   creation" xfail).
3. **Runtime** — even a fully compiled real game "still hangs" per zorkie's
   `WIP.md` (parser/`SYNTAX` runtime gaps).

So cloak-via-zorkie is real compiler work, not one fix. The harness is built to
track exactly this: each item above turns the `COMPILE-FAIL` into a later failure
(or a boot/replay desync the `score_timeline` localizes), until it goes green.

## Reuse these

- `scripts/test_zorkie_compilation.py` — the existing zorkie↔ZWalker bridge
  (subprocess-compile a `.zil`, load the output in `zwalker.zmachine.ZMachine`,
  report compile/boot pass-fail). Generalize its input from `examples/` to the
  compiled real games and add the L2 replay step.
- `scripts/replay_solve.py` — the verifier. Its `#% WIN_TEXT` / `#% MAX_SCORE`
  header directives and per-build `_SCORE_VAR_OVERRIDES` are exactly the knobs a
  recompiled build needs.
- `scripts/solve_*_adaptive.py` — the 24 recorders; the re-derivation engine.
- [`docs/z_format_notes_from_zorkie.md`](z_format_notes_from_zorkie.md) — a
  distilled `.z`-format cross-check (header extension table, V5+ unicode/alphabet
  tables, packed-address formulas, checksum = `sum(data[0x40:]) & 0xFFFF`) for
  validating that a source build's layout is what ZWalker expects.
- **ZILF** as the reference compiler (its integration/interpreter suites are
  already being ported into zorkie's pytest tree; its stdlib+samples are vendored
  at `~/src/zorkie/tests/test-games/zilf/`). Diff zorkie against ZILF, and use
  ZWalker's verified-JSON corpus as the behavioral oracle above both.

## One-line summary

The released `.z` files and the historicalsource ZIL are *different games*; our 50
walkthroughs verify the released binaries. To turn them into a zorkie
compiler-correctness test, re-run the adaptive recorders against a ZILF build of
each game to mint a source-matched walkthrough, then replay that same walkthrough
against the zorkie build — a win means zorkie compiled it right, and a desync
points at the bug.

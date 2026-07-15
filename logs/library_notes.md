# All Quiet on the Library Front - solve notes

- **Title / author / release**: "All Quiet on the Library Front - An Interactive
  Vignette", by Michael S. Phillips. Release 2 / Serial 951204 / Inform v1502
  Library 5/12 (Inform 5). Z-machine V5. IF Comp 1995 entry (5th place).
- **Binary**: `games/zcode/library.z5`.
- **Premise**: you're a slacker student who needs to check out the one
  comprehensive biography of Graham Nelson from the college library to write
  a Computer Science paper on "The History of IF Games". Grab the book and get
  it out of the building before the 5:00 pm closing time.

## Boot behavior
- The title screen is a `read_char` prompt ("[Please press SPACE to begin.]").
  The first recorded command must be a keypress; sending the literal word
  `enter` (harness maps it to RETURN) satisfies it and lands you in the Lobby.
- **Boot is deterministic**: two boots produce byte-identical output, so no
  boot-time RNG. Seed is pinned after `start()`; no `restart` prelude needed.

## Scoring / verification model (important quirk)
- This is a **clock/status-line game**: the status line shows the TIME
  ("Time: 3:00 pm"), not a score.
- The game IS internally scored, **max 30**. `SCORE` prints
  "You have so far scored N out of a possible 30, in K turns"; `FULL` prints
  the per-item breakdown; the winning banner says
  "you scored 30 out of a possible 30, in 36 turns".
- BUT zwalker's `ZMachine.get_score()` does **not** read this game's score
  global -- it returns garbage (0 early, 1 at the end). `get_turns()` likewise
  reads wrong (returns 1). This is the known clock-status-game situation that
  `_SCORE_VAR_OVERRIDES` exists for, but I'm not allowed to patch zwalker.
- Therefore this is verified as a **WIN_TEXT solve** with **no** `MAX_SCORE`
  directive. (A `MAX_SCORE: 30` directive would make replay_solve require
  `get_score()==30`, which returns 1, so it would falsely fail.) `w.max_score`
  is `None`, so the WIN_TEXT-only criterion is `win_seen` alone -> `won=True`.
- The route still collects the full 30/30 (a genuine complete solve); the
  adaptive recorder asserts the true point total via the game's own SCORE text
  (probed with a save/restore so the probe isn't recorded).

## Determinism
- No combat, no random NPCs, no random events. The clock is a plain
  one-tick-per-command counter. The identical command list wins under **every**
  interpreter seed (checked 1-24 -> 30/30 every time). Seed 1 is canonical.

## Route mechanics learned empirically
- **Card <-> key swap** requires first asking the attendant (Alan) about the
  key and having the topic flow (Nelson/rare/key) established via Marion the
  reference librarian; then `give card to attendant` yields the key (+5).
- **Red herring**: `look under stairs` in the Ground Floor Stairwell (+1);
  `give herring to grue` at the Second Floor Stairwell painting (+2).
- **Bio**: unlock+open the rare-books door before entering (avoids any blocked-
  move rollback); `take nelson` (+5). Re-lock behind you.
- **Novel** "Debt of Honor": `search shelves` in Second Floor Stacks (+5).
- **Security gates / technician (Release-2 behavior)**: `ask technician about
  gates` in the Computer Lab makes Tom storm off to dismantle the gates (+2) --
  *this single ask is what disables the gates and enables the win*. Tom then
  follows you to the Lobby, but asking him there again only prints flavor; no
  second ask is required (pjg's release-2 walkthrough implies a second ask, but
  the binary shows it's unnecessary). Avoid `x gates` in the Lobby: it's
  ambiguous with the howto manual Tom carries.
- **Printout**: after Tom leaves, `x printout` auto-takes the Encyclopedia
  Frobozzica printout (+5). Give it to Marion (+2). `xyzzy` gives +1.
- **Endgame**: in the Lobby, `give novel to attendant` (+2, distracts Alan so
  he doesn't notice the smuggled bio), `give key to attendant` (returns your ID
  card), then `e` through the disabled gates -> "*** You have won ***".

## Win text (WIN_TEXT anchor)
- The ending epilogue: you graduate, then "meet an investor who loves IF, and
  you write a wildly successful game...". This investor/IF line is unique to
  the ending (absent from boot), so the directive is:
  `#% WIN_TEXT: investor who loves IF, and you write a wildly successful game`

## Sources (verbatim, gitignored, scratchpad only)
- `logs/library_source_pjg.txt` - pjg's release-2 step solution (IF Archive).
- `logs/library_source_welbourn.txt` - David Welbourn's Key & Compass page
  (release 1). Both cross-checked; final route machine-validated on the binary.

## Verification
- `python3 scripts/replay_solve.py games/zcode/library.z5 walkthroughs/library_verified_win.txt --seeds 24 --out solutions/library_verified.json`
  -> `VERIFIED 1/None at seed 1 | 37 cmds | died=False | won=True`
  (win_text_seen=True). Ran twice, identical.

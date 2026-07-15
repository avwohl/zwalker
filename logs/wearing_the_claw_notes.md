# Wearing the Claw — solve notes

## Identity (confirmed from the running binary)
- Title banner: `WEARING THE CLAW / An Interactive Fantasy / Copyright (c) 1996, 1997 by Paul O'Brian.`
- `Release 3 / Serial number 970327 / Inform v1502 Library 5/12`
- Z-machine V5, `games/zcode/wearing_the_claw.z5`.
- IF Comp 1996 entry (8th place).

## Boot behavior
- The title screen prints `Welcome to WEARING THE CLAW... [Please press SPACE to continue]`
  followed by an Emily Dickinson epigraph — this is a `read_char` prompt.
- Sending `enter` (RETURN in this harness) once satisfies the keypress AND
  flushes the entire prologue (Lord Midel's plea, the family's animal curse,
  the magical transport). After that single `enter` you are standing at
  **Dirt Road** with the game banner already printed. There is only ONE intro
  keypress; the prologue does not pause again.
- Boot draws no RNG: two fresh boots produce byte-identical output. So the RNG
  seed is pinned right after `start()`, and no `restart` prelude is needed.

## Scoring
- **Scoreless.** `score` / `full` are not verbs ("That's not a verb I
  recognise"). `w.vm.get_score()` reads 0 for the whole game and `w.max_score`
  is None. So the solve is a WIN_TEXT solve — no `#% MAX_SCORE`.
- Win is declared by the WIN_TEXT phrase `save another foolish wizard`
  (Marnian's parting whisper in the denouement, printed in the same turn as
  `*** You have won ***`; the phrase occurs nowhere else).

## Endings (for the death/fail tripwires)
- `*** You have died ***` — if you hit/anger Cerberus at South of River, or if
  Lord Midel decapitates you (you didn't `enter cage` in time, or you left it).
- `*** You have failed ***` — if you say `yeyos` without the pendant.
- `*** You have won ***` — Midel defeated, Marnian lifts the curse.
- The game becomes unwinnable (no banner) if the black coat is ever destroyed by
  water, so the route is careful to stow the coat before every wet location.

## Determinism / randomness
- Deterministic puzzle ladder: no timers, no combat rounds, no wandering NPCs.
- The only randomness is flavor text: a fearful child on the beach, crying
  gulls, breeze lulls, the "black fly" that stings near the river. None gate a
  puzzle, so any seed reaches the same ending with an identical command list —
  but because that flavor consumes RNG, exact reproduced TEXT needs a pinned
  seed. Seed 1 is verified; the recorder wins on seeds 1–4 too.

## Walker rollback
- This V5 game exposes real room-object changes, so `GameWalker.try_command`
  detects every genuine move and its blocked-move rollback never fires on the
  winning path. Blocked probes en route answer `There's no path that way.`,
  which is not a rollback pattern. No period-suffixed directions were needed.

## Route correction vs. the source walkthrough
- The source (David Welbourn, Release 3) is accurate, but the flattened
  room-by-room summary I first extracted dropped one step in the Beach maze:
  from **Beach (south)** you must go `e` to **Beach (southeast)** BEFORE the
  `nw. e. e. e. n.` loop back into town to Goodman's. Adding that `e` fixed the
  only divergence; everything else replayed verbatim.

## Key puzzle logic
- **Disguise the paw:** townsfolk (and Old Bill) recoil from the visible wolf
  paw. `buy glove` (costs the gold piece) then `tie glove to paw` (uses the
  handkerchief, since a human glove won't stay on the paw by itself). Only then
  will Old Bill `buy contract` (costs the topaz) for one-way ship passage.
- **The coat** ("PhantomPiercer, BarrierBreaker") is found at the island's
  Southwest Corner. Worn, `touch silver wall` dissolves the mirror wall and lets
  you walk the illusory Styx/Cerberus/brimstone gauntlet. WATER destroys the
  coat, so it must be stowed (remove / put in pack / close pack) crossing the
  river and passing the dripping barrier; wear it only to step past Cerberus,
  and never touch/hit the dog (death).
- **Pendant of Elinor:** Queen Clea gives it after `look in crystal` three times
  (the crystal reveals Midel's treachery). The pendant "destroys lies", so on
  the way out the gauntlet is revealed as **Bare Hallway** + **Foyer**.
- **Word of returning:** `read plaque` at the island Southeast Corner teaches
  `yeyos`; saying it (with the pendant) teleports home to the Town Square.
- **Endgame:** Midel has illusion-swapped himself with Marnian. `give pendant to
  marnian` unmasks the fraud (Midel can't remove the pendant); `wear coat` +
  `enter cage` survives Midel's sword via the coat's magic; `give coat to
  marnian` frees him to bind and transform Midel and lift the curse → win.

## Verification
- `python3 scripts/replay_solve.py games/zcode/wearing_the_claw.z5 \
   walkthroughs/wearing_the_claw_verified_win.txt --seeds 24 \
   --out solutions/wearing_the_claw_verified.json`
  → `VERIFIED 0/None at seed 1 | 160 cmds | died=False | won=True`
  (win_text_seen=True), reproduced on two runs.
- `scripts/solve_wearing_the_claw_adaptive.py` wins on seeds 1–4.

# The Jewel of Knowledge — research notes

## Identity (confirmed from the game's own banner via `version`)
- Title: **The Jewel of Knowledge**
- Author: **Francesco Bova**, Copyright (c) 1999
- **Release 2 / Serial 990710 / Inform v6.15 Library 6/7**, Z-machine V5
- Binary: `games/zcode/jewel.z5`
- Max score: **90** (the game's `score` verb: "out of a possible 90").
  `GameWalker.max_score` is `None` (no banner/serial entry for this post-Infocom
  title), so the walkthrough declares `#% MAX_SCORE: 90`.

## Premise
You are a spelunker on the sixth (final) layer of the Earth's crust hunting the
fabled Jewel of Knowledge for the Druids of Amylya. Your friend Jacob dies in the
opening; you press on alone past three ancient dragons (white/dead, black, red)
and a gypsum-flower maze to the Jewel Room. The TRUE win is to **touch the mirror
and go home WITHOUT the jewel** (taking the jewel is a slow-poison death).

## Determinism (why a pinned seed suffices)
- **Boot is deterministic**: two `start()` boots are byte-identical, so the RNG is
  pinned right after `start()` with no `restart` prelude.
- Every hazard is **turn-based**, not random:
  - Gaseous Geyser erupts on the 4th turn after you enter (both visits).
  - Black Dragon blasts acid on the 14th turn in his lair (13 free turns).
  - On the Divide, the black then red dragon exhaust themselves on fixed turn
    counts; the +10 fires when the red dragon collapses.
  - The Underground River floats you a fixed number of turns.
- The gypsum-flower **maze** exit path is fixed (NE, S, W, N, E) and, better, each
  disturbed flower's sediment *names* the correct exit
  ("...blows it to the <direction>!"), so the recorder reads it adaptively.
- Empirically **all of seeds 1–6 win 90/90 with the identical 248-command list** —
  the game has no route-affecting randomness. Seed 1 is the recorded/verified one.

## Intro skip
The game supports its own `bypass` command ("Type 'bypass' to skip the intro if
you replay the game"). From a fresh boot, `bypass` then `yes` drops you straight
onto the Rocky Plateau (Sixth Layer) carrying only the sword — the exact state the
normal Jacob-conversation prologue leaves you in after the floor collapses. Using
it shaves the five `ask jacob about ...` turns (jewel, dragon, ariana, druids,
amylya — the fifth triggers the fall) and their `[Press any key]` flush. The
alternative full prologue also works and was tested; `bypass` is cleaner.

## Score breakdown (90; from David Welbourn's Release-2 Key & Compass guide,
## each line machine-confirmed against this binary)
Action points (72):
- 2  pull quartz — uncover a fault line
- 3  throw book at outcrop — dislodge unstable rock (also refinds firebug+book)
- 2  smell smoke — inhale lit moon salt (visit the Druids)
- 3  ask Allarah about black dragon — obtain the ebony key
- 2  enter mist — leave the Temple
- 2  clean dirt with moss — clean a dirty floor (reveals trapdoor)
- 3  clean skeleton with moss — reveal air bladder + crampons
- 2  climb porous — reach Shaft Base (also a "visit" milestone, see below)
- 3  put bladder in hole — blow open the porous wall (new passage)
- 3  shoot mushroom (3rd shot) — expert marksman
- 3  break ice with pickaxe — break through the ice wall
- 2  escape flower maze (step onto Obsidian Door)
- 3  unlock door with lockpick — open the obsidian door
- 5  put lye in coat — withstand the Black Dragon's acid
- 2  kill dragon with sword — sever a claw
- 2  se — flee to Top of the Ramp (also a "visit" milestone)
- 3  push boulder — drop boulders on the Black Dragon
- 5  ask dragon about red dragon — a free ride to the Red Dragon's lair
- 10 z on the Divide — withstand both dragons' combined attacks
- 3  shoot chandelier with bow
- 5  remove ring — survive the river (coat warmth reaches you)
- 10 touch mirror — return home, WIN
Sundry item points (6): 2 lockpick, 2 coat, 2 ring.
Location-visit points (12): 2 each for Fifth Layer Dropoff, Shaft Base, Obsidian
Door, At the Top of the Ramp, Red Dragon's Lair, Underground River. These are
collected automatically while walking the route (several coincide with the action
milestones above), which is why the recorder's per-segment score asserts land on
the same cumulative totals the guide predicts.

All 90 points are reachable and reached; nothing is missable in Release 2.

## Key mechanics / gotchas
- The **coat of many colours** (from the dead White Dragon's claws) takes on the
  property of whatever is placed inside it: lye (a base) neutralises the Black
  Dragon's acid; embers keep you warm in the freezing river. The red dragon's
  attack rips the lye back out, freeing the coat for the embers.
- Wear the **ring of heat resistance** to survive the Divide, but you MUST
  `remove ring` in the river or the ring blocks the coat's warmth and you freeze.
- Do **not** kill the Black Dragon before he blasts you (instant death), and do
  **not** shoot him with the crossbow (needs the arrow later; he must stay alive
  to give the ring and the ride). Do **not** take the jewel.
- No `[Press any key]` prompts occur on the `bypass` route.

## Sources (verbatim copies gitignored under logs/jewel_source_*; notes are mine)
- David Welbourn, *Jewel of Knowledge — map and walkthrough*, Key & Compass
  (plover.net) — explicitly "based on Release 2 of the game"; primary authority.
- "pjg" (Paul J. Godfrey) annotated solution, IF Archive `solutions/jewel.sol`
  (labelled Release 1 / 990629; route + point tags cross-checked, agrees).
- Minimal walkthrough, IF Archive `solutions/jewel.wlk` (confirms `bypass`/`yes`
  and the maze verb-variety trick).

## Verification
`python3 scripts/replay_solve.py games/zcode/jewel.z5 walkthroughs/jewel_verified_90.txt --seeds 24 --out solutions/jewel_verified.json`
=> `VERIFIED 90/90 at seed 1 | 248 cmds | died=False | won=True` (run twice, identical).

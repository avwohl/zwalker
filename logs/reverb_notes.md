# Reverberations ("Reverb") — verified-solve notes

## Identity (from the boot banner + header)
- Title: **REVERBERATIONS** — subtitle "A Hectic Voltairian Adventure"
- Author: **Russell Glasser**. Copyright 1996, "Updated and revised 1998".
- Release 1 / Serial number 990110 / Inform v6.10 Library 6/5. Z-machine **V5**.
- IF Competition 1996 entry (finished 13th). Binary: `games/zcode/reverb.z5`.
- Max score **50** (the game's own SCORE verb and status line say "out of a
  possible 50"; confirmed by the death screen "you scored 30 out of a possible
  50" and the win screen "scored 50 out of a possible 50").

## The plot in one line
You are Stanley, a slacker pizza-delivery boy. A pizza delivery to the courthouse
snowballs into foiling mobster Guido's release, exposing the mayor's mob ties,
surviving a car-bomb/earthquake and two assassination attempts, and finally
dropping the whole mafia through the floor — winning the DA (Jill) in the bargain.

## Scoring quirk (decides WIN_TEXT vs MAX_SCORE)
`vm.get_score()` reads Z-machine global 17. In THIS Inform build global 17 is
**not** the score global — it holds the constant **3** for the entire game while
the real score (status-line "Score: N", drawn by the game itself in V5) climbs
0 → 50. `get_turns()` (global 18) is likewise garbage (reads 4 at boot).
`get_max_score()` returns None (no banner/serial entry).

Consequence: a `#% MAX_SCORE: 50` directive can NEVER verify because
`get_score()` never equals 50. So the win is declared by **`#% WIN_TEXT:`
alone**, anchored on the unique closing banner
`You Rule!\s+The game's totally over` (absent at boot). replay_solve prints
"VERIFIED 3/None" — the 3 is exactly that garbage global; the machine-checked
win is `win_text_seen=True` with `died=False`.

I did NOT touch zwalker/zmachine.py — no `_SCORE_VAR_OVERRIDES` entry was added
(WIN_TEXT is sufficient and is the prescribed approach for this class of game).

## Determinism
- Boot draws no randomness: two boots are byte-identical, so no `restart`
  prelude is needed; the RNG is pinned right after `start()`.
- Every hazard is a turn-based scripted event (henchman, thug-gets-up,
  Jill-appears-in-2-turns, earthquake-crack-in-2-turns). With an identical
  command list every seed lines up identically. The final 72-command list wins
  **50/50 on all of seeds 1..24** (verified by both the adaptive harness and
  replay_solve).

## Map (compass)
```
Behind Counter --SW--> Pizza Parlor --S--> Street(by Pizza Parlor)
Street(by Pizza Parlor):  E--> Street(by Department Store)   W--> Street(Near Courthouse)
Street(by Department Store) --S--> Barkley's Clothing Dept
   Clothing:  SW--> Hardware Dept    SE--> Cosmetics Dept   (Hardware<->Cosmetics also E/W)
Street(Near Courthouse):  S--> Courthouse    W--> Downtown
Downtown --W--> Office Building (ground)
   Office Building --U--> 2nd Floor --E--> Law Office (Jill / Gunther & Associates)
   2nd Floor --U--> 3rd Floor --E--> Mayor's Office
   3rd Floor --U/N--> Roof (lightning rod)
Mayor's Office --E(jump out open window)--> "Hangin' Out" --jump--> Law Office
Roof --tie rope to rod; hold rope; jump--> back into Mayor's Office
```
Stair flavor text says "emerge south/north" but the reliable verbs are `u`/`d`
between floors and `n`/`u` up to the roof.

## Score ladder (12 actions = 50)
| action | +pts | cum | where |
| --- | --- | --- | --- |
| search pizza (finds metal file) | 2 | 2 | Courthouse |
| show file to district attorney | 5 | 7 | Courthouse (Guido jailed; Guido grabs the box) |
| get file (from mayor's cabinet) | 3 | 10 | Mayor's Office |
| jump out window | 5 | 15 | -> Hangin' Out |
| jump (into Jill's arms) | 5 | 20 | -> Law Office |
| put bomb in sewer | 5 | 25 | Street (triggers the earthquake) |
| spray thug | 5 | 30 | Cosmetics Dept |
| get rope | 2 | 32 | Hardware Dept |
| show box to guard | 3 | 35 | Downtown (bluff past him with the closed box) |
| jump (rope swing off roof) | 5 | 40 | -> Mayor's Office (mob party) |
| break glass with hammer | 3 | 43 | Mayor's Office (fire-axe case) |
| hit floor with axe | 7 | 50 | WIN |

No points are unreachable — the route hits the full 50/50.

## Timed-death traps (why the recording has no probe turns)
1. Mayor's office: `get file` summons a henchman; `jump out window` must be the
   next real action.
2. Hangin' Out: `kick second window`, then exactly **two** `wait`s bring Jill;
   `jill, hold me` then `jump`. Jumping before she is ready = fatal fall.
3. Cosmetics: `spray thug` -> `kick thug` -> **move immediately** (`nw`). Any
   dawdle and the thug gets up: "*** You are toast ***".
4. Endgame: `get axe`, then exactly **two** `wait`s for the earthquake crack,
   then `hit floor with axe`.

SCORE/FULL and stray `look`/`wait` probes consume a turn and shift these timers,
so none are left in the recording.

## Harness notes
- Pathway: `GameWalker(data); w.start(); w.vm.rng.seed(seed); w.try_command(cmd)`
  — identical to replay_solve, so the recording replays bit-for-bit.
- No walker-rollback issues: every directional command in the route genuinely
  changes rooms and none of the success outputs match the "locked./closed."
  blocked patterns, so no move is silently rolled back. All directions are bare
  words (`n`, `sw`, ...) which replay_solve's VOCAB leaves untouched (it only
  rewrites the period forms "n."/"s."/"e."/"w.").
- No death-marker false positives: the win text and route never contain any
  string in replay_solve's DEATH_MARKERS list.

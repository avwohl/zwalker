# MINI-ZORK I — research notes

Binary: `games/zcode/minizork.z3` — MINI-ZORK I, **Release 34 / Serial 871124**,
Z-machine V3, `vm.get_max_score()`/SCORE verb both report **350**.
Boots cleanly; two boots are **byte-identical** (no boot-time RNG draw), so the
interpreter RNG is pinned right after `start()` with **no `restart` prelude**.

Authoritative source: the reconstructed ZIL of this exact release,
`github.com/the-infocom-files/zork1-mini` (its README pins "Version 34/871124").
MiniZork is a cut-down Zork I: ~69 rooms, **15 treasures** (vs Zork I's 19).
Everything below is read from that ZIL and confirmed empirically against the
binary via GameWalker.

## What is present vs cut
Present: white house + forest + egg tree, Cellar/**troll**, Studio (painting),
Round Room hub, **Reservoir + Dam** (drain puzzle), Temple/Altar/Egyptian/
Entrance-to-Hades/**Hades** (torch, bell, book, candles, coffin, sceptre, skull),
the 10-room **maze** + **Cyclops** + **Thief's Lair**, **Frigid River** +
Sandy Beach/Cave + Aragain Falls + **rainbow** (pot of gold), the **Coal Mine**
(basket/coal→diamond machine), and the **Stone Barrow** endgame.
Cut from Zork I: Loud Room (**platinum bar**), Atlantis Room (**crystal
trident**), Torch Room (torch moved to the Temple pedestal), Gallery (painting
moved to the Studio, east of the Cellar), the clockwork **canary / brass
bauble** (the jeweled egg no longer opens), and many connector rooms.

## Scoring model — exact, and it must land on 325 (verbs.zil / above-ground.zil)
There is **no trophy-case deposit value** (no TVALUE). Points come only from:

- **First TAKE of each treasure** — `SCORE-OBJ` adds the object's `VALUE` then
  zeroes it, so re-taking a stolen/recovered treasure never double-counts.
  The 15 treasures and their VALUEs (sum = **215**):
  jeweled egg 6, painting 7, ivory torch 12, gold coffin 13, sceptre 9,
  crystal skull 22, trunk of jewels 15, jade figurine 13, sapphire bracelet 10,
  huge diamond 25, bag of coins 11, silver chalice 20, large emerald 18,
  jeweled scarab 15, pot of gold 19.
- **Room-entry VALUE** (awarded once via `SCORE-OBJ` in `GOTO`): Kitchen 10,
  Cellar 25, Thief's Lair 20 = **55**.
- **Scored events** = **55**: kill troll 10 (`KILL-VILLAIN`), open the dam
  sluice gates / LOW-TIDE 20 (`BOLT-F`), `pray` at the Altar 15 (`V-PRAY`,
  `ALTAR-SCORE`), reach the Drafty Room while it is lit 10 (`NO-OBJECT-ROOM-F`,
  `DRAFTY-ROOM-SCORE`).

215 + 55 + 55 = **325**. The win is in `LIVING-ROOM-F` (M-END on `PUT ... IN
TROPHY-CASE`): when `COUNT-TREASURES(case) == 15` **AND** `SCORE == 325`
(both EXACT equality), it fires `<SETG SCORE 350>`, sets `WON-FLAG`, and clears
`INVISIBLE` on the parchment `MAP` and `TOUCHBIT` on West-of-House. Then
`take map`/`read map` points SW; West-of-House gains a `SW TO INSIDE-THE-BARROW
IF WON-FLAG` exit, and entering the Barrow calls `FINISH` — the victory.

**Consequence:** a single **death is −10** (`JIGS-UP`), which makes the exact
325 unreachable → the run must be perfectly **death-free** and hit every scored
action exactly once. No other SCORE writes exist in the source.

## Randomness / creatures
- **Troll** (Troll Room, STRENGTH 2). `HERO-BLOW` vs troll is a flat 45% to
  land; death gives +10 and drops the axe. Dies in ~2–7 sword blows; a few
  seeds let it kill the player, so the seed is swept.
- **Thief** (`thief.zil`, STRENGTH 5) roams every non-`SACREDBIT` underground
  room (`I-THIEF`) and steals `TREASUREBIT` items from rooms/inventory into his
  bag; `DROP-JUNK` only ever drops non-treasures, so stolen **treasures stay in
  his bag until he dies**, when `DEPOSIT-BOOTY` drops them all in his lair.
  Player to-hit is **15 + SCORE/4** (`HERO-BLOW`) → ~72% at score 227, ~91% at
  305, so fight him **late/high**. He attacks at 60%/round; at STRENGTH 6 the
  player survives a high-score fight comfortably. **The torch is TREASUREBIT**,
  so he can steal your light — the route kills him *before* the coal-mine trip
  (which depends on the torch) and keeps the lamp lit as a fallback.
- **Cyclops** (Cyclops Room) blocks the stairs up to the lair — not a fight:
  say **`ULYSSES`** and he flees through the east wall, setting `MAGIC-FLAG`
  (opens Cyclops→Living Room, the return shortcut) and clearing the stairs up.
- **Grue**: moving *into* darkness is an 80% instant kill (`GOTO`/`V-WALK`);
  there is **no** stationary dark-room grue daemon, so dropping items in the
  dark is safe — only the next *move* must be into a lit room.
- **Vampire bat** (Bat Room): without the **garlic** held, `FLY-ME` drops you
  in a random Coal-Mine cell. Carry the garlic (from the Kitchen sack).
- **Frigid River**: the boat drifts downstream a seed-dependent number of turns
  per command; the buoy (→ emerald) is grabbable only at River-3, and a 4th
  drift is the falls (death). The recorder spams `take buoy` until it sticks,
  then lands east on Sandy Beach.

## Timed / stateful gotchas baked into the route
- **Trap door** bars behind you on the first Cellar entry (one-way down); the
  return path is Cyclops→Living-Room (after `ULYSSES`) or the Slide-Room→Cellar
  chute. The Temple is a one-way rope drop, exited via Altar→Windy-Cave or by
  `pray` (→ Forest Edge).
- **Carrying limits**: LOAD = `100 − (6−STRENGTH)*10`, so troll/thief wounds
  cut capacity — `@heal` (wait to "perfect health") before heavy lifting (esp.
  the size-55 coffin). Item **count** > 7 risks a "holding too many things"
  fumble (`FUMBLE-NUMBER 7`), so keep ≤7 and stash spare tools on the
  `SACREDBIT` (thief-free) Living-Room floor.
- **Lamp** burns out after ~140 lit turns (`LAMP-TABLE` 75/50/15/0), so the
  ivory **torch** is the primary light; the lamp is backup + the mine light.
- **Coffin** (size 55) cannot be taken *down* from the Altar (`COFFIN-CURE`),
  so it leaves only via `pray`. Its weight also forbids carrying it with the
  pot, so the sceptre/rainbow (Trip 4a) and the coffin (Trip 4b) are split.
- **Skull exorcism** at Entrance-to-Hades: `ring bell` (spirits recoil, drops
  held candles), re-take + `light match` + `light candles with match`, then
  `read book` (XB→XC timing windows, 6 then 3 turns) → `HADES-FLAG`, gate opens.
- **Coal→diamond**: the Gas Room kills instantly if you carry any *lit flame*
  (torch/candle/match), so cross it on the **lamp**; the flaming torch rides
  the basket down the shaft to light the Drafty Room (+10) and Machine Room.
  Ladder-Room↔Drafty-Room requires **empty hands** (no item > weight 4), so
  drop tools at the Ladder Room and shuttle coal/torch/screwdriver/diamond via
  the basket (`lower basket` from the Shaft Room; `raise chain` from the Shaft
  Room when the basket is at the bottom and out of scope). Machine: `open lid`,
  `put coal in machine`, `close lid`, `turn switch with screwdriver`, reopen.

## Verification
`scripts/solve_minizork_adaptive.py` plays this route under a pinned seed,
adapts the four random spots (troll/thief melee, heal waits, buoy), and records
every command. Over seeds 1–8 it wins clean at 1, 4, 7, 8 (others: troll/thief
kill the player). Seed **1** is shipped.
`walkthroughs/minizork_verified_350.txt` (405 cmds) replays via
`scripts/replay_solve.py --seeds 24` → **350/350, died=False, won=True**,
reaching the Stone Barrow.

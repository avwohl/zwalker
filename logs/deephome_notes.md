# Deephome: A Telleen Adventure — research notes

Game: *Deephome: A Telleen Adventure* by Joshua Wise (1999). Inform 6, Z-machine
V5. Release 1 / serial 991210. Binary: `games/zcode/deephome.z5`.

You are a Dwarven Reclaimer sent to make the abandoned mountain city of Deephome
ready for its people's return. Tasks (from the King's Order you start with):
restore **power**, restore **water**, open the **gate**, and make the city
**safe** — i.e. deal with the three spirits haunting it.

## Win condition and score
- The game ends `*** You have won ***` when **all** of: power on, water on, gate
  open, and all three spirits handled. It does **not** require max score.
- SCORE reports "out of a possible 300". The real maximum is **300**; the top
  rank at exactly 300 is: "You have gone beyond the call of duty and vanquished
  the spirits. You will be remembered forever by your people."
- Off-by-one oddity: visiting *every* one of the 46 Deephome rooms gives 46
  location points and pushes the total to **301**, which prints the absurd "301
  out of a possible 300" and, ironically, a *lower* rank ("a rather successful
  adventurer and a boon to your people"). Our route therefore intentionally
  skips exactly one optional room (**Dwarven Village**, +1) so the win lands on
  the canonical **300** with the top rank.

### Point table (sums to 300 on our route; 301 if all 46 rooms visited)
- +5   entering the city (push the mountain symbol; opens the barred door)
- +45  visiting Deephome rooms (1 each; 45 of the 46 — Dwarven Village skipped)
- +10  taking the lump of coal (dig the coal-mine rock wall with the pickaxe)
- +30  power on (fuel + fire the City Generator)
- +10  driving off the terrock (green moss into its waterfall nest)
- +30  water on (turn the Water Works wheel, after clearing the intake pipe)
- +40  opening the city gate (seat the gear, throw the lever, push the button)
- +20  defeating the Eranti (combat, south of Ember)
- +10  catching the squirrel (hole + net + acorns + climb the tree)
- +20  giving the benign spirit a host (release the squirrel in the throne room)
- +30  exorcising the dark spirit Indanaz in the temple
- +40  exorcising the shadow spirit Kebarn in the treasury

## The three spirits
- **Indanaz** — Dark Spirit (class Ternalim). First seen in the Main Hall, where
  it paralyses you for ~4 turns, then relocates to the Great Temple of Kraxis.
  Banish (in the temple): drop the gold coin, pour water on it, put ashes on it,
  put the four-leaf clover on it, `pray to Kraxis`, then `manaz`.
- **Kebarn** — Shadow Spirit (class Partaim). In the Treasury vault. Banish:
  open + drop the net, put the coin in the net, pour water on the net, take the
  coin back, `pray to Kraxis`, then `manaz`.
- **Cholok** — benign Luminous Spirit (class Yetzuiz). In the Throne Room. Not
  exorcised — she needs an animal host: catch the squirrel in the net and open
  the net in the throne room; she inhabits it and leaves.
- The encyclopedia/exorcism-book lookups in the walkthroughs are **player hints
  only** — the rituals are physical actions; no lookup is a game-state
  prerequisite (verified: the route performs zero lookups and both rites work).
- Death: saying `manaz` without an immediately-preceding `pray to Kraxis` kills
  you; the terrock or the Eranti can kill you in combat. We never trigger these.

## Puzzle dependency chain (why the route is ordered as it is)
- Metal ("sharp") pick <- forge scraps: needs the **hammer** (Eranti reward) +
  a torch-lit forge + the anvil. So the Eranti must be beaten *before* the pick.
- Pick unlocks: the bank **deposit box** (-> large key) and the shack **chest**
  (-> net).
- Large key unlocks the vault door -> the **gold coin** (both rituals need it).
- Net is used first to trap the squirrel, then (freed after the throne-room
  release) reused for the Kebarn rite.
- Water bottle is fillable only after **water is on**; it's used (and refilled)
  for both rites. Ashes come from burning a blank paper with the torch.

## Randomness / determinism (basis for a pinned seed)
- **Boot draws no randomness** — two boots are byte-identical — so the seed is
  pinned right after `start()`; no `restart` prelude is needed.
- The **only** state-relevant randomness is the **Eranti fight** at the pond.
  Combat rolls are seeded; with the sword wielded + shield worn the dwarf
  auto-heals between blows and reliably wins. The recorder loops `kill eranti`
  until the score jumps +20 and records exactly the count for the chosen seed
  (10 blows at seed 1, never in danger). Adaptive sweep: the route reaches
  300/300 at seeds 1–5 (blow counts 10/3/9/3/5); seed 6 is an unlucky seed where
  a bad combat streak kills the dwarf and the recorder correctly aborts it. The
  verified walkthrough is pinned to seed 1, and replay_solve stops at the first
  winning seed (seed 1), so the unlucky seeds are never used.
- Everything else is turn-based clockwork: the Main-Hall paralysis (~4 turns;
  waited out with five `z`s) and the metal scraps melting in the furnace (one
  `z`). Identical command lists line these up identically under any seed.

## zwalker / interpreter quirks (V5; none required touching shared code)
- `vm.get_current_room()` is stuck at object **10 ("west wall")** the entire
  game (this is why the prior `solutions/deephome_solution.json` exploration got
  stuck examining the door in a phantom "west wall" room). State here is tracked
  from the parsed status line and room headers instead.
- `vm.get_score()` reads V3 status-var 17, which on this V5 build is a fixed low
  value (5 at boot, 10 at end) — **never** the real score. The TRUE score is the
  status-line "Score: N" (global var 21). We read the status line.
- Consequence for verification: a `#% MAX_SCORE: 300` directive would make
  `replay_solve.is_won` compare the broken `get_score()` against 300 and report
  **won=False** (confirmed empirically: "VERIFIED 10/300 ... won=False"). The
  fix would be a `_SCORE_VAR_OVERRIDES` entry in `zwalker/zmachine.py`, but that
  is shared code and out of bounds. So the walkthrough is verified purely via
  `#% WIN_TEXT: \*\*\* You have won \*\*\*` (with no MAX_SCORE), which makes
  `is_won` reduce to `win_seen` -> **won=True**. The JSON's `"score": 10` is this
  documented `get_score()` artifact; the real verified score is 300.
- Object-scope gotchas (must reveal before taking): `x clover` then `take four
  leaf clover`; `look in box` then `take large key`; `search wealth` then `take
  gold coin`. The pickaxe answers to "axe"; the sharp pick answers to "metal
  pick"; the coin must be acquired as "gold coin" (later "coin" resolves).
- The blocked-move rollback hazard (`try_command` undoing a move that looks
  unchanged and reads "locked./closed.") never fires on this route: no needed
  move's output matches a BLOCKED_PATTERN, so plain short directions are safe
  (no period-suffix workaround needed). A full-route anomaly scan is clean.

## Railway
Four station wings (Main Hall, Smithy Court, Barracks, Treasury) linked by a
rail car: `enter car`, `push <yellow|green|red> button`, `out`. The
colour->destination is not a simple fixed map, so the route just pushes the
button the walkthrough uses from each station and verifies the destination.

## Sources (downloaded verbatim to gitignored logs/deephome_source_*.txt)
- David Welbourn's Key & Compass map+walkthrough (Release 1) — plover.net.
- AllThingsJacq ClubFloyd transcript (2025) — allthingsjacq.com.
Notes and route here are in my own words; the route was rebuilt and
machine-verified against the binary.

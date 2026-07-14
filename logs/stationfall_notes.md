# Stationfall (Release 107 / Serial 870430, Z-machine V3) — mechanics notes

Own synthesis from the official ZIL source (github.com/historicalsource/stationfall,
files `ship.zil`, `station.zil`, `village.zil`, `globals.zil`, `interrupts.zil`,
`verbs.zil`, `misc.zil`), cross-checked against two independent human
walkthroughs and, decisively, against the r107 binary itself via the GameWalker
pathway. Where a citation and the binary disagreed, the binary won (none did).

Score/turn globals are the standard V3 pair: score = global 1 (variable 17),
turns = global 2 (variable 18). "Turns" is the Galactic Standard Time
chronometer (`MOVES`, mirrored from `INTERNAL-MOVES`, misc.zil:362-369), not a
move counter: a non-move action elapses 7 millichrons (misc.zil:381,601), a
room-to-room move 22, WAIT 40, eating 15, drilling 30, the storage-bin scene
63, and each spacetruck flight turn 240 (misc.zil:355). Max score 80
(rank table verbs.zil:72-86; 80 = "Intergalactic Mega-Hero").

## The determinism problem: boot-time RNG

`GO` sets the day-1 clock to `4430 + RANDOM 1220` (misc.zil:190) — this draw
happens during boot, BEFORE the harness pins the RNG seed, so the raw game is
not reproducible even under a pinned seed. Verified empirically: three boots
gave 5558 / 4874 / 5617.

Fix used by the route: the first two recorded commands are `restart` + `yes`.
The Z-machine RESTART opcode reloads memory but keeps the interpreter RNG
object, so `GO`'s `RANDOM 1220` re-runs on the *seeded* stream and the whole
game becomes a pure function of the seed (verified: seed 1 always restarts at
GST 4706). Everything below assumes that prelude.

A second boot-anchored value: `WAKING-UP` resets the clock each morning to
`1600 + RANDOM 80` (globals.zil:1067) — also seeded after the restart trick.

## Copy protection: the spacetruck course (VARIABLE, parsed at runtime)

`SPACETRUCK-TYPE` (verbs.zil:2126-2162) accepts a course number only when both
pilot and copilot seats are occupied (Floyd climbs in by himself). The correct
course is computed from the chronometer *at the moment of typing*
(verbs.zil:2140-2152):

    X = INTERNAL-MOVES / 50 ; X = X - 132 ; X = X * X ; X = X / 4
    RIGHT-COURSE = X + 103          (integer division, truncating)

(the printed table on the original "Assignment Completion Form" feelie).
The harness reads the turns global and types `((t//50 - 132)**2)//4 + 103`.
A wrong course leaves the truck dead in empty space — unwinnable, and sleeping
there suffocates you (globals.zil:1015-1025, ship.zil:1222).

Docking is `I-SPACETRUCK` counter 5 with the right course: +5 and it queues
the station interrupts `I-WELDER -1`, `I-FLOYD -1`, `I-PLATO 750`,
`I-ROBOT-EVILNESS 1000` (ship.zil:1198-1207).

## Scoring table (sums to 80)

Routine awards (each also bumps ROBOT-EVILNESS +1 except docking):
| pts | event | citation |
|-----|-------|----------|
| 5 | spacetruck docks at the station (right course) | ship.zil:1205 (or globals.zil:1135 if asleep) |
| 6 | validated Illegal Space Village Entry Form in a connection slot (opens iris hatch) | globals.zil:742 |
| 3 | first sleep — waking into day 2 | globals.zil:1072 |
| 6 | ostrich sticks its head up the PX dispenser hole and knocks out the stuck item | station.zil:322 (OSTRICH-INTO-DISPENSER) |
| 3 | putting the explosive into the (medium) hole drilled in the Commander's safe | station.zil:984 |
| 7 | taking the seven-pointed star while hanging from the balloon | station.zil:1509 (awards DIODE-M's VALUE 7, then zeroes it; DIODE-M VALUE at station.zil:1542) |
| 7 | Floyd knocks the stun ray from Plato's hands (requires FLOYD-TOLD) | station.zil:3588 |
| 4 | turning the casino roulette wheel (reveals exits) | village.zil:734 |
| 5 | wrapping the foil over the pyramid — the win | station.zil:3950 |

Object VALUEs, +awarded on first take via SCORE-OBJ (verbs.zil:2585-2592):
| pts | object | citation |
|-----|--------|----------|
| 3 | stick of ostrich nip (pet-store ceiling panel) | village.zil:546 |
| 5 | coin (vaporize the loan shark's strongbox with the zapgun) | village.zil:1632 |
| 4 | reflective platinum foil (break the barbershop mirror) | village.zil:304 |
| 7 | key (inside the blown safe) | station.zil:1030 |
| 3 | medium drill bit (Floyd pulls it from the hot heating chamber) | station.zil:2537 |

Room VALUEs, awarded on first entry via DESCRIBE-ROOM (verbs.zil:2660-2668):
| pts | room | citation |
|-----|------|----------|
| 5 | Armory (security door needs ID rank > 6) | station.zil:1063 |
| 3 | Vacuum Storage (outside the village airlock) | village.zil:1346 |
| 2 | Top of Air Shaft | station.zil:3703 |
| 2 | Factory | station.zil:3873 |

5+6+3+6+3+7+7+4+5 + 3+5+4+7+3 + 5+3+2+2 = **80**.

## The clock, days, and hard deadlines

- Hunger: first warning at boot+1330 (misc.zil:197), then +450/+300/+150/+150,
  death at level 5 (globals.zil:1194-1220). Any meal resets and requeues
  +2250 (verbs.zil:684-703). Foods: two goo blobs (survival kit), Thermos
  soup, grocery vacuum taffy, Greasy Straw nectar. Waking with any hunger sets
  level 3 with a 200 warning ("incredibly famished", globals.zil:1122-1127).
  The route eats: gray goo (docking), orange goo (day-2 breakfast), soup
  (lunch, usually at the warehouse), taffy as harness insurance.
- Sleep: warnings begin at absolute GST 8100 (`QUEUE I-SLEEP-WARNINGS
  <- 8100 INTERNAL-MOVES>`, misc.zil:196), then +320/+160/+80/+40, collapse at
  level 5 (globals.zil:899-947). Sleeping anywhere but a bed after docking is
  a `PROB DAY*40` machine-rolls-over-you death (globals.zil:1041-1048).
  In the Sick Bay bed the level-1 warning converts to I-FALL-ASLEEP in 16
  (globals.zil:907-912). Sleeping on the Duffy (SPACETRUCK-COUNTER -1) is the
  brig/firing-squad death (globals.zil:1026-1040, counter init ship.zil:1152).
  Sleeping with the nip near the awake ostrich, or with the explosive in the
  drilled hole, is death (globals.zil:1038-1049); in a worn spacesuit too
  (globals.zil:1010-1017).
- Day 3+ is designed as a losing spiral: the chronometer stops (MOVES 9947,
  globals.zil:1069), the elevator becomes a death trap (verbs.zil:2163-2172),
  the exercise machine relocates (globals.zil:1140-1145). The route finishes
  on day 2 and never touches the elevator.
- Endgame deadline: opening the Dome bin queues I-ANNOUNCEMENT 140
  (station.zil:2117); announcement 1 requeues itself +470, announcement 2
  queues I-LAUNCH 200 (station.zil:3661-3676); launch = reactor H-bomb death
  (station.zil:3678-3691). Falling through the bottom grating re-queues
  I-ANNOUNCEMENT 1 (station.zil:2200), i.e. announcement 2 fires the next
  turn and the real budget from the fall is ~200 millichrons (~28 actions) —
  the route needs ~5.

## Welders (the roaming hazard)

`I-WELDER` runs every turn after docking (interrupts.zil:5-43). In any lit
room without NWELDERBIT, while not in bed and not stunned, a welder appears
with probability NUMBER-OF-WELDERS % (= 4, globals.zil:1281), consuming an
extra `RANDOM 4` for its number. Once present: turn 2 "moves closer", turn 3
quiet, turn 4 kills. Any successful room change despawns it ("you hear the
welder move off"). The harness bounces out-and-back via a per-room table the
moment welder text appears, and parks all multi-turn stationary work in
NWELDERBIT rooms (Chapel, Laundry, Quarters, Main Storage, Robot Shop, Casino,
Flophouse, Pawn Shop, Loan Shark, Doc's, Field Office, Paper Recycling, Sick
Bay, Airlock, Vacuum Storage, Dome, Armory, File Room). Shooting a welder
removes it permanently (globals.zil:1240-1260) but wastes a zapgun shot; the
route never needs to. Entering the air-shaft grating dequeues I-WELDER for
good (station.zil:2205).

## Floyd

Picked up on the Duffy: `insert robot form in slot`, `type 3`
(verbs.zil:2093-2113). He auto-boards the truck and takes the copilot seat.
`I-FLOYD` (interrupts.zil:105-356) runs every turn and is the game's biggest
RNG consumer (PROB 45 to act; PICK-ONE chatter; PROB 80 follow; PROB 17
re-join; PROB 6 wander off). Hazard: with PROB 6 he pockets the FIRST object
lying in your room (interrupts.zil:188-205) — everything except the nip,
spacesuit, detonator, timer and explosive. The route therefore never leaves a
needed stealable item on a floor: the only stash is detonator+timer in the
Commander's Quarters (detonator has CONTBIT, timer is exempt, and the pilfer
branch only ever inspects the first object). At ROBOT-EVILNESS > 17 he
migrates to the Factory (interrupts.zil:266-274) wearing his eye patch; the
bin explosion forces him there anyway (station.zil:2119).

Required Floyd interactions: fetching the medium bit from the heating chamber
("Yikes, it's hot!", he drops it — the +3 is scored when *you* take it), and
the Plato rescue below. In the finale you must `shoot floyd` (ship.zil:497-513,
sets FLOYD-SHOT, ROBs his pockets onto the Factory floor) before the pyramid
can be approached; wrapping the foil then wins (+5) — PYRAMID-F,
station.zil:3893-3969. Never TAKE the dropped stun gun: with FLOYD-SHOT it
queues I-LAUNCH -1 (station.zil:3622-3625) — instant loss.

## Plato and the attack (the +7 floating event)

Plato is introduced by I-PLATO (station.zil:3410, queued 750 after docking).
`I-ROBOT-EVILNESS` fires every 1000 millichrons, +1 evilness each time
(station.zil:3466-3472); nearly every scoring event adds +1 more. Once
evilness > 11 at a tick, I-PLATO-ATTACK is queued and fires at the first turn
where you are: not with Plato already in the room, not in the Airlock/Vacuum
Storage, no welder present, not in bed, in the light (station.zil:3481-3495).
Stage 1 stuns you and ROBs your whole inventory onto the floor
(station.zil:3499-3504); stages 2-4 are monologue; stage 5 kills you UNLESS
FLOYD-TOLD is set, which any of "floyd, help / save me / kill plato / take
gun" does while stunned (ship.zil:324-333). Rescue = +7 (station.zil:3588),
Plato is destroyed. The harness watches every output for the stun text,
answers `floyd, help` each stun turn, then re-takes the ROBbed inventory
(dropping re-grabbed junk so the 6-item hand limit can't jam later takes).
In practice the attack fires between GST ~3400 and ~4600 on day 2 (evilness
crosses 12 around the foil/star events); the route also waits for it
explicitly before arming the bomb, since being stunned next to a ticking
timer is fatal.

## The village, ostrich, balloon, star

- Iris hatch: one validated form opens BOTH connections (single global flag,
  globals.zil:744; VILLAGE-BOUNDARY-F village.zil:5-33). The crumpled form is
  in the Printing Plant trash can (station.zil:2715-2740); the laundry presser
  irons it (station.zil:1360-1424 — do not linger: I-PRESSER kills you ~50
  millichrons after turning it on, station.zil:1426-1443); the validation
  stamp is under the Commander's bed (globals.zil:876-882) — the log tape is
  pure hints and the route skips it (the reader also explodes after 14 turns,
  interrupts.zil:435-456).
- ID card: Shady Dan's machine sets any rank 1-10 (village.zil:1830-1890);
  the armory security door needs rank > 6 (station.zil:3051-3079) and
  auto-closes after ~2 turns — enter immediately. Never remove the magnetic
  boots while carrying the ID (scrambles it, village.zil:1946-1950); the
  route drops the ID at End of Corridor right after the armory.
- Ostrich (village.zil:1687-1768): starts awake in Doc Schuster's; follows
  whoever carries the nip visibly (verbs.zil:2974-3017, handles hatch/gravity
  crossings). At the PX with the item stuck ("type 6" after the coin —
  dispenser code station.zil:200-326), `scare ostrich` makes it stick its
  head up the hole: +6 and the timer drops out. `give nip to ostrich` knocks
  it out cold and ends the escort.
- Balloon (village.zil:378-540): open the cage, then spray the spore can in
  an adjacent room to pull it one room at a time (village.zil:1458-1533);
  12 sprays available (SPRAY-COUNTER, village.zil:1535), the route needs 9
  plus re-sprays after welder bounces. It will not enter the Chapel while the
  eternal flame burns (village.zil:1496-1500) — the pulpit switch turns the
  flame off (station.zil:1550-1640). Grabbing the leash in zero-g just makes
  it fart and scatter your inventory (village.zil:480-490); in the Chapel
  (gravity) it lifts you to the star: take star = +7, the M-series hyperdiode
  is inside. The spacesuit glove also blocks the leash grab.
- The spacesuit cannot pass the iris hatch (village.zil:10-15), so suit and
  boots live and die in the village; both come off in the repressurized
  airlock.

## The safe, the bomb, the melt clock

- The drill (Paper Recycling Plant) drills exactly ONE hole ever
  (MAKE-HOLE-WITH-DRILL, station.zil:998-1015 — a second attempt kills the
  drill), so it must be the safe, with the MEDIUM bit installed (small = too
  small for the explosive, DRILLED-HOLE-F station.zil:965-985).
- The explosive (FREZONE) is tethered in Vacuum Storage (village.zil:1363);
  suit + boots + headlamp required (vacuum is dark). Closing the outer
  airlock door starts I-EXPLOSIVE-MELT every turn (village.zil:1250-1255):
  MELT-COUNTER += C-ELAPSED, or C-ELAPSED/4 inside the *closed* Thermos;
  at >210 it sublimes (interrupts.zil:358-383). Budget in the closed
  Thermos ≈ 840 millichrons — enough for the walk back plus assembly, but
  not for detours; the harness fetches it late and assembles immediately.
- Assembly: explosive into the hole (+3), `connect detonator to explosive`,
  `connect timer to detonator` (DETONATOR-F station.zil:1796-1860), with the
  M-series hyperdiode (from the star) inside the detonator — the J-series
  diode from the Studio bursts (station.zil:1526-1532). Timer max 100
  (station.zil:368); it counts down by C-ELAPSED per turn (I-TIMER,
  interrupts.zil:385-433). The route sets 22 so the boom lands on the very
  next room-move, one room away in the office (same-room detonation is
  death); the blast opens the safe and queues
  I-LIGHTS-OUT in 20+RANDOM 200 (interrupts.zil:415) — after that the whole
  station is dark except Factory/Computer Control (I-LIGHTS-OUT,
  station.zil:3635-3659) and the headlamp (92 turns of battery,
  village.zil:240, I-HEADLAMP interrupts.zil:45-62) carries the rest of the
  game. Key from the safe: +7.

## Endgame

Unlock the Dome storage bin with the key, open it: scripted explosion knocks
you out, ROBs your inventory onto the Dome floor, loosens the grating, moves
Floyd to the Factory and starts the announcement clock (HOUSING-F,
station.zil:2111-2140). Re-take zapgun/foil/jammer (headlamp stays worn),
bend the grating, enter it (Top of Air Shaft +2, welders permanently off),
7 x down, `turn on jammer` (set to 710 with the twenty-prong fromitz board
plugged in — the frequency is hard-coded, station.zil:3780 and the gym sign
globals.zil:453), `open grating`: you fall into Computer Control, the jammed
exercise machine freezes and the forklift arrives (I-EXERCISE-MACHINE,
station.zil:3776-3805); `turn off jammer` makes the waking machine and the
forklift destroy each other (JAMMER-F, station.zil:152-165). Up to the
Factory (+2), `shoot floyd`, `put foil on pyramid`: +5, USL/TELL-SCORE/QUIT —
the Oliver ending ("Play game... Play game with Oliver?"), final banner
"Your score is 80 (of 80 points), giving you the rank of Intergalactic
Mega-Hero."

## RNG consumers and how the route absorbs them

| consumer | draw | absorption |
|----------|------|------------|
| boot start time | RANDOM 1220 pre-seed (misc.zil:190) | `restart`+`yes` prelude re-rolls it on the seeded stream |
| morning clock | RANDOM 80 (globals.zil:1067) | post-seed, deterministic per seed |
| welder spawn | PROB 4 + RANDOM 4 per eligible turn | room-table bounce; NWELDERBIT rooms for stationary work |
| Floyd chatter/wander/steal | many PROBs per turn (interrupts.zil) | deterministic per seed; no stealable floor stashes; Factory ROB recovers anything he carried off |
| Plato attack placement | eligibility scan per turn | output-triggered handler works anywhere; forced wait before bomb assembly |
| dreams / radio / Greasy Straw whiff | PROB 60/30/33 + PICK-ONE | cosmetic |
| lights-out delay | 20+RANDOM 200 after the blast | headlamp already on before leaving the File Room |
| sleep-outside-bed death | PROB DAY*40 | never sleeps outside the Sick Bay bed |

## Verification status

Harness: `scripts/solve_stationfall_adaptive.py` (GameWalker pathway, seed
pinned after `start()`, `restart`+`yes` recorded prelude). Score checkpoints
asserted at dock=5, form-drill=5, village-form=14, day2=17, village-east=20,
armory=25, px-timer=36, star=47, frezone=54, key=71, pyramid=80 (+7 attack
bonus applied wherever the floating Plato attack has already landed).

Seeds tested: 1-20 -> 20/20 at 80/80, won-text confirmed, no deaths
(345-379 commands per seed). Large seeds 99, 777, 12345 -> 3/3.
Shipped recording: `walkthroughs/stationfall_verified_80.txt` (seed 1,
375 commands including the restart prelude and one score-flush `z`),
verified three times (independent random boots each run) via
`python3 scripts/replay_solve.py games/zcode/stationfall.z3
walkthroughs/stationfall_verified_80.txt --seeds 5`:
VERIFIED 80/80 at seed 1, won=True, died=False, finishing on day 2 at
GST 5700. Verification JSON: `solutions/stationfall_verified.json`.
Ending text: the Oliver scene ("Play game... Play game with Oliver?")
followed by "Your score is 80 (of 80 points), giving you the rank of
Intergalactic Mega-Hero." 

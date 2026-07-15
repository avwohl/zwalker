# Suspended (Infocom, 1983) — research notes for the verified solve

Binary: `games/zcode/suspended.z3` — Release 8 / Serial 830521, Z-machine V3.
Authority: official ZIL source, github.com/historicalsource/suspended
(cloned to `logs/suspended_zil/`, gitignored). Independent walkthroughs:
IF Archive `solutions/Sols1.zip` and `solutions/Sols3.zip`, both carrying the
John L. Moss ~68-move speedrun (verbatim copies in
`logs/suspended_source_sols1.txt` / `_sols3.txt`, gitignored). The Moss route
was used as the skeleton; every mechanic below was confirmed in the ZIL and
machine-validated.

## The game model

You are the suspended human controlling six robots by cryolink; each typed
command addresses one robot ("POET, GO TO WEATHER CONTROL") and costs one
cycle, during which every robot with a goal moves one room (I-FOLLOW,
main.zil:49; FOLLOW-GOAL, goal.zil:194). There is no conventional score:

- `SCORE` prints "There have been N casualties (original population:
  30,172,000) in N cycles." (V-SCORE, verbs.zil:267-275). vm.get_max_score()
  is None, so the solve is verified by a `#% WIN_TEXT:` directive.
- Status display is a custom 3-line robot tracker (INIT-STATUS-LINE,
  status.zil): Cryolink target, casualties this cycle, cycle count, and all
  six robot locations. zwalker's vm.get_score() reads 0 throughout —
  harmless garbage, documented here as expected.

## Disaster clocks (all FIXED cycle counts, queued in GO, main.zil:34-56)

| event | cycle | ZIL |
|---|---|---|
| Acid floods the Cavernous Room (ACIDMIST) | 15 | ACID-KILLS, main.zil:10; I-TREMOR1 sets ACID-FIXED false, robots.zil:497-498; queued main.zil:45 |
| Second quake wrecks hydroponics + transit autopilots | 75 | RTD-KILLS, main.zil:8; I-TREMOR2 knocks hydro levers off optimum, robots.zil:545-564; DO-RTD only kills when MOVES>75, robots.zil:717-755 |
| Human intruders enter the Sterilization Chamber | 100 | PEOPLE-APPEAR, main.zil:12; I-PEOPLE1, people.zil:29-36 |

The verified route wins at cycle 71, so the cycle-75 and cycle-100 chains
never fire. Note ACID-FIXED starts TRUE (globals.zil:355) — the Cavernous
Room is safe until cycle 15, which is why Whiz is sent through it to the
Secondary Channel immediately (he arrives cycle 15, crossing at 13-14).

### Weather / casualty engine

- Pressures start P1=55 P2=50 P3=55, dials start 55/55/55 (globals.zil:323-325,
  347-348). Every 5 cycles I-WEATHER drifts each pressure 1/5 of the way to
  its dial and subtracts DECAY from P2 (robots.zil:566-577); DECAY starts 6
  and grows every 25 cycles (I-DECAY, robots.zil:586-589). WINDS =
  |P2-P3|+|P1-P2|; DEGREES = 60 + 2*(avg-60).
- I-SCORE runs every cycle (robots.zil:699-715): casualties accrue when
  WINDS>25 ((WINDS-25)/5, worse over 50) or DEGREES<40, plus transit terms
  after cycle 75. TOTAL-SCORE>30000 => ALL-DEAD + FINISH (loss).
- FIX: set weather dial 2 to 100 (V-SET, verbs.zil:1883-1920; the dials live
  in the surface Weather Control Area, rooms.zil:1359). The high dial makes
  P2 climb against the decay, keeping WINDS below the casualty threshold for
  the whole run. Total accrued: 5 (plus the starting 3 = 8,000 casualties).
- Hydroponics levers start AT optimum (70/30/50, globals.zil:347-348 vs
  WATER-OPT/MINERALS-OPT/WATTS-OPT, globals.zil:374-376) and only get knocked
  off by the cycle-75 quake; FOOD-TONS<=0 quits the game (I-FOOD,
  robots.zil:591-618). Winning before 75 makes food a non-issue.
- Transit switches only kill after cycle 75 (DO-RTD checks MOVES>RTD-KILLS)
  — leave them alone on this route.

### Acid exposure = robot death in 5 cycles

Entering ACIDMIST from CORRIDOR-4 with ACID-FIXED false sets
DEADBOTS[robot]=1 (MOVE-RBT?, goal.zil:306-316; also ACIDMIST-FCN M-BEG,
rooms.zil:1457-1462). I-ROBOTKILLER (robots.zil:799-820) increments the
counter every cycle: warnings at 3 and 5, JIGS-UP at 7 (DYING1/2/3,
globals.zil:388-390; JIGS-UP sets DEADBOTS=30 = permanently dead,
verbs.zil:335-343). Net: an exposed robot gets the exposure cycle plus four
more actions. That budget shapes the three kamikaze runs:

- Poet (exposed c.51): MIDMIST 52, FC1 53, arrives Primary Channel 54,
  plugs TV 55, aims at sign 56 — dies that same cycle, transmission sent.
- Waldo (exposed c.55): reaches the Secondary Channel on his 5th cycle
  (c.60) and dies on arrival — the fourteen-inch cable arrives with the
  corpse, which is exactly where Whiz has been waiting since cycle 15.
- Sensa (exposed c.65): arrives Primary Channel c.68, swaps the cable c.71,
  dies c.72 (after the win under this recording; c.70 in tighter probes).

The only other acid fix is the intruders' (STU-1-F sets ACID-FIXED T,
people.zil:478-479) — far too late at cycle 100+.

## Repair chains (win condition)

Win = END-GAME (robots.zil:620-697), reached ONLY from CIRCLE-FCN
(objects.zil:1610-1648) when both correct circles are pressed while
`REDSET==REDWIRE` and `ORANGESET==ORANGE-WIRE`. Those globals start as the
damaged cables (main.zil:43-44) and are set by V-REPLACE (verbs.zil:2172-2196):
replacing in GROOVE2 (Primary Channel, TUBE2) sets REDSET, in GROOVE1
(Secondary Channel, TUBE1) sets ORANGESET. When both are correct,
I-WIRE-MESSAGE announces "Reset codes may be entered now" (robots.zil:766-772).
Touching any OTHER groove cable (pink/yellow/green/white/black/blue) is
instant robot death (GROOVE-CONT, objects.zil:967-974).

1. **Fix Iris** (blind at boot): Waldo wears the microsurgery grasper
   (SURGERY-HAND, Middle Supply, objects.zil:391-423; Waldo-only), opens her
   panel, swaps the fried blue CX1 "rough device" for the blue RX1 "rough
   object" from the basket of ICs, closes the panel => IRIS-FIXED
   (PANEL-FCN, objects.zil:65-108: needs NEWCHIP1+CHIP2+CHIPS0 in the panel).
2. **Reset machine** (Main Supply Room): put red RX0 IC in the red socket and
   yellow RX2 IC in the yellow socket, press the orange button => front panel
   pops open exposing the fourteen-inch orange wire, the glass fuse, and the
   eight code circles (ORANGE-BUTTON-FCN, objects.zil:1429-1443). TRAP:
   grabbing the orange wire while the fuse is in the machine is instant death
   (ORANGE-WIRE-FCN, objects.zil:1465-1473) — Iris must TAKE FUSE first.
   The circles are dead unless the fuse is back in the machine
   (CIRCLE-FCN, objects.zil:1612). Iris also parks the spare sixteen-inch
   cable (Middle Supply, objects.zil:1241-1248) in the machine, per the
   classic route.
3. **Fourteen-inch (orange) cable -> Secondary Channel GROOVE1** replacing
   the nine-inch orange cable: Waldo hauls it (dies), Whiz swaps it.
4. **Twelve-inch (red) wire -> Primary Channel GROOVE2** replacing the
   four-inch red cable: only Sensa can turn the flowswitch that opens FRED's
   cabinet in Gamma Repair (FLOWSWITCH-FCN, objects.zil:489-507), moving
   FRED needs TWO robots at once ("both sensa and auda, move fred";
   TWOBOTS-FCN, robots.zil:458-493, reveals REDWIRE), and the wire must be
   cut free with the wire cutter (REDWIRE-FCN, objects.zil:574-580; V-CUT
   requires WIRECUTTER, verbs.zil:2198-2217) from the Small Supply top shelf
   (needs standing on the wedge, TOPSHELF-FCN, objects.zil:303-309).
5. **Reset code**: the two-circle code (out of FOO MUM BLE BAR KLA CON BOZ
   TRA) is generated by GENERATE-CODES (objects.zil:1660-1667, PICK-ONE =
   RANDOM per macros.zil:97) the first time the TV camera is TAKEN (TV-FCN,
   objects.zil:790-793) — the ONLY state-relevant RNG draw in the game, and
   it happens well after the seed pin. Poet plugs the TV into the Primary
   Channel hole and aims it at the signpost; fixed Iris receives "It says
   XXXYYY." (verbs.zil:1860-1866). Pressing circles early is merely rejected
   ("Code entry premature", clears presses, keeps the code); pressing a
   WRONG pair after balance regenerates the code (objects.zil:1645-1648).

### Terrain gates

- The Hallway Junction <-> Sloping Corridor step needs WEDGE-PLACED=2
  ("put ramp at dropoff" there; STEP-FCN, globals.zil:278-295; gate in
  MOVE-RBT?, goal.zil:299-305). Once set it stays set even after the wedge
  is picked back up — the wedge can then serve as the Small Supply shelf
  step.
- Hallway End <-> Vehicle Debarkation is car-only (goal.zil:317-320); the
  car auto-shuttles when boarded ("get in car" / "get out of car").
- Iris cannot pass the Angling Corridor toward the CLC (goal.zil:321-328) —
  irrelevant here.

## Endings

- WIN: END-GAME prints "All systems returning to normal ... You successfully
  completed your task, bringing the Filtering Computers back into balance,
  in N cycles." (robots.zil:696) — this exact phrase appears nowhere else in
  the game (grep across all ZIL) and is the WIN_TEXT. Ranking brackets
  (robots.zil:651-673): TOTAL-SCORE<=40 => "a home in the country and an
  unlimited bank account", ranking 1 (best) of 7. Our run: 8,000 casualties
  (start 3 + 5 accrued), rank 1.
- LOSSES (none print anything like the WIN_TEXT): intruders pull your plug
  (PARRIVE5/PARRIVE7, people.zil:317-324, 465-470), food collapse
  (robots.zil:614-618), 30,000,000 casualties (I-SCORE => ALL-DEAD + FINISH,
  robots.zil:712-714), all six robots dead (DEAD-FCN, robots.zil:117-122).

## Determinism / harness notes

- Boot draws no RNG (two boots byte-identical; GENERATE-CODES is not called
  at boot) => pin `w.vm.rng.seed(seed)` right after `w.start()`, no restart
  prelude.
- All event timing is cycle-count clockwork; the only stream-relevant draw is
  the reset code, plus cosmetic PICK-ONE quips (robot yuks, Iris-blind
  lines, parser NOT-FOUND lines) that shift the stream — hence replay the
  recorded command list verbatim.
- Adaptive recorder: scripts/solve_suspended_adaptive.py — waits (recording
  `iris, look` filler cycles) for arrival interrupts, reads the code off the
  transmission, presses the matching circles. 12/12 wins on seeds 1-12,
  identical 71 cycles / 8,000 casualties / rank 1 every time (only the code
  pair differs per seed).
- No zwalker rollback hazard: no bare direction commands in the route (all
  commands are "robot, ..." forms, which _normalize_direction ignores).

# Starcross (Infocom, 1982) — research notes for the verified 400/400 solve

Binary: `games/zcode/starcross.z3` — Release 18 / Serial 830114, Z-machine V3,
standard score game (`vm.get_max_score()` = 400, from "total of 400 points").

Authority: official ZIL source, github.com/historicalsource/starcross
(files: `actions.zil`, `verbs.zil`, `emerg.zil`, `dungeon.zil`, `main.zil`,
`syntax.zil`; also `invisicluessc.mss` = the official InvisiClues source and
`starcross.txt` = Lebling's Nov-1981 design memo, both in the same repo).

Independent walkthroughs consulted (verbatim copies in the gitignored
`logs/starcross_source_eristic.txt` and `logs/starcross_source_walkthroughking.txt`):
- eristic.net/games/infocom/starcross.html (very detailed, includes the
  full coordinates table and a point breakdown that matches the ZIL exactly)
- walkthroughking.com/text/starcross.aspx (independent command list)

## The 400-point breakdown (all confirmed in ZIL)

- 12 crystal rods, 25 points each = 300. Every rod object carries
  `(VALUE 25)` in dungeon.zil (black 553, yellow 669, pink 763, clear 937,
  brown 1230, blue 1480, green 1524, violet 1561, red 1702, gold 1776,
  silver 1802, white 1967). `SCORE-OBJ` (verbs.zil:196) awards the value on
  first touch — it is called from ITAKE (verbs.zil:582), V-PUT
  (verbs.zil:620), the room scorer (verbs.zil:884), and several bespoke
  spots: blue rod via the transporter trick (actions.zil:1476-1482), brown
  rod via POINT (actions.zil:2779), silver rod via LOOK-INSIDE the gun
  (actions.zil:3173), clear rod via TAKE from the projector
  (actions.zil:3794), rod-rack inserts (actions.zil:4208).
- Room "Red Dock" `(VALUE 25)` dungeon.zil:534 — scored on first entry
  (GOTO calls SCORE-OBJ on the room, verbs.zil:884). = 25.
- Room "Control Bubble" `(VALUE 25)` dungeon.zil:2238. = 25.
- Pressing the blue spot (EXECUTE-BUTTON-FCN, actions.zil:4119-4137) with
  course+target+speed set and VIEW-STATUS 1 awards `CONTROL-SCORE` = 25
  (actions.zil:4139). = 25.
- WIN-GAME (actions.zil:4141): if TARGET is 4 (Earth) and COURSE-SHAPE is
  3 (ellipse) or 4 (circle), `SCORE-UPD 25` + `SETG WON-FLAG T` + the
  winning text ("The artifact, under your assured control, moves serenely
  toward Earth...") then FINISH. = 25.

Total 300 + 25 + 25 + 25 + 25 = 400. Deaths cost -10 each (JIGS-UP,
verbs.zil:315-318), so the verified run must never die.

## Randomness inventory (what the pinned seed controls)

- **Which unknown mass appears** — `<SETG MASSNUM <RANDOM 8>>` inside
  I-ALARM (actions.zil:38). I-ALARM is queued with tick 1 in GO
  (main.zil:32) so the roll happens at the END OF THE FIRST PLAYER TURN,
  i.e. AFTER `w.vm.rng.seed(seed)` is pinned post-`start()`. Two boots are
  byte-identical; no `restart` prelude is needed. The recorder reads the
  detector screen at run time and looks the coordinates up in the fixed
  MASS-LOCS table (dungeon.zil:186-198):

      UM08 150/210/17   UM12 100/345/107  UM24 100/285/87  UM28 250/45/178
      UM31 150/105/67   UM52 175/165/35   UM70 100/135/101 UM91 50/15/121

  (seed 1 rolls UM24 -> r 100, theta 285, phi 87). FIND-DESTINATION
  (actions.zil:186-226) matches the entered R/THETA/PHI against that table.
- **Course-correction burn length** — `30 + RANDOM 30` seconds
  (actions.zil:518), text only.
- **Bad-air clock** — `I-BAD-AIR` queued `75 + RANDOM 50` turns after the
  tentacle grabs the ship (TENTACLE-APPEARS, actions.zil:766-767); four
  strikes 40 turns apart then death EVEN IN THE SUIT (emerg.zil:214-235,
  "artifact shuts down"). Fixed permanently by the red rod in the SECOND
  red slot (oxygen; RED-SLOT-F emerg.zil:149-169 disables I-BAD-AIR,
  queues I-FRESH-AIR). The route repairs air by ~turn 75.
- **The maintenance mouse** — I-MOUSE (actions.zil:955-1032) runs every 2
  turns from the moment of docking; MOVE-MOUSE picks exits with PROB 50,
  15%/tick to head to the Garage while carrying loot, 40%/tick to leave
  the Garage. It ROBs its current room every tick — but RIPOFF
  (verbs.zil:1307) only steals objects with TOUCHBIT already set, so only
  things the player has handled and dropped are at risk. Mouse starts in
  Room on Ring Four (dungeon.zil:1344). Disks the mouse dumps go to the
  GARAGE FLOOR, everything else into the trash bin (actions.zil:967-972).
- **Trash-bin searches** — escalating PROB: search 1 always fails and sets
  TRASH-COUNT 25, then each further search succeeds with TRASH-COUNT% and
  adds 25 (actions.zil:1086-1119). At most 5 searches produce the green rod.
- **Weasel chief** — appears in Village Center `3 + RANDOM 3` ticks after
  the NW-edge look queues I-CHIEF-APPEARS (actions.zil:2506, 2601); after
  the trade he waits CHWAIT max 10 I-CHIEF ticks before leaving insulted
  (turns hostile, actions.zil:2842-2865); his warren path length is
  `CHPATH = 5 + RANDOM 5` follow legs (actions.zil:2879); I-CHIEF requeues
  every 1-2 turns (PROB 75, actions.zil:2888).
- **JATO with no target** — firing the gun in a weightless room without
  "at <bubble>" picks a random target with 20% chance of GROUND = death
  (actions.zil:3689-3696). Always "fire gun at drive bubble".
- **Take fumbles** — ITAKE (verbs.zil:533-575): holding more than
  FUMBLE-NUMBER=7 direct items makes every further TAKE fumble with
  probability count*FUMBLE-PROB(8)%, dumping the second-held item (and in
  RMUNGBIT rooms scattering both). THIS is what the metal basket
  (ROD-RACK, YELLOW-LOCK, dungeon.zil:2372; actions.zil:4195) is for: rods
  inside it count as one held item (CCOUNT counts direct children only).
  The verified route baskets every loose rod and never holds more than 7
  items, so no take can fumble regardless of seed.
- Cosmetic: spider questions, computer snark, hunt scenes (I-HUNTERS,
  PROB 40), tape selections.

## Timed events

- I-ALARM every turn until silenced; computer forces it off at move 15.
- I-BURN 3 turns after "computer, confirm" — DEATH if the seat belt is not
  fastened (actions.zil:654-674). I-TRIP every 3 turns, 5 legs; then
  I-VIEW every 2 turns, 4 views; the 5th I-VIEW tick fires
  TENTACLE-APPEARS (actions.zil:747-800) — DEATH if not belted in
  (also queues I-MOUSE and I-BAD-AIR). About 25 turns of waiting total.
- I-NEST: 15 turns after the nest is smashed the rat-ants rebuild and
  reabsorb EVERYTHING still lying in the wreck (actions.zil:3074) — grab
  the red rod and the tape library immediately.
- I-NIGHT every 128 turns: cosmetic day/night in the interior.

## Puzzle mechanics (ZIL confirmations that differ from/ sharpen the walkthroughs)

- **Black rod**: push FOURTH bump (Earth on the solar-system relief) ->
  tiny bump appears; push tiny bump -> black rod extrudes (BUMP-FCN,
  actions.zil:2158-2202). TAKE BLACK ROD also opens the red outer airlock
  door (BLACK-KEY-FCN actions.zil:2111-2118). Pressing any other bump
  flattens the sculpture (puzzle still solvable? NO — rod gone; avoid).
- **Airlocks**: safety interlock — inner and outer door can never be open
  together (AIRLOCK-OPEN actions.zil:2345+). Opening the outer door onto a
  SPACEBIT dock without the suit on = instant death (ACADEMY-DEATH).
  Yellow outer door is jammed: first OPEN prints "Perhaps if you pushed
  again", the second OPEN works (YELLOW-DOORS-FCN actions.zil:2242-2259).
- **Red rod**: any tool with SIZE > 5 thrown at the nest smashes it — the
  tape library qualifies; the tool AND rod land in the smashed nest, both
  takeable (NEST-FCN actions.zil:3023-3062).
- **Yellow rod**: give tape library to the spider (SPIDER-FCN GIVE,
  actions.zil:1240-1258); rod lands on the floor. The spider keeps the
  player permanently, so the nest must be done first.
- **Repair room** (down the hatch in Thin Forest): yellow rod in yellow
  slot sets ALWAYS-LIT (emerg.zil:127-134) — the yellow hall and airlock
  are dark until then; red rod in SECOND red slot = O2 (first = methane,
  third = ammonia -> poison-air death, emerg.zil:149-169).
- **Blue rod** (Laboratory): rod is embedded in FORCE-FIELD-1. Take both
  disks off the wall, DROP one (red) on the lab floor, PUT the other
  (blue) UNDER the globe, put a junk object (the square) ON the globe,
  SET DIAL TO 4: the globe expands, the disk under it becomes
  WAS-UNDER-GLOBE, the object on the old field falls onto it, the disk
  transporter fires, and — the special case in JUNK-INSIDE
  (actions.zil:1456-1482) — the blue rod is scored and teleported onto
  the OTHER disk. SET DIAL TO 1, pick everything back up. (Stepping on a
  disk while the other is under the globe = death, DISK-FCN:1540.)
- **Pink rod**: safety line tied to suit AND hook is required to go west
  from Yellow Dock (YELLOW-DOCK-EXITS actions.zil:2301); jumping or
  walking unmoored throws you into space (BRODY, I-SUFFOCATE).
- **Clear rod**: LOOK AT PROJECTOR THROUGH BLACK ROD (V-LOOK-SAFELY;
  smoked glass also works) reveals the rod inside the projector; TAKE it
  (SLIDE-PROJECTOR-FCN actions.zil:3758-3800). Looking without a filter =
  blinded + grue death.
- **Gold rod + control precondition**: open panel, put square (CARD) in
  slot, THEN turn on switch -> gold rod falls out (SWITCH-FCN
  emerg.zil:8-41). Inserting the card while the switch is on fries the
  computer (I-MELTDOWN). CRITICAL: the control-bubble slots REJECT rods
  unless SWITCH-ON? and CARD in SLOT (CONTROL-SLOT-FCN actions.zil:3837)
  — repairing the ship computer is mandatory for the endgame.
- **Green rod**: drop a disk where the mouse is, wait for it to collect
  ("picks up some refuse"), wait for it to trundle to the Garage
  (15%/tick); disks are dumped on the Garage FLOOR. Drop the other disk
  in Room on Ring Four, stand on it -> teleport to the Garage (stand on a
  disk = GOTO the other disk's room; "Nothing happens" while the other
  disk is not on a room floor — safe retry probe). Search the trash bin
  until "Ahah, there's something!", take green rod, walk out NORTH to
  Room on Ring Four. `EMPTY MOUSE` (MOUSE-FCN, actions.zil:900) pulls
  everything back out of the mouse — the recovery tool if it steals a disk.
- **Silver rod**: LOOK INSIDE GUN scores and reveals it; TAKE it OUT
  before ever firing — firing with the rod chambered wastes 2 of the gun's
  3 charges as a misfire (ZAP-GUN-FCN actions.zil:3160-3210, ZAP-CNT 3)
  and all 3 charges are needed for axis propulsion.
- **Brown rod**: enter Village Center suitless-wearing (suit carried),
  wait for the chief, GIVE SUIT TO CHIEF (refused while worn,
  GIVE-TO-CHIEF actions.zil:2564), POINT AT BROWN ROD (actions.zil:2779).
  Then wait for him to leave and FOLLOW CHIEF each time he slips away;
  after CHPATH legs through the maze he stops at Center of the Warren and
  points at the ladder (I-CHIEF actions.zil:2842-2888).
- **Violet rod**: down the ladder = Green Airlock; Green Dock is
  pressurized (plastic umbilical, no SPACEBIT — dungeon.zil:774) so no
  suit needed. MOVE SKELETON exactly once (twice = death,
  actions.zil:2898-2912); take rod; drop the carried disk and stand on it
  to teleport out — walking back into the warren after touching the rod is
  death (ALIEN-GUARDS actions.zil:2943; VILLAGE-FCN actions.zil:2547),
  and the village must never be re-entered afterwards.
- **Drive bubble**: climb the great tree (impossible while the suit is
  carried — UP-A-TREE-EXIT actions.zil:3261), JUMP from Top of Tree to
  the entrance (TREETOP-FCN actions.zil:3296; jumping from Up a Tree or
  the entrance is death). Silver rod in silver slot opens the hatch
  (leave it there — taking it closes the hatch). Inside: take white rod
  (floats by the white slot, dungeon.zil:1959-1967), put it in the WHITE
  slot (activates the drive; the black slot that appears is the emergency
  shutoff — black rod there ends the game unwon, actions.zil:3450).
- **Crossing the axis**: out, up (On Drive Bubble), JUMP (-> Floating in
  Air, ON-BUBBLE-FCN actions.zil:3661), then FIRE GUN AT DRIVE BUBBLE
  three times (JATO actions.zil:3689: each shot moves one axis room
  toward the fore end; exactly 3 charges, exactly 3 rooms). Down; gold
  rod in gold slot opens the control-bubble hatch; in = Control Bubble
  (+25 room).
- **Endgame console** (CONTROL-SLOT-FCN actions.zil:3831+, spot functions
  4030-4137): clear rod in clear slot -> five colored slots appear; pink,
  brown, green, blue, violet rods into like-colored slots (each projects
  a control: pink=view screen, brown=target spot, violet=course spot,
  green=speed spot, blue=execute spot). TOUCH LARGE SQUARE once ->
  VIEW-STATUS 1 (inner solar system — required by target select AND
  execute). TOUCH BROWN SPOT x4 -> Earth (TARGETS: Sun Mercury Venus
  EARTH Mars Jupiter). TOUCH VIOLET SPOT x4 -> circle (COURSES: center /
  parabola / ellipse / CIRCLE; 3 or 4 wins, 1 = ram Earth, 2 = lost
  forever). TOUCH GREEN SPOT x1 -> slow (speed select requires the white
  rod installed in the drive bubble). TOUCH BLUE SPOT -> +25 (execute) +
  WIN-GAME +25 -> 400/400 and FINISH.

## Interpreter/pipeline notes

- Harness: GameWalker exactly as replay_solve replays it; seed pinned
  after start(). The adaptive recorder wins seeds 1-4 (4/4 tried); the
  shipped recording is seed 1 (240 commands, 265 moves), replay-verified
  twice.
- No boot randomness (MASSNUM rolls on turn 1, post-pin) — verified by
  diffing two boots.
- Walker rollback: only DIRECTION_NORMALIZE words (n/s/e/w/up/down/in/out
  variants) can be rolled back on a blocked-move match; port/starboard/
  fore/aft and all verb commands are exempt. The recorded route never
  bumps a closed door (airlock doors are opened before every move), so no
  "west." workarounds were needed.
- DEATH_MARKERS: Starcross's JIGS-UP banner is "**** You have died ****",
  which replay_solve already matches; the verified run never dies.

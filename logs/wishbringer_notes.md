# WISHBRINGER (Infocom, 1985) — Mechanics Notes for Deterministic Replay
Target binary: Release 68 / serial 850501, Z-machine V3, 100 points max
(games/zcode/wishbringer.z3 — header verified: version 3, release 68,
serial 850501, flags1 bit1 set = TIME status line).

Sources used:
- ZIL source: github.com/historicalsource/wishbringer (authoritative).
  Repo is the Release 69 / serial 850920 source (COMPILED/j2.z3 header
  confirms r69) — one release after our r68; every mechanic cited below
  was re-verified empirically against the r68 binary. Build order:
  wishbringer.zil IFILEs MISC, PARSER, GLOBALS, SYNTAX, VERBS, PEOPLE,
  SOUTH, CENTER, WEST, EAST, NORTH, BRIDGE, FOG, SHOPPE, ISLAND, UNDER,
  CEMETERY, TOWER, BOXES, MAGICK.
- ifarchive.org/if-archive/infocom/hints/solutions/wishbringer.step1
  (Futtrup/Lintermans 1992 command list; claims "100 points without any
  wishes").
- ifarchive.org/if-archive/infocom/hints/solutions/wishbringer.step2
  (Jacob Gunness 1990 command list, annotated).
- zedlopez.github.io/invisiclue/ Wishbringer InvisiClues conversion
  (cross-checks on wish preconditions and non-wish solutions).
- EMPIRICAL VERIFICATION: the route in wishbringer_route.txt was
  machine-played to 100/100 against the r68 binary by
  scripts/solve_wishbringer_adaptive.py (researched on the raw ZMachine,
  then ported to the GameWalker/replay_solve pathway) across the
  pinned-seed sweeps listed at the end of these notes; 179 commands,
  162 game moves, 0 deaths, 0 Boot Patrol captures, 0 of the 7 Wishes used.

---

## 0. THE SCORE GLOBAL — read this first

Wishbringer is a V3 TIME game. The two standard status-line globals hold
the CLOCK, not the score:

- global index 1 (variable 0x11) = `SCORE` in the ZIL = HOUR of day
  (starts 15 = 3 PM; misc.zil:140; wraps 23->0, misc.zil:536-537).
- global index 2 (variable 0x12) = `MOVES` in the ZIL = MINUTE of hour
  (1 turn = 1 minute; misc.zil:531-537). `vm.get_score()` therefore
  returns the HOUR. Do not use it.

**THE REAL SCORE is `GSCORE`, global index 136 (0-based from the globals
table; variable number 152 = 0x98).** Defined verbs.zil:178; updated only
by UPDATE-SCORE (globals.zil:344-354) and one silent `<SETG GSCORE <+
,GSCORE 5>>` at the endgame (center.zil:2135). Verified empirically: +1 on
post-office entry, +5 on envelope take, and every event below, across
many seeds. **Teach the interpreter: score = word at (globals_addr +
2*136).**

- True move counter `GMOVES` = global index 135 (incremented with the
  minute in CLOCKER, misc.zil:531-532; matches "in N moves" from V-SCORE,
  verbs.zil:182-186).
- Time freezes inside the Magick Shoppe: CLOCKER skips the minute/GMOVES
  increment while HERE = INSIDE-SHOPPE and the shoppe clock isn't running
  (misc.zil:529-537). Interrupt queues still run there.
- Timeless verbs (GAME-VERB?, misc.zil:406-416): score, time, brief,
  verbose, super-brief, save, restore, quit, restart, script, unscript,
  version, tell. `score`/`time` are safe telemetry anywhere.
- PROB macro (misc.zil:112-113): true iff `RANDOM(100) <= n` — one RNG
  call per evaluation.

## 1. THE OPENING AND THE CLOCK

- GO (misc.zil:137-161): start at HILLTOP at 15:00, holding nothing.
  Queues from turn 0: I-PROMPT-1/2 (prompt tutorial), I-CRISP-CALLING
  (south.zil:47, "Somebody inside the Post Office is calling you" while
  on Hilltop), I-VOSS-CALLING (people.zil:781), I-BARKING (south.zil:715,
  poodle flavor + hints), I-BEFORE-FIVE (parser.zil:2456-2464).
- Mr. Crisp (I-GIVE-ENVELOPE, people.zil:108-160): enter the post office
  (S; south.zil:103-113 enables the script; **I-HOORAY fires: +1 point
  AND sets `POWER <- RANDOM(3)-1`**, south.zil:118-122 — the magic word
  is rolled HERE). CRISP-SCRIPT 1 = greeting; 2 = envelope tossed onto
  the counter ("tossing it onto the service counter" — sync string);
  3 = "drums his fingers" (PROB 50 insult — RNG). Take the envelope
  (+5, VALUE on take) and leave. If you dawdle holding it, ANGER (5)
  counts down and Crisp throws you out to Hilltop (harmless, but noisy).
- THE DELIVERY DEADLINE: I-BEFORE-FIVE (parser.zil:2456-2464): warnings
  at 16:00 and 16:30; **at 17:00, if you are not inside the Magick
  Shoppe, FIRED = game over** (globals.zil:805-818). Budget: 120 minutes
  = 120 turns from start. The verified route reaches the shoppe at
  ~15:57. Entering the shoppe with the envelope disables the deadline
  (ENTER-SHOPPE, shoppe.zil:395-402) and the clock freezes inside.
- The shoppe scene: knock ("Come in!"), open door, W. I-WOMAN-SCRIPT
  (people.zil:1176) brings the old woman in ~3 turns. GIVE ENVELOPE TO
  WOMAN (+5, people.zil:1117-1129), OPEN ENVELOPE, READ LETTER TO WOMAN
  (+1, people.zil:1270-1281; enables I-RECRUIT). I-RECRUIT
  (people.zil:1307-1385): script 1 offers the metal can — TAKE CAN (+3;
  refusing 4 turns = thrown out, quest over); scripts 2-4 = the
  transformation speech; script 4 runs SKEW.

## 2. THE STONE AND THE SEVEN WISHES

The stone arrives inside the metal can's false bottom: OPEN CAN (a snake
pops out — see troll below), TAKE CAN, SQUEEZE CAN (shoppe.zil:704-718:
squashes the can, drops the stone at your feet), TAKE STONE (+5 VALUE,
magick.zil:11). While held it glows (I-GLOW, parser.zil:2567-2597) —
**it is the route's light source** (tunnels, jail, grue nest, library).

Each wish requires an item precondition (magick.zil), sets the wish's
TOUCHBIT, and increments `SPELLS` (verbs.zil:180):
- RAIN: hold OPEN umbrella (umbrella: TWILIGHT-GLEN, cemetery.zil:721),
  outdoors (magick.zil:176-244). Fills the pit / clears the fog.
- ADVICE: hold conch shell (TIDAL-POOL, east.zil:615) — 7 cryptic hints
  via I-SHELL-TALK (parser.zil:2604).
- DARKNESS: drink the grue milk first (MILK-SCRIPT window of 4 turns,
  under.zil:404-477), lit room (magick.zil:383-489). Scares hellhound /
  troll / gravedigger for 2 turns (I-ECLIPSE, magick.zil:523).
- FLIGHT: sit on the broom (LABORATORY, tower.zil:1492), outdoors or lab
  (magick.zil:70-99). Flies you to Cliff Edge and ENDS THE QUEST early
  (TO-FINISH) — never use it.
- FORESIGHT: wear the 3D glasses (magick.zil:253-300). Pure vision.
- FREEDOM: eat the chocolate first (Crisp's desk, Festeron post office
  only — SKEW deletes it if unclaimed, people.zil:1451-1455;
  magick.zil:108-146). Escapes jail/chains.
- LUCK: hold the horseshoe (LOOKOUT-HILL, west.zil:729;
  magick.zil:319-341). Passive rerolls: troll accepts the coin, vapors
  steal one item instead of everything, etc.

**Do wishes cost points? NO.** SPELLS only changes the endgame text: the
"Congratulations" screen adds "You've used N of the Stone's 7 Wishes"
and, if SPELLS>0, a paragraph suggesting a wishless replay
(shoppe.zil:890-895; verbs.zil:190-191). 100/100 is reachable either
way, BUT every wish burns a turn, needs an extra item (extra weight,
extra RNG exposure), and FLIGHT/DARKNESS have plot side effects. **The
verified full-score route uses ZERO wishes**; every wish-solvable puzzle
has the mundane solution listed in §5. The wish preconditions (umbrella,
conch, milk, chocolate, horseshoe, broom, glasses) are therefore NOT
needed except the glasses+broom (needed mundanely for the lab/case).

## 3. FESTERON -> WITCHVILLE (SKEW)

Trigger: I-RECRUIT script 4 (people.zil:1370-1385) after the letter is
read — the old woman leads you out, runs SKEW (people.zil:1397-1504) and
drops you at CLIFF-EDGE; the clock jumps to 18:00 (SCORE=18, MOVES=0).
SKEW changes (selected):
- All room TOUCHBITs cleared (re-describes everything).
- Troll + toll gate to NORTH-OF-BRIDGE; vulture into the gnarled tree.
- Pit opened with platypus inside (or, if you disturbed the leaves in
  Festeron, it stays as-is — see one-shots §8).
- Fountain contents -> STEEP-TRAIL limbo; piranha + brass token into the
  fountain. **The gold coin is unobtainable after SKEW.**
- BOOTS to FESTERON-POINT; I-BOOT-PATROL enabled. I-BREAK-IN enabled.
- Miss Voss to ROTARY-EAST holding the ticket; gravedigger to the movie
  LOBBY; hellhound (Alexis) replaces the poodle at OUTSIDE-COTTAGE;
  church gets debris/speaker; south cemetery gate opens, I-CREAK armed
  (north gate self-opens at EDGE-OF-LAKE, parser.zil:2472-2483).
- **If Miss Voss's violet note was not accepted in Festeron, SKEW
  REMOVES it — 6 points and the Alexis hint gone, plus the torture
  chamber becomes much harder (bribe path). Fatal for 100/100.**
- Post-transformation, standing at CLIFF-EDGE: I-FOG-RISING
  (fog.zil:23-52) engulfs you in fog after 4 turns. Leave promptly (the
  route goes D into the fog maze immediately anyway).
- Moonset deadline: I-BEFORE-MOONSET (parser.zil:2497-2523): hourly
  reminders; **at 06:00 the quest fails**. Budget: 720 turns from 18:00.
  The route finishes ~19:45 game time.

Map differences that matter: Post Office -> the Tower (moat, drawbridge);
the steep trail becomes the FOG maze (same TLOC cell graph, fog.zil);
Pleasure Wharf tidal beach flooded ("The tide is in", east.zil:47-51 —
conch/tidal pool unreachable in Witchville); WEST-OF-HOUSE (the Zork
white house + mailbox easter egg) appears off ROCKY-PATH (north.zil).
There is no "granite wall" in Wishbringer — that's a Zork artifact; the
Zork homage here is the white house/mailbox (optional, skipped).

## 4. THE BOOT PATROL — deterministic!

I-BOOT-PATROL (parser.zil:2730-2862). ZERO randomness:
- Fixed 19-slot loop BOOT-PATH (parser.zil:2628-2648): FESTERON-POINT ->
  ROCKY-PATH -> SOUTH-OF-BRIDGE -> RIVER-OUTLET -> LOOKOUT-HILL ->
  RIVER-OUTLET -> EDGE-OF-LAKE -> ROTARY-WEST -> ROTARY-SOUTH ->
  ROTARY-EAST -> PLEASURE-WHARF -> WHARF -> PLEASURE-WHARF ->
  ROTARY-EAST -> PARK -> ROTARY-WEST -> ROTARY-NORTH -> SOUTH-OF-BRIDGE
  -> ROCKY-PATH -> (wraps).
- **The boots advance one slot ONLY on turns when the player did NOT
  change rooms** (LAST-PLACE == HERE check, parser.zil:2737-2756). Keep
  walking and they are frozen. Every stationary action (take, open,
  wait...) outdoors OR indoors advances them by one.
- Eclipse (darkness wish) suspends them (parser.zil:2732).
- Blowing the whistle to return from Misty Island RESETS the boots to
  slot 0 / FESTERON-POINT (island.zil:46-49) — a free re-sync the route
  exploits.
- Proximity warnings from DIRECTION-TABLES (parser.zil:2678-2700):
  "You hear the tramp of marching boots ..." = they're one room away;
  "...coming this way!" = your room is their next slot. Good sync
  strings for a watchdog, but with the verified pacing no collision ever
  occurs (nearest approach: boots at ROTARY-SOUTH while we're at PARK).
- Capture (HERE == boots' room): branch/broom confiscated
  (DEPOSIT-BRANCH), everything else kept. Visit 1: Jail Cell, 24-turn
  countdown (JAIL-SCRIPT, parser.zil:2864-2903; at 0 = torture ending).
  Escape: PUSH BUNK, drop down the hole (hole limit 18 units — drop
  loot first, re-enter tunnels to collect). Visit 2: hole is cemented
  (JAIL-AGAIN, boxes.zil:605-612), 16-turn countdown, only the FREEDOM
  wish escapes. Visit 3: fed to the sharks — fatal UNLESS the seahorse
  was rescued in Festeron (SAVED-BY-HORSES, boxes.zil:581-603, dumps you
  at FESTERON-POINT stripped of nothing). So: capture budget = 1 safe
  capture (2 with freedom wish prepped); the route takes ZERO.
- I-JAIL flavor wails: PROB 10 per turn in cell (RNG); I-BREAK-IN: PROB
  10 while in cell (parser.zil:2466-2470).

## 5. COMPLETE ROUTE (see wishbringer_route.txt for the exact list)

Festeron, 15:00 (all times from the verified seed-42 run):
1. S (post office +1; POWER rolled), Z until envelope tossed, TAKE
   ENVELOPE (+5), N.
2. W, W, YES (Creepy Corner; BE-SURE prompt cemetery.zil:222-247), N
   (copse; gravedigger greets), W (glen; I-DIGGER-FOLLOWS
   cemetery.zil:483-500 — he hands back anything, leaves via the north
   gate and LOCKS it, ending up at EDGE-OF-LAKE), E, D (into grave —
   only possible once he's gone, cemetery.zil:164-175), TAKE BONE (+1),
   U (weight <= 18 to climb out), S, E, E (Hilltop).
3. E (Outside Cottage; poodle), GIVE BONE TO POODLE (+3,
   south.zil:595-610; buys exactly ONE pass), N (Rotary South;
   I-VOSS-BABBLE people.zil:789-849), Z until she holds out the note,
   TAKE NOTE (+3; refusing until ANGER=0 is -10 and kills the run).
4. N (Park), LOOK IN FOUNTAIN, TAKE COIN (+1 — LAST CHANCE before SKEW).
5. E, E, E (Wharf's End; I-HORSE-DEATH 4-turn timer, people.zil:916),
   TAKE SEAHORSE, THROW SEAHORSE IN BAY (HORSE-SAVED?,
   globals.zil:535-546 — 3rd-capture insurance, no points), W.
6. N, N, W, W, N, N, E (Cliff Bottom), U (trail, TLOC=1,
   bridge.zil:374-381), W, N, U, E, S, U (Cliff Edge, +1 first exit,
   fog.zil:170-180). Trail cell graph (fog.zil:107-197): wrong moves
   roll PROB-TUMBLE (T-PROB += 10 per miss, cumulative death!) — never
   deviate.
7. KNOCK ON DOOR, OPEN DOOR, W. Z x3 (woman arrives), GIVE ENVELOPE TO
   WOMAN (+5), OPEN ENVELOPE, READ LETTER TO WOMAN (+1), Z x2, TAKE CAN
   (+3), Z x3 -> SKEW -> Cliff Edge, 18:00, score 24.

Witchville:
8. D (fog, TLOC=6), N, W, D, S, E, D (Cliff Bottom; WALK-OUT-OF-FOG).
9. TAKE BRANCH (snaps off; vulture flies off, I-VULTURE PROB 5/turn
   begins, bridge.zil:615-621), TAKE BRANCH (now held).
10. W (North of Bridge; troll demands toll). OPEN CAN (+3: rattlesnake;
    FRIGHTEN-TROLL bridge.zil:652-668, troll gone for good; can drops
    open), TAKE CAN, SQUEEZE CAN (stone drops), TAKE STONE (+5; glows),
    OPEN GATE, S, S, W, S (Edge of Lake; I-CREAK arms the north gate).
11. LOOK IN PIT, PUT BRANCH IN PIT (platypus grabs, west.zil:220-260),
    TAKE BRANCH (+5; X drawn in sand), DROP BRANCH, DIG IN SAND
    (whistle; west.zil:127-143 — see one-shot warning §8), TAKE WHISTLE
    (+3), BLOW WHISTLE -> Misty Island (island.zil:29-43).
12. W (Throne Room; I-KING-BLAB island.zil:148-215), Z (hat offered),
    TAKE HAT (+1; refusing 4 turns = granola mines death), Z, Z (script
    4: RETURN-FROM-ISLAND), BLOW WHISTLE -> Edge of Lake; whistle
    consumed; **boots reset to slot 0**.
13. S, YES (Twilight Glen; I-VAPORS armed, cemetery.zil:579-660: turn 1
    notice, turn 2 condense, turn 3 = grabbed, ALL items scattered to
    RANDOM rooms — run breaker!), E (copse), D (grave = ESCAPE-VAPORS,
    cemetery.zil:177-186), N (Tunnel Fork), E (Under Cell).
14. PUSH BUNK (from below via PSEUDO-BUNK, center.zil:2833-2850), DROP
    ALL (hole limit 18 units, CANT-FIT-INTO? globals.zil:455-467), U
    (Jail Cell), TAKE BLANKET (+3), D, TAKE ALL (stone re-glows).
15. N, E (Grue's Nest; I-GRUE-SLEEP under.zil:247-269: baby wakes turn 3
    in light = death), PUT BLANKET ON BEAST (+3, COVER-GRUE
    under.zil:225-233, disables the timer), OPEN FRIDGE, TAKE WORM (+3).
    (The milk bottle stays — only needed for the darkness wish.)
16. W, W (Under Hill), OPEN STUMP, U (Lookout Hill; horseshoe here —
    skipped, luck wish not needed), N, E, E, E (Festeron Point).
17. GIVE HAT TO PELICAN (+5, people.zil:1018-1034): the lighthouse
    "traces a word on a passing cloud: XXXX" — **PARSE THE WORD**
    (KALUZE / FRATTO / SORKIN, people.zil:1054, selected by the POWER
    roll at the post office). Saying an unheard word at the tower =
    permanent refusal ("only guessing", parser.zil:735-741) — the
    pelican MUST precede the tower.
18. W, W, S, S (Park), PUT WORM IN FOUNTAIN (piranha busy 3 turns,
    center.zil:905-968), TAKE TOKEN (+3).
19. E (Rotary East; Voss), GIVE COIN TO VOSS (+3; ticket,
    people.zil:703-719), IN (lobby), GIVE TICKET TO GRAVEDIGGER
    (people.zil:456-466), N (theater), LOOK UNDER SEAT (glasses found,
    center.zil:512-520), TAKE GLASSES (+3), S, OUT, YES ("might not let
    you in again" prompt, center.zil:281-295). The MOVIE itself is
    OPTIONAL on r68: panel/switches/kitty/broom pre-exist in the
    LABORATORY (tower.zil:1352,1376,1408,1492); watching it (wear
    glasses + 6 turns) is flavor.
20. E, S (Video Arcade), PUT TOKEN IN SLOT (+1, east.zil:576-596), PUSH
    JOYSTICK WEST x2, PUSH JOYSTICK SOUTH x2 (star on 5x5 plus-shaped
    grid, start H5/V3, HILLTOP = H3/V5, east.zil:397-476 + DESTINATIONS
    boxes.zil:616-622), PRESS RED BUTTON, YES, YES (+5; teleport to
    Hilltop; machine is one-shot).
21. SAY <WORD> (+3; drawbridge lowers, parser.zil:744-756), S
    (Vestibule; I-CRISP-CAPTURE people.zil:186-283: turn 1 = princess
    reveal), Z (turn 2 = captured, chained in Torture Chamber, items
    kept), GIVE NOTE TO CRISP (CRISP-SEES-NOTE people.zil:305-330: he
    drops coat + rusty key, leaves, hatch closes; do NOT stall — from
    script 5 he confiscates one carried item per turn and pockets the
    STONE if he sees it).
22. TAKE COAT ("You got it!"), TAKE KEY (+3), UNLOCK CHAINS WITH KEY
    (+1, tower.zil:713-728; OPEN-TORTURE-CHAINS clears THROWNBIT on
    confiscated loot), PULL LEVER (frees Tasmania; **PUSH LEVER UP =
    TORTURE -10 and unforgivable**, tower.zil:970-977), TAKE NOTE, READ
    NOTE (+3, SAY-NOTE center.zil:1613-1628: "ALEXIS, HEEL").
23. OPEN HATCH, U (Round Chamber), LOOK BEHIND PAINTINGS (crank
    revealed, tower.zil:299-345), U (Fuzziness — the lab is only
    reachable through 3D), WEAR GLASSES (-> Laboratory,
    verbs.zil:2036-2074), TAKE BROOM, OPEN SECOND SWITCH (+3, SW2
    security, tower.zil:1385-1397 — REQUIRED before breaking the museum
    case), D (Fuzziness), TAKE OFF GLASSES (-> Round Chamber,
    verbs.zil:2077-2108), TURN CRANK (+1; drawbridge opens,
    tower.zil:354-368 — it TOGGLES, turn once), N, N (Hilltop; bridge
    slams behind you, I-SLAM-BRIDGE tower.zil:439-451).
24. E (Outside Cottage; hellhound), ALEXIS, HEEL (+5, south.zil:654-668;
    requires NOTE-READ), OPEN DOOR, IN, TAKE STEEL KEY (+3; on the
    bookcase), OUT, N (Rotary South).
25. UNLOCK LIBRARY DOOR WITH STEEL KEY (+3, center.zil:1490-1507), IN
    (Circulation Desk), Z (door slams + locks after 2 turns,
    I-SLAM-DOOR center.zil:1395-1425 — the glowing stone is now the only
    light), S (Museum).
26. BREAK CASE WITH BROOM (center.zil:1940-1961; valid tools: broom,
    branch, conch, bottle, umbrella, horseshoe; **with SW2 still on this
    is the alarm -> torture ending**), PUT STONE IN SCULPTURE ("Wait!"
    — the Evil One appears), YES ("Don't!"), YES (the ending fires:
    silent +5, center.zil:2100-2145; -> Cliff Edge, sunrise, SUCCESS).
27. Z (Chaos rubs your leg), KNOCK ON DOOR (jumps the finale script,
    shoppe.zil:151-157), Z (old woman, congratulations, END-ROOM,
    "Your score is 100 points out of 100, in 162 moves").

## 6. THE 100-POINT BREAKDOWN (r68, all verified)

VALUE-on-first-take items (V-TAKE, verbs.zil:2230-2240), 40 pts:
	envelope +5 (shoppe.zil:399), metal can +3 (shoppe.zil:528),
	stone +5 (magick.zil:11), gold coin +1 (center.zil:838),
	old bone +1 (south.zil:767), violet note +3 (center.zil:1556),
	whistle +3 (island.zil:9), wizard's hat +1 (island.zil:250),
	blanket +3 (center.zil:2696), earthworm +3 (under.zil:485),
	brass token +3 (east.zil:568), 3D glasses +3 (center.zil:561),
	rusty key +3 (tower.zil:835), steel key +3 (south.zil:913).
UPDATE-SCORE events, 60 pts:
	post office entry +1 (south.zil:122), envelope to woman +5
	(people.zil:1129), letter read +1 (people.zil:1281), trail top
	first time +1 (fog.zil:178), bone to poodle +3 (south.zil:609),
	snake scares troll +3 (shoppe.zil:584 or bridge.zil:250 — same
	event, once only), platypus rescue +5 (bridge.zil:464), blanket
	on grue +3 (under.zil:233), hat to pelican +5 (people.zil:1033),
	worm... (token machine) +1 (east.zil:591), ticket from Voss +3
	(people.zil:719), arcade->Hilltop +5 (east.zil:553), magic word
	+3 (parser.zil:754), chains unlocked +1 (tower.zil:728), violet
	note read +3 (center.zil:1616), security switch +3
	(tower.zil:1397), crank +1 (tower.zil:362), ALEXIS HEEL +5
	(south.zil:668), library unlocked +3 (center.zil:1506), stone
	into sculpture +5 (center.zil:2135, silent).
Penalties (all avoidable): -10 each for: disturbing the leaves at Edge
of Lake in Festeron (west.zil:368), refusing Voss's note (people.zil:806),
stone to the vulture (bridge.zil:519), stone to the pelican
(people.zil:1016), torture machine PUSH LEVER UP (tower.zil:975), grue
milk to Chaos (tower.zil:1254).
Max = 100 confirmed by UPDATE-SCORE's own text ("out of 100",
globals.zil:354) and the r68 finale ("100 points out of 100").

## 7. RANDOMNESS INVENTORY (ranked by replay risk)

1. **THE MAGIC WORD (must be PARSED)** — `POWER = RANDOM(3)-1` rolled at
   first post-office entry (I-HOORAY south.zil:120); revealed only in
   the pelican text "traces a word on a passing cloud: (KALUZE|FRATTO|
   SORKIN)" (people.zil:1027, table 1054). Parse it there; `SAY <word>`
   at Hilltop. Hardcoding = 2/3 chance of ruin (a wrong-word guess is
   rejected, and any word said before the pelican permanently locks the
   drawbridge word out, parser.zil:735-741).
2. **Vapor scatter** (cemetery.zil:637-660): 3rd consecutive turn in
   Witchville cemetery = all items to `<PICK-ONE ,DROP-OFFS>` random
   rooms. Never triggered on-route (2-turn dash into the grave); treat
   "stroke your face with ghostly fingers" as a one-turn-left alarm.
3. **PROB-TUMBLE on the trail/fog maze** (fog.zil:229-240): each wrong
   direction adds 10% cumulative death chance and consumes RNG. The
   route makes zero wrong moves; a replayer must never "explore" here.
4. I-VULTURE — PROB 5 per outdoor turn after the branch snaps
   (parser.zil:2485-2495, bridge.zil:615-621): flavor sighting only,
   but consumes RNG on its schedule. Absorbed by text-anchored sync.
5. I-RATTLE — PROB 5 per turn while carrying the unsquashed can
   (shoppe.zil:722-728). Flavor; RNG consumer between TAKE CAN and
   SQUEEZE CAN.
6. PLACE-CLOSES / Crisp dialogue — PROB 50 rolls (people.zil:152-170)
   on post-office turns; READ-BEG PROB 50 x4 (people.zil:1249-1264) if
   you stall before reading the letter; princess begging PROB 50
   (people.zil:360-365); jail wails PROB 10/50 (parser.zil:2466-2470,
   2891-2895; boxes.zil:540) — all flavor-text-only RNG consumers.
7. PICK-ONE random selection (parser.zil:1916) in dozens of flavor
   tables (YUKS, IGNORANCE, FACES, CRAMPS at under.zil:25-30 — two PROB
   50s per tunnel-room look, etc.). Consumes RNG on nearly every turn;
   harmless as long as replay syncs on text milestones, never on RNG
   position.
8. Boot Patrol, jail countdowns, grue timer, movie script, king script,
   Crisp scripts, piranha window, door slam, fog cells: ALL
   deterministic counters — no RNG.
Values that must be PARSED from text at runtime: the magic word (only
one). Everything else is schedule-driven; the @until sync blocks absorb
all timing/text variance.

## 8. HARD BUDGETS, ONE-SHOTS, TRAPS (r68)

- 17:00 Festeron deadline (~120 turns; route uses ~57 + frozen shoppe
  time) and 06:00 Witchville moonset (720 turns; route uses ~105).
- ONE-SHOT: gold coin must be taken in Festeron (SKEW dumps fountain
  contents into STEEP-TRAIL limbo, people.zil:1432-1434). No coin -> no
  ticket -> no glasses -> no lab -> max 100 impossible.
- ONE-SHOT: violet note must be ACCEPTED in Festeron (SKEW removes it
  otherwise, people.zil:1447-1451). Also the only sane Crisp exit.
- ONE-SHOT: DIG IN SAND before rescuing the platypus sets LAKE-SAND
  RMUNGBIT and the whistle can NEVER be found (west.zil:127-143) —
  island, hat, pelican word all lost. Order: rescue first, then dig.
- ONE-SHOT: LOOK UNDER LEAVES in Festeron = -10 AND platypus never
  appears in the pit (DESCRIBE-PIT west.zil:363-368 + SKEW branch
  people.zil:1424-1430). Don't touch the leaves.
- ONE-SHOT: the arcade machine breaks after one game (GAME-OVER,
  east.zil:559-561). The 4 joystick moves + button must be right; only
  H3/V5 (Hilltop) awards +5.
- Troll: giving him the COIN (no luck wish) = coin tossed to the ground
  and refused forever after a second offer (REMOVEd,
  bridge.zil:190-233); the can/snake is the correct move and worth +3.
- Torture chamber: from CRISP-SCRIPT 5 onward Crisp confiscates one item
  per turn; if he ever handles the STONE it goes into the coat pocket
  and stays retrievable, but if he empties your hands entirely = chute
  death (NO-BRIBE people.zil:332-341). Give the note on the first
  possible turn.
- Museum: breaking the case with SW2 still closed = torture ending
  (center.zil:1956-1961). Exiting the theater while wearing the glasses
  = dumped into Fuzziness (EXIT-AUDITORIUM center.zil:544-551) —
  recoverable (remove glasses) but wasteful.
- Weight limit 18 for the grave exit and both hole traversals
  (globals.zil:455-467, cemetery.zil:196-204); the branch and an OPEN
  umbrella block them outright. The route's DROP ALL before the jail
  hole handles the only tight spot.
- Death budget: 0. Captures: 0 (1 survivable; 3rd fatal without the
  seahorse rescue).
- r68 vs r69 quirks: none found that affect the route; all cited
  mechanics behaved identically on r68 in verification. The historical
  source's j2.z3 is r69/850920; nj2.z3 is the later "solid gold" style
  build — neither is our target.

Useful sync strings (all stable across seeds, verified):
- "tossing it onto the service counter" (envelope available)
- "You have been warned" (cemetery entry accepted)
- "locking the north gate|locks it" (gravedigger gone)
- "holding it out to you" (Voss note / king's hat offers)
- "springs suddenly to life" (seahorse saved)
- "score just went up by N" (every UPDATE-SCORE; the machine-readable
  companion is global 136)
- "traces a word on a passing cloud: X" (THE word)
- "Nice of you to drop by" (tower capture complete)
- "Violet scolds me when I'm late" (Crisp gone; coat available)
- "reveals a metal crank" / "You got it" / "finished the story"

## 9. VERIFICATION STATUS

scripts/solve_wishbringer_adaptive.py plays the full route with 19
score-asserted checkpoints. On the research pathway (raw ZMachine, seed
pinned before boot): **100/100 on all 92 seeds tested** (1-64, 77, 99,
111, 123, 222, 333, 444, 456, 555, 666, 777, 789, 888, 999, 1000, 1234,
2000, 2024, 3000, 4711, 5678, 7777, 8080, 9999, 12345, 31337, 54321,
65535), 179 commands, 162 game moves, finishing at 19:45 game time. All
three magic words exercised (word varies by seed and is parsed at the
pelican). No captures, no deaths, no wishes. After porting to the
GameWalker pathway (seed pinned after start(), matching replay_solve):
100/100 on seeds 1-10; the seed-1 recording is
walkthroughs/wishbringer_verified_100.txt, replay-verified by
scripts/replay_solve.py (won=True, died=False).

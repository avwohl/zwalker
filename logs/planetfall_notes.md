# PLANETFALL (Infocom, 1983) — Mechanics Notes for Deterministic Replay
Target binary: Release 37 / serial 851003, Z-machine V3, 80 points max
(games/zcode/planetfall.z3 — header verified: version 3, release 37, serial 851003).

Sources used:
- ZIL source: github.com/historicalsource/planetfall (authoritative). The build is
  planetfall.zil, which IFILEs SYNTAX, MISC, GLOBALS, PARSER, VERBS, COMPONE
  (Kalamontee complex), COMPTWO (Lawanda complex) — planetfall.zil:20-26.
- ifarchive.org/if-archive/infocom/hints/solutions/planetfall.step1
  (Paul D. Smith command list) and planetfall.step2 (Jacob Gunness command list,
  1990) — two independent complete walkthroughs.
- ifarchive.org/if-archive/infocom/hints/solutions/planetfall.txt (prose, 3 parts).
- walkthroughking.com/text/planetfall.aspx (Day 1/2/3 structure).
- zedlopez.github.io/invisiclue/planetfall.html (InvisiClues conversion; consulted
  for cross-checks).
- EMPIRICAL VERIFICATION: the entire route in planetfall_route.txt was
  machine-played to 80/80 against the r37 binary under the project Z-machine
  (zwalker.zmachine) on 65/65 distinct pinned RNG seeds
  (seeds 1-30, 42, 50-100 by tens, 77, 99, 111..999 by 111s, 123, 456, 789,
  1000, 1234, 2000, 2024, 3000, 4711, 5678, 7777, 8080, 9999, 12345, 31337,
  54321, 65535), 420-490 moves, game complete early on in-game Day 2.
  Both the 2-pour and 3-pour communications variants were exercised.
  Every mechanic below marked [verified] was observed in those runs.

---

## 0. THE CLOCK IS NOT TURN-BASED — read this first

Planetfall's clock counts "millichrons" (Galactic Standard Time), not turns.

- `C-ELAPSED-DEFAULT = 7` (misc.zil:428): an ordinary non-movement action = 7 units.
- `DEFAULT-MOVE = 20` (globals.zil:8): a room-to-room walk = 20 units, but each
  room's C-MOVE table can override per direction (V-WALK, verbs.zil:429-465):
  the long east-west hall = **160** (compone.zil:732, 898, LONG-HALL-F 907-917),
  Underwater up = 35, Crag up = 40, ladder rift crossing = 33
  (LADDER-EXIT-F compone.zil:1053-1065), lobby west = 30, many 25s, bio-lock 10s.
- Notable per-action costs: `wait` = **40** (verbs.zil:832), `look` = 9,
  `inventory` = **18**, eat/drink = 15 (globals.zil:1065, compone.zil:854),
  read graffiti = 28, play with Floyd = 30, extend ladder 36 / collapse 21
  (compone.zil:678,683), Floyd hole-trip 50 (comptwo.zil:262), board fetch 22
  (compone.zil:1897), the final foray door-close **95** (comptwo.zil:1857-1858),
  pod-trip turns 54 each (misc.zil:238-239), shuttle turns 600/velocity
  (misc.zil:240-241), pod exit 30 (globals.zil:938).
- TIMELESS verbs (misc.zil:263-272): score, time, save, restore, version, brief,
  script, **#random** — all cost 0. `time`/`score` print the GST clock: use them
  freely as a scheduling oracle. `score` also prints the Day number.
- Interrupt queues are countdowns decremented by C-ELAPSED each turn
  (CLOCKER misc.zil:459-480); `<QUEUE I-X -1>` = every turn. Queue ticks do NOT
  advance overnight and are NOT reset by the daily clock rewind — only
  INTERNAL-MOVES is rewound (RESET-TIME).
- GO (misc.zil:73-107) starts the game at `INTERNAL-MOVES = 4450 + RANDOM(180)`
  (misc.zil:86) — the displayed chronometer time is RANDOM; parse it, never
  hardcode it. Queues at start: I-BLATHER -1, I-AMBASSADOR -1,
  I-RANDOM-INTERRUPTS 1, I-SLEEP-WARNINGS 3600, I-HUNGER-WARNINGS 2000,
  I-SICKNESS-WARNINGS 1000.

`#random N` (syntax.zil:55, V-$RANDOM verbs.zil:1551-1555) is compiled into r37:
it executes `<RANDOM -N>`, i.e. SEEDS the interpreter RNG, is timeless, and
prints nothing. [verified: after `#random 5` two divergent games produce
byte-identical futures]. The production recorder can use this as a mid-game
RNG resync at any quiet prompt. (It does not reschedule already-queued
interrupt ticks — e.g. the explosion time is fixed at end of turn 1.)

## 1. The opening on the Feinstein

- I-RANDOM-INTERRUPTS fires at end of turn 1 (misc.zil:109-112): queues
  **I-BLOWUP-FEINSTEIN at RANDOM(90)+240 units** (241-330 → 6-8 `wait`s at 40
  units each), calls COMM-SETUP (see §5) and sets NUMBER-NEEDED = RANDOM(1000)
  (the conference-room dial combination — not needed for points).
- While waiting on Deck Nine: I-BLATHER (globals.zil:680-729) PROB 5 per turn
  brings Blather; I-AMBASSADOR (globals.zil:802-834) PROB 15 brings the
  ambassador, who **hands you the brochure** (globals.zil:827) — SIZE 4 of
  dead weight; drop it (it caused a "load too heavy" failure at the tool room
  on ~half the seeds until the route dropped it). [verified]
  Both NPCs are harmless on Deck Nine; do NOT wander to Deck Eight/Reactor
  Lobby — 4 turns there with Blather = brig = death at the explosion
  (globals.zil:683-691, 1207-1212).
- The explosion sequence, one BLOWUP-COUNTER step per turn once it starts
  (globals.zil:1162-1268):
  counter 1 "A massive explosion rocks the ship" — pod door opens;
  counter 2 emergency bulkheads shut;
  counter 3 pod door clangs shut — DEATH unless in the pod or on Deck Nine;
  counter 4 pod slides down the tube;
  counter 5 Feinstein explodes — DEATH on Deck Nine; if in the pod but NOT in
  the safety web: **PROB 20 death** (globals.zil:1178-1183).
  => CRITICAL cadence: on the turn after "massive explosion": `w`; next turn
  `get in web`; then wait. [verified]
- Pod trip: I-POD-TRIP every turn at 54 units each (globals.zil:1272-1325),
  TRIP-COUNTER messages 1,2,3,7,8,9,10; at counter 11: if in web, "The pod
  lands with a thud" and kit+towel appear (TRIP-COUNTER set to 15); if not in
  web, death. About 13-14 `z` after the web.
- Leaving: `stand` starts I-SINK-POD (SAFETY-WEB-F globals.zil:983-995);
  SINK-COUNTER 5 = death regardless of the door (globals.zil:1342-1352), so:
  stand / take kit / open door ("cold ocean water rushes in") / out.
  POD-EXIT-F (globals.zil:929-948) sends OUT/UP to Underwater (30 units).
- Underwater (compone.zil:7-33): DROWN counter, death after 2 turn-ends → `u`
  immediately to Crag (+3; the pod itself was +3 on entry).

## 2. The clocks

### 2.1 Day cycle / sleep
- I-SLEEP-WARNINGS (globals.zil:2026-2087). Day 1 first warning at +3600 units
  ("You begin to feel weary"), then re-queued +400 ("really tired"), +135
  ("you'll probably drop"), +50-60 ("barely keep your eyes open"), then level 5:
  in a dorm you're dumped into a bunk; on Crag(day1)/Balcony(day3)/Winding
  Stair(day5) you drown; anywhere else **PROB 30 grue death** (globals.zil:2078).
- Voluntary sleep only when SLEEPY-LEVEL > 0 (V-SLEEP verbs.zil:1724-1731), but
  `get in bed` works at any sleepiness: with SLEEPY>0 it queues I-FALL-ASLEEP 16
  (2-3 turns); at SLEEPY=0 you lie awake and the next warning converts to
  I-FALL-ASLEEP 16 because you're already in bed (globals.zil:2028-2034).
  => Route: go to Dorm B, `get in bed`, then `z` until "***** SEPTEM".
  NEVER sleep in the Infirmary bed — instant-death robot (globals.zil:2108-2116).
- WAKING-UP (globals.zil:2197-2255): DAY+1; **all non-worn carried items are
  dumped on the floor at the bed**; an OPEN canteen is emptied
  (globals.zil:2208-2211 — close it before bed!) and the flask is always
  emptied (2212-2214); prints "***** SEPTEM <day+5>, 11344 *****".
  Hunger at wake: if HUNGER-LEVEL>0 you wake FAMISHED = level 4 with a
  100-unit fuse (2236-2240) — always go to bed with hunger reset;
  if 0, hunger re-queued at only **+400** (2242) — breakfast is mandatory daily.
- RESET-TIME (globals.zil:2257-2287): day-start GST and sleep-warning queue:
  day2 1600+R80/5800; day3 1750+R80/5550; day4 1950+R80/5200; day5 2150+R80/4800;
  day6 2450+R80/4300; day7 2800+R80/3700; day8 3200+R80/3000;
  **day 9 wake = "you don't seem to have survived the night" — hard game-over**.
- Rising water (WATER-LEVEL-F compone.zil:151-160): Crag unreachable after day 1,
  Balcony flooded from day 4, Winding Stair from day 6. Irrelevant to a 2-day
  route, but never sleep on the cliff path.

### 2.2 Hunger/thirst
- I-HUNGER-WARNINGS (globals.zil:2295-2318): first at +2000 units, then
  +450 (ravenous) +150 (faint) +100 (millichrons warning) +50 → death
  ("You collapse from extreme thirst and hunger").
- Kit goo (globals.zil:1055-1082): must hold the OPEN kit; resets hunger and
  re-queues at **1450**; three blobs (red/green/brown), each single-use;
  goo cannot be taken out or dropped.
- Kitchen dispenser (compone.zil:795-881, BUTTON-PSEUDO globals.zil:2580-2603):
  open canteen in the niche + press button = fill; `drink liquid` (drink=eat
  synonym, syntax.zil:122) requires holding the canteen, resets hunger and
  re-queues at **3600** — 2.5x better than goo. Kitchen door needs the kitchen
  card each time (door auto-closes ~50 units after you leave, globals.zil:1470).
- Verified schedule for the 2-day route: goo #1 at the day-1 growl (~GST 6500);
  canteen drink at the kitchen ~8450 (covers the night); carry the REFILLED,
  CLOSED canteen to bed; day 2 growl comes at wake+400 (~2050) → drink and
  abandon the canteen; goos #2/#3 cover the rest of day 2 (growls ~+1450).

### 2.3 Sickness (The Disease)
- I-SICKNESS-WARNINGS (globals.zil:2330-2369): queued 1000 at start, re-queues
  every 700, but only *advances* when SICKNESS-WARNING-FLAG is set — which
  happens once per WAKING-UP (globals.zil:2199) and once at the first
  Lawanda Platform entry (comptwo.zil:23-26). So: level 1 early day 2,
  level 2 shortly after reaching Lawanda (2-day route peaks at level 2 —
  "unusually weak... fever"). Death at level 9; in practice the day-9 wake
  kills you first.
- Each level costs **LOAD-ALLOWED −10** (globals.zil:2334) off the base 100
  (globals.zil:15) — this is the mechanic that actually bites (see §7 weight).
- The infirmary MEDICINE (comptwo.zil:169-204): sickness −2, LOAD +20 — a
  worthwhile detour only for longer routes; unused here.
- The CURE: there is none you can take. The disease is cured only in the
  ending scene by the medical robot (comptwo.zil:1438-1440). The computer fix
  (§6) is what makes "DRUG TESTEENG 99.985%" finish — the whole plot deadline
  is the day-8 limit, not a separate disease timer.

## 3. FLOYD

- Activation: Floyd starts inert in the Robot Shop. **Search the robot BEFORE
  turning him on**: you get the lower elevator access card (+1) deterministically
  (compone.zil:2079-2088, CARD-STOLEN=T). This bypasses FLOYD-REVEAL-CARD-F
  (globals.zil:1440-1468), whose card reveal is heavily random (PROB 5-40 by
  day). `turn on robot` → "Nothing happens." +2 (compone.zil:2062-2071) and
  I-FLOYD queued 25 (~4 turns) — he springs to life shortly after. [verified]
- I-FLOYD runs EVERY turn Floyd is active (compone.zil:2158-2271) and is the
  game's main RNG noise source:
  present: PROB 6 wanders off (only in FLOYDBIT rooms, when FLOYD-FOLLOW);
  else PROB 40 → a floydism (PICK-ONE of 20 strings — a second RANDOM);
  absent + following: PROB 80 catches up ("Floyd follows you");
  absent, not following: auto-follows into booths/locks/elevators/shuttle
  cabins/mini booth; else PROB 30 bounds in (+nested PROB 15 variant).
  => Every turn Floyd is alive consumes 1-3 RNG draws. All post-activation
  synchronization MUST be text-based, never draw-count-based.
- Orders can fail because he wandered: retry pattern required (route uses a
  wait-for-return + reissue loop; hit on seed 31337). [verified]
- Needed for: (a) the shiny fromitz board — in the Repair Room
  `floyd, go north` sends him through the robot hole (FLOYD-THROUGH-HOLE
  comptwo.zil:257-271, sets BOARD-REPORTED), then `floyd, take shiny board` —
  he tosses it to you (compone.zil:1887-1901; a MOVE, not a take — no fumble
  roll); (b) the COMPUTER-FLAG — set when Floyd follows you into the Computer
  Room (KLUDGE compone.zil:2280-2293 → COMPUTER-ACTION comptwo.zil:1514-1524)
  or by `show output to floyd`; (c) the Bio Lab foray below.
  He is NOT needed for the helicopter (a red herring — locked, key only
  appears in the ending joke).
- THE FORAY (Bio Lock East): with Floyd present and COMPUTER-FLAG set, at
  turn-end he peers through the window and volunteers (BIO-LOCK-EAST-F
  comptwo.zil:1717-1759; also reveals the mini card object). NOT random.
  ONE-SHOT: if you dither more than 3 turn-ends after the offer he gives up
  permanently (WAITING-COUNTER, FLOYD-GAVE-UP comptwo.zil:1722-1732) and the
  mini card becomes unobtainable → 80 impossible.
  CRITICAL 5-turn cadence (I-FLOYD-FORAY comptwo.zil:1949-2030):
    `open door`  (Floyd plunges in)
    `close door` (skirmish sounds — door open now = you die)
    `z`          (three knocks + tearing metal)
    `open door`  (Floyd stumbles out clutching the card — door closed now =
                  Floyd dies inside and the card is lost forever)
    `close door` ("not a moment too soon", +2, the song, C-ELAPSED 95)
    `take mini card` (+1).
  Floyd's death IS required for the last 2 points on r37 (comptwo.zil:1991),
  and the mini card is required for the endgame. He is rebuilt in the best
  ending (comptwo.zil:1441-1446).

## 4. Complete route (as machine-verified; ~430-490 moves, ends Day 2 ~GST 5200)

Day 1 (start GST 4451-4630):
1. Deck Nine: `z` until "massive explosion rocks the ship" (6-9 z's);
   `w`; `get in web`; `z` until "pod lands with a thud"; `stand`; `take kit`;
   `open door`; `out`; `u` (Crag +3, pod +3).
2. `u` x3 to Courtyard; drop brush + brochure; open kit.
   N, NE, E, E, E(long hall) to Corridor Junction.
3. S,S,S,SW Tool Room: take magnet, flask, laser, pliers. E to Machine Shop.
4. N x4, N to Admin Corridor South: `put magnet on crevice` — the key leaps to
   the magnet (MAGNET-F compone.zil:1584-1593; no need to hunt the random
   "glint" PROB 20 room message, ADMIN-CORRIDOR-S-F compone.zil:936-942);
   DROP THE MAGNET before ever holding a card (I-MAGNET scrambles one held
   card per turn, compone.zil:1595-1613; HELD? is transitive, parser.zil:1173).
5. S, E Elevator Lobby: drop laser+pliers (overnight stash), press blue button,
   press red button (both elevators called now; arrivals are random,
   RANDOM(20)+40 and RANDOM(40)+80, compone.zil:2554,2564 — they stay open).
6. W, S,S,S,SE Robot Shop: `search robot` (+1 lower card), put lower card in
   kit, `turn on robot` (+2). NW,N,N, E Storage East: take good bedistor.
   W, N, E lobby: drop bedistor (stash). W to Junction.
7. W(long),W Mess Corridor: eat goo when the growl has fired;
   unlock padlock with key, take padlock (frees the hook), drop padlock+key,
   open door, DROP KIT (ladder 80 + kit 25 > LOAD 100), N Storage West (+4),
   take ladder, S, E, E(long), N, N Admin Corridor: drop ladder, extend ladder,
   put ladder across rift, N (+4, crossing costs 33).
8. W Small Office: open desk, take kitchen card + upper card; W Large Office:
   open desk, take shuttle card; E,E,S(cross),S,S Junction.
9. E lobby; upper elevator up (slide upper card — enable lasts 180 units,
   globals.zil:1398; press up; trip 50 units; sync "elevator door slides open");
   S Tower Core (+4); NE Comm Room: PARSE "A <color> colored light is flashing".
10. Comm cycle (repeat until fixed, 2 or 3 total pours — see §5): SW, elevator
    down, W, S x4 Machine Shop, put flask under spout, press <color> button,
    take flask, N x4, E, elevator up, S, NE, `pour fluid into hole`;
    "all go off except one, a <color> light" → new color; "go dark" → +6 done.
    Day 1 performs exactly one pour; the rest happen day 2 morning.
11. Evening: elevator down, W, W(long), W, take kit, S Mess Hall, take canteen,
    open canteen, slide kitchen card through slot, S Kitchen (+4):
    put canteen in niche, press button, take canteen, drink liquid,
    put canteen in niche, press button, take canteen, close canteen,
    drop kitchen card, N, N, W, N Dorm B: get in bed, z until "SEPTEM".
Day 2 (start GST 1600-1680):
12. stand; take kit, upper card, shuttle card (into kit), flask, canteen;
    S,E,E,E(long),E lobby; finish comm cycles (step 10) until "go dark" (+6);
    drop flask in the Comm Room, come down, drop upper card.
    (Drink the canteen at the wake+400 growl, then abandon it.)
13. take lower card (from kit), take laser, take pliers, take bedistor
    (order matters: bedistor last keeps every take at CCOUNT<=7 — §7);
    S into Lower Elevator (open since day 1), slide lower card through slot
    (enable 200 units), press down button (trip 100), sync "slides open",
    drop lower card, N, E Kalamontee Platform (+4).
14. Shuttle (before GST 6000! globals.zil:1797-1801): S into Alfie, E control
    cabin east, take shuttle card, slide shuttle card through slot,
    drop shuttle card, `push lever up`, `z` x11 (display reaches 60; the
    "Hafwaa Mark" sign passes on the next command), `pull lever` (center),
    `pull lever` (down), `z` until "glides into the station" (11 z's;
    velocity profile lands exactly on SHUTTLE-COUNTER 24 at speed 0 —
    I-SHUTTLE globals.zil:1901-1940, DESCRIBE-SHUTTLE-ARRIVE 1976-2015).
    W, N Lawanda Platform (+4). [verified: clean "glides into the station"]
15. E, U, NE, E, E, N Course Control: open lid, take fused bedistor with
    pliers (ZATTRACT — comptwo.zil:595-607), drop fused bedistor,
    put good bedistor in cube (+6), drop pliers. (NEVER touch the good
    bedistor afterwards: instant death, compone.zil:1424-1428.)
16. S, W, W, N Repair Room: wait for Floyd; `floyd, go north` (he finds the
    shiny board, 50 units); `floyd, take shiny board` (retry if he wandered).
    S, E, N Planetary Defense: open panel, take second board (the fried one
    comes out), drop fried board, put shiny board in socket (+6).
17. S, E, S, S, S Computer Room (Floyd follows → "Uh oh. Computer is broken" —
    else `show output to floyd`); take output (reading it is optional: the
    damaged sector is the CONSTANT 384, comptwo.zil:1552); drop output.
18. NE Main Lab, S Lab Storage: take old battery, drop old battery, take new
    battery, put new battery in laser (NEW-SHOTS = 21-30; OLD-SHOTS = 3-5,
    compone.zil:3122-3123 — the old battery is never sufficient).
19. N, open bio-lock door, SE Bio Lock West, E Bio Lock East (Floyd
    auto-follows into locks), z until "Floyd will get card", then the CRITICAL
    foray cadence of §3 (+2, +1 mini card).
20. W, open door, W, SW Computer Room, S Mini Booth: slide mini card through
    slot ("please type in damaged sector number", activation window 30 units),
    `type 384` (any other 2-4 digit number = death, verbs.zil:1628-1652).
21. Inside the computer: E Strip Near Station (+4), N, N Strip Near Relay:
    `set dial to 1` (MANDATORY: any other setting destroys the relay and the
    game — comptwo.zil:2865-2872), `shoot speck with laser` repeatedly until
    "vaporizes into a fine cloud" (+8; two hits needed; hit chance starts 0
    and grows +12 per miss — SHOOT-SPECK comptwo.zil:2842-2872; 3-15 shots;
    I-FRY 200-unit exit fuse starts, comptwo.zil:2850,2880-2889).
22. S — the microbe lands in front of you (comptwo.zil:2478-2496).
    `set dial to 6`, then `shoot microbe with laser` each turn (a hit sets
    MICROBE-HIT and freezes its 2-turn kill counter — I-MICROBE
    comptwo.zil:2939-2965) until laser warmth >= 8 (warmth = shots fired
    minus idle turns; I-WARMTH comptwo.zil:2789-2813), then
    `throw laser off strip` — microbe lunges after it (+needs warmth>7,
    STRIP-F comptwo.zil:3017-3036). Do NOT let warmth exceed 13 while zapping
    (death, comptwo.zil:2942-2948). The route's accounting: speck shots n,
    minus 2 idle turns (walk + dial), plus microbe zaps to reach 9.
23. S, W Station 384 → automatic teleport to the Auxiliary Booth (+4)
    (STATION-384-F comptwo.zil:2410-2424; I-ANNOUNCEMENT 130 queued: "Revival
    procedure beginning" fires mid-chase — cosmetic).
24. N Lab Office: search desk (memo auto-taken), open desk, take gas mask,
    wear gas mask, `press red button` (fungicide flood; I-UNFLOOD 50-unit
    window — comptwo.zil:2351-2368). CRITICAL escape, one command per turn:
    open office door / W (Bio Lab — flooded + mask = survive,
    comptwo.zil:2061-2073) / open lab door / W (Bio Lock East) / W (Bio Lock
    West — one-turn grace, EXTRA-MOVE-FLAG comptwo.zil:2091-2095) /
    open door (the east door has ALREADY auto-closed after 30 units,
    I-BIO-EAST-CLOSES comptwo.zil:1868-1873, so the interlock allows it —
    do NOT close it manually, that extra turn is fatal [verified]) /
    W Main Lab / W / W / S ProjCon Office / S Cryo-Elevator (door open since
    the computer fix) / `press button` (+5, chase disabled,
    globals.zil:2652-2663). Never revisit the room you were in two turns ago
    (SECOND-TO-LAST-ROOM death, comptwo.zil:2101-2105).
25. z until "The elevator door opens onto a room" (100-unit descent), `n` —
    the Cryo-Anteroom Veldina scene runs (comptwo.zil:1393-1478): with course
    control fixed you save the planet; with comm+defense also fixed the
    S.P.S. Flathead lands, you make Lieutenant First Class and Floyd is
    rebuilt. FINISH prints "Your score would be 80 ... Galactic Overlord".
    (Do NOT press the elevator button a second time after arrival — the
    famous last-move death, globals.zil:2664-2674.)

## 5. The communications puzzle (biggest structured randomness)

COMM-SETUP runs at end of turn 1 (compone.zil:3121-3126):
- ORDER-LTBL = random permutation of colors 1..7 (RANDOMIZE-ORDER,
  compone.zil:2938-2959 — a rejection-sampling loop, HEAVY variable RNG use);
- STEPS-TO-GO = 1+RANDOM(2) → **2 or 3 pours needed** (50/50);
- CHEMICAL-REQUIRED = the first needed color.
Enunciator shows the needed color when you enter the Comm Room ("A <color>
colored light is flashing", compone.zil:2847-2869) and after each correct pour
("all go off except one, a <color> light", compone.zil:3008-3023).
Colors → machine-shop buttons: red/blue/green/yellow/gray/brown/black =
KUULINTS/KATALISTS buttons (compone.zil:1692-1771; COLOR-LTBL 1775-1785).
The flask holds one dose; it is emptied every night (WAKING-UP).
**Pouring a WRONG color shuts the whole console down permanently**
(COMM-SHUTDOWN, compone.zil:3024-3034; −6 if it was already fixed) — the
colors MUST be parsed from this run's text at runtime.
The white BAAS/ASID buttons produce base/acid (CHEMICAL-FLAG 8/9) which
dissolve ACIDBIT items (compone.zil:3035-3100) — never needed; never press them.

## 6. The 80-point breakdown (all from ZIL; sums verified in play)

Rooms, first entry (VALUE prop, scored by GOTO→SCORE-OBJ verbs.zil:897-913,214-218):
	3	Escape Pod (globals.zil:900)
	3	Crag (compone.zil:52)
	4	Storage West (compone.zil:605)
	4	Kitchen (compone.zil:793)
	4	Admin Corridor North (compone.zil:1035)
	4	Tower Core (compone.zil:2738)
	4	Kalamontee Platform (compone.zil:3189)
	4	Lawanda Platform (comptwo.zil:16)
	4	Auxiliary Booth (comptwo.zil:2381)
	4	Strip Near Station (comptwo.zil:2453)
Objects, first take (VALUE 1 each):
	1	kitchen access card (compone.zil:1228)
	1	upper elevator access card (compone.zil:1238)
	1	shuttle access card (compone.zil:1248)
	1	lower elevator access card (compone.zil:1257; via search-robot SCORE-OBJ compone.zil:2084)
	1	miniaturization access card (comptwo.zil:1578)
Events:
	2	turning Floyd on (compone.zil:2068-2070)
	2	first laser shot ever (comptwo.zil:2693-2695)
	6	communications fixed (compone.zil:3000-3002)
	6	planetary defense fixed (comptwo.zil:412-417)
	6	planetary course control fixed (comptwo.zil:570-575)
	2	Floyd's sacrifice completed (comptwo.zil:1991)
	8	computer fixed / speck vaporized (comptwo.zil:2846-2851)
	5	cryo-elevator button during the chase (globals.zil:2652-2659)
Total 38 + 5 + 37 = 80.
Reversible losses: wrong pour after comm fixed −6 (compone.zil:3027);
acid on the installed bedistor −6 (compone.zil:3049); munging the cube −6
(compone.zil:3093). The route triggers none.

## 7. Randomness inventory, ranked by replay risk

1. COMM COLORS + POUR COUNT (parse from text, mandatory): 2-vs-3 pours changes
   the day-2 command count by a full tower round-trip; a wrong pour is
   permanent. Strategy: @comm adaptive loop keyed on the color words.
2. SPECK MARKSMANSHIP (parse, mandatory): PROB(counter), counter += 12/miss,
   TWO hits needed; observed 3-15 shots. Battery holds 21-30 (both values
   random and invisible — cannot be parsed; theoretical exhaustion odds are
   ~1e-9, accepted). The shot count also feeds the WARMTH ledger used for the
   microbe (window: >7 to throw, <=13 while zapping). Strategy: @speck /
   @microbe loops that count shots and idle turns.
3. FLOYD'S I-FLOYD (stream noise + behavioral): 1-3 RANDOM draws EVERY turn he
   is active; PROB 6 wander can break `floyd, ...` orders (must retry); PROB 80
   follow means his location is only softly controlled. All sync must be text
   milestones. His special-room auto-follow (locks/elevators/cabins) is the
   reliable rail the route leans on.
4. EXPLOSION TIMING: RANDOM(90)+240 units → variable count of opening waits
   (@until "massive explosion"). The two turns after it are CRITICAL.
5. ELEVATOR ARRIVALS: RANDOM(20)+40 (upper), RANDOM(40)+80 (lower) — @until
   "slides open" (calls made a half-day early hide the latency entirely).
6. BLATHER (PROB 5) / AMBASSADOR (PROB 15) pre-explosion: stream noise; the
   ambassador's brochure is a weight hazard — drop it. The GANGWAY bellowing
   (PROB 15, globals.zil:651-657) never fires in this route.
7. CLOCK VALUES: start GST 4450+R180, day starts +R80 — parse via timeless
   `time`/`score`; never use absolute times as triggers, only text.
8. FUMBLE (ITAKE verbs.zil:545-585): carrying >7 top-level objects makes every
   take roll PROB(count*8) to drop something (spilling open canteen/flask!).
   Strategy: structural — the route never issues a take at CCOUNT>7 (worn
   uniform + chronometer count!). Nesting used: cards ride inside the kit.
9. NIGHT: DREAMING PROB 13/PROB 60 + PICK-ONE (globals.zil:2145-2156) — noise.
10. SLEEP COLLAPSE (PROB 30 grues) and DARKNESS MOVEMENT (PROB 75 grue,
    verbs.zil:509-513 / GOTO 902-907) — never triggered: sleep is scheduled,
    no dark room is ever entered (the lamp/flashlight is not needed).
11. NUMBER-NEEDED = RANDOM(1000) (conference dial): unused for points; if ever
    needed, read it from the lab-uniform combination paper (comptwo.zil:1680).
12. KEY GLINT PROB 20 (compone.zil:936-942): bypassed — the magnet fishes the
    key without ever seeing it.

## 8. Hard budgets, one-shots, unwinnable traps

- DAY LIMIT: dead on waking on day 9 (globals.zil:2285-2287). Route uses 2 days.
- SHUTTLE CURFEW: activation refused when GST > 6000 (globals.zil:1797-1801);
  crash at >=20 speed = death; 0 < speed < 20 at the buffer = survivable crash
  that permanently breaks that car (ALFIE/BETTY-BROKEN). The verified profile
  (up, 11 z, pull, pull, 11 z) docks at exactly counter 24 / speed 0.
- COMM: one wrong pour = those 6 points gone forever.
- LASER DIAL: shooting the speck at any setting but 1 destroys the relay =
  computer can never be fixed = no ending at all (comptwo.zil:2865-2872).
- MINI BOOTH: typing any valid-looking sector other than 384 = death.
- FORAY: >3 turn-ends of hesitation = Floyd gives up forever (mini card lost);
  wrong door state on foray turns 2/3/4/5 = your death or Floyd dies with the
  card. 5-turn CRITICAL section.
- CHASE: any non-productive turn once the mutants are unfrozen = death; the
  only free turns are the Bio-Lock-West grace, the cryo-elevator grace, and
  the flood window (50 units). Backtracking two rooms = death. CRITICAL.
- CRYO BUTTON: pressing it again after the descent = death at the last move.
- MAGNET: each turn it is carried it scrambles one carried card (even inside
  containers). Carry it only between the Tool Room and the crevice.
- WEIGHT: LOAD 100 − 10/sickness level; ladder=80 (day-1 haul must be
  near-empty-handed); day-2 kit+laser+pliers+bedistor = ~76-84 vs LOAD 90/80 —
  the route sheds the canteen and flask before Lawanda.
- INVENTORY COUNT: keep <=7 (incl. worn uniform+chronometer) at every take.
- DESTROYED/CONSUMED en route (by design): Floyd (+2), laser (thrown to the
  microbe), flask contents nightly, open-canteen contents nightly, one goo per
  ~1450 units, brochure/brush/magnet/padlock/key/cards abandoned after use.
- DEATH BUDGET: zero. Every death in Planetfall ends the run (FINISH offers
  only RESTART/RESTORE/QUIT — no Zork-style resurrection).

## 9. Release-37 quirks and sync strings

- r37/851003 is the final Planetfall release; the historicalsource ZIL matches
  its behavior at every mechanic used above (all line numbers are that repo).
  Earlier releases (20/830316, 26/830419, 29/840118) differ mainly in bug
  fixes; the classic walkthroughs (written against earlier releases) still
  parse identically for every command used here [verified against r37].
- FINISH prints "Your score would be 80" (V-SCORE's ASK? phrasing,
  verbs.zil:220-252) — match "would be", not "is", at the ending.
- Debug verbs compiled in: `#random N` (RNG reseed, timeless — see §0),
  `#command` (script input), `#record`/`#unrecord`.
- Useful sync strings (all verified verbatim in r37 output):
  "massive explosion rocks the ship" (explosion turn),
  "You feel the pod begin to slide" (counter 4),
  "pod lands with a thud" (landing),
  "cold ocean water rushes in" (door),
  "leaps from the" (key on magnet),
  "find and take a magnetic-striped card" (lower card),
  "Nothing happens." (Floyd switch-on),
  "spanning the precipice" (ladder),
  "Elevator enabled." / "The elevator door slides open." (elevators),
  "colored light is flashing" / "except one, a" / "go dark" (comm),
  "kitchen door quietly slides open", "fills almost to the brim",
  "certainly quenched your thirst", "***** SEPTEM" (new day),
  "Shuttle controls activated.", "Hafwaa Mark", "glides into the station",
  "manage to remove" (fused bedistor), "warning lights go out" (course),
  "squeezes through the opening" / "manage to catch it" (fromitz board),
  "warning lights stop flashing" (defense), "Computer is broken" (flag),
  "resting in the depression" (battery), "Floyd will get card" (offer),
  "plunges into" / "Floyd stumbles out" / "not a moment too soon" (foray),
  "type in damaged sector" / "walls of the booth sliding away" (mini),
  "vaporizes into a fine cloud" (+8), "elephant-sized monster" (microbe),
  "plummet into the void" (microbe gone), "Auxiliary Booth" (return),
  "hissing from beyond the door" (flood), "monsters reach it" (+5),
  "The elevator door opens onto a room" (descent done),
  "Veldina" / "Your score would be 80" / "Galactic Overlord" (win).

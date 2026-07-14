# SORCERER (Infocom, 1984) — Mechanics Notes for Deterministic Replay
Target binary: Release 18 / serial 860904, Z-machine V3.

Sources used:
- ZIL source: github.com/historicalsource/sorcerer (authoritative; "snapshot of the Infocom development system at time of shutdown", so late-final code — every mechanic below matches r18 walkthrough behavior; the one known cross-release delta is called out in §13)
- ifarchive.org/if-archive/solutions/infocom/solutions/sorcerer.step1 (Paul David Doherty, written against Revision 13/851021)
- .../sorcerer.step2 (Paul D. Smith step file)
- .../sorcerer.step3 (anonymous step file, close to the Jacob Gunness solution)
- .../sorcerer.txt (Jacob Gunness prose solution + spell/potion list)
- ifarchive.org/if-archive/solutions/infocom/invisiclues/Sorcerer.inv (InvisiClues text conversion; confirms 3-fweep maze plan, gnome search, grue suit/repellent equivalence, exact time-loop sequence)

All file:line citations refer to the historicalsource ZIL files. Note on tick timing:
`<QUEUE I-FOO n>` is decremented by the CLOCKER at the end of the queuing turn, so
an interrupt queued with n fires at the end of turn (queue-turn + n − 1). Evidence:
vilstu drunk inside the Coal Bin Room queues I-OLDER-SELF 1 (guild.zil:764) and the
twin arrives the same turn. All turn arithmetic below uses this convention; the
replayer should sync on message text, not exact turn numbers.

---

## 1. The opening dream

- GO (misc.zil:186-207) starts you in TWISTED-FOREST with `SLEEPING` true, queues
  I-WAKE-UP at 7 and I-HELLHOUND every turn (misc.zil:190-191), and calls I-HELLHOUND
  once before the first prompt (so the "hellhound racing straight toward you" warning
  prints before you ever type).
- I-HELLHOUND (belboz.zil:59-80): second firing while you are still in Twisted Forest
  = "tears you apart". Up the tree (TREE-BRANCH) swaps you to the boa clock
  (I-BOA, belboz.zil:127-146, same warn-then-kill pattern). Any other room dismisses
  the hound permanently.
- I-WAKE-UP (belboz.zil:5-9) = lightning-bolt JIGS-UP after 7 turns no matter what.
  Entering the fort Parade Ground while dreaming also fires it early (fort.zil:61-68).
- ANY death while SLEEPING is the wake-up: JIGS-UP's sleeping branch
  (verbs.zil:2857-2896) prints "...you wake up in a cold sweat", clears the touched
  flags of the dream-visited overworld rooms, queues the real game daemons
  (I-PARROT −1, I-MAILMAN 25, I-TIRED 80, I-HUNGER 21, I-THIRST 18, verbs.zil:2877-2881),
  rolls the journal code `CODE-NUMBER = RANDOM 12` (verbs.zil:2883), awards **+5**
  (verbs.zil:2886), puts you in bed in Your Quarters, and turns the lights off
  ("Your frotz spell seems to have worn off during the night").
- Randomness in the dream: NONE on the minimal path. The dream map is the real
  overworld, so wandering could hit PROB sites (minefield, river bank, snake pit),
  but a single `Z` gets you killed by the hellhound at the end of turn 1 with zero
  RANDOM calls consumed. **The wake-up RANDOM 12 is the game's first RNG draw**, so
  keeping the dream to exactly one command makes the journal code a fixed function of
  the pinned seed.
- Nothing done in the dream persists (touch flags are cleared; you carry nothing).

## 2. Spell system vs Enchanter

Initial spell book contents (objects `IN SPELL-BOOK`, globals.zil:951-1046):
GNUSTO, FROTZ, REZROV, YOMIN, IZYUK, PULVER, VEZZA — seven spells, all COUNT 0.
There is NO gaspar and NO fweep in the starting book (gaspar is a scroll in
Helistar's Quarters, guild.zil:473-495; fweep is a scroll in the Hidden Cave).

- ALWAYS-MEMORIZED: gnusto, frotz, rezrov (globals.zil:1087-1092) — castable forever,
  never consume a slot or a memorization. Everything else must be LEARNed.
- Slots: `SPELL-MAX` 4 / `SPELL-ROOM` 3 initially (globals.zil:1229-1231) — i.e. you
  can hold 3 learned copies on day 1. Casting a memorized spell decrements its COUNT
  and refunds the slot (PRE-CAST, verbs.zil:2019-2021).
- LEARN (globals.zil:1101-1160): needs the spell in the book, the book in hand, and
  light (or blort). Learning with SPELL-ROOM = 0 calls FORGET-SPELL — a RANDOM other
  memorized copy is lost (globals.zil:1140-1146, 1167-1194). Never do this.
- Sleep wipes ALL memorized spells (FORGET-ALL, called from V-SLEEP verbs.zil:1450)
  but grows capacity: `REAL-SPELL-MAX+1` each sleep (verbs.zil:1441-1443).
  Day 1 max 4, after sleep 1 → 5, sleep 2 → 6, sleep 3 → 7.
- I-TIRED firings shrink SPELL-MAX/SPELL-ROOM by 1 each (globals.zil:1327-1334) but —
  unlike Enchanter — do NOT randomly forget anything by themselves; only an
  over-capacity LEARN does.
- Casting from scrolls: any spell can be cast straight off a legible scroll in hand;
  the scroll vanishes (PRE-CAST verbs.zil:1987-1996). While FWEEPed (a bat) you cannot
  cast at all — "a high-pitched squeak" (verbs.zil:2008-2011). A soaked (MUNGBIT)
  scroll/book is illegible (verbs.zil:1981-1986).
- GNUSTO refuses AIMFIZ and YONK only ("too long, too complicated, too powerful",
  verbs.zil:2210-2216; scroll survives the attempt). Everything else can be inscribed;
  gnusto consumes the scroll (verbs.zil:2217-2233). No Krill-style probe counter
  exists in Sorcerer.

Scroll inventory (location — effect — needed?):
- AIMFIZ — Cellar trunk (guild.zil:1167-1180) — teleport to a person. **Required**
  (the only way out of the Guild Hall); cast on Belboz, +20 (globals.zil:618-625).
  Cast on almost anyone/anywhere else = death or nothing (V-AIMFIZ, verbs.zil:2132-2168).
- GASPAR — Helistar's Quarters (guild.zil:473-495) — resurrection; GASPAR ME sets
  RESURRECTION-ROOM = HERE (globals.zil:390-392; death handling verbs.zil:2903-2961).
  Optional (used by the "quick" maze exit; our route skips it).
- MEEF — Library (guild.zil:872-891) — wilt plants. **Required twice** in the endgame
  (spenseweeds, vines). +10 on first take (SCORE-OBJECT, verbs.zil:2530-2532).
- FWEEP — Hidden Cave, under the bat guano (belboz.zil:709-716, 786-802) — become a
  bat for 15 turns (V-FWEEP verbs.zil:2269-2302, I-UNFWEEP belboz.zil:803-820).
  **Required** (glass maze). Auto-drops everything you carry when cast.
- YONK — cannon at Fort Griffspotter after the guano trick (fort.zil:296-345, 365-374)
  — augment a spell; YONK MALYON sets MALYON-YONKED (verbs.zil:2461-2471).
  **Required**; +10 on take. Cannot be gnusto'd (one-shot).
- MALYON — arcade prize (park.zil:608-637) — animate. **Required** (dragon);
  +10 when the hawker hands it over. Gnusto-able.
- SWANZO — Hollow, beyond the glass maze (maze.zil:757-768) — exorcise. **Required**
  (finale). +25 only when taken in the STONE-HUT after the chimney drop
  (SCORE-OBJECT verbs.zil:2519-2524).
- GOLMAC — Slanted Room (coal.zil:1101-1110) — time travel. **Required**; GOLMAC ME
  (globals.zil:394-415) rewinds the mine.
- VARDIK — starts inside the older self, ends up in the kerosene lamp after golmac
  (coal.zil:1081-1090; globals.zil:397-398) — mind shield, 12 turns
  (globals.zil:383-385, I-UNVARDIK end.zil:777-781). **Required**; +25 on take.
- No melbor/exex/ozmoo/kulcad/guncho etc. in this game. VEZZA and YOMIN are flavor
  (VEZZA consumes RANDOM — verbs.zil:2419 — avoid casting it).

## 3. Survival clocks

Hunger/thirst (globals.zil:1371-1394):
- I-THIRST first fires at turn 18, then every 9; I-HUNGER at 21, then every 11
  (initial queues verbs.zil:2880-2881). Six warnings each ("a bit" → "dangerously",
  globals.zil:1396-1414); the firing after "dangerously" thirsty = death
  (hunger cascades into the thirst death, globals.zil:1375-1377). Unfed timeline:
  thirst death ≈ turn 72.
- **BERZIO potion** (ochre vial, Store Room, guild.zil:906-957): drinking gives +10,
  zeroes both levels, sets BERZIOED. While BERZIOED each daemon firing re-queues
  itself 580+RANDOM 80 (hunger) / 540+RANDOM 100 (thirst) turns out
  (globals.zil:1372-1374, 1385-1387). I-UNBERZIO clears the flag after 100 turns
  (guild.zil:943, 960-962) **but the daemons have already been pushed to ≈turn
  560-660**, so on any sane route (<300 turns) hunger and thirst never return: the
  potion effectively retires both clocks for the whole game. There is no food or
  water management at all. (The two BERZIOED re-queues each consume one RANDOM at
  fixed turns 18 and 21 — deterministic under a pinned seed.)
- Berzio does NOT set UNDER-INFLUENCE; the other four potions do, and drinking a
  second potion while one is active is a RANDOM-flavored instant death
  (TWO-POTIONS, globals.zil:1281-1296). Space out fooble → vilstu (17-turn fooble
  expiry, or any sleep, clears it).

Sleep (I-TIRED globals.zil:1318-1352, V-SLEEP verbs.zil:1432-1553):
- I-TIRED first fires 80 turns after waking/sleeping, then every 8. Each firing:
  LOAD-ALLOWED −10, FUMBLE-NUMBER −1, SPELL-MAX −1, AWAKE +1 and a "You are
  <tired-ness>" message. At AWAKE > 8 (10th firing, ≈turn 152 of the day) you
  collapse into forced sleep wherever you stand.
- SLEEP is refused while AWAKE = −1 ("you really aren't tired", verbs.zil:1436-1439),
  i.e. you can only sleep after the first I-TIRED firing (≥80 turns into a day).
- Sleeping in the Guild Hall before you have left (TWISTED-FOREST untouched) =
  Jeearr captures you → Chamber of Living Death, game over (verbs.zil:1452-1472).
  Other lethal sleep spots: river bed rooms, coal mine (with or without vilstu),
  Twisted Forest, Tree Branch, Snake Pit, Mine Field, Meadow, Drawbridge, River Bank,
  Hollow, Lagoon (verbs.zil:1474-1527).
- Sleep effects: capacity +1, full slot refill, all memorized spells wiped, MOVES+50,
  load/fumble reset, I-TIRED requeued 80, AWAKE=−1, WEAR-OFF-SPELLS (all potion and
  spell effects end; the toll gnome goes back to sleep; the park gnome vanishes —
  globals.zil:1206-1223). PROB 50 of a cosmetic dream (1-2 RANDOM draws per sleep,
  verbs.zil:1549-1553).
- Alcohol/cask/brogmoid: **do not exist**. "Brogmoid" is only a monster name on the
  infotater wheel (guild.zil:1034-1046) and a Cellar room synonym. No drinking clock.
- Other death clocks: coal-gas I-SUFFOCATE (2-turn warn, then death; coal.zil:106-113),
  vilstu wear-off I-BREATHE (19 + 4 + 6 turns; 3rd stage = death if still in the mine,
  else total exhaustion: AWAKE=8, LOAD 20, FUMBLE 1, I-TIRED 8 — guild.zil:778-815),
  underwater I-DROWN (warnings on your 3rd/4th consecutive turn-ends on the Lagoon
  Floor, death on the 5th; end.zil:287-306), and the 8-turn Belboz window (§10).

## 4. The Guild Hall opening

- You wake in bed, in the dark. `FROTZ ME` sets ALWAYS-LIT permanently
  (ME-F, globals.zil:427-441; LIT? honors it, gparser.zil:1448-1452) — one cast covers
  the entire game including the dark guild rooms, the mine after you give the book
  away, and skips every dark-room grue roll (GOTO: PROB 80 devoured moving dark→dark
  without light/spray/suit, verbs.zil:2818-2827). Cast it first.
- The Lobby south exit is blocked by a warning nymph (guild.zil:618-621) — the ONLY
  way out of the Hall is aimfiz. Belboz is missing (Frobar's note, guild.zil:521-538).
- Key: `MOVE HANGING` (or look behind it) in Belboz's Quarters drops the key, **+15**
  (guild.zil:391-405). The parrot squawks hints with PROB 40 per turn while you are
  in the room (guild.zil:107-125 — RNG consumer, deterministic under fixed commands).
- Journal (desk drawer, guild.zil:307-350): must be unlocked WITH THE KEY (rezrov is
  explicitly refused, guild.zil:333-337). Reading it shows `"Current code: <monster>"`
  — CODE-TABLE[CODE-NUMBER] (guild.zil:1034-1046). No separate "Helistar diary";
  Helistar's room just holds the gaspar scroll.
- Infotater (WHEEL, guild.zil:352-377): the in-game object just points you at the
  physical feelie. The actual monster→buttons data is NEXT-CODE-TABLE
  (guild.zil:1054-1070), 1=black 2=gray 3=red 4=purple 5=white:
	bloodworm	white gray black red black
	brogmoid	red purple red black purple
	dorn	gray purple black gray white
	dryad	black gray white red red
	grue	black black red black purple
	hellhound	purple white gray red gray
	kobold	red purple black purple red
	nabiz	purple black black black red
	orc	red gray purple gray red
	rotgrub	gray red gray purple red
	surmin	black black purple red black
	yipple	gray purple white purple black
- Trunk (Cellar, guild.zil:1072-1165): press the five buttons in exactly that order;
  the trunk pops open on the 5th press, **+25**, revealing the moldy aimfiz scroll.
  **One wrong press sets TRUNK-SCREWED permanently** (guild.zil:1137, 1153-1154) —
  the trunk can never open again and the game is lost. CRITICAL.
- Mail: I-MAILMAN fires at turn 25 (queue verbs.zil:2878; guild.zil:674-690). If the
  matchbook (Store Room; its ad explains the trick, guild.zil:966-994) is in the
  brass receptacle at that moment, the ORANGE (vilstu) vial is delivered alongside
  Popular Enchanting; the mailman closes the receptacle. **Matchbook must be in the
  receptacle by end of turn 24** or the vilstu potion never exists and the mine is
  unwinnable. CRITICAL window. Take the vial (+10 on first touch,
  SCORE-OBJECT verbs.zil:2527-2529) after the doorbell.
- Amulet (tiny box in the desk drawer, guild.zil:181-259): a Belboz-proximity meter
  (glows brighter as you近 his region, AMULET-GLOWS guild.zil:235-249). Zero points,
  zero mechanics on the winning path — optional flavor; we skip it.
- Must-do before leaving: frotz me; matchbook → receptacle (≤ turn 24); drink berzio
  (+10); key → open journal → read code; take meef scroll (+10) & gnusto; collect
  orange vial (+10); press buttons (+25); take moldy scroll; AIMFIZ BELBOZ (+20).
  Optional: gnusto gaspar (skipped — no points, only needed for the death-warp
  maze exit).

## 5. Getting out and the overland route

- There is no mail-gnome exit and no walking exit: AIMFIZ BELBOZ is the only way out
  (globals.zil:618-625/881-885). You do NOT need to know where Belboz is — the spell
  works on the name and dumps you in the Twisted Forest ("although Belboz is not in
  sight"), +20, and queues the REAL hellhound (I-HELLHOUND −1).
- Arrival is a CRITICAL 1-command window: the hound warning fires as you land; the
  very next command must be NE (Forest Edge) or you die.
- Mined path north of Forest Edge (belboz.zil:190-211): entering is safe, but every
  exit roll is PROB 50 south / guaranteed death otherwise — a pure red-herring
  deathtrap. Never enter.
- Snake Pit (down the slimy hole): I-SNAKE-PIT fuse = 1+RANDOM 3 queued on entry
  (belboz.zil:241-256) — minimum 2 ticks, so a straight pass-through (enter, leave
  next turn) is always safe. One RANDOM consumed per entry.
- Meadow locusts (I-LOCUSTS belboz.zil:343-366): warning at your 1st and 2nd turn-ends
  in the Meadow, death at the 3rd. Never spend more than 2 turn-ends there.
- River Bank collapse (belboz.zil:379-408): your first 3 turn-ends on the bank are
  free (BANK-COUNTER, never resets); from the 4th on, PROB 75 death unless the river
  is dry or you are flying. Route discipline: visit 1 = arrive + pulver + leave
  (2 ends), visit 2 = arrive + leave (3rd end, free), visit 3+ = flying only.
- PULVER RIVER works only at River Bank (belboz.zil:429-446): I-TRICKLE at +3,
  I-FLOOD at +5 (belboz.zil:459-484) — being in the river bed at the flood is death.
  CRITICAL window: pulver → D → NE (Hidden Cave) uses 2 of the 5 turns. The Hidden
  Cave (+20 on entry, belboz.zil:684-687) exit after the flood is DOWN to Pit of
  Bones; the mouth re-floods.
- Hidden Cave: take soiled scroll + bat guano (guano take reveals/drops the scroll,
  belboz.zil:748-760; take both), gnusto fweep. The amber (blort) vial is optional
  (see-in-dark 24 turns, belboz.zil:762-784) — useless under frotz me.
- Drawbridge (belboz.zil:830-870): the first turn-end on it just sets a flag; EVERY
  later turn-end on foot is PROB 40 collapse → alligator death. Our route crosses it
  exactly once on foot (the free crossing, Ruins-bound) and never returns.
- Stagnant Pool NW = tentacle death (belboz.zil:597-604); Top of Falls jump = death.
  Both off-route.
- IZYUK ME = 3 turns of flight (verbs.zil:2304-2324, I-FLY globals.zil:1008-1023).
  Used: fort return over bank (1 cast), chasm out (1), chasm back (1). While flying
  you cannot re-cast izyuk ("You are already flying").
- Chasm (belboz.zil:1508-1543): jumping is PROB 75 death; flying west/east is free.
  Zorkmid tree room beyond: TAKE COIN, **+15**, tree vanishes (belboz.zil:1596-1615).
- Toll gate (belboz.zil:1119-1315): the fat gnome sleeps. WAKE GNOME → he demands one
  zorkmid; I-GNOME then fires every turn and at PATIENCE 5 he gives up; waking him a
  second time after that = Tholl the Toll Troll death (belboz.zil:1236-1243). Rezrov
  on the gate: first time he slams it (and starts the patience clock); with him awake
  it is death (belboz.zil:1136-1152). GIVE COIN TO GNOME = **+20**, gate opens
  permanently, gnome sleeps. SEARCH GNOME (gate open, once only, not as a bat)
  steals the coin back (belboz.zil:1253-1263) — this is what funds the park gnome.
  A frotzed coin is refused by both gnomes (belboz.zil:1265-1268; park.zil:104-106) —
  never frotz the zorkmid.

## 6. Fort Griffspotter / river region; the amusement park

- Fort (fort.zil): Parade Ground → LOWER FLAG, EXAMINE FLAG → aqua (FOOBLE) vial
  drops (fort.zil:160-168). Fooble = coordination for 17 turns
  (fort.zil:196-221; I-UNFOOBLE 222). Needed only for the arcade throw.
- Cannon (Gun Emplacement, fort.zil:296-345): the "pile of scrolls" is sleeping
  yipples; reaching in = a bite (cosmetic, tracked 20 turns, fort.zil:307-311, 358-361).
  PUT GUANO IN CANNON scatters them leaving the real YONK scroll (+10 on take).
  This is the guano's only use.
- There is no flask, no cannonball, and no balloon in Sorcerer (the balloon is
  Zork II). The "trunk" is the Cellar button-chest (§4), unrelated to pulver.
- Amusement park (park.zil): the entrance gnome materializes when you first try WEST
  (park.zil:55-70), waits 6 turns (I-PARK-GNOME, park.zil:72-78), reappears if you try
  again. GIVE COIN TO GNOME → PARK-FEE-PAID, he vanishes for good (park.zil:90-113).
  Note: sleeping despawns him via WEAR-OFF-SPELLS (globals.zil:1219-1222) but the
  paid flag persists.
- Arcade (park.zil:530-660): TAKE BALL, drink fooble, THROW BALL AT BUNNY. With
  FOOBLED it always hits: **+10**, hawker hands over the glittering malyon scroll
  (park.zil:617-628). Without fooble it always misses (PICK-ONE flavor RNG).
- Casino (park.zil:678-760): the slot machine is 3 independent weighted reels
  (PROB 25/33/50 chains — 3-6 RANDOM draws per pull); triple non-gold pays one
  zorkmid then breaks; triple pot-of-gold is DEATH by coin avalanche. It exists only
  as a fallback if you wasted the zorkmid (per InvisiClues). Off-route — never pull.
- Haunted House / Flume / Roller Coaster: flavor deathtraps and PROB-65 message mills
  (park.zil:161-215, 336-520). Off-route.
- Hall of Carvings dragon (belboz.zil:1656-1712): plain malyon only makes it shiver.
  Sequence: (gnusto malyon earlier), LEARN MALYON, YONK MALYON (consumes the yonk
  scroll, sets MALYON-YONKED), MALYON DRAGON → wall crumbles, southern passage opens
  (DRAGON-MOVED). Casting malyon on the dragon a SECOND time = barbecue death
  (belboz.zil:1687-1691). Sooty Room entry beyond = **+20** (coal.zil:33-35).

## 7. The glass maze

Fully deterministic. 27 cubical rooms (3×3×3), tracked as ROOM-NUMBER with six
exit tables; entry is always room 13 (maze.zil:465). PRE-* tables before the swanzo
scroll is taken (maze.zil:489-523), POST-* after (maze.zil:525-560) — taking the
scroll shuffles the panels (SCROLL-F globals.zil:1052-1066 → REARRANGE-MAZE-TABLE
maze.zil:634-660). Room 30 ≡ the Hollow (east side), room 40 ≡ Outside Glass Arch
(west side). Floorless rooms kill non-flyers (PLUMMET maze.zil:483-487; NO-FLOOR?
maze.zil:188-196); UP/DOWN require flying. As a bat you get a sonar readout of the
solid surfaces (RADAR-VIEW maze.zil:236-330).

- It is NOT crossable blind on foot and item-mapping is unnecessary: FWEEP is the
  intended tool (InvisiClues: "three FWEEPs to make the round trip").
- Inbound (PRE tables, from 13): N E S S W D E E N N U U S E → Hollow
  (13→10→11→14→17→16→7→8→9→6→3→12→21→24→[E=30]). 14 moves — cast FWEEP ME at the
  arch, walk in (E), fly the 14; the spell (15 ticks) expires exactly on arrival.
  First arrival at the Hollow = **+20** (maze.zil:444-446/664).
- Hollow: a giant bird steals the spell book if you carry it here (HOLLOW-F
  maze.zil:685-693) — the auto-drop when fweeping protects you; never bring the book.
  TAKE SCROLL (maze shifts), PUT SCROLL IN HOLE → it lands in the Stone Hut fireplace
  (BRICK-STRUCTURE-F maze.zil:719-737) AND queues I-DORN-BEAST 2.
- Dornbeast (maze.zil:770-846): unavoidable once the scroll is taken (InvisiClues).
  Warning fires first (in the Hollow: next firing there = hypnotic-gaze death).
  In the maze it chases one room behind you, killing you only if your room matches
  its current or previous room (never backtrack). Lure it east into floorless room
  27 while flying: it follows and plummets (SPLATTERED, corpse lands in room 9,
  chase interrupt disabled forever — maze.zil:824-836). No RNG anywhere in the chase.
- Outbound (POST tables, from 24): W S E [dorn splatters] D D W W U U N N D E
  (24→23→26→27→18→9→8→7→16→25→22→19→10→11; 14 moves — 2nd fweep expires at room 11,
  which has a floor), re-FWEEP (cannot be done early: bats can't cast), then
  S E N D W S W U W (11→14→15→12→3→2→5→4→13→[W=40] out; 9 moves), then ~5-6 waits
  until human ("the fweep spell has worn off").
- The gaspar alternative ("quick and dirty", used by step1/sorcerer.txt): gnusto
  gaspar in the guild, GASPAR ME at the arch, and after the chimney drop walk
  W S E on foot — room 27 has no floor, you die, and the guardian angel rebuilds you
  at the arch (RESURRECTION-ROOM; glass-maze resurrections themselves are permadeath,
  verbs.zil:2913-2919, which is why you cast it OUTSIDE). Works on r18, saves ~15
  turns, but costs a death (scroll scatter + FORGET-ALL + WEAR-OFF-SPELLS,
  verbs.zil:2900-2911) — our replayer treats death text as failure, so we use the
  pure 3-fweep route.
- Afterwards: Stone Hut, TAKE PARCHMENT SCROLL from the fireplace = **+25**
  (SCORE-OBJECT verbs.zil:2519-2524), gnusto swanzo.

## 8. The coal mine time loop (golmac)

Setup: only reachable through the dragon passage. Sooty Room (+20) → E: the tunnel
caves in behind you (no return) and COMBO = RANDOM 873 is rolled on first entry to
the Coal Bin Room (coal.zil:70-97). Without vilstu, I-SUFFOCATE kills in 4 turns.
Drinking vilstu inside disables it and queues I-OLDER-SELF 1 (guild.zil:760-764).
You must be holding the spell book when the older self first appears (that moment
records YOUNGER-HAS-SPELL-BOOK, coal.zil:305-315).

The recorder: I-OLDER-SELF firings 2-4 record YOUR command (verb/objects) of that
turn into MOVE-ONE/TWO/THREE tables (DATA-TO-TABLE coal.zil:391-394); firing 2 also
speaks the combination ("The combination is N", OLDER-TELLS-COMBO coal.zil:378-382);
at whichever firing finds him holding the book he dives down the lower chute taking
the vardik scroll out of play (coal.zil:340-356). Later, as the older self, the
younger self REPLAYS those recorded actions one per turn (I-YOUNGER-SELF
coal.zil:486-498, YOUNGER-ACTIONS coal.zil:500-560) — including handing you the book
back at the step where you originally gave it (coal.zil:508-513).

Exact phase A (you = younger; T counts from the vilstu drink):
	T1	drink orange potion	(twin slides out of the chute at end of turn)
	T2	give book to twin	(recorded #1; combo spoken at end of turn — SYNC: capture N)
	T3	drop vial	(recorded #2; twin dives down the lower chute with book+vardik)
	T4	e	(recorded #3; Dial Room)
	T5	turn dial to N	(DIAL-F coal.zil:715-745; sets DIAL-OPEN on match)
	T6	open door	(**+20**, coal.zil:683-697; REZROV on this door = alarm death)
	T7	e → Shaft Bottom;  T8 take rope;  T9 u;  T10 nw;  T11 take beam
	T12	nw;  T13 w → Top of Chute
	T14	tie rope to beam;  T15 put beam across chute;  T16 put rope in chute
	T17	d — climb the rope. HARD GATES (CHUTE-EXIT-F coal.zil:983-1010): must have
		ROPE-PLACED, must be carrying NOTHING (worn items exempt, NOTHING-HELD?
		verbs.zil:3071-3079), and AWAKE ≤ 0 (≤88 turns since last sleep) — any
		failure dumps you into the Coal Bin Room and desyncs the loop.
		Success = Slanted Room, **+20**, vardik spell un-hidden.
	T18	take shimmering scroll
	T19	golmac me — cast from the scroll. GOLMAC ME (globals.zil:394-415): sets
		GOLMACKED (a second golmac ever = POOF, cease to exist), closes the lamp,
		puts the VARDIK scroll in the lamp compartment, restores golmac scroll/rope/
		beam/dial/door to their pre-loop state. You are now the older self.
	T20	open lamp;  T21 take smelly scroll (**+25**)
		(vilstu warning #1 fires ≈ here — "beginning to wear off")
	T22	e — down the chute to the Coal Bin Room (leaving the Slanted Room is POOF
		unless [golmacked & no golmac scroll] or [not golmacked & carrying it] —
		SLANTED-ROOM-EXIT-F coal.zil:1040-1051). Younger self appears holding the book.
	T23	younger self, the combination is N — V-COMBO/YOUNGER-SELF-F
		(coal.zil:437-448; syntax.zil:123-124): sets COMBO-REVEALED only if N matches.
		At end of this turn the younger self hands you the spell book (replay of T2).
	T24	d — dive the lower chute → COVE: **+20**, all loop interrupts disabled
		(COVE-F end.zil:29-60). If GOLMACKED and NOT COMBO-REVEALED → POOF (the
		paradox: you never told yourself the combination). If somehow not golmacked,
		rope/beam/scrolls are confiscated instead.

Ways it can desync (all must be avoided): not holding the book at the twin's arrival
(no handback later — book lost); dropping/throwing the book down the LOWER chute
(soaked + retconned into the lagoon, LOWER-CHUTE-F coal.zil:222-238, COVE-F
end.zil:32-33); descending the rope loaded/tired; entering Shaft Bottom after taking
the vardik scroll (instant suffocation, SHAFT-BOTTOM-F coal.zil:823-827); saying a
wrong number; waiting too long (vilstu death at wear-off stage 3 inside the mine,
≈29 turns after drinking); sleeping anywhere in the mine (death); rezroving the dial
door. Grues are irrelevant here (rooms are ONBIT or you are frotzed); the troglodyte
at Top of Chute (PROB 30/turn-end, coal.zil:937-955) and coal spills in the Bin Room
(PROB 35/turn-end, coal.zil:94-97) are cosmetic RNG consumers only. There is no mine
elevator in this game.

After landing: ~6 waits until vilstu stage 3 ("final effects... vanish") leaves you
exhausted (AWAKE=8), then SLEEP immediately (I-TIRED comes every 8 turns and the
10th-awake collapse is close).

## 9. Endgame at the lagoon and Belboz

- Learn (after the cove sleep): meef ×2, swanzo. Then DROP ALL (book included — the
  Surface of Lagoon soaks every carried scroll and the book, LAGOON-F end.zil:230-244;
  you need empty hands anyway).
- E (Surface of Lagoon) → D (Lagoon Floor; I-DROWN starts) → MEEF WEEDS (crate
  revealed, SPENSEWEEDS-F end.zil:324-333) → TAKE CRATE → W (back to the Cove shore,
  4 underwater turn-ends — inside the 5-turn drowning budget).
- OPEN CRATE **+15** (end.zil:346-351): the GRUE PROTECTION KIT holds the grue suit,
  a brass lantern, and a can of grue repellent. Suit and repellent are equivalent
  passes through the Grue Lair (GRUE-LAIR-F end.zil:528-540 checks SPRAYED? or the
  suit merely carried); the spray lasts only 5 turns (I-SPRAY end.zil:431-444) so
  WEAR SUIT is the robust choice. The mutated grues ignore light entirely — frotz
  does not help here.
- TAKE SMELLY SCROLL (left in the drop pile), NE (Ocean Shore North), N (Mouth of
  River — PROB 15/turn-end cosmetic vine message, end.zil:474-483), MEEF VINES
  (walking into them uncleared = death, VINES-EXIT-F end.zil:508-518), W (Grue Lair),
  W (Mammoth Cavern **+20**, end.zil:604-610).
- Three doors: black → Chamber of Living Death, silver → Hall of Eternal Pain — both
  strip you and end the game in eternal torment (end.zil:719-755). White door only.
- VARDIK ME (cast from the smelly scroll; 12-turn shield) → OPEN WHITE DOOR
  (**+20**, auto-enters the hideout and queues I-BELBOZ-AWAKES 8 — end.zil:762-773).
  From the moment the door opens you have 8 turns before possessed Belboz wakes and
  throws you into the Chamber of Living Death (end.zil:874-885). One command needed:
- SWANZO BELBOZ. Jeearr is expelled, strikes your vardik shield, and dissipates:
  **+25**, score 400, "you have been appointed as the next leader of the Circle of
  Enchanters" (SWANZO-BELBOZ end.zil:803-871). Swanzo without VARDIKED active =
  possession, SCORE −99, game over (end.zil:857-870).
- The "fake-Belboz test" is optional flavor: YOMIN BELBOZ shows the spider-thing
  wrapped around his mind (globals.zil:626-633). The knife on the wall enables the
  tragic alternate ending (kill Belboz, swanzo the corpse — win the fight, lose the
  game; KILL-BELBOZ end.zil:786-801). Neither is on the route.
- Easter egg: if you meefed Belboz's morgia plant back in the guild, the victory text
  ends with "What happened to my morgia plant?" (end.zil:820-823).

## 10. Route-relevant one-shots and hard budgets

- One zorkmid economy: coin → toll gnome → stolen back once → park gnome. The search
  is one-shot (COIN-STOLEN). Casino is the only (suicidal) fallback.
- One-shot scrolls: aimfiz, yonk (un-gnustoable); golmac, vardik (used from scroll);
  malyon (we gnusto it), swanzo/meef/fweep (gnusto'd).
- TRUNK: zero mistakes allowed, ever.
- Mailman: matchbook in receptacle by end of turn 24.
- Mine: whole run ≤88 turns after sleep (AWAKE gate), ≤~29 turns after drinking
  vilstu, empty-handed on the rope.
- Days: no global day limit (unlike Enchanter — no TOD/nightfall clock at all);
  the only day pressure is the per-day awake budget (collapse ≈ turn 152).

## 11. The 400-point breakdown (every SETG SCORE in the source)

	+5	waking from the dream	verbs.zil:2886
	+15	key falls from the wall hanging	guild.zil:396
	+10	drinking the berzio potion	guild.zil:944
	+10	taking the orange (vilstu) vial	verbs.zil:2527-2529
	+10	taking the dusty (meef) scroll	verbs.zil:2530-2532
	+25	opening the trunk (button code)	guild.zil:1159
	+20	aimfiz belboz	globals.zil:623 (dup guard 883)
	+20	first entry, Hidden Cave	belboz.zil:687
	+15	plucking the zorkmid	belboz.zil:1611
	+20	paying the toll gnome	belboz.zil:1273
	+20	reaching the Hollow (maze crossed)	maze.zil:445, 664
	+25	taking the swanzo scroll in the Stone Hut	verbs.zil:2517-2524
	+10	taking the yonk scroll	verbs.zil:2533-2535
	+10	winning the arcade ball game (malyon scroll)	park.zil:622
	+20	first entry, Sooty Room	coal.zil:35
	+20	opening the dial door	coal.zil:683-691
	+20	reaching the Slanted Room by rope	coal.zil:1002
	+25	taking the vardik (smelly) scroll	verbs.zil:2524-2526
	+20	first entry, Lagoon Shore (Cove)	end.zil:35
	+15	opening the crate	end.zil:346-351
	+20	first entry, Mammoth Cavern	end.zil:606, 610
	+20	opening the white door	end.zil:760-768
	+25	vanquishing Jeearr (finale)	end.zil:847
	TOTAL 400. (Losing finale sets SCORE −99, end.zil:871.)

## 12. Randomness inventory, ranked by replay risk

Under a pinned interpreter seed everything is reproducible IF the command stream is
byte-identical, because every RANDOM call then happens at the same point in the
stream. The ranking below is (a) what varies per seed and must be parsed at runtime,
then (b) what merely consumes RNG or threatens death if the route drifts.

1. **Journal code — RANDOM 12 at wake** (verbs.zil:2883). Seed-determined but
   unknown a priori. HANDLING: keep the dream to exactly one command (zero prior
   RNG draws), READ JOURNAL, parse "Current code: <monster>", map through the
   NEXT-CODE-TABLE (§4), emit the five press commands. One wrong press = unwinnable.
2. **Mine combination — RANDOM 873 on first Coal Bin entry** (coal.zil:73).
   HANDLING: parse "The combination is <N>." from the twin, echo N in both
   `turn dial to N` and `younger self, the combination is N`. Wrong/omitted echo =
   locked door / POOF paradox.
3. **Fatal PROBs that must never be rolled** (all avoided structurally by the route):
   river-bank collapse PROB 75 (belboz.zil:401) — never on foot past the 3rd
   turn-end; drawbridge PROB 40 (belboz.zil:841) — cross once only; dark-room grue
   PROB 80 (verbs.zil:2819) — frotz me makes it unreachable; chasm leap PROB 75
   (belboz.zil:1536) — always izyuk; minefield PROB 50 (belboz.zil:202) — never
   enter; casino triple-gold death (park.zil:718-745) — never pull; TWO-POTIONS
   overlap death (globals.zil:1281-1296) — sleep between fooble and vilstu.
4. **Scheduled RNG consumers** (fire at fixed turns given a fixed script — harmless
   but they shift the stream if commands are inserted/removed): I-THIRST re-queue
   RANDOM 100 at turn 18 and I-HUNGER RANDOM 80 at turn 21 (globals.zil:1374, 1387);
   parrot PROB 40 each turn spent in Belboz's Quarters (guild.zil:109); snake-pit
   fuse RANDOM 3 per entry (belboz.zil:244); sleep dream PROB 50 (+PICK-ONE) per
   sleep (verbs.zil:1549-1553); coal-bin spill PROB 35/turn-end (coal.zil:96);
   troglodyte PROB 30/turn-end at Top of Chute (coal.zil:941); vine twitch PROB 15/
   turn-end at Mouth of River (end.zil:476). NOTE: inserting an extra Z anywhere
   shifts all subsequent draws — re-derive the journal code/combo from text, never
   hardcode them.
5. **Refusal-message RNG**: YUKS/HO-HUM/MISSES tables use PICK-ONE (RANDOM) — any
   rejected command consumes a draw. A clean script never triggers them; a replayer
   that retries garbage will diverge (harmlessly, since all remaining hard values
   are parsed from text).
6. **Non-random hazards often mistaken for RNG**: dornbeast chase (fully
   deterministic pursuit), glass maze layout (fixed tables), locusts/hellhound/boa/
   suffocate/drown/Belboz-awakes (fixed counters), gnome patience (fixed 5),
   fweep/izyuk/vardik/fooble/spray durations (fixed 15/3/12/17/5), the mailman
   (fixed turn 25).

## 13. Release-18 notes vs earlier releases

- step1 was written against Revision 13 (851021): it never searches the toll gnome
  and instead wins a second zorkmid at the casino slot machine, and it takes the
  suit from the crate ("get suit"). The r18 ZIL has both SEARCH GNOME
  (belboz.zil:1253-1263) and the full grue kit (suit + lantern + repellent,
  end.zil:370-440) — InvisiClues confirms suit and repellent both work. Our route
  uses search-gnome + suit; no casino.
- sorcerer.txt (Gunness) uses the repellent spray; that also works on r18 but only
  for 5 turns — the suit is strictly safer.
- Known r18 text quirk usable as a sync string: "You here a commotion from the room
  to the west." (sic, coal.zil:319-320).
- The parser supports MANY-object takes ("take vial and matchbook"); WAIT = 3 game
  ticks, cut short by any interrupt output (verbs.zil:1876-1883).
- This source's V3 build has no day/night TOD system (the %ZORK-NUMBER 4 branch in
  LIT? is dead code for Sorcerer).

# ENCHANTER (Infocom, 1983) — Mechanics Notes for Deterministic Replay
Target binary: Release 29 / serial 860820, Z-machine V3.

Sources used:
- ZIL source: github.com/historicalsource/enchanter (authoritative; snapshot is late-development, z4.serial reads "24" — release 24-era code, final r29 is a bugfix respin; all timers/probabilities below cross-check against four independent walkthroughs with no discrepancies found)
- ifarchive.org/if-archive/solutions/infocom/solutions/enchanter.txt (prose solution)
- .../enchanter.step1 (Paul D. Smith step file)
- .../enchanter.step2 (Paul David Doherty step file, written against Release 16)
- .../enchanter.step3 (anonymous step file)
- ifarchive.org/if-archive/solutions/infocom/invisiclues/Enchanter.inv (InvisiClues text conversion)
- walkthroughking.com/text/enchanter.aspx (cross-check only)

All file:line citations below refer to the historicalsource ZIL files.

---

## 1. Spell system

Initial spell book contents (objects with `(IN SPELL-BOOK)`):
- GNUSTO (magic.zil:35-44) — always castable, never consumed ("Always memorized", magic.zil:522-523).
- FROTZ (magic.zil:46-55) — starts with COUNT 1, i.e. already memorized once.
- NITFOL (magic.zil:158-167) — COUNT 0 (in book, not memorized).
- BLORB (magic.zil:231-240) — COUNT 1 (already memorized once). Useless on the winning path; BLORB ME is instant death (globals.zil:143-149).

Memorization model (this is the whole system):
- `SPELL-MAX` = total spells you may hold in your head at once; starts at 4 (magic.zil:661). `SPELL-ROOM` = free slots; starts at 1 (magic.zil:662-663) because frotz+blorb (and conceptually gnusto) are pre-loaded.
- LEARN/MEMORIZE (SPELL-F, magic.zil:573-617): requires the spell inscribed in the book, the book in hand (magic.zil:581-584), and light (magic.zil:588-590). Consumes one slot; you may memorize the same spell multiple times (each cast burns one copy).
- Casting (PRE-QUICK-CAST, magic.zil:478-533): decrements the spell's count and *refunds the slot* (`SPELL-ROOM+1`, magic.zil:529-530). So slots = MAX − (copies currently in head). Yes: spells vanish from memory after one casting.
- Over-memorizing when SPELL-ROOM = 0 forgets a RANDOM other memorized spell (FORGET-SPELL, magic.zil:600, 621-647; RANDOM-ELEMENT at 643). Avoid ever doing this.
- Sleeping wipes ALL memorized spells (FORGET-ALL called at sleep.zil:200) but raises capacity by one: `REAL-SPELL-MAX+1`, `SPELL-MAX` reset (sleep.zil:189-191). Day 1 max 4, after 1st sleep 5, after 2nd sleep 6, etc.
- Staying awake too long shrinks capacity: each I-TIRED firing does `SPELL-MAX−1` (min 1) and, if that leaves zero free slots, randomly forgets a spell (sleep.zil:99-105). Keep head-count low late in a day.

Casting unmemorized: ANY spell can be cast directly from a legible scroll held in inventory; the scroll vanishes on casting (PRE-QUICK-CAST, magic.zil:503-509; the "vanishes" message is suppressed when the target is Krill, magic.zil:506-508). This is how KULCAD, GUNCHO, IZYUK and (optionally) KREBF are used, since:
- GNUSTO cannot copy KULCAD, GUNCHO or FILFRE ("too long, too complicated, too powerful", magic.zil:727-737); attempting gnusto on KULCAD/GUNCHO triggers a Krill mind-probe (see below).

Krill probe budget (not random, but a hard counter): every KULCAD or GUNCHO cast — and every gnusto attempt on those scrolls — increments PROBE via MORE-PROBE (magic.zil:531-532, 735-736, 754-785), EXCEPT when cast in PIT / REAL-STAIR / ENDLESS-STAIR / WARLOCK-TOWER (magic.zil:755-757). PROBE > 3 = instant death (magic.zil:758-764). The optimal route makes zero probes (kulcad at the Winding Stair, guncho in the Tower — both exempt rooms).

Spell effect timers (all via QUEUE, ticks = player turns):
- NITFOL: 20 turns (magic.zil:916). Expiry makes the turtle stop understanding/following (magic.zil:904-911).
- EXEX on self: 45 turns (magic.zil:960); suspends hunger/thirst/tired clocks, and TOD advances only every other turn (main.zil:375-377, magic.zil:933-943). NEVER cast exex on yourself in the Warlock's Tower — frozen solid, death (magic.zil:954-958).
- EXEX on another: 15 turns (magic.zil:964). One EXEX at a time globally (HASTED? single global, magic.zil:946-949).
- OZMOO on self: 8 turns (magic.zil:849).
- IZYUK: 4 turns of flight (magic.zil:1096).
- MELBOR on self: PERMANENT. `PROTECTED-FROM-EVIL` is set (magic.zil:976-984) and never cleared anywhere in the source. One cast protects for the rest of the game (guards, Junction ambush, temple capture, sleep robbery). It does NOT protect in the Warlock's Tower endgame (stair.zil:431-446, 491-501).
- FROTZ: permanent light on target (+20 points first object frotzed, magic.zil:803-820). "FROTZ ME" works (sets ALWAYS-LIT, globals.zil:138-142) but scores nothing.

## 2. Hunger and thirst daemons

- I-THIRST first queued at turn 41; I-HUNGER at turn 67 (main.zil:34-35).
- Each firing prints the next warning and requeues in 10 turns; the 6th consecutive firing (count > 5) is death (I-THIRST sleep.zil:48-57; I-HUNGER sleep.zil:69-78). So with no drink: warnings at 41/51/61/71/81, death at 91. No food: warnings 67/77/87/97/107, death 117.
- DRINK (verbs.zil:981-1010): only allowed when ≤60 turns remain on the thirst clock ("You aren't the least bit thirsty", verbs.zil:993-996 — note at game start the clock is 41, so you may drink immediately). Drinking requeues the daemon at remaining+39 (verbs.zil:997) and zeroes the warning counter — i.e. a drink is a full reset plus ~39-60 turns of headroom, NOT a fixed reset to 41.
- EAT BREAD (outside.zil:276-303): same gate (≤60 remaining, outside.zil:282-285); requeues at remaining+47 (outside.zil:294). First drink +15 (verbs.zil:999-1000), first eat +10 (outside.zil:287-288).
- Supplies: bread SIZE 8 = 8 eats (outside.zil:272, decrement 286); loaf is in the closed shack oven (outside.zil:268-269 — OPEN OVEN first). The jug (shack, outside.zil:309-318) holds water SIZE 4 = 4 drinks per fill (verbs.zil:1005-1009). Refill only at Shady Brook; drinking AT Shady Brook consumes nothing (verbs.zil:1003-1004). Beach/swamp water is fouled (RMUNGBIT, outside.zil:418-423) and undrinkable (verbs.zil:982-989).
- The clocks are turn-based; the +42 MOVES jump at sleep does NOT advance them (sleep only adds to the MOVES counter, sleep.zil:193).
- On (non-ozmoo) death, bread and jug are teleported to EAST-FORK (verbs.zil:421-425).
- Practical cadence: one drink ≈ every 40-55 commands, one eat ≈ every 50-65. Three jug-drinks + one brook-drink + 3 eats cover a ~200-command run.

## 3. Sleep daemon

- Day length: MOVES-PER-DAY 86; sleep advances the MOVES counter by MOVES-PER-SLEEP 42 (sleep.zil:10-11).
- I-TIRED first fires at turn 86 of each day (queued main.zil:33, requeued at day length after each sleep, sleep.zil:198), then every 10 turns (sleep.zil:106). Each firing: carrying capacity −10 (sleep.zil:94-95), fumble threshold −1 and fumble probability +1 (sleep.zil:96-98), SPELL-MAX −1 with possible random spell forget (sleep.zil:99-105). After the 11th firing (AWAKE > 10, i.e. ~186 turns awake) you collapse into forced sleep (sleep.zil:108-113).
- SLEEP is refused unless ≤10 turns remain to day end, i.e. ≥76 turns since last sleep (TILL-TIRED test, sleep.zil:167-173). Refused outright at REAL-STAIR/PIT (fatal warning, sleep.zil:168-169) and in noisy rooms ENGINE-ROOM/CLOSET/SE-TOWER (sleep.zil:174-175). Lying on the bed when a full 86-turn day has elapsed auto-sleeps (BED-F, castle.zil:176-183); I-TIRED firing while in bed also auto-sleeps (sleep.zil:89-93).
- Sleep effects: capacity +1 and full slot refill, ALL memorized spells wiped, fumble stats reset, MOVES += 42, TOD += 42, and THREE additional rooms get blighted/munged (sleep.zil:189-204).
- Theft while asleep — branch order in V-SLEEP matters (sleep.zil:236-298):
  1. Outdoors, unprotected: PROB 20 (MOLESTED, +5 per day, main.zil:383) something comes; then PROB 45 (MUNCHED, +5/day) you are eaten (death), else you are ROBbed — outdoors the loot is REMOVEd (destroyed) (sleep.zil:236-250).
  2. First sleep while the gallery portrait is untaken: gallery hint dream, NO robbery (sleep.zil:251-260); repeats PROB 70 on later sleeps (261-267).
  3. First sleep after the door illusion exists un-dispelled: door hint dream, NO robbery (268-275). (A second dream fires once after you kulcad the door, 276-283 — you never see it on the good route.)
  4. Otherwise, unprotected indoors: PROB 50 the room's loot, then PROB 50 your inventory, is moved to WARLOCK-TOWER (sleep.zil:284-292) — the SPELL BOOK is stealable (RIPOFF exempts only scrolls, bread, jug, invisibles: verbs.zil:1701-1712).
  5. MELBOR (PROTECTED-FROM-EVIL) suppresses all robbery branches.
- The bed dream is REQUIRED-ish: sleeping IN the bed the first time (while the vaxum scroll is unfound) moves the hidden BEDPOST-BUTTON into scope — the damsel dream (sleep.zil:213-224). Without it "PRESS BUTTON" has no referent. HOWEVER, `REZROV BEDPOST` opens the compartment without the dream (castle.zil:229-237), so the dream is technically optional; PUSH BUTTON and REZROV BEDPOST both award the +20 (castle.zil:271-279, 229-237). Route uses the bed sleep anyway (it is the safe day-1 sleep spot).
- No other dream is mechanically required; gallery/door dreams are hints only.

## 4. Day/night cycle

- TOD runs 0-127, +1 per turn (I-TIME, main.zil:374-392); table of times sleep.zil:17-30 (~1 TOD unit ≈ 11 min). SUNRISE 10, DUSK 81, NIGHTFALL 97 initially (main.zil:369-372).
- Each TOD wraparound (new day): NIGHTFALL −20, DUSK −20, MOLESTED +5, MUNCHED +5, LOSSAGE +1 (main.zil:378-384). When NIGHTFALL < 0 — i.e. at the start of the 6th day of game time — Belboz announces universal night and the game is lost (main.zil:385-392). Hard global limit ≈ 5×128 ≈ 640 turns; a good route uses 3 days.
- Darkness outdoors at night is COSMETIC ONLY: all outdoor rooms carry both ONBIT and LIGHTBIT, and LIT? accepts ONBIT unconditionally (gparser.zil:1389-1417; room flags e.g. outside.zil:16, 44). Night only changes descriptions/window views. Nothing on the route is gated on time of day.

## 5. Complete route (see enchanter_route.txt for the exact command list)

Geography anchors: start at Fork (WEST-FORK). Shack NE (bread in oven, jug; lantern is a red herring — broken, outside.zil:234-245). Shady Brook via Trail Head NE (water). Crone's hovel: Village, S — first entry she GIVES you the rezrov scroll and expels you (HOVEL-KLUDGE, outside.zil:471-502; deterministic, one turn). Castle west gate: East Fork, E, E; `REZROV GATE` +20 (castle.zil:54-65).

Scroll inventory (name / spell / where / how):
- scribbled / REZROV (open) — crone, free (outside.zil:486).
- shredded→faded / ZIFMIA (summon) — inside the egg, Jewel Room atop NW tower. `REZROV EGG` +5 opens it (egg.zil:130-143); manual opening (turn handle, press knob, pull slide, move crank, push button) also works but the scroll is shredded EITHER way (egg.zil:192-214). Repair with KREBF (+10, egg.zil:262-271); krebf can be cast straight from the crumpled scroll, no gnusto needed.
- crumpled / KREBF (repair) — on the ground in FOREST-1, north of the rezrov-able North Gate (magic.zil:263-272, castle.zil:1078-1086).
- damp / CLEESH (newt) — under the lily pad in the Swamp (FOREST-2). `LOOK UNDER LILY PAD` works with no precondition (castle.zil:1206-1220); nitfol-ing the frogs is pure flavor.
- frayed / GONDAR (quench) — Library: `EXAMINE TRACKS` places the rat hole (castle.zil:1003-1009), `REACH IN HOLE` +25 (castle.zil:1021-1037).
- black / OZMOO (cheat death) — Gallery niche. You MUST enter the gallery WITHOUT a light source to see the lighted portrait (GALLERY-F/DESCRIBE-PORTRAIT-GALLERY, gallery.zil:29-70 — carrying light removes the portrait from scope). `MOVE LIGHTED PORTRAIT` +25 reveals the niche with the black scroll and the black candle (eternal flame, a permanent light, gallery.zil:145-211). The candle left in the niche keeps the gallery lit thereafter.
- gold leaf / VAXUM (charm) — bedpost compartment, Bedroom above SW tower (magic.zil:98-106; castle.zil:203-279). Sleep in bed → dream → `PRESS BUTTON` +20.
- stained / EXEX (haste) — Secret Passage east of the dungeon cell: `OPEN DOOR`, N, `MOVE BLOCK`, E (castle.zil:298-434). The silver spoon there is a decoy treasure.
- vellum / MELBOR (protection) — inside the jewelled box (Closet/KNOT-ROOM south of Courtyard-1). The rope defeats rezrov and untying; `CUT ROPE WITH DAGGER` +25 (knot.zil:54-170) using the sacrificial dagger from the ozmoo sequence. (Kulcad also de-magics the rope — a trap; never spend kulcad here.)
- brittle / KULCAD (dispel) — Control Room (CLOSET) beyond the Engine Room; only the exex-hasted turtle can fetch it (+25). Cannot be gnusto'd.
- powerful / GUNCHO (banish) — Translucent Room "P" (T-I), guarded by the Unseen Terror. +50 for stealing it with the Terror re-trapped. Cannot be gnusto'd.
- ornate / IZYUK (fly) — materializes from the bannister when you kulcad the Winding Stair (stair.zil:76-88).
- purple / FILFRE — Map Room, pure gag (fireworks + credits).

Order used (3 game days): Day 1 — crone, shack, brook (drink +15, frotz book +20, learn rezrov x2), gate +20, Jewel Room (rezrov egg +5, take egg), gallery dark-entry (+25, take black scroll), gnusto+learn ozmoo, take box, walk into Temple → captured, ozmoo+sacrifice +35, recover gear in south cell, cut rope +25, gnusto+learn+cast MELBOR (permanent), exex scroll from secret passage, eat +10, Library (+25 gondar), bed +sleep (dream). Day 2 — press button +20, gnusto vaxum, rezrov North Gate, krebf scroll +10, gnusto zifmia/cleesh, swamp scroll, Mirror Hall 4 wait-loop, zifmia +10, vaxum, escort (carry egg), point at door +35, map+pencil, Translucent maze +50 guncho, sleep in South Hall. Day 3 — learn gondar/cleesh/nitfol/exex, turtle errand +25, Landing, kulcad stairs +10, izyuk, fly east +10, gondar/cleesh/guncho +50. Total 400.

## 6. Translucent Rooms / map-and-pencil

Map letters ↔ rooms (terror.zil:101-171 POINT props; TMAZE-ROOMS terror.zil:728): B=T-A (entry, below the Dungeon), R=T-B, K=T-C, H=T-D, J=T-E, M=T-F, V=T-G, F=T-H, P=T-I (isolated; Terror + guncho scroll live there, terror.zil:8-15, magic.zil:242-243).

Initial passages (TMAZE tables, terror.zil:184-281): B-R, R-H, R-M, K-J, H-M, J-V, M-V, V-F. Drawing a line opens the physical passage, erasing closes it (CONNECT/DISCONNECT, terror.zil:539-593). Budget: pencil 2 draws, eraser 2 erases (terror.zil:76-77) — exactly enough. KULCAD on map or pencil = instant game loss (END-OF-WORLD, terror.zil:54-60, 85-91). WRITE ON any spell scroll with the pencil defaces it permanently (verbs.zil:1780-1798).

The Terror: the moment a path exists from its room to T-A, I-TERROR runs every turn and it advances one room per turn along the escape path (terror.zil:646-713; pathfinder TWALK/PATH-OUT? 734-797 — fully DETERMINISTIC, no RANDOM). If it reaches T-A the world ends (terror.zil:680-681). While it is in YOUR room you cannot walk (terror.zil:352-358). Re-trapping it (path search fails → TERROR-TRAPPED, terror.zil:730-732) and then standing in T-A with the powerful scroll scores +50 (terror.zil:300-308).

Verified deterministic sequence (Paul D. Smith variant — no walking while the Terror is co-located; from T-A after entering via Dungeon DOWN):
- S (→R), E (→M). You are at point M (T-F).
- DRAW LINE FROM P TO F   (pencil 2→1; Terror leaves P: P→F this turn — not your room)
- ERASE LINE FROM P TO F  (eraser 2→1; Terror F→V via V-F)
- ERASE LINE FROM M TO V  (eraser 1→0; Terror's path search now fails — trapped at V, sealed in the {V,J,K,F} pocket)
- DRAW LINE FROM M TO P   (pencil 1→0; opens a private SE corridor from M)
- SE (→P), TAKE POWERFUL SCROLL, NW (→M), W (→R), N (→B/T-A) → scream + 50 points.
("LINE" is a parser buzzword, syntax.zil:11, so "draw line from p to f" = MAKE FROM OBJECT TO OBJECT, syntax.zil:646-669; "connect p to f" / "erase from m to v" are equivalent.)
The classic alternative (draw F-P; SW blocked once by the Terror; SW; erase V-M; erase B-R; draw J-B; walk P-F-V-J, W to B) is also deterministic but spends one wasted blocked turn and routes you through the Terror's pocket. What it unlocks: the GUNCHO scroll only. KULCAD is NOT needed here.

## 7. The turtle

Rainbow turtle on the Beach (gears.zil:287-300). Sequence (all windows in turns):
- NITFOL TURTLE (starts the 20-turn understanding window, magic.zil:913-916).
- TURTLE, FOLLOW ME (gears.zil:388-400). It follows you room-to-room (I-TURTLE, gears.zil:576-629); it refuses to lead down stairs, gets tired after following >20 rooms (gears.zil:633-650), and won't enter West Castle/Dungeon (580-583).
- Walk Beach→Meadow→South Gate→SE Tower→UP to Engine Room (4 moves; it follows up the stairs, gears.zil:602-604).
- EXEX TURTLE (15-turn haste window, magic.zil:963-964).
- Single input line: `TURTLE, SE. TAKE SCROLL. NW` — chained orders must be ON ONE LINE because a remote turtle cannot hear a new TELL across the machinery (gears.zil:444-460), but once WINNER=turtle, subsequent sentences on the same line stay addressed to it. Hasted crossing SE survives (CROSS-ENGINE-ROOM, gears.zil:127-140); remote TAKE works (gears.zil:401-420); hasted return NW survives the spear trap on its shell (RECROSS-ENGINE-ROOM, gears.zil:177-190).
- On arriving in your room with the scroll it drops it: +25 (I-TURTLE, gears.zil:621-629). TAKE BRITTLE SCROLL.
Failure modes: un-hasted crossing = squashed turtle, counts as YOUR death (gears.zil:141-156, ozmoo can't save it, 147-152); nitfol expiry mid-errand = it stops obeying; if YOU try to cross, hasted or not, the spear trap kills you (gears.zil:205-229). Optional: `THANK TURTLE` sends it home (gears.zil:540-549).

## 8. The bedraggled adventurer

- Appearance: while you stand in ANY Hall of Mirrors room (1-4), each turn end has PROB 15 that he appears behind the glass (MIRROR-HALL-F M-END, purloined.zil:381-393). Once visible, each subsequent turn he leaves with PROB 25, and he vanishes instantly if you leave the room (I-LG-ADVENTURER, purloined.zil:417-426). ⇒ wait-loop in Mirror Hall 4; the turn after the appearance message, cast ZIFMIA.
- ZIFMIA ADVENTURER: +10, he materializes with lantern and sword (purloined.zil:470-482). Works only on the behind-glass apparition (the "great magic of his own" exception, magic.zil:868-882).
- VAXUM ADVENTURER: charms him for exactly 20 turns (purloined.zil:654-659; I-ADVENTURER-UNCHARM 713-718). EVERYTHING you need from him must finish inside this window. He can be re-vaxumed if you still have copies.
- Following: he follows you room-to-room only while charmed AND you are carrying a treasure — EGG, MAGIC-KNIFE (dagger), JEWELLED-BOX or SILVER-SPOON (GOTO hook verbs.zil:927-938; WINNER-HAS-TREASURE? verbs.zil:952-957). Carry the egg for the 2-room escort Mirror Hall 4 → North Gate → Guarded Door.
- The Guarded Door (PURLOINED-ROOM): monstrously trapped illusion; touching/attacking it 5 times = death (purloined.zil:197-203); rezrov mocked (209-214). While he is present and charmed: `POINT AT DOOR` (or ADVENTURER, OPEN DOOR) → NO-ILLUSIONS: +35, the illusion collapses, the real door opens, he walks up into the Map Room (purloined.zil:185-193, 1037-1062). Drop the egg first — he pockets it and stays put (PURLOINED-ROOM-A, purloined.zil:1010-1032).
- KULCAD also dispels the door (purloined.zil:163-180) — a trap; you'd never reach Krill.
- Theft: any turn he is in a room he takes every treasure and each other takeable item with PROB 25 (ADVENTURER-TAKE, purloined.zil:887-915) — in the Map Room that means the map, the pencil and the purple scroll are each at risk per turn. While charmed, `ASK ADVENTURER FOR MAP` / `... FOR PENCIL` recovers non-treasures (V-ASK-FOR, verbs.zil:1727-1746; he refuses treasures and his lantern/sword).
- Losing him: attacking him = your death (purloined.zil:633-638); cleesh/guncho/frotz drive him off (with anything he carries — cleesh REMOVEs him and his inventory, magic.zil:1077-1083); the gang can kill him (PROB 70 survival, castle.zil:877-906); he "Restore...."s out of existence on the Winding Stair (stair.zil:40-47). After the door, he is expendable — just recover map/pencil first.
- He is needed ONLY for the door (endgame requires no adventurer).

## 9. The ozmoo / sacrifice sequence (required for r29's 400)

Required: it is the only source of the dagger (cuts the box rope → melbor) and of +35 TEMPLE-POINT.
- Trigger: end any turn standing in TEMPLE without PROTECTED-FROM-EVIL and without LETTER-OF-TRANSIT (TEMPLE-F, temple.zil:269-275) → TAKE-TO-TOWER (279-307): all possessions confiscated to the south cell TOWER-S; if a kulcad/guncho scroll is among them it is DESTROYED (temple.zil:300-305) — never be captured holding those. You are locked in the north cell; I-TAKE-TO-ALTAR queued in 4 turns (temple.zil:306).
- In the cell: OZMOO ME (must be memorized — no book needed to cast; 8-turn effect covers the 4-turn wait), then WAIT. The sacrifice fires: with DEATH-CHEATED set you revive on the Altar, +35, the glowing dagger is put in your hands (temple.zil:315-358). Without ozmoo it is a normal death (JIGS-UP).
- LETTER-OF-TRANSIT: set on revival, lasts 10 turns, re-armed 3 turns at a time while you stay inside the Temple (I-LETTER-OF-TRANSIT, temple.zil:356-368). Window plan: D to Temple, OPEN SOUTH CELL DOOR, S into TOWER-S, TAKE ALL, CUT ROPE WITH DAGGER (+25), OPEN BOX, TAKE VELLUM SCROLL, GNUSTO MELBOR, LEARN MELBOR, MELBOR ME — all ~11 turns, and melbor makes the letter irrelevant before you re-cross the Temple. (Alternative: drop everything outside before capture; costs ~4 extra commands.)
- Rezroving the cell door instead summons the guards for an immediate altar trip (temple.zil:199-218) — same result if ozmoo is up, but the take-all-in variant is cleaner.
- Death bookkeeping: an ozmoo'd sacrifice does NOT count as a death. Real deaths: 3 are survivable (Belboz revival, scrolls of power confiscated!, bread/jug dumped at East Fork, scroll-type items dropped in the death room); the 4th is game over (JIGS-UP, verbs.zil:339-438).

## 10. KULCAD target choice and the endgame

Kulcad works on: banquet illusion (castle.zil:576-581), box rope (knot.zil:151-156), guarded door (purloined.zil:163-180), strong box, eternal flame, map/pencil (= instant loss), and the Winding Stair. Exactly one cast exists. The ONLY target with no alternative solution is the WINDING STAIR — the stair illusion (Junction → E to Landing → E) loops forever otherwise. Rope→dagger, door→adventurer, everything else→don't. InvisiClues confirms ("you then lose the ability to use KULCAD elsewhere").

Endgame, exact turn-critical sequence (memorize GONDAR and CLEESH beforehand; hold the brittle + powerful scrolls; carry a light — the frotzed book (SIZE 0) survives what follows; ENDLESS-STAIR and REAL-STAIR are dark rooms and dark-room movement is 85-90% fatal, verbs.zil:562-567/919-925):
1. At ENDLESS-STAIR: `KULCAD STAIRS` (+10, STAIR-DISPEL stair.zil:57-93). Hunger/thirst/tired daemons are killed (67-71); every carried item of SIZE>4 is destroyed (bread, dagger, egg, box, portrait...) (DESTROY-ALL 292-304); the bannister becomes the ornate IZYUK scroll in your hands; you hang over the Bottomless Pit; I-FALL-FOREVER fires in 5 turns = death (stair.zil:89).
2. Next turn: `IZYUK ME` (cast from scroll; 4-turn flight, magic.zil:1093-1101).
3. Next turn: `E` — fly east, +10, Warlock's Tower (stair.zil:199-217). (Down explores the pit = optional death.)
4. Entering, Krill summons the dragon; I-DRAGON fires in 2 ticks — you get exactly ONE command: `GONDAR DRAGON` (stair.zil:327-348, 394-399, 436-446).
5. The shadowy being appears; I-SHAPE in 2 ticks — ONE command: `CLEESH MONSTER` (or VAXUM MONSTER — both work, stair.zil:453-462).
6. Krill chants; I-BYE in 2 ticks — ONE command: `GUNCHO KRILL` cast from the powerful scroll (+50, KRILL-F stair.zil:512-541).
Winning text: "Krill recoils as he hears the first words of the guncho spell. ... a spell of power, and is gone! ... 'The evil of Krill is ended this day. From beyond hope, you have proved yourself great and worthy.' ... Here ends the first chapter of the Enchanter saga, in which, by virtue of your skills, you have joined the Circle of Enchanters."
Guncho'ing dragon/shape, nitfol/vaxum on the dragon, or hesitating = death. Melbor/ozmoo do not protect here (stair.zil:431-434). Score 400/400 = "Member of the Circle of Enchanters" (verbs.zil:241-250).

## 11. The 400-point breakdown (globals magic.zil:824-843; SCORE-MAX 400 at magic.zil:843)

	Points	Event	Award site
	20	rezrov the iron gate (ENTRY-POINT)	castle.zil:58-60
	20	first frotz of an object (LIGHT-POINT)	magic.zil:814-815
	15	first drink (DRINK-POINT)	verbs.zil:999-1000
	10	first eat (EAT-POINT)	outside.zil:287-288
	5	opening the egg (EGG-POINT)	egg.zil:132-133 (or 205-207 by hand)
	10	krebf the shredded scroll (REPAIR-POINT)	egg.zil:267-268
	25	moving the lighted portrait (GALLERY-POINT)	gallery.zil:155-156 / 181-183
	35	surviving the sacrifice (TEMPLE-POINT)	temple.zil:351-352
	25	cutting the box rope (BOX-POINT)	knot.zil:163-164 (via ROPE-DISSOLVES)
	20	opening the bedpost (CHARM-POINT)	castle.zil:232-233 / 274-275
	25	gondar scroll from the rat hole (QUENCH-POINT)	castle.zil:1034-1035
	10	zifmia the adventurer (SUMMON-POINT)	purloined.zil:475-476
	35	guarded door opened (DOOR-POINT)	purloined.zil:1059-1060
	50	guncho scroll taken w/ Terror trapped (TERROR-POINT)	terror.zil:307-308
	25	turtle delivers kulcad scroll (TURTLE-POINT)	gears.zil:626-627
	10	kulcad the stairs (STAIR-POINT)	stair.zil:74-75
	10	fly east over the pit (FLY-POINT)	stair.zil:209-210
	50	guncho Krill (WARLOCK-POINT)	stair.zil:539

Note: the InvisiClues sheet lists egg=10/repair=5; the ZIL says EGG-POINT 5 / REPAIR-POINT 10 (magic.zil:827-828). Trust the ZIL.

## 12. Randomness inventory, ranked by replay risk

All probabilities are `PROB n` = `n > RANDOM(100)` (macros.zil:122-124). LUCKY/ZPROB is compiled out — flat percentages.

1. **Adventurer appearance / departure** — PROB 15 per turn spent in a mirror hall to appear (purloined.zil:381-393); once visible, PROB 25 per turn to leave (417-426). THE dominant variance (geometric, median ~4-5 turns, p95 ~18). Handling: wait-loop in Mirror Hall 4 ("wait" = 1 appearance check, do NOT leave the room), fire `ZIFMIA ADVENTURER` on the very next input after the appearance text (interrupts run after your action, so he cannot leave first). All subsequent day-2 timing must be milestone-synced, not turn-synced.
2. **Adventurer pilfering in the Map Room** — each turn he's there and doesn't quip (PROB 25 quip gate when co-located, purloined.zil:747), each takeable item is grabbed with PROB 25 (887-915). Handling: enter the Map Room the turn after the door opens; `TAKE MAP AND PENCIL` immediately; on failure branch to `ASK ADVENTURER FOR MAP` / `ASK ADVENTURER FOR PENCIL` (guaranteed while charmed, verbs.zil:1738-1742). Must complete inside the 20-turn vaxum window. A replayer needs this one conditional branch.
3. **Random spell forgetting** — FORGET-SPELL picks a RANDOM memorized spell (magic.zil:641-647) whenever (a) you memorize with zero free slots, or (b) I-TIRED fires with zero free slots (sleep.zil:99-105). Handling: never over-memorize; keep at least one free slot after turn ~80 of any day; day-1 trick: cast the pre-memorized frotz BEFORE learning rezrov twice (cast refunds a slot, making both learns deterministic).
4. **Sleep robbery** — indoors unprotected: PROB 50 room loot, PROB 50 inventory (incl. spell book) to Warlock Tower (sleep.zil:284-292); outdoors: PROB 20 then PROB 45 DEATH (236-250). Handling: sleep #1 in the bed (damsel-dream branch preempts robbery, 213-224); melbor before every later sleep (permanent after one cast). Never sleep outdoors.
5. **Fumbling** — carrying more than FUMBLE-NUMBER (7) items makes each TAKE fail with PROB count×FUMBLE-PROB (8, worsens when tired) (verbs.zil:622-648). A failed take still burns a turn. Handling: cap inventory at 7 (route max is 7, transiently, in Tower-S).
6. **Guards in Library/Banquet Hall** — PROB 30 per turn-end there spawns the approach warning, guards arrive 2 turns later, then a deterministic pursuit→temple-capture chain (castle.zil:599-711). Handling: route visits the Library only after MELBOR (guards then ignore you, castle.zil:663-674); likewise the Junction insta-capture (867-875).
7. **Movement in darkness** — PROB 90 death on a failed walk in the dark (verbs.zil:562-567); PROB 85 death entering a dark room from a dark room (GOTO, verbs.zil:919-925). Handling: never be lightless; frotz the book turn ~20 and keep it (drop it only for the one dark gallery entry, in the adjacent lit-by-nothing-needed South Hall).
8. **Adventurer vs gang skirmish** — PROB 70 he survives (castle.zil:892). Never co-occurs on this route (melbor).
9. **State-neutral RNG consumers** (matter only for RNG-stream alignment under a pinned seed): I-SCURRY flavor noises, requeued every 15+RANDOM(20) turns with PROB 25/50 message rolls (outside.zil:725-751); PICK-ONE message-table shuffles (macros.zil:134-146) in yuks/hellos/dreams/quips; dream selection PROB 50 (sleep.zil:293-298); adventurer quip/`Hello, Sailor` rolls (purloined.zil:747-758). Because the adventurer wait-loop already varies the draw count, a deterministic replayer must sync on TEXT MILESTONES (appearance line, "drops a brittle scroll", the Terror scream), not on absolute turn numbers or RNG-call counts.
10. **Parser ambiguity resolution** picks RANDOMLY among equally-matching objects (parser.zil:889 / gparser.zil:1113). Handling: always use disambiguated nouns — "scribbled scroll", "black scroll", "gold leaf scroll", "stained scroll", "crumpled scroll", "faded scroll", "brittle scroll", "powerful scroll", "vellum scroll", "south cell door".

Non-random hard budgets a replayer must respect: Krill probes ≤3 (route uses 0); deaths ≤3 (route uses 0 — the sacrifice doesn't count); pencil 2 / eraser 2 (route uses 2/2); world ends at the 6th dawn (route: 3 days); collapse after ~186 turns awake per day.

Release-29 notes: the historicalsource snapshot self-identifies as release 24; r29 (860820) is the final V3 release. The Doherty step file was written against r16 and every command in it (including "draw line from X to Y", "reach in(to) hole", multi-sentence turtle orders) matches this source's syntax tables (syntax.zil:379-685), so no release-specific command differences are expected; the only caution is cosmetic text drift, so replay verification should key on point awards (SCORE deltas) rather than exact prose where possible.

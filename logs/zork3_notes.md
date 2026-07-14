# Zork III (Release 25 / serial 860811) — walkthrough synthesis and timing notes

Sources used (fetched 2026-07-13):

- **[A]** Jacob Gunness step-file, IF Archive: https://ifarchive.org/if-archive/solutions/infocom/solutions/zorkIII.step (pure command list, complete game; mirrored at abandonwaredos.com)
- **[B]** eristic.net walkthrough: http://www.eristic.net/games/infocom/zork3.html (prose + exact commands, complete; includes points list and timing notes)
- **[C]** IF Archive prose solution zorkIII.txt: https://ifarchive.org/if-archive/solutions/infocom/solutions/zorkIII.txt (identical text also at https://the-spoiler.com/ADVENTURE/Infocom/zork.3.2.html)
- **[D]** The Walkthrough King: https://www.walkthroughking.com/text/zork3.aspx (complete; Royal Puzzle sequence identical to [B])
- **[E]** Infocom InvisiClues (text conversion): https://zedlopez.github.io/invisiclue/zorkiii.html (mechanics, limits, official puzzle solution, points list)
- **[SRC]** Original Infocom ZIL source: https://github.com/historicalsource/zork3 (authoritative for probabilities/timers; file:line cites below). The historicalsource tree matches the late-release game; nothing any source flagged as r25-specific, and no source mentioned behavior differences between releases.

Where sources disagree, both variants are recorded. Timings marked [SRC] are read directly from the ZIL and trump walkthrough folklore.

---

## 1. Opening (Endless Stair, lamp, sword vision)

You start at the bottom of the Endless Stair; intro prints the dream-vision (tumbling down the staircase / the hooded figure). The brass lantern is in the room; the sword is embedded in a rock at the Junction (1 S) and CANNOT be taken there ("you can't take it just now" [B]; it teleports to you later, see section 2).

- [A]: `GET LAMP / S / LIGHT LAMP` then detours west for bread + old man first (see section 10 note).
- [B]/[C]/[D]: `GET LAMP / TURN ON LAMP / S / S / S / S` (4 south = Lake Shore), `TURN OFF LAMP / DROP LAMP` at Lake Shore (light sources die permanently if they get wet — InvisiClues [E]: "The light sources cannot be relit once they've gotten wet"; lamp is expendable after the torch is secured).
- Lamp battery is generous (warnings at 300/100/50 ticks remaining, actions.zil:36) but the standard plan abandons the lamp at Lake Shore and uses the torch for the whole rest of the game.

## 2. Land of Shadow — hooded figure, mercy mechanic

All from [SRC] shadow.zil:

- Appearance: each end-of-turn in a lit Shadow room (while figure strength > 3): 30% chance the figure appears blocking a RANDOM exit of the current room (shadow.zil:1727-1741 SHADOW-ROOMS); separately 30% chance of the "You can hear quiet footsteps nearby" flavor. WAITing in place works as well as wandering.
- On arrival the sword teleports into your hand ("From nowhere, the sword from the junction appears in your hand, wildly glowing!") and you score 1 point (encounter).
- Fight: `ATTACK FIGURE` [B] / `KILL FIGURE WITH SWORD` [A] (first attack = 1 more point). Both sides start at strength 5. Your hit chance = (your_strength*10+10)%; on a hit, 85% deal 1 damage / 15% deal 2 (a 2-damage blow can NOT reduce it below 1 — it's clamped, shadow.zil:300-302). Only a 1-damage hit can kill it (strength 0).
- KILLING IT IS A LOCKOUT: SHADOW-DIES removes the SHADOW object with the hood and cloak still inside it (shadow.zil:373-380) — game unwinnable. Stop attacking at strength 1: diagnostic line "The figure appears to be badly hurt and defenseless."
- Mercy: `TAKE HOOD` (or `REMOVE HOOD`, [A]) works only at strength exactly 1 (strength 2 → "strong enough to force you back"; 3+ → "cannot get close enough"). Success: you get the hood, figure vanishes, CLOAK IS DROPPED ON THE GROUND → then `TAKE CLOAK`.
- Its counterattack: chance (its_strength*10+10)%; 90% of hits deal 1 (cannot kill you — at 1 strength you get the sword-handed-back mercy message), 10% deal 2 which CAN kill you outright. So the fight is survivable-but-random; save before entering Shadow Land ([B],[C] both advise it).
- Healing: every 10 turns both your strength and its strength regain 1 (I-CURE, shadow.zil:277-283). Don't dawdle mid-fight or it re-arms; conversely you can retreat and heal.
- The figure blocks one random direction; you can't exit that way while it stands there.
- [A] does `DROP SWORD` after taking the hood (not required; [C] keeps the sword and later uses it to block the beam).
- Exits: going east ends up at Creepy Crawl or Foggy Room [C]; from either, N reaches the Junction.

## 3. Scenic Vista — flashing table

All deterministic [SRC] shadow.zil:1458-1505 and dungeon.zil:931:

- Indicator cycles I → II → III → IV → I ... changing every 4 turns, timer queued at game start (`QUEUE I-VIEW-CHANGE 4`). So the indicator is a pure function of the global move counter: it changes on moves 4, 8, 12, ... (starts at "I").
- Destinations (VIEW-ROOMS): I = Timber Room (Zork I), II = Room 8 (Zork II, has the grue repellent can), III = Damp Passage (Zork III), IV = "Zork IV" Sacrificial Altar = INSTANT DEATH on entry (shadow.zil ZORK-IV-F). Never touch at IV.
- `TOUCH TABLE` (parses as rub/touch) teleports you to the room matching the current indicator and awards the point (first time). You are snapped back after 3 turns (`QUEUE I-VIEW-SNAP 3` — "You are limited to three moves" [E]); plan on 2 useful actions plus the snap-back turn ("GET CAN, then WAIT" is the canonical use).
- Standard sequence ([A],[B],[C],[D]): `GET TORCH`, wait for II, `TOUCH TABLE`, `GET CAN`, `WAIT` (snap back), wait for III, `TOUCH TABLE`, `DROP TORCH`, `WAIT` (snap back). This pre-positions the torch at Damp Passage — the ONLY way to have light on the far side of the lake ([E]: no working light source can cross the lake).
- The torch at the Vista: it's the light source for the Vista trip itself; you drop it in Damp Passage BEFORE swimming back so it never gets wet.

## 4. Lake Frigid

[SRC] shadow.zil:1290-1440:

- Enter with `ENTER LAKE` / `JUMP LAKE` (or JUMP from shore). Entering the surface (On the Lake) scores the "jump in the lake" point.
- Carrying: you can't carry more than weight 25 underwater; anything you're carrying beyond the amulet is at risk — taking non-amulet items underwater has a 30% failure/drop chance per try. Entering the water makes you drop items (the can, torch if carried — hence drop lamp/torch on shore first). [B]: "you just dropped the can of repellent" on second entry; retrieve it from the lake bottom.
- `DIVE` / `D` to the bottom (In the Lake). Air: after 3 turns underwater you auto-surface ("You run out of air", I-IN-LAKE queued 3).
- Hypothermia: a per-entry counter ticks every turn in the water (surface or bottom): warning at 4 ("icy waters are taking their toll"), "You are becoming very weak..." at 6, DEATH at turn 8. Counter resets each fresh entry. So ~7 turns max per dip; [B]'s "2 turns to leave after the weak warning" matches.
- Fish: each turn underwater, 10% "hungry-looking fish" warning, 4% INSTANT DEATH (swallowed). Roc: each turn on the surface, 10% the roc appears; you then have 2 turns to dive/leave or die (I-ROC 2). Both skipped if invisible.
- Amulet: on the lake bottom as "small, shiny object" — `TAKE OBJECT` / `GET AMULET`; 50% success per attempt [SRC, E]. Keep trying; budget the air/cold clock. Best practice ([B],[D]): SAVE on Western Shore before entering.
- Shore exits from On the Lake: W = Western Shore (Scenic Vista is S of it), S = Southern Shore (dark cave S toward Key Room), and back E to Lake Shore (start side). Layout per [B]: Lake Shore (E side, start), Western Shore (W, → S to Scenic Vista), Southern Shore (S, → repellent country).
- Repellent: `SPRAY REPELLENT ON ME` (accepts ON MYSELF [A]; [B] uses APPLY REPELLENT TO ME). Effect lasts exactly 5 turns (`QUEUE I-SPRAY 5`, shadow.zil:1717-1727), one use only. Route S, S, E = 3 moves in the dark to the lit Key Room — fits with 2 turns spare. Spraying it not-on-yourself wastes the can (SPRAY-USED?).
- Key Room: `GET KEY`, `MOVE COVER` / `RAISE MANHOLE COVER`, `D` to the Aqueduct; then N, N, N (Aqueduct → Water Slide → down slide) lands in Damp Passage where the torch waits. The trip back through the dark is not survivable (repellent expired), so the aqueduct is the only way out — and it must be BEFORE the quake (section 5).

## 5. The earthquake

[SRC]: `<ENABLE <QUEUE I-CLEFT <+ 70 <RANDOM 70>>>>` — queued at game start (dungeon.zil:930; in the gmain.zil build it's queued right after the first command, gmain.zil:165-167). So the quake fires on a uniformly random turn in [71, 140]. ([B] says "around turn 85-130", filfre.net says "100-150"; the code says 71-140.)

Opens:
- The cleft next to the Great Iron Door (Museum Ante ↔ Museum Entrance): CLEFT-FLAG set → E/W passage usable. This is the ONLY way into the Royal Museum / Puzzle / Jewel Room region. The Great Iron Door itself never opens [E].

Closes (lockouts):
- AQ-FLAG cleared → the aqueduct breaks between AQ-2 and AQ-3 ("The arch before you is broken."). If the key has not been retrieved and the aqueduct walked BEFORE the quake, the key (and the game) is lost — [E]: "The secret is to traverse this area before it is destroyed by the earthquake." If you are ON the aqueduct when it fires, you're trapped (death by grue/starvation).
- If you're at Aqueduct View / on the aqueduct / at the Great Door / off in another Zork via the table when it hits, you get special (mostly fatal or trapping) text — [B] "For Your Amusement" and I-CLEFT location cases.

Deterministic-replay consequence: do the entire lake/vista/key/aqueduct phase comfortably inside the first ~70 moves; then park at the Great Door and `WAIT` until the quake fires; all post-quake content is gated only on CLEFT-FLAG.

## 6. Flathead Ocean / Viking ship

[SRC] shadow.zil:2003-2037 (FLATHEAD-OCEAN-F):

- Each end-of-turn standing at Flathead Ocean (room is lit): 20% chance per turn the ship appears — but ONLY if it has never appeared before (BOAT-SEEN). The ship appears EXACTLY ONCE per game.
- It stays 2 turns (`QUEUE I-BOAT-DISAPPEAR 2`) then is gone forever. Miss the window → no vial → you cannot use the potion route past the Guardians (mirror-box route still works, so not strictly game-fatal).
- While the ship is visible: `HELLO SAILOR` (exact phrase; the sailor "waited three ages" for it). He throws the vial onto the beach and sails off. Then `GET VIAL` (it lands "near you in the sand"; [B] does LOOK first). Saying it before/after the ship: "Nothing happens yet."/"Nothing happens anymore."
- No prerequisite: not gated on quake, amulet, or anything else — just presence, light, and the once-only 20%/turn spawn. Expect a geometric wait (median ~4 turns, 95th percentile ~14).
- Do NOT confuse with the FYA "count occurrences of HELLO SAILOR" gag counter; only the at-ship greeting matters.

## 7. Aqueduct + Key

Covered in section 4/5; summary of command variants:

- [A]: `GET KEY / MOVE COVER / D / N / N / N / GET TORCH`
- [B]: `GET KEY / RAISE MANHOLE COVER / D / N / N / N` ("north three times to the Damp Passage")
- [D]: manhole, D, "go north twice to the Water Slide, then down the slide into the Damp Passage" (N, N, then N or D down the slide — the slide is one-way).
- The aqueduct walk is dry (pre-quake) and one-way in practice; the Water Slide dumps into Damp Passage and cannot be climbed back.
- MUST complete before the quake (section 5). The key is required for the endgame bronze door; the key "changes shape constantly" when examined (flavor).

## 8. Museum time machine (776 GUE ring theft)

Post-quake, from Great Door/Museum Ante: `E` through the cleft → Museum Entrance. [SRC] tm.zil:

- Setup in 948: `N` (Tech Museum), `PUSH GOLD MACHINE SOUTH` (→ Museum Entrance), `OPEN STONE DOOR`, `PUSH GOLD MACHINE EAST` (→ Jewel Room). Set `TURN DIAL TO 776` (can be done before or after pushing; [C] sets it in the Tech Museum first, [B] in the Jewel Room). `SIT ON SEAT` / `GET IN MACHINE`, `PUSH BUTTON`.
	- Pushing the button does nothing unless you're ON the seat and the dial differs from the current year [E].
	- Scoring: the point is for pushing the button with the dial set to exactly 776 [E, SRC tm.zil:529]. ([B] says "any number other than 948" — wrong per source.)
- You travel ALONE — no possessions cross time. Your stuff stays in the 948 Jewel Room; collect it on return.
- In 776 (Jewel Room, pre-cage): guards are outside; they leave after 3+RANDOM(12) turns → `WAIT` repeatedly until "You hear, from outside the door, guards marching away..." (tm.zil:827: 4-15 turns).
- `TAKE RING` and ONLY the ring [C emphatic]. [SRC] TGOTO: success requires, at the moment you leave 776: ring concealed under the seat, the time machine still in the (old) Tech Museum, AND the sceptre and jewelled knife still on the pedestal. Touching the other jewels → "mystery"/"clumsy robbery" outcomes: the plaque changes or the machine is removed = ring unobtainable.
- `OPEN DOOR`, `W` (Entrance), `OPEN WOODEN DOOR`, `N` (Tech Museum — machine is here in 776), `PUT RING UNDER SEAT` ([A]: LIFT SEAT then HIDE RING UNDER SEAT), `GET IN MACHINE`, `TURN DIAL TO 948`, `PUSH BUTTON`.
- Back in 948: `LOOK UNDER SEAT` → you automatically take the ring (hidden 172 years). `STAND` / `GET OUT`, `OPEN WOODEN DOOR`, `S`, `OPEN STONE DOOR`, `E` (Jewel Room), `GET ALL` (your belongings), then W, S, (S) to the Royal Puzzle Entrance.
- Timer: 40 moves after arriving in the past you snap back automatically (`QUEUE I-SNAP 40`, tm.zil:633) — the whole 776 errand must fit in 40 moves (it takes ~12-20 incl. guard wait; not tight but real).
- A museum robot occasionally (rarely) tidies up/closes doors [E, B-FYA]; harmless but can close the wooden/stone doors — just re-open.

## 9. Royal Puzzle — complete push sequences

Entry: from Museum Entrance go S (down a few steps) to Royal Puzzle Entrance; `READ NOTE`; `D` through the hole drops you into the start square. First `PUSH <dir> WALL` on sandstone scores the 7th point. Exit: maneuver a ladder-block under the entry hole, `UP` from atop... (the NW/N,W final moves position you at the ladder; then UP). There is also an emergency exit: put the LORE BOOK in the slot — opens a way out but FORFEITS the book (not recommended; [E] "not the best way out").
Both solutions below are verified-complete transcriptions; they enter from the same hole. "AGAIN" repeats the previous push. SAVE before entering [B],[C],[D] — a wrong push can wedge the puzzle permanently.

Variant 1 — InvisiClues/official ([E], reproduced verbatim by [B] and step-by-step by [D]):

	D. PUSH EAST WALL. S. S. SE. PUSH SOUTH WALL. N. NE. PUSH SOUTH WALL. TAKE BOOK.
	PUSH SOUTH WALL. E. NE. PUSH WEST WALL. SW. NW. NE. PUSH SOUTH WALL. SW.
	PUSH EAST WALL. NE. PUSH SOUTH WALL. NW. N. N. N. PUSH EAST WALL. SW. S. SE. NE. N.
	PUSH WEST WALL. NW. PUSH SOUTH WALL. AGAIN. W. NW. NW. PUSH SOUTH WALL. SE. SE. SE. NE.
	PUSH WEST WALL. AGAIN. SW. PUSH NORTH WALL. AGAIN. AGAIN. NW. UP.

Variant 2 — Gunness [A] (same as [C] in numbered-prose form):

	D. PRESS SOUTH WALL. E. S. E. E. PRESS SOUTH WALL. GET BOOK. PRESS SOUTH WALL.
	PRESS WEST WALL. AGAIN. E. E. N. N. N. N. PRESS EAST WALL. W. S. S. S. S. E. E. N. N. N.
	PRESS WEST WALL. N. W. PRESS SOUTH WALL. E. E. S. S. S. W. W. N. PRESS EAST WALL.
	W. W. W. N. N. W. N. PRESS EAST WALL. AGAIN. AGAIN. S. PRESS SOUTH WALL. N. E. E. S.
	PRESS SOUTH WALL. W. PRESS WEST WALL. AGAIN. S. W. PRESS NORTH WALL. AGAIN. AGAIN. W. N. U.

	([C]'s prose of the same route, step 9, says "push the North wall until it won't move any
	more" = PUSH NORTH WALL x3 total; then "West and North", then up — matching [A]'s
	W / N / U. [C] ends the book pickup leg "E, S, E, E, push South wall, GET BOOK" —
	identical to [A].)

Notes: the puzzle state is fully deterministic — no randomness inside. Movement is by compass (incl. diagonals) within a 2-D grid; PUSH only (never pull) [E]. Anything movable hit by a sliding wall "snaps" into the side room [E]. The two variants are genuinely different routes; "Innumerable other sequences will reach the same result" [E]. Score point on first sandstone push. After `UP` you exit at the Royal Puzzle Entrance.

## 10. Old man, beam, button, mirror box, Guardians of Zork

Old man (Engravings Room, NE of Damp Passage; carved north wall):
- Presence: 30% chance per ENTRY to the room (until fed) [SRC 3actions.zil:1765-1769] — if absent, step out and re-enter.
- Prerequisite: the waybread (`GET BREAD` at the Cliff — do this before/when there).
- `WAKE MAN` / `SHAKE MAN` — he wakes but FALLS ASLEEP AGAIN AFTER 3 TURNS (`QUEUE I-OLD-MAN-SLEEPS 3`); give the bread immediately: `GIVE BREAD TO OLD MAN`. He reveals the secret door outline and vanishes. ATTACKING him = he vanishes forever = lockout.
- `OPEN SECRET DOOR` (needed; revealing does not open), then N.
- [A] does this whole errand at the very start of the game (before the lake); [B]/[D] do it after the Royal Puzzle. Both work; the old man is not time-gated.

Beam and button (through secret door: Button Room, then N = Beam Room, N = Mirror Room S side):
- Block the red beam with any object: [B] `DROP CAN` (empty repellent can) in the Beam Room; [C]/[D] `PUT SWORD IN BEAM`; [A] `DROP CHEST`. Any carried object works [E].
- Then back S to Button Room, `PRESS BUTTON`: "Click. Snap!" The mirror-side panel unlocks for exactly 7 turns (`QUEUE I-MRINT 7`, actions.zil:1049) — the beam must still be blocked at button time. You must walk N, N, N (Beam Room → south Mirror Room → through the open panel into the box) within that window.

Inside the mirror box ([SRC] actions.zil MDIR init = 270, i.e., mahogany wall faces WEST at start — fixed, not random):
- Panels: mahogany = pushes box forward (direction it faces) IF channel aligned; pine = swings open to exit the box; red/yellow = rotate 45 degrees clockwise per push; white/black = rotate 45 degrees counterclockwise per push. Short pole: raised = box can rotate; dropped in the floor channel = box steadied for N-S movement (and cannot rotate). T-bar arrow/compass rose = facing of mahogany wall.
- Wobble kills: if the box moves with the short pole raised, it "sways unsteadily" — if the Guardians can see the box (later hallway sections), they smash it. Lower the pole before pushing mahogany [B], [E].
- Standard no-potion route [B]: `RAISE SHORT POLE`, `PUSH YELLOW WALL` x2 (270→315→0 = mahogany faces north), `LOWER SHORT POLE`, `PUSH MAHOGANY WALL` x3 (ride north past the Guardians), `RAISE SHORT POLE`, rotate with `PUSH WHITE WALL` (x4: N→NW→W→SW→S) until mahogany faces south, `PUSH PINE WALL`, `N` out to the Dungeon Entrance. The rotation at the end matters: "Rotate the structure so that the door doesn't open into their field of view" [E].
- Potion shortcut route [A]/[C]/[D]: `RAISE SHORT POLE`, `PUSH WHITE PANEL`, `AGAIN` (270→225→180 = mahogany faces south), `LOWER SHORT POLE` ([A]; [C]/[D] omit the lower), `PUSH PINE PANEL`, `N` (exit the box on its north side, still south of the Guardians), then `OPEN VIAL`, `DRINK LIQUID`, and walk N past the Guardians to the door.
	- CRITICAL TIMING [SRC] 3actions.zil POTION-F: invisibility expires via `QUEUE I-VISIBLE 3` — and if you are in the Guardians' corridor (MRG/MRGE/MRGW) when it fires, you are killed. You get 2 safe moves. Drink at the last moment, directly south of the Guardians, then move N, N without pause. ([E] says "will last only two moves".)
	- Pine panel auto-closes 5 turns after opening (I-PININ 5) — exit promptly.
- Do NOT ride the box while carrying nothing... (no such constraint — but the box only moves N/S in its channel; total trip is 3 pushes).

## 11. Endgame — Dungeon Master, Parapet, cell, bronze door, Treasury

Door: at the end of the corridor north of the Guardians is the huge wooden door with barred panel. You cannot open it: `KNOCK ON DOOR`.
- Requirement [SRC] 3actions.zil LOOK-LIKE-DM?: you must be CARRYING (held or worn — code checks possession, not worn state) ALL SEVEN: HOOD, CLOAK, AMULET, RING, STAFF, LORE BOOK, KEY. The sword, vial, torch, chest, etc. are irrelevant. If any is missing he turns you away ("Come back when you are ready").
- On success he admits you: "Command me as you will, and complete your quest!" The DM follows you automatically from here (I-FOLIN enabled on entry [SRC]; [E] gives `DUNGEON MASTER, FOLLOW ME` if he's ever not following; `MASTER, STAY`/`WAIT` to park him).

Geography: door room → N → an E-W corridor; `E` (or `W`), `N`, `N` reaches the Parapet over the flaming pit ([A]: N, E, N, N; [B]: north, then east or west, then north twice). The sundial has numbers 1-8 and a button; south across the north corridor is the prison cell.

Sequence (merged; all sources agree on structure):
1. At the Parapet (DM in tow): `TURN DIAL TO 4` then `PRESS BUTTON` — summons cell 4 to the corridor position. (4 is hardcoded: only cell 4 has the bronze door; bronze door object made visible only when dial=4 cell is in place [SRC] CELL-MOVE/KEY-F. The lore book hints this: "READ BOOK" [A].)
2. `S` (north corridor), `OPEN CELL DOOR`, `S` — you are in the cell. The DM will NOT enter ("I am not permitted to enter the prison cell").
3. Order the DM (he must be at the Parapet to work the dial — command him there first):
	- [B]: `TELL DUNGEON MASTER TO GO TO THE PARAPET`, then `TELL DUNGEON MASTER TO TURN THE DIAL TO 1` (ANY number except 4 works — [C] uses 1, [A] uses 8), then `TELL DUNGEON MASTER TO PRESS THE BUTTON`.
	- Order syntax per game manual/[E]: `MASTER, GO TO THE PARAPET` / `MASTER, TURN THE DIAL TO 1` / `MASTER, PUSH THE BUTTON` (comma form equivalent to TELL ... TO ...).
4. When he pushes the button, the cell door closes and cell 4 (with you inside) rotates back to its HOME position (GOOD-CELL). Warning [E]: once this has happened, if you can't open the bronze door there is NO WAY BACK — this is the point of no return; every one of the 7 items should be in hand (they are, from the knock check, unless you dropped something).
5. `UNLOCK BRONZE DOOR WITH KEY` — "The key seems to mold itself to the shape of the lock." Works ONLY in cell 4 at its home position [SRC KEY-F: HERE == GOOD-CELL]. Then `OPEN BRONZE DOOR`, `S` (or OUT).
6. You are in the Treasury of Zork (NIRVANA). The DM materializes, taps you with the staff, and you become the Dungeon Master. Game over (there is no score-based ranking beyond 7/7).

Note: while waiting at the Parapet do not `SPIN DIAL` (randomizes the setting). The flaming pit destroys anything dropped in.

## 12. The 7 score points

Per [E] (InvisiClues, authoritative) and confirmed in [SRC] (each guarded by a one-shot flag):

1.	Jump in / enter the lake (first time on the lake surface) — shadow.zil ON-LAKE-F.
2.	Touch the viewing table (first TOUCH/RUB that teleports you) — shadow.zil VIEWING-TABLE-F.
3.	Reach the Cliff Ledge (first arrival, chest present) — shadow.zil CLIFF-LEDGE-F.
4.	Encounter the hooded figure (its first appearance) — shadow.zil SHADOW-ARRIVAL.
5.	Attack the hooded figure (first attack) — shadow.zil SHADOW-F.
6.	Push the time machine button with the dial set to 776 — tm.zil TM-BUTTON-F ([B] loosely says "other than 948"; code requires exactly 776... i.e., YEAR-BUILT).
7.	Push a sandstone wall in the Royal Puzzle (first push) — actions.zil CPPUSH.

"It is possible to have all 7 points without correctly solving any of the puzzles" [E]. There is no point for winning; the Treasury entry ends the game.

---

## Release-dependence notes

- We run Release 25 / serial 860811 (the final Zork III release). No source calls out behavioral differences between releases for any of the mechanics above. The historicalsource ZIL contains both an older init (dungeon.zil, quake queued at startup) and the later gmain.zil variant (quake queued after the first command) — a one-turn phase difference in the quake window at most.
- [B] mentions a scripting bug (burning the lore book only works when not holding it) as a curiosity; r25-safe to ignore.
- The "TOUCH TABLE" verb, "HELLO SAILOR", "SPRAY REPELLENT ON ME", "MASTER, ..." order syntax are all present in the r25 parser per all sources.

## Biggest timing/randomness risks for deterministic replay (ranked)

1.	**Hooded figure fight** — the single largest RNG sink: 30%/turn spawn, per-blow hit rolls both ways, 10% of its hits deal 2 damage (can kill you), and the final state must be EXACTLY strength 1 for TAKE HOOD. A fixed command list cannot guarantee the fight transcript; replay needs a loop: attack until "badly hurt and defenseless" appears, then TAKE HOOD, TAKE CLOAK. Also the figure blocks a RANDOM exit, so the post-fight escape route can vary.
2.	**Earthquake window (turn 71-140, uniform)** — everything lake/key/aqueduct-side must be done before it (lockout), and the museum side only after. Deterministic strategy: finish the aqueduct by move ~70, then WAIT at the Great Door until it fires (1-70 extra WAITs).
3.	**Viking ship** — appears once, 20%/turn, visible 2 turns. Replay must WAIT-loop at Flathead Ocean and issue HELLO SAILOR the turn the ship text appears (or the turn after at the latest).
4.	**Amulet grab** — 50% per TAKE, under a 3-turn air limit and ~7-turn cold limit, with a 4%/turn underwater instant-death fish and 10%/turn surface roc. Needs retry loops (resurface, re-dive) and accepts occasional deaths without point loss (dying scatters inventory though — treat as restore point).
5.	**Old man presence** — 30% per room entry; loop leave/re-enter. After WAKE, bread must be given within 3 turns.
6.	**Guard departure in 776** — 4-15 turns random WAIT; bounded by the 40-move snap-back (still ample).
7.	**Vista indicator phase** — deterministic (changes every 4 moves from game start), but a replay whose move count shifts by even one move changes which numeral is up; key on the displayed numeral, not on absolute turn numbers.
8.	**Invisibility potion = 2 safe moves** and dying-if-it-expires-between-Guardians; the mirror-box (pole-down) route has zero RNG and is preferable for deterministic replay; then the vial/potion becomes entirely optional.
9.	**Mirror panel windows** — button opens the panel for 7 turns; pine panel closes after 5; both deterministic but tight enough to matter.
10.	**Museum robot** — rare random tidier that can close the stone/wooden doors between your setup moves; harmless if the replayer re-opens doors on failure.

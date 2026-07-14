# SPELLBREAKER (Infocom, 1985) — Mechanics Notes for Deterministic Replay
Target binary: Release 87 / serial 860904, Z-machine V3, 600 points
(games/zcode/spellbreaker.z3 — header verified: version 3, release 87, serial 860904).

Sources used:
- ZIL source: github.com/historicalsource/spellbreaker (authoritative; dev-system snapshot).
  The shipped build compiles Z6.ZIL which INSERT-FILEs MISC, PARSER, SYNTAX, INTERRUPTS,
  VERBS, MAGIC, GLOBALS, GUILD, C1..C4. NOTE: `actions.zil` is a stale copy of `magic.zil`
  and is NOT part of the build (z6.zil:INSERT-FILE list) — cite magic.zil, not actions.zil.
- ifarchive.org/if-archive/infocom/hints/solutions/spellbreaker.step
  (Erik Futtrup / Twan Lintermans step file, 1992).
- ifarchive.org/if-archive/infocom/hints/solutions/spellbreaker.txt (prose walkthrough).
- walkthroughking.com/text/spellbreaker.aspx (2001 walkthrough).
- zedlopez.github.io/invisiclue/spellbreaker.html (InvisiClues conversion; the vault
  chapter documents the 3-jindak limit and the coin-weighing tree).
- EMPIRICAL VERIFICATION: the entire route below was machine-played to 600/600 against
  the actual r87 binary under the project Z-machine on 20 distinct pinned RNG seeds
  (530–561 moves). Every mechanic below marked [verified] was observed in those runs.

Tick convention: `<QUEUE I-FOO n>` fires at the end of turn (queue-turn + n − 1);
`<QUEUE I-FOO -1>` fires every turn-end. The replayer must sync on message text,
never on absolute turn numbers — retry loops shift everything.

---

## 1. The opening: Council Chamber

- GO (misc.zil:290-303): starts in COUNCIL-CHAMBER; queues I-TIRED 80 and I-ORATION −1;
  sets `MAGIC-BOX-CUBE = WATER-CUBE` (the gold box starts "attuned" to the water cube).
- I-ORATION (interrupts.zil:63-130): four guildmaster speeches, one per turn-end
  (Sneffle turn 1, Hoobly 2, Gzornenplatz 3, Ardis 4). At OCOUNT 4 everyone becomes
  amphibians (`CLEESHED? = T`), **BLORPLE-SPELL is silently added to your spell book**
  (interrupts.zil:104), and the SHADOW moves to GUILD-HALL with I-SHADOW-GOES 1 queued.
- You cannot leave/cast/attack in the chamber before the cleesh (COUNCIL-CHAMBER-F,
  guild.zil:168-200 — Orkan stops everything). Exactly **4 waits** (`z` ×4), then `s`.
- I-SHADOW-GOES (interrupts.zil:145-173): the figure runs Guild Hall → Belwit Square
  one turn later, then "jumps into the air ... explosion": **EARTH-CUBE is moved to
  BELWIT-SQUARE (invisible)** and the orange CLOUD appears; I-CLOUD-GONE queued 20
  (interrupts.zil:160). You do NOT need to chase it turn-perfectly; the cube waits.
- The cloud: `lesoch` (V-LESOCH, magic.zil:866-889) dissipates it instantly and reveals
  the "small featureless white cube". Alternative: wait ~20 turns for I-CLOUD-GONE
  (interrupts.zil:175-188) — lesoch is faster. Lesoch here has only **P=50%**
  (see §10) — a fizzle just needs learn+recast. [verified both success and fizzle]
- Grab bread AND fish in the Guild Hall on the way (grouper bait, §5.3). +points:
  first blorple awareness (reading the book or first blorple cast) = **+15**
  (SEE-BLORPLE, magic.zil:820-823). Each cube on first touch = **+25** (SCORE-OBJECT,
  verbs.zil:1737-1746).
- No deadline in the opening. The only opening RNG is the lesoch fizzle roll.
- Samarra Easter egg (harmless): after you first touch the DEATH-CUBE, entering Belwit
  Square makes the shadow appear/vanish once (BELWIT-SQUARE-F guild.zil:458-462,
  I-SAMARRA interrupts.zil:136-143).

## 2. Spell system

Initial book (objects IN SPELL-BOOK, magic.zil): LESOCH (132), JINDAK (174),
MALYON (288), GNUSTO (299), FROTZ (310), REZROV (321), YOMIN (332). BLORPLE is added
at the cleesh (interrupts.zil:104). GNUSTO/FROTZ/REZROV are known by heart — never
occupy slots, always castable (SPELL-F magic.zil:410-412; PRE-CAST magic.zil:593-594).

Spells acquired en route (all gnusto-able except girgol):
- CASKLY ("perfect") — stained scroll, ROC-NEST (magic.zil:244).
- THROCK ("grow plants") — dirty scroll, CLIFF-MIDDLE (magic.zil:224).
- GIRGOL ("stop time") — flimsy scroll, materializes in the ZIPPER (§5.2). **Cannot be
  gnusto'd**: "too long, too complicated, too powerful"; uniquely, the scroll SURVIVES
  the gnusto attempt (V-GNUSTO magic.zil:1174-1179). Castable only from a scroll copy.
- ESPNIS ("sleep") — dusty scroll, OGRE-BEDROOM (magic.zil:184).
- LISKON ("shrink living thing") — damp scroll inside the BOTTLE (magic.zil:264).
- TINSOT ("freeze") — white scroll, GLACIER-ROOM (magic.zil:204).
- SNAVIG ("shape change") — inside the moldy DEAD-BOOK (present-day dungeon cell,
  c2.zil:1046-1092); caskly the book first (+15, DEAD-BOOK-SCORE c2.zil:1076-1092),
  then `gnusto snavig` while HOLDING the book.

Memorization: SPELL-MAX=SPELL-ROOM=REAL-SPELL-MAX=4 initially (magic.zil:520-522).
LEARN (magic.zil:396-452): needs the spell in YOUR book and the book directly in hand
(`<IN? SPELL-BOOK WINNER>` — a book inside the zipper canNOT be learned from).
Casting decrements COUNT and refunds SPELL-ROOM at end of PERFORM (misc.zil:658-663)
— **a fizzled cast still consumes the memorization** (PRE-CAST sets SPELL-CAST before
the probability roll, magic.zil:595). Learning over capacity calls FORGET-SPELL — a
RANDOM memorized copy is lost (magic.zil:433-436, 469-484). Never over-learn.

Sleep (V-SLEEP, verbs.zil:1237-1348): wipes ALL memorized spells (FORGET-ALL,
verbs.zil:1306) but REAL-SPELL-MAX+1 (max 8, verbs.zil:1296-1299), MOVES+=50,
FUMBLE-NUMBER reset to 8, LOAD-ALLOWED reset, I-TIRED requeued 150 (verbs.zil:1304).
Death also FORGET-ALLs (JIGS-UP verbs.zil:2034).

THE MAGIC CUBE IS GOD MODE [verified]: while the MAGIC-CUBE is held —
- I-TIRED is a complete no-op (interrupts.zil:455): no fatigue, no stat decay ever again;
- LEARN never fails and bypasses ALL capacity checks (magic.zil:420, 440-441:
  "You easily learn ..." — unlimited copies);
- every spell except girgol succeeds unconditionally (SPELL-PROB? magic.zil:639-641).
Acquire it (§5.9) and the rest of the game is RNG-free on the spell axis.

## 3. Survival clocks

- **NO hunger, NO thirst.** There is no I-HUNGER/I-THIRST anywhere in the build. Bread
  and fish are grouper bait only (KNIFE-F even jokes "you really weren't feeling very
  hungry", guild.zil:12-17).
- **Tiredness is the only body clock.** I-TIRED first fires at end of turn 80
  (misc.zil:295), then every 8 turns (interrupts.zil:454). Each firing (unless the
  magic cube is held): LOAD-ALLOWED −10, FUMBLE-NUMBER −1 (min 1!), SPELL-MAX −1
  (min 1) and SPELL-ROOM −1, AWAKE +1 (interrupts.zil:453-478). At AWAKE > 8 you are
  FORCED asleep on the spot (interrupts.zil:467-472) — fatal in the ogre cave, ocean,
  roc nest, flooded oubliette (V-SLEEP death branches verbs.zil:1239-1290).
- While AWAKE ≥ 0, every LEARN fails with PROB 5×AWAKE ("You can't concentrate...",
  magic.zil:421-427); at AWAKE > 6 learns ALWAYS fail.
- **FUMBLE-NUMBER decay is the sneakiest killer**: it is the direct-inventory carry cap
  (ITAKE, verbs.zil:1724). It silently drops from 8 toward 1 between sleeps, making
  `take` commands fail ("You're holding too many things...") and desyncing scripts.
  Countermeasures [verified]: sleep on schedule; keep ≤5 objects directly in hand
  (stash everything in the open zipper — zipper contents still count as "held"
  recursively for spell-probability purposes, HELD? verbs.zil:2157-2167, GOT?
  c4.zil:1477-1480 — but NOT against the fumble cap, which counts only direct children).
- Sleep scheduling that works [verified on 20 seeds]: insert a one-turn opportunistic
  nap at every safe checkpoint: `sleep` → if "you really aren't tired ... thrash around"
  proceed; if "Ah, sleep! ... snore blissfully" you slept (spells wiped — always nap
  BEFORE a learn block, never between learn and cast). Never sleep at: Bazaar
  (PROB 75 possessions stolen, verbs.zil:1339-1344), ogre cave/lair, glacier is OK but
  cold resets, roc areas, ocean, flooded oubliette, Castle (espnis-self there = −99).
  Dreams consume RNG on sleep: PROB 50 + PICK-ONE of 4 dreams (verbs.zil:1330-1335).

## 4. THE CUBE SYSTEM

13 real cubes (CUBE-LIST c4.zil:1810-1834). Each has a hidden dictionary adjective
("AQ".."MQ") and a NAME slot. BLORPLE cube-in-hand teleports you INSIDE the cube
(V-BLORPLE magic.zil:825-852); the cube vanishes while you're inside
(BLORPLE-OBJECT) and **reappears in your hand when you leave its interior rooms**
(RECOVER-CUBE magic.zil:856-864). Blorple is refused with "Nothing happens" while
you stand in a cube-interior room (magic.zil:827 — `GETP HERE P?CUBE`); adjacent
non-interior rooms (Dark Cave, Meadow, Oubliette, maze, Plain...) are fine.
Blorple requires the cube DIRECTLY in hand (PRE-CAST magic.zil:590-592) and never
fizzles (SPELL-PROB? magic.zil:662-663). Blorpling a non-cube-connected thing or the
un-jindak'd time cube drops you in DULL-ROOM (exit returns whence you came,
c1.zil:23-45).

LABELS: `write "foo" on cube` with the **burin directly in hand** (V-WRITE/QWORD,
CUBE-F c3.zil:2251-2272; WRITE-ON-CUBE c4.zil:1840-1856). The label must be in double
quotes when writing; afterwards refer to the cube by the bare label ("blorple 3",
"take 3", "put 3 in box"). Labels are matched on the FIRST 6 CHARACTERS only
(QCOPY/MATCH? parser.zil:658-693) — keep them unique in 6 chars; digits work and are
what the historical walkthroughs use. Re-writing replaces the old label ("You replace
the word...") — a classic desync trap if a `take cube` silently failed and the write
lands on an already-labelled cube in hand [verified failure mode]. `take cube`
(unqualified) resolves to the first VISIBLE UNLABELLED cube (GENERIC-CUBE-F
interrupts.zil:7-28) — cubes inside the open zipper are visible, so label everything
promptly.

The 13 cubes — location, interior desc, box-figures TEXT, how obtained:

| # | ZIL object | label (route) | interior | TEXT (gold-box figures) | where/how |
|---|---|---|---|---|---|
| 1 | EARTH-CUBE (c1.zil:47) | "1" | Packed Earth | moles | Belwit Square, lesoch the cloud |
| 2 | LIFE-CUBE (c4.zil:480) | "2" | Soft Room | rabbits | keystone of the hermit's hut, caskly hut (c1.zil:1364-1400) |
| 3 | WATER-CUBE (c2.zil:7) | "3" | Water Room | dolphins | inside the gold box in the ogre's lair |
| 4 | CHANGE-CUBE (c4.zil:781) | "4" | Changing Room | butterflies | in the CHUNK in the water pipe (IN-PIPE, c2.zil:707-800) |
| 5 | AIR-CUBE (c3.zil:7) | "5" | Air Room | eagles | rodent idol's mouth (§5.4) |
| 6 | DEATH-CUBE (c4.zil:745) | "6" | Boneyard | worms | Dungeon (PRISON) above the oubliette |
| 7 | CONNECTIVITY-CUBE (c4.zil:1753) | "7" | String Room | spiders | roc's nest under the egg, 2nd visit by carpet (§5.6) |
| 8 | LIGHT-CUBE (c4.zil:447) | "8" | Light Room | fireflies | grouper's nest, ocean floor (§5.7) |
| 9 | MIND-CUBE (c3.zil:1583) | "9" | No Place | owls | MAZE-1, compass-rose maze (§5.8) |
| 10 | DARK-CUBE (c3.zil:1335) | "10" | Dark Room | grues | on the brown rock, Plain (§5.9) |
| 11 | FIRE-CUBE (c3.zil:1059) | "11" | Fire Room | salamanders | pillar in the grue cave (§5.10) |
| 12 | MAGIC-CUBE (c4.zil:1424) | "12" | Magic Room | unicorns | volcano outcropping via gold-box trick (§6) |
| 13 | TIME-CUBE (c4.zil:1501) | (x1..x12) | Sand Room | turtles | the vault weighing puzzle (§7) |

Interior connections that matter (room exits):
- Packed Earth: E→Hall of Stone (one-way loop), W→Cave Entrance (ogre), S→Cliff Middle,
  D→midair fall (roc), N→gold-box exit (c1.zil:59-77).
- Water Room: N→Oubliette, S→splash into Mid-Ocean, E→box exit (c2.zil:20-36).
- Air Room: N→Glacier, W→Bazaar, S/D→midair, D→box exit (c3.zil:20-46).
- Soft Room: S→Meadow (weed, shears), E→box exit (c4.zil:493-510).
- Changing Room: N→Bare Room (compass rose, no exits!), W→Carving Room (maze),
  E→box exit (c4.zil:794-826).
- Boneyard: N/OUT→Belwit Square (this is also where deaths dump you), W→box exit
  (c4.zil:758-780).
- String Room: S→Enchanters' Retreat (Belboz), E→box exit (c4.zil:1766-1786).
- Light Room: W→Volcano Base (lava fragment), S→box exit (c4.zil:460-478).
- No Place (mind): E→INNER VAULT, S→Plain (rocks), W→box exit (c3.zil:1596-1660).
- Dark Room: D→Dark Cave→Grue Cave→Light Pool→Pillar, U→box exit (c3.zil:1348-1366).
- Fire Room: N→Volcano (vent + outcropping), S→Cliff Top, E→box exit (c3.zil:1072-1090).
- Magic Room: N→Meadow, E→CASTLE (needs all 13 cubes: MAGIC-DOOR-EXIT c4.zil:1492-1498),
  S→box exit.
- Sand Room (time): U→PAST Ruins Room, D→PAST Dungeon Cell (c4.zil:1513-1536).

## 5. Major puzzles, exact commands and timing

### 5.1 First roc trip (stained scroll = caskly)
`blorple 1`, `frotz burin` (NEVER `frotz me` — a self-frotzed player is executed at the
grue snavig: GRUE-F globals.zil:686-688), `d` (first d = warning, FALL-WARNING?
c3.zil:34-45), `d` again → MIDAIR falling. I-FALLING (interrupts.zil:1103-1130): from
EARTH-ROOM, UD-COUNT=4 and ROC-PROB starts 25 (first-ever entry) then +25/turn with a
PROB roll each turn (50%, 75%, then 100% — catch guaranteed by the 3rd roll on a first
fall). On LATER falls ROC-PROB starts 0 (MIDAIR touched) → rolls 25/50/75 then
SMASH-PROB 20/40/... — **≈9.4% death per re-fall** [verified death on seed 11].
Death here is survivable (§11): you respawn in the Boneyard with all items; relearn
blorple, `blorple 1`, `d`, retry. After the catch: 4 automatic flight turns
(I-ROC-FLY interrupts.zil:998-1022) → In Roc Nest, roc present (so no hatch timer).
`take stained scroll`, `gnusto caskly` (deterministic: 75+5×cubes+20 earth ≥100),
`learn blorple`, `blorple 1`. SYNC: "settles to the ground, and releases you."

### 5.2 The zipper and the flimsy scroll (girgol)
Ruins Room (Packed Earth → E→Hall of Stone → S). `take zipper`, `open zipper`,
`reach into zipper` — FIRST reach moves GIRGOL-SCROLL into the zipper ("Oops, it
slipped away again", ZIPPER-F c1.zil:873-882, ZIPPER-SCROLL? flag) — then
`look into zipper`, `take flimsy scroll` (+10). The zipper is a MAGICBIT vehicle-bag
(capacity 1000): its closed interior blocks light both ways; contents ride along and
count as held for spell odds but not for the fumble cap. It is ALSO the time-loop
artifact you must abandon in the past (§8).

### 5.3 Avalanche → hermit's hut (life cube), coin
Cliff Middle: `take dirty scroll` (+10), `gnusto throck`. `u` → Cliff Top. Entering
queues I-AVALANCHE? −1 with SLIDE-PROB 10 (+10 per turn, interrupts.zil:735-748,
c1.zil:1068-1074): each turn a PROB roll; when it triggers: "the whole dike is about
to give way!", then next turn-end I-AVALANCHE: "Huge rocks and boulders are tumbling
down... If you don't do something soon, you will die!" — the next firing at Cliff Top
kills (interrupts.zil:757-792). **CRITICAL 1-turn window**: on the turn after the
"you will die" line, cast `girgol` (from the flimsy scroll in hand — deterministic,
SPELL-PROB? magic.zil:666-671; the scroll VANISHES, PRE-CAST magic.zil:578-582).
STOP-AVALANCHE (c1.zil:1076-1082): rocks freeze for 12 turns (QUEUE I-GIRGOL 12).
`u` ×4 (Boulder-1/2/3 → Mountain Top — being on a boulder when girgol expires = death,
I-GIRGOL interrupts.zil:532-537, but there is NO need to hurry once on top: when it
expires the avalanche falls harmlessly and the cliff route is gone forever — you leave
by blorple). `take coin` (500-zorkmid piece, ZORKMID c3.zil:197-208), stow coin/bread/
knife in zipper, `w` → Stone Hut: `caskly hut` (FIZZLE-PRONE ~55%: retry loop
learn caskly + caskly hut until "The hut begins to melt", HUT-F c1.zil:1364-1400) —
hermit appeased, LIFE-CUBE freed → `take cube` (+25), `write "2" on cube`, `e`,
`learn blorple`, `blorple 2`. NEVER `malyon` the keystone cube (hut collapses, death,
c1.zil:1197-1205). SYNC: "about to give way" → "you will die!" → girgol.

### 5.4 Weed → ogre (water cube + espnis + gold box)
Soft Room S → Meadow: `take weed` twice (WEED-PLANTED? 2→1→0, "pulls out of the
ground, taking a good-sized ball of earth", c4.zil:634-660). Do NOT cut it (a cutting
can't be planted, c4.zil:679-683). blorple 1, `w` → Cave Entrance, stow spare cubes
(fumble headroom), nap checkpoint, `n` → Cave. First entry queues I-OGRE-KILLS-YOU 12
(c1.zil:1604-1606) — the ogre tramples you in ~12 turns unless neutralized (the timer
requeues every 2 while he's incapacitated, interrupts.zil:560-576). `plant weed`,
`learn throck`, `throck weed` (fizzle-prone ~80%; retry with relearn) → "spurt of
explosive growth ... Ragweed!" → SNEEZY for 10 turns (OGRE-SNEEZING c4.zil:739-742,
I-STOP-SNEEZING interrupts.zil:1354-1364). Within the window: `d` (past the sneezing
ogre, OGRE-BEDROOM-EXIT c1.zil:1634-1656), `take dusty scroll` (+10), `take gold box`
(+10), `u`, `s` (out). Then safely: `gnusto espnis`, `open box`, `take cube`
(WATER-CUBE, +25), `write "3" on cube`, box into zipper, `learn blorple`, `blorple 3`.
yomin ogre (hay-fever hint) is flavor only. Espnis-ing the ogre (20 turns,
I-ESPNIS actions ~magic.zil:1023-1040) is a backup neutralizer.

### 5.5 Ocean drop / bottle (liskon) / pipe (change cube)
EVERY entry Water Room → S dumps you in Mid-Ocean, rips the WATER-CUBE from you into
the water (sinks in ~3 turns, I-CUBE-SINKS) and spawns the grouper with I-GROUPER 2
(OCEAN-ROOM-F c2.zil:57-82). I-GROUPER eats, in priority order, FISH > BREAD >
WATER-CUBE > BOTTLE floating in Mid-Ocean (interrupts.zil:859-874), then dives.
Trip 1: carry ONLY the fish (drop the rest in the Water Room — anything in the ocean
gets soaked; scrolls/book are RWATER-ruined). `s`, `drop fish` (eaten at turn-end),
`take 3`, `take bottle`, `blorple 3` (casting works at the surface; not underwater,
PRE-CAST magic.zil:559-562). `open bottle`, `take damp scroll` (+10), `gnusto liskon`,
`take all`. `n` → Oubliette: `liskon me` (retry loop; "squashed and pushed and
squeezed") → 15-turn small window (I-LISKON 15), `frotz bottle` (retry — your pipe
light), `drop all except bottle and 3`, `enter outflow pipe`, `w`, `take cube`
(CHANGE-CUBE in the chunk, +25), `w`, `climb out of pipe` → Ruins Room, `blorple 3`,
`n`, `take all`, `write "4" on cube`, bottle into zipper, `take 1`, `blorple 1`.
Growing back inside the pipe/cabinet/bottle = death (TOO-LARGE interrupts.zil:631-649).

### 5.6 Serpent + idol (air cube), glacier (tinsot), Emporium (carpet)
Packed Earth E, N → Smooth Room. `liskon snake` (retry; "the tail tip slips out") —
15-turn window — `n`, `n` → Temple. **Idol (CRITICAL fixed cadence, verified):**
`malyon idol` → animates, I-UNMALYON-IDOL 4 / I-IDOL 2 queued (c1.zil:497-506);
`z`; `espnis idol` → "suddenly looks very tired and begins to yawn" (queues
I-FULL-YAWN 2, I-IDOL-ASLEEP 3, c1.zil:518-521); `z` → yawn opens AND the malyon
expires the same turn-end, in that order → "turned back into basalt ... caught in a
cheek-stretching yawn" (I-UNMALYON-IDOL interrupts.zil:665-680). `climb idol`,
`look into mouth`, `take cube` (AIR-CUBE on the tongue, +25, MOUTH-F c1.zil:574-647),
`d`, `write "5" on cube`, `learn blorple`, `blorple 5`.
  - If espnis FIZZLES the window is lost: wait for "turns back into basalt", relearn,
    redo the whole malyon/z/espnis/z cycle [verified recovery].
  - While animated, climbing/giving/malyon-again = death (IDOL-CRUSHES-YOU).
  - Never put items in the mouth: a later malyon swallows them AND the cube forever
    (c1.zil:481-487) — unwinnable.
Air Room: `n` → Glacier: `take white scroll` (+10), `learn blorple`, `blorple 5`.
Glacier clock: FREEZE-COUNT hypothermia death at 10 turns; ANY walk = PROB 75 crevasse
death (c3.zil:70-94) — enter, grab, blorple out, never walk.
`w` → Bazaar, `take coin` (from zipper), `e` → Emporium (50-turn I-KICKED-OUT limit,
c3.zil:143; casting any spell = thrown out, c3.zil:151-160). Haggling is FULLY
DETERMINISTIC (MERCHANT-WANTS 900, −100 per counter-offer, max 4 speeches;
NEW-OFFER/MAKE-NEW-OFFER c3.zil:375-447): `buy blue carpet` (speech: 800),
`offer 300` (700), `offer 400` (600), `offer 500` → "Done, then!" — he takes the coin
and hands you the SCRUFFY RED carpet; `take blue carpet` → "How silly of me! You
wanted this one with the cubes" — swap, +10 (ASK-ABOUT-CARPET c3.zil:315-373).
`w`, `gnusto tinsot` anywhere safe, `learn blorple`, `blorple 3`.

### 5.7 Oubliette flood (death cube), moldy book (snavig), carpet trips (connectivity cube), grouper dive (light cube)
Oubliette (Water Room N). Everything except the burin goes INTO the zipper, CLOSED —
the rising water soaks whatever you carry openly (SOAK-PLAYER; book/scrolls ruined).
Learn tinsot ×4 (fizzles possible pre-magic-cube; book is sealed once the flood
starts). `n`, `rezrov trap door` (retry; "creaks open"), `tinsot channel` → partial
blockage ("only partially blocked", PARTIAL-BLOCKAGE magic.zil:1106-1110),
`tinsot channel` again → "large icy cap over the outflow pipe ... begins to fill"
(FREEZE-FLAG 2 → I-OUBLIETTE-FILLS −1: one level/turn, 4 levels, then 5 turns later
it drains, I-OUBLIETTE-EMPTIES; interrupts.zil:899-956), `tinsot water` → ice floe
(magic.zil:1079-1084), `climb on floe`, then just try `u` every turn until it works
(needs: full + on floe + trap door open; OUBLIETTE-UP-EXIT c2.zil:372-395) → Dungeon.
`take cube` (DEATH-CUBE in PRISON, +25), `open zipper`, retrieve book+burin,
`write "6" on cube`.
`e`, `n` → Dungeon Cell: `rezrov cabinet` (bursts it open — the PRESENT cabinet only!),
`take moldy book` (+10), `caskly moldy book` (retry; "mold and rot retreat", +15),
`gnusto snavig` (hold the book), `s`, `w`.
`u` → Guard Tower: entering moves the ROC here and starts a 5-turn grab countdown
(GUARD-TOWER-F c2.zil:1118-1131, I-ROC interrupts.zil:981-994: descriptions "tiny
black dot"→"large object"→"large bird approaching"→"circling the tower", grab on the
5th) — the countdown resets on every entry. **4-command budget per visit.**
Visit 1: `drop carpet`, `sit on carpet` (must SIT, not stand), `u` (roc "flees
goggle-eyed"). Flying (MAGIC-CARPET-F c3.zil:658-842): `w` ×4 → "above a giant bird's
nest", `d` → In Roc Nest. Roc absent ⇒ I-ROC-HATCHES 5 queued at landing
(ROC-NEST-F c2.zil:1283-1322) — **4-command exit budget**: `get off carpet`,
`take cube` (CONNECTIVITY-CUBE, +25 — blocked only while the mother roc is present),
`sit on carpet`, `u`. Then `e` ×4, `d` → Guard Tower (roc countdown restarts):
`get off carpet`, `take carpet`, `write "7" on cube`, `d` — exactly 4 commands.
If the egg hatches with you there, the chick eats the cube and then you
(I-ROC-HATCHES/I-YUM-YUM interrupts.zil:1024-1060) — cube LOST FOREVER = unwinnable.
`learn blorple`, `blorple 3`.
Grouper dive: nap checkpoint, learn blorple + snavig ×3 (fizzle margin ~85%/cast,
book unavailable mid-ocean), everything into the CLOSED zipper (open = soaked at
turn-end, SOAK-IF-OPENED c2.zil:626-631), carry just the zipper. `s` (cube 3 splashes
in again), `take 3` (before the grouper eats it — nothing tastier this time... it
eats the BOTTLE if you left it floating; keep the bottle zipped), `snavig grouper`
("You change." — everything you hold drops to the OCEAN FLOOR, GROUPER-F
c2.zil:307-320 — convenient), `d`, wait ~10 turns until "You have become yourself
again. Fortunately your gills have stored some oxygen" (I-SNAVIG 12,
interrupts.zil:482-512) → **2-command drowning budget** (I-DROWN 3,
interrupts.zil:514-519): `take all` (includes the LIGHT-CUBE from the open grouper
nest, +25), `u` ("pure, sweet air"), `blorple 3`. Retrieve book/burin from zipper,
`write "8" on cube`, `n` (can't blorple inside a cube room), `learn blorple`,
`blorple 8`.

### 5.8 Lava fragment, compass-rose maze (mind cube)
Light Room `w` → Volcano Base: entering queues I-ROCK-ARRIVES 2 → "One fragment of
molten lava explodes out of the flow and drops right at your feet!" (c3.zil:1148-1177).
`tinsot fragment` (retry) → "cool enough to touch", `take fragment` (the green rock's
food — NOT the opal; the idol's opal eye is a red herring that shatters). `take 4`,
`blorple 4` → Changing Room, `n` → Bare Room (NO exits — blorple is the only way out),
`take compass rose` (+10, MAGICBIT), `blorple 4`, `w` → Carving Room.
`put rose in carving` → octagonal hole opens north; all arms reset to silver, north
arm turns lead (COMPASS-CARVING-F c4.zil:870-907). `take rose`, `n` → MAZE-9.
In each octagonal room: `touch <dir> rune with rose` opens a hole if that wall's rune
is silver (real passage) AND that arm of the rose is still silver — each arm is
one-use until re-seated in the carving (MAZE-F c4.zil:1326-1409). Route:
`touch nw rune with rose`, `nw` (→MAZE-5); `touch w rune with rose`, `w` (→MAZE-4);
`touch ne rune with rose`, `ne` (→MAZE-2); `rezrov alabaster` (the plug; the west
rune here is gold, MAZE-2-DOOR-F c4.zil:1152-1185), `w` → MAZE-1 (all-lead walls —
a one-way trap: without blorple+book+a cube you are stuck forever). `take cube`
(MIND-CUBE, +25), `write "9" on cube`, stow cube 4, `learn blorple`, `blorple 9`.

### 5.9 The Plain: green/brown rocks (dark cube) — ADAPTIVE, RANDOM
No Place `s` → Plain. Casting anything but blorple here fails harmlessly
(PLAIN-SPELL-FAIL c4.zil:60-70). `give fragment to rock` → "Mmm. That looks good."
(ROCK-F c4.zil:302-311), `sit on rock`.
Grid: 4×4, loc = 4*row+col, valid 1..15 (no loc 0). Green rock starts at 5=(1,1),
brown (with the DARK-CUBE on its back) at 7=(1,3) (c4.zil:74-76; reset to 5/5 on
entry, PLAIN-ROOM-F c4.zil:53-55). Command `rock, <dir>`; green moves N/S/E/W
(edge-limited, ROCK-WALK c4.zil:334-378) plus the unique diagonal 1<->4
(NE from 4, SW from 1). After every green move the brown rock flees per I-OTHER-ROCK
(interrupts.zil:1231-1352) and its move is PRINTED ("The brown eyed rock slides
gracefully <dir>."). **You capture by moving the green rock ONTO the brown rock's
square** (or when the brown is forced onto yours): "The brown eyed rock, mesmerized by
the looming presence of the green eyed rock, does not move." Then `jump on brown rock`,
`take cube` (+25), `write "10" on cube`.
Brown's exact flee automaton (for the replayer's simulator) — with R=green (row,col),
O=brown, evaluated top-down; PROB 50 marks true RNG branches:
1. O==R → mesmerized (caught).
2. O=loc1: if R∉{4,5,8} and (Δrow+Δcol) even → SW(→4); elif R≠5 → S; elif R≠2 → E.
3. O=loc4: if R∉{1,2,5} and even → NE(→1); elif R≠5 → E; elif R≠8 → S.
4. O=5 and R∈{1,4}: R=4→E else S.
5. same row: row0 or (row1,col0) → S; row3 → N; else PROB50 N/S.
6. same col: col0 or (col1,row0) → E; col3 → W; else PROB50 W/E.
7. corner (3,0): PROB50 E/N; corner (3,3): PROB50 W/N; corner (0,3): PROB50 W/S.
8. R below → N (if legal); R right → W (if legal); R above → S; R left → E;
   final fallback → SW.
Winning strategy [verified, catches in ~5-15 moves]: track both positions exactly
(update brown from the printed direction), and pick the green move maximizing capture
probability by expectimax over this automaton (iterative deepening, prefer the
SHALLOWEST forced win — a fixed-depth search oscillates forever). Captures come from
corner PROB-50 mistakes and the forced-adjacency traps around locs 1/4.
This is a VARIABLE section: exact commands differ per seed.

### 5.10 The dark dimension (fire cube)
Nap checkpoint, then in Dark Cave (Dark Room `d`): stow every cube EXCEPT "10" plus
the rose in the zipper, learn snavig + blorple, `close zipper` (the frotzed bottle
inside must not leak light), **`drop burin`** (your only open light source; carrying
ANY light into the grue cave = "grues notice" death; being LIT yourself from `frotz me`
= instant fried-grue death, GRUE-F globals.zil:686-688). `d` → Grue Cave in darkness:
I-GRUES-NOTICE 2 queued (GRUE-CAVE-F c3.zil:1452-1461) — **snavig grue must succeed on
the very next turn**; with ~10 cubes held (zipper counts) + the dark cube P≥100 ⇒
deterministic [verified]. `snavig grue` ("You feel yourself changing in a very
unpleasant way..."), `d` → Light Pool (as a grue the light burns: I-FRIED-GRUE 2 —
get out of the pool fast), `climb on pillar`, `take cube` (FIRE-CUBE, +25), then wait
~7 turns on the pillar for "You have become yourself again" (grues can't cast:
PRE-CAST magic.zil:554-558). `blorple 10` → Dark Room, `d`, `take all` (burin back),
`open zipper`, `write "11" on cube`, `learn blorple`, `blorple 11` (blorple works in
Dark Cave — it has no CUBE property).

## 6. The gold box: exact ZIL mechanics [verified]

MAGIC-BOX (c1.zil:1691-1767): a box that fits EXACTLY ONE cube (only objects with a
NAME slot are accepted: "Strangely, you can't fit it in." for everything else).
Global MAGIC-BOX-CUBE (starts = WATER-CUBE, misc.zil:298) is set whenever a DIFFERENT
cube is inserted ("...the decorations on the box change subtly. They now depict
<TEXT of that cube>"). Taking the cube back OUT does NOT reset it — the box stays
attuned to the LAST cube inserted.
MAGIC-BOX-EXIT (c1.zil:1700-1716): every cube-interior room has one spare exit
"PER MAGIC-BOX-EXIT" (see table §4). That exit works iff (a) the box currently sits
in a real room that is NOT the Emporium and NOT itself a cube interior, and (b) you
are inside the cube the box is attuned to. It leads to the box's location.
So the box is a one-way portal: attune box to cube X, leave/throw the box somewhere
unreachable, blorple into X, walk out of the spare exit — you emerge at the box.
The famous use — the volcano outcropping (OUTCROPPING-ROOM c3.zil:1224-1276):
Fire Room `n` → Volcano vent; the MAGIC-CUBE sits on an outcropping 20 feet out in
the lava. `take box` (from zipper), `put 10 in box` (figures become grues; in the
vault this action would count as a spell! InvisiClues + USE-SPELL path),
`take 10` (back out — attunement stays), `throw box at outcropping` (THROW-ONTO
c3.zil:1321-1334: "bounces on the outcropping and ends up perched..."), stow cube 11,
`learn blorple`, `blorple 10` → Dark Room, `u` (the box exit) → Outcropping.
`take box`, stow it, then `take cube` → **+25 and the power blast** ("You feel more
powerful... The very stuff of magic crackles from your fingertips") = the MAGIC-CUBE
god-mode of §2. `write "12" on cube`, stow burin, `take 7`, `learn blorple`,
`blorple 7` → String Room, `s` → Enchanters' Retreat.
(The box also anchors DEATH-ROOM W, MIND-ROOM W, MAGIC-ROOM S etc. — any cube room
can use it; only this one is required.)

## 6.5 Belboz — RANDOM question, must be parsed [VARIABLE]

`ask belboz about me` → Belboz asks ONE question chosen by `RANDOM 6`
(BELBOZ-F globals.zil:826-853). Answer with `answer <name>`:

| question contains | answer |
|---|---|
| "hardest trick is making it look easy" | barsap |
| "invented the golmac spell" | barbel |
| "wrote of the Coconut of Quendor" | gustar |
| "famed for his skill with fireworks" (Borphee) | dimithio |
| "skill at Double Fanucci" | forburn |
| "Of the necromancers ... best-known" | berknip |

Correct → +25, "Good! I knew it was you all along," and he hands over the WROUGHT IRON
KEY (ANSWER-BELBOZ globals.zil:971-995). A recognized-but-WRONG name also gives +25
and the key — but sets FAKE-KEY: the key later dissolves at the past cabinet and
Belboz entombs you (FORLORN-ENCYSTMENT, DEATHS=3 ⇒ terminal; CABINET-F
c2.zil:1013-1020, globals.zil:997-1003). An unrecognized answer, attacking him, or
taking things from him = immediate encystment. Asking about cube/shadow is optional
flavor. This is the same class of runtime-parse VARIABLE as Sorcerer's journal code.

## 7. THE VAULT / WEIGHING PUZZLE [verified across 20 seeds]

Getting in: `blorple 9` (No Place) → `e` → Inner Vault ("Something begins to break
through the nothing", SCALES-ROOM-EXIT c3.zil:1606-1610). Prep INSIDE the Inner
Vault: stow cube 9 and the key in the zipper (hands: book + zipper + cube 12 ONLY),
learn jindak ×3 + blorple ×2 (magic cube ⇒ learns can't fail), then
`rezrov steel door` — the vault door opens ONLY with the magic cube held
(VAULT-DOOR-F c3.zil:1684-1716; "The mechanisms whirr madly... swings ponderously
open"). Do NOT touch the treasure (it turns to junk / triggers alarm paths,
MAKE-JUNK c3.zil:1942-1948). `n` → Outer Vault; the steel door slams behind you.

State on every entry (SCALES-ROOM-F M-ENTER, c3.zil:1836-1855 + JUGGLE-CUBES
c3.zil:1894-1916): the 12 vault cubes (CUBE-1..CUBE-11 + the real TIME-CUBE) are
SHUFFLED (PICK-ONE ×12 + PROB 50 splits) into two piles of six, and the pre-baked
labels "x1".."x12" (P-QBUF, parser.zil:695-721) are assigned POSITIONALLY:
**x1..x6 = first pile, x7..x12 = second pile, always.** Which label the real cube
wears is therefore uniform-random per entry — [verified: 20 runs produced x1, x4,
x5, x6, x8, x9, x10, x11, x12...]. Also rolled per entry: REAL-VALUE/FAKE-VALUE =
3/2 or 2/3 with PROB 50 (c3.zil:1849-1855) — i.e. whether the real cube glows
BRIGHTER or DIMMER than fakes is also random.

Measurement: `jindak` (no object). In this room it MEASUREs the two piles (raw sum of
values; fakes count FAKE-VALUE, the real cube REAL-VALUE, any other magic item +1 —
keep piles at EQUAL CUBE COUNTS or the comparison is meaningless; MEASURE
c3.zil:1971-1983, V-JINDAK magic.zil:972-1001). Possible reports [exact texts]:
- "Both piles of cubes glow with a faint blue glow. Both piles seem to glow with identical brightness."
- "However, the first pile is glowing more brightly."
- "However, the second pile is glowing more brightly."

Budget: every spell cast in this room increments SPELLS-USED; when it exceeds 2 the
alarm fairy appears (USE-SPELL magic.zil:617-625) — so **exactly 3 jindaks**, and the
3rd starts the clock: I-GUARDS 2 → warning at +1, at +2 the guards burst in and kill
you if still inside (I-ALARM/I-GUARDS interrupts.zil:1186-1226). After the 3rd jindak
you have exactly enough for `take <label>` then `blorple <label>`. Also: `save` is
blocked in this room (c3.zil:1833-1835); putting a cube in the gold box here counts
as a spell; rezrov/malyon on the doors from inside sets SPELLS-USED=2 instantly
(PRE-CAST magic.zil:596-600). Moving cubes between piles/zipper costs no spells and
has no turn limit before the 3rd jindak.

Blorpling the real cube requires USED-JINDAK? (set by any jindak this visit) — an
un-verified time cube blorples to the Nondescript Room like a fake (V-BLORPLE
magic.zil:830-833). Blorpling the right cube = +25 (CUBES-TO-PILES c3.zil:1883-1889)
and → Sand Room; the Treasury is then permanently guard-locked (re-entry = death).
Blorpling a fake = Nondescript Room, cubes re-pile, you may re-enter (fresh shuffle)
unless the guards have been triggered.

**Decision tree (12-coin, unknown bias, 3 weighings) — hold ≤1 loose cube at any
moment, park spares in the open zipper [this exact procedure verified]:**

W1: `take x1`,`put x1 in zipper`, same for x2, x7, x8. `jindak`.
    Piles now {x3..x6} vs {x9..x12}. Note result R1.
CASE R1 = identical:
  real ∈ {x1,x2,x7,x8}. Park x3,x4 in zipper; put x1,x2 on FIRST pile
  (P1={x1,x2,x5,x6}). `jindak` (R2).
  - R2 identical: real ∈ {x7,x8}. Put x7 on first pile, park x1 (P1={x7,x2,x5,x6}).
    `jindak` (R3): identical → **x8** (in zipper); unequal → **x7** (on pile 1).
  - R2 unequal: real ∈ {x1,x2}. Put x7 on first pile, park x1 (P1={x7,x2,x5,x6}).
    `jindak` (R3): identical → **x1** (in zipper); unequal → **x2** (on pile 1).
CASE R1 = unequal (remember direction D1 = which pile was brighter):
  real ∈ {x3,x4,x5,x6} ∪ {x9..x12}. Rearrange to P1={x3,x4,x5,x9},
  P2={x6,x1,x2,x7} (take x9→first pile, x6→second pile, x1,x2,x7→second pile),
  park x8,x10,x11,x12 in zipper. `jindak` (R2).
  - R2 identical: real ∈ {x10,x11,x12}, bias known: BRIGHT iff D1 was pile 2.
    Put x10 on first, x11 on second (5v5 is fine — equal counts). `jindak` (R3):
    identical → **x12** (zipper); pile1-brighter → **x10** if bright else **x11**;
    pile2-brighter → **x11** if bright else **x10**.
  - R2 same direction as D1: real ∈ {x3,x4,x5}, bias BRIGHT iff D1 was pile 1.
    Park x3 and x6; move x4 to second pile; put x10 and x8 (known good) on first
    pile → P1={x5,x9,x10,x8}, P2={x1,x2,x7,x4}. `jindak` (R3):
    identical → **x3** (zipper); result in the bias direction on pile 1 → **x5**;
    otherwise → **x4**.
  - R2 opposite direction from D1: real ∈ {x6 (now pile 2), x9 (pile 1)}.
    Park x9; put x8 on first pile → P1={x3,x4,x5,x8} all good. `jindak` (R3):
    identical → **x9** (zipper); unequal → **x6**.
Finally: `take <answer>` (turn 1 after alarm), `blorple <answer>` (turn 2) → Sand Room.
**Record the answer label — it is the TIME CUBE's name for the rest of the game**
(the replayer must carry this as a runtime variable, like Sorcerer's journal code).

## 8. The past (time cube interior) and the two paradox checks

The Sand Room (inside the time cube) leads DOWN to the PAST Dungeon Cell and UP to
the PAST Ruins Room — the same locations you visited ~400 years later.

PAST CELL (c4.zil:1660-1749): stow the time cube; `take key` (from zipper),
`unlock cabinet with key` (FAKE-KEY = death here), `open cabinet`,
`take vellum scroll` (+10; BLANK-SCROLL starts in PAST-CABINET, magic.zil:1294-1301),
learn blorple ×4 (last chance — the book is about to be abandoned; magic-cube
unlimited learning), `put book in cabinet`, `close cabinet`, `lock cabinet with key`,
stow the key, take the time cube back, `rezrov door` (needs magic cube; queues
I-PRISON-GUARDS 2 — **1-turn window**), `blorple <time-label>` → Sand Room.
LEAVE CHECK (PAST-CELL-EAST-F M-LEAVE, c4.zil:1673-1700): +25 iff cabinet NOT
rezrov-burst, LOCKED, contains ONLY the spell book, the cell door is OPEN, and the
cabinet is the only object in the room. Anything else → time-sickness death with
DEATHS=3 (terminal). Walking out the door = guards kill you. Entering when the book
is already in the cabinet (i.e., re-entry) = instant death (paradox, c4.zil:1698-1700).
This is why rezroving the PAST cabinet (vs the present one) is an unwinnable trap:
its lock "has been burst" and can never satisfy the check.

PAST RUINS (c4.zil:1537-1607): on entry the GIRGOL-SCROLL is (re)created inside the
SACK (c4.zil:1567-1569 — this is how the scroll you burned at the avalanche exists
again: the loop is engineered by the room) and I-WATER-RISING 3 starts (flag +1 every
4 turns; at 2 the floor floods and floor items are soaked; at 4 you're waist deep;
next tick = hypothermia death, interrupts.zil:1370-1387). Girgol memorized would pause
it — you don't have girgol; just be quick (~10 command budget, comfortable):
`open sack`, `take flimsy scroll`, `take burin` (from zipper),
`copy flimsy scroll to vellum scroll` → "Copied." — **requires the burin in hand AND
the magic cube held** (girgol is copyable only with the cube: BLANK-SCROLL-F
magic.zil:1319-1324). The COPY swaps physically: the ORIGINAL girgol spell moves onto
the vellum (which you keep) and the "copy" stays on the flimsy scroll
(magic.zil:1325-1339). Then `empty zipper into sack`, `put flimsy scroll in zipper`,
`close zipper`, `drop zipper`, `take sack`, `blorple 12`.
LEAVE CHECK (c4.zil:1571-1594): +25 iff the room contains ONLY the zipper and the
zipper contains ONLY the flimsy scroll and is CLOSED. Otherwise: time-sick death,
DEATHS=3, terminal. (That zipper+scroll is exactly what your past self finds in §5.2.)

## 9. Endgame: the Castle [verified, including the losing branch]

`blorple 12` → Magic Room; `e` → Castle — the door admits you only with ALL 13 cubes
GOT? (held directly, in your held sack/zipper, in the castle, or as blorple-object;
MAGIC-DOOR-EXIT + GOT?/COUNT-CUBES c4.zil:1477-1498).
On entry: "Mocking laughter echoes around you." I-SHADOW-ARRIVES 2, then I-SHADOW −1
runs a 10-beat script (interrupts.zil:190-356), one beat per turn-end:
1 thanks / 2 hypercube + its 4 cubes appear / 3 reveals it is your shadow /
4 monologue + **"Now for a small precaution." — freezes you** (FROZEN?=5; you thaw one
stage per turn only because you hold the magic cube, I-UNFREEZE interrupts.zil:420-444)
+ takes the earth cube / 5 air+fire+water (square of light) / 6 life+death+light+dark /
7 all remaining but the magic cube + its own four / 8 compresses cube-in-cube — the
tesseract tumbles / 9 removes any "detritus" from the hypercube, **takes the magic
cube from you and thrusts it into the center: "Chortling gleefully, it prepares to
jump into the hypercube!"** / 10 back-flips in — WIN/LOSS evaluated.

The knife trick [both walkthroughs, mechanism verified]: on move ~4 after entering
(before the shadow's own freeze at beat 4), `take knife` (from the sack) — ANY take
with the shadow present triggers FREEZES-YOU early (CASTLE-F c1/guild.zil:631-654),
and the beat-4 freeze then SKIPS (already frozen, FREEZES-YOU precaution branch,
interrupts.zil:380-384). Your 5-stage thaw completes a turn sooner — WITHOUT it the
thaw ends exactly one turn late and the girgol attempt fizzles into a re-freeze =
guaranteed loss [verified both ways]. Route: `e`, `z`, `z`, `z`, `take knife`, then
`z` until "prepares to jump into the hypercube!".
During beats 5-7, any verb besides wait/look/examine gets you re-frozen
(SHADOW-F guild.zil:553-562) — only `z`.

**CRITICAL 3-turn window** (girgol holds only 3 turns here, magic.zil:958-962):
1. `girgol` — cast from the VELLUM scroll in hand ("As you cast the spell, the vellum
   scroll vanishes! The shadow freezes in mid-leap!"). Girgol-from-scroll at the
   Castle is deterministic (SPELL-PROB? magic.zil:666-673). Memorized girgol is
   impossible (never in your book).
2. `take 12` — special-cased: "You tug and pull at the cube... you free it!"
   (CASTLE-F beat-9 branch; a multi-object take breaks the spell = loss).
3. `put sack in hypercube` — works only while frozen and only if the hypercube is
   EMPTY ("You push the sack into the hypercube, where it hangs unsupported.").
4. `z` — time resumes; beat 10: the shadow leaps in.
Outcome logic (I-SHADOW beat 10, interrupts.zil:313-356): magic cube still inside →
shadow wins, SCORE=−99. Hypercube EMPTY → "you, it and all the world blink out"
(WON?=1, −99). Contains a MAGIC item (MAGICBIT/SCROLLBIT/any cube) → "Everything will
be as it was!" then world-ends (WON?=2, −99). Contains a NON-magic object (the burlap
SACK — its contents are not checked) → **WON?=3: "You've destroyed magic itself!" ...
the hypercube vanishes with a pop ... "A new age begins today," says Belboz —
SCORE set to 600, FINISH.**
Also: blorple is dead at the Castle after beat 8 (magic.zil:646-649) — no escape;
girgol cast too early (beat ≤7) is word-of-power-cancelled or wasted; sleeping/espnis
at the castle = −99 (V-SLEEP verbs.zil:1250-1257).

## 10. Randomness inventory (ranked by replay risk)

1. **Spell fizzles — SPELL-PROB? (magic.zil:638-701).** Every cast of a learned spell
   except blorple rolls PROB P unless P≥100. P = base 50 (gnusto/frotz 75) + 5 per
   GOT? cube + 20 per spell-specific booster cube (pairs at magic.zil:650-691: e.g.
   caskly: change+connectivity; tinsot: water+fire; snavig: change+dark; jindak:
   light+connectivity; liskon/rezrov/gnusto: change+earth; throck: life+water;
   espnis: mind+death; malyon: fire+life; lesoch: air+fire; yomin: mind+light).
   A fizzle prints "The casting feels wrong, and sure enough, <PICK-ONE FIZZLES>"
   (2 RNG draws) and CONSUMES the memorization. With the magic cube held everything
   except girgol is deterministic (magic.zil:639-641); girgol-from-scroll is
   deterministic. Replay handling: success-text retry loops (relearn + recast) on
   EVERY fizzle-able cast; carry cubes (zipper counts) to push P to 100 at the
   critical one-shot casts (snavig grue MUST be P≥100).
2. **The roc fall (interrupts.zil:1103-1130).** First fall from Packed Earth:
   ROC-PROB 25 start ⇒ catch guaranteed ≤3 rolls, but the catch TURN varies (sync on
   "releases you"). Any REPEAT fall (after a death) starts ROC-PROB at 0: ≈9.4%
   chance of smash-death per attempt. Replay: z-loop; on "tumble helplessly...fatal"
   → Boneyard recovery (n, relearn blorple, blorple 1, d, retry) — budget §11.
3. **Vault shuffle + bias (c3.zil:1849-1916).** Position of the real cube among
   x1..x12 AND brighter/dimmer bias re-rolled every entry. MUST be solved adaptively
   by the §7 decision tree, parsing the three jindak report strings. ~15 RNG draws.
4. **Brown rock chase (interrupts.zil:1231-1352).** PROB 50 branches in the flee
   automaton; solved adaptively (§5.9) by parsing the printed flee directions.
5. **Belboz's question (globals.zil:848).** RANDOM 6; parse and answer (§6.5 table).
   Wrong-but-recognized answers are delayed unwinnability — never guess.
6. **Avalanche start (interrupts.zil:735-748).** SLIDE-PROB 10 +10/turn at Cliff Top;
   one draw per turn until it fires. Text-sync then 1-turn girgol window.
7. **Learn failures while tired (magic.zil:421-427).** PROB 5×AWAKE per learn.
   Handled by retry + nap checkpoints; eliminated after the magic cube.
8. Cosmetic/consumed-only draws that still SHIFT the RNG stream: ogre sneeze flavor
   PROB 50 (interrupts.zil:807/817), meadow rabbit PROB 20 once (c4.zil:575),
   sleep dreams PROB 50 + PICK-ONE (verbs.zil:1330-1335), refusal YUKS/FIZZLES
   PICK-ONE, shadow glimpse PROB 33 on `find figure` (guild.zil:491-496), flotsam
   PROB 75 (interrupts.zil:846-849), MIDAIR entry RANDOMs when arriving from
   LOST-IN-CLOUDS (c3.zil:976-990 — never go there), glacier walk PROB 75 death
   (c3.zil:79 — never walk there), bazaar sleep theft PROB 75 (verbs.zil:1339-1344),
   FORGET-SPELL random pick (magic.zil:469-484 — never over-learn).
   Values that must be PARSED at runtime (Sorcerer-journal-style): the vault jindak
   reports + resulting time-cube LABEL (used again for two later blorples), Belboz's
   question, the brown rock's printed moves, all sync texts.

## 11. Hard budgets and one-shots

- **Deaths: 3 maximum.** JIGS-UP (verbs.zil:2029-2060): the shadow revives you in the
  Boneyard with all possessions but ALL spells forgotten; the 4th death ends the game
  ("mocking laughter haunts you for eternity"). The three time-paradox deaths (past
  cell, past ruins ×2 variants) and Belboz encystment SET DEATHS=3 first — i.e. they
  are always terminal (c4.zil:1579,1604,1706; globals.zil:998).
- Girgol castings: exactly two exist — the flimsy scroll (avalanche) and the vellum
  copy (castle). The vellum takes ONE copy ever (ALREADY-USED, magic.zil:1311-1312).
  Wasting either = unwinnable.
- One-shot/one-chance items & windows: avalanche girgol (1 turn); idol yawn
  (~4-turn malyon life); ogre sneeze window (10 turns; total cave stay ≤12);
  guard-tower visits (4 commands); roc-nest 2nd visit (4 commands);
  ocean-floor surfacing (2 commands); grue-cave transformation (1 turn);
  vault post-alarm (take+blorple in 2 turns); past-cell exit (1 turn);
  castle girgol window (3 turns).
- Unwinnable traps: connectivity cube eaten by the roc chick; air cube swallowed by a
  re-malyoned idol; any cube dropped in midair (DROP-IN-AIR removes it forever, the
  gold box uniquely survives to LOST-ON-LAND, c3.zil:1013-1023); rezroving the PAST
  cabinet; wrong-but-recognized Belboz answer; treasure theft (junk + guards); losing
  the book to water; being in MAZE-1/Bare Room without blorple; giving cubes to the
  shadow early (SHADOW-F guild.zil:520-525 — it keeps them, but they land in the
  castle so GOT? still counts them... don't).
- Carry budget: FUMBLE-NUMBER starts 8, −1 per I-TIRED firing, reset only by sleep,
  frozen forever once the magic cube suspends I-TIRED. Keep ≤5 direct-hand objects
  from midgame on; the endgame was verified with hands = {book/sack, zipper, 12, +2}.

## 12. Release-87 quirks and useful sync strings

- The vault cubes present as PRE-LABELLED "x1".."x12" (P-QBUF parser.zil:695-721) —
  in r87 you never label them yourself; labels are positional per shuffle
  (x1..x6 = pile 1). The "balance" is jindak-glow, not a physical scale; there are no
  "pan" commands. The three report strings in §7 are the complete outcome alphabet.
- `actions.zil` in the source dump is a stale MAGIC.ZIL draft with a different
  FORGET-SPELL — the build behavior follows magic.zil [verified by fizzle behavior].
- Blorple-inside-a-cube prints exactly "Nothing happens." — a cheap desync probe.
- The idol interrupt ordering (yawn before unmalyon on the same tick) is what makes
  the published malyon/z/espnis/z cadence work; do not add or remove waits.
- Useful SYNC strings (verbatim substrings, r87):
  opening cleesh: "slips quietly out the door" ; cloud gone: "gives up and dissipates" ;
  roc: "releases you" ; avalanche: "you will die!" ; frozen rocks: "no longer falling" ;
  hut: "begins to melt" ; weed: "spurt of explosive growth" ; liskon self: "squashed" ;
  snake: "tail tip slips out" ; idol: "begins to yawn" / "cheek-stretching yawn" ;
  carpet deal: "Done, then!" / "How silly of me!" ; flood: "icy cap" / "The oubliette
  is full" ; dive: "You change." / "become yourself again" / "pure, sweet air" ;
  grue: "changing in a very unpleasant way" ; magic cube: "blast of power" ;
  belboz: "Good! I knew it was you" ; vault: "identical brightness" / "first pile is
  glowing more brightly" / "second pile is glowing more brightly" ; copy: "Copied." ;
  castle: "prepares to jump into the hypercube!" / "freezes in mid-leap" ;
  victory: "A new age begins today" (SCORE forced to 600, interrupts.zil:350).
- Tiredness telltales to watch (I-TIRED ladder, TIRED-TELL): "beginning to tire",
  "feeling tired", "getting more and more tired", "worn out", "dead tired",
  "so tired you can barely concentrate", "moving on your last reserves of strength",
  "practically asleep", "so exhausted you can't stay awake any longer" (forced sleep).

## 13. Scoring (600)

SCORE-OBJECT (verbs.zil:1737-1746) on first touch: any real cube +25, any SCROLLBIT
+10, any other MAGICBIT +10. Event list:
- +15 blorple discovered (magic.zil:820-823)
- 13 cubes × 25 = +325 (time cube via c3.zil:1883-1889; magic cube via c3.zil:1238-1259)
- scrolls ×10: stained, flimsy, dirty, dusty, damp, white, moldy book, vellum = +80
- magic items ×10: zipper, gold box, blue carpet (c3.zil:350), compass rose = +40
- +15 caskly on the moldy book (DEAD-BOOK-SCORE, c2.zil:1076-1092)
- +25 Belboz's question answered (globals.zil:976-978)
- +25 past cell paradox satisfied (c4.zil:1690-1692)
- +25 past ruins paradox satisfied (RUINS-SCORE, c4.zil:1595-1608)
Subtotal 550; the win branch then FORCES `SCORE = 600` (interrupts.zil:350) — the
remaining 50 are the finale bonus. All losing ends force SCORE = −99
(interrupts.zil:355, verbs.zil:1251). Rank at 600: "Scientist".

## 14. Verified route summary

The companion file `spellbreaker_route.txt` is the exact command list that achieved
600/600 on 20/20 pinned seeds (530-561 moves; ~370 fixed commands plus adaptive
blocks). Its adaptive sections (marked VARIABLE) are: the vault decision tree, the
Belboz answer, the rock chase, and the retry/nap loops; everything else is a fixed
sequence.

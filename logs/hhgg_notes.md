# The Hitchhiker's Guide to the Galaxy — research notes (verified solve)

Target binary: `games/zcode/hhgg.z3` — Release 60 / Serial 861002, Z-machine V3,
score game, `vm.get_max_score()` = 400.

## Sources

* **Official ZIL source (AUTHORITY):** github.com/historicalsource/hitchhikersguide,
  branch `master` (Infocom internal codename "S4"). Its `COMPILED/s4.z3` header is
  version 3 / release 60 / serial 861002 — an exact match for our binary, so every
  file:line cited below corresponds to the shipped game. Local verbatim copies
  (gitignored): `logs/hhgg_source_zil_<name>.zil.txt` for earth/vogon/heart/unearth/
  globals/verbs/misc/parser/syntax/s4.
* **Walkthrough A:** IF Archive `solutions/Sols1.zip` — full prose walkthrough
  (start → Magrathea). Local: `logs/hhgg_source_walkthrough_sols1.txt`.
* **Walkthrough B (independent):** IF Archive `solutions/Sols3.zip` ("The Djin &
  The Ice-Queen", Apple II solution disks) — terse step list. Local:
  `logs/hhgg_source_walkthrough_sols3.txt`.
* **InvisiClues:** complete transcription of the original booklet (via the
  zedlopez/invisiclue repo, `HHGG.inv`). Local: `logs/hhgg_source_invisiclues.txt`.
* Everything was then machine-validated with the adaptive recorder
  (`scripts/solve_hhgg_adaptive.py`), which won 8/8 on interpreter seeds 1–8.

## Boot determinism

Two boots leave **byte-identical VM memory** (only the un-seeded Python RNG state
differs), so no `restart` prelude is needed: pin `w.vm.rng.seed(seed)` right after
`w.start()` and the whole game is deterministic per seed.

## The 400 points (every SETG SCORE site on the winning path)

| # | Event | Points | Running | ZIL |
|---|-------|--------|---------|-----|
| 1 | Swallow the buffered analgesic | +10 | 10 | earth.zil:435 |
| 2 | Drink beer ×3 as Arthur (5 each) | +15 | 25 | earth.zil:1909 |
| 3 | First entry to the Vogon Hold | +8 | 33 | vogon.zil:58 |
| 4 | Babel fish lands in your ear | +12 | 45 | vogon.zil:238 |
| 5 | ENJOY POETRY (needs the fish) | +15 | 60 | vogon.zil:773-774 |
| 6 | Glass case opens (typed word) | +25 | 85 | vogon.zil:477-479 |
| 7 | Engine-room 3rd LOOK reveals spare drive | +25 | 110 | heart.zil:1483-1489 |
| 8 | Take the Nutrimat/Computer Interface (lair) | +25 | 135 | unearth.zil:441 |
| 9 | Party completed (Phil leaves with Trillian) | +25 | 160 | heart.zil:1211 |
| 10 | Dais exit after rifles destroyed (Zaphod) | +25 | 185 | unearth.zil:1333 |
| 11 | First beer as Ford (FORD-POINT global = 15) | +15 | 200 | earth.zil:1858,1895 |
| 12 | Take the common-sense particle (synapse maze) | +25 | 225 | unearth.zil:718 |
| 13 | Sauna blooms the plant (pot + plant held) | +25 | 250 | heart.zil:990-991 |
| 14 | Drink the real tea | +100 | 350 | globals.zil:1393 |
| 15 | First entry to Marvin's Pantry | +25 | 375 | heart.zil:66-68 |
| 16 | Hand Marvin the required tool | +25 | 400 | heart.zil:247-248 |

Penalties avoided: eat the sandwich −30 (earth.zil:2023); drink the tea
substitute −30 and a second gulp is death (heart.zil:819-829); firing the spare
drive at the wrong moment −30 (heart.zil:1699); **entering the Pantry with score
< 300 is instant death** (`<L? ,SCORE 300> <JIGS-UP "In fact, a lethal dose.">`,
heart.zil:62-63) — hence tea (+100) before the Pantry.

Note: the only `SETG SCORE 200` in the source (verbs.zil:251) is inside the
commented-out debug verb `;<ROUTINE V-$CHEAT ...>` (verbs.zil:188) — not live code.

## Randomness inventory (what the pinned seed freezes)

1. **Glass-case password** — `<SETG LINE-NUMBER <RANDOM 6>>` and
   `<SETG WORD-NUMBER <RANDOM 3>>` at first Hold entry (vogon.zil:56-57).
   The case switch names the position ("first/second/third word from the second
   verse", vogon.zil:495-508). The second verse's first spoken line is LINE-A/B/C
   by LINE-NUMBER (I-CAPTAIN counter 7, vogon.zil:687-693, order table comment
   vogon.zil:726-732): A = "Fripping lyshus wimbgunts…", B = "Gashee morphousite,
   thou…", C = "Bleem miserable venchit!…". `V-TYPE` (verbs.zil:2032-2080)
   accepts exactly the right word **in quotes** (`type "wimbgunts"`); any other
   quoted input MUNGs the case = death. Seed 1: LINE-A first + word 3 → wimbgunts.
2. **Improbability-trip destinations** — DARK-F M-ENTER runs a PROB chain until a
   destination hits (globals.zil:801-841): HEART (100 after airlock/whale/dream
   deaths → Entry Bay), VOGON (100 first dark, then 10 = Hold-revisit bounces),
   TRAAL 60→10 (lair), TRILLIAN 15→25→10 (party), FORD 15→25→10 (country lane),
   ZAPHOD 0→25→10 (speedboat; only unlocked once TRAAL first hits, 813-817),
   FLEET 0→60→10 (war chamber; only unlocked by careless words), WHALE always 0
   ("Bug #60"). Scenario order is therefore seed-dependent, with instant
   dream-death "bounces" on revisits.
3. **Careless words** — a *failed* parse of a >3-word input after the Earth is
   demolished arms I-CARELESS-WORDS (misc.zil:405-410, and dangly-bit-in-tea also
   arms it, heart.zil:1815-1819), which sets `FLEET-PROB 60` (unearth.zil:456).
   A successful long command does NOT arm it — the input must fail (e.g.
   `put stone in satchel` with no stone in scope).
4. **Synapse maze** — every exit is blocked with PROB 40; an unblocked step bumps
   MAZE-COUNTER, and the particle is only present at counts 3/17/36
   (unearth.zil:675-686). Take it the same turn — it retreats on the next step.
5. **Controlled dark (whale)** — pushing the switch with the dangly bit in *real
   tea* sets DARK-CONTROLLED (heart.zil:1721-1723); each turn that falls through
   to the litany advances CURRENT-EXIT through DARK-EXIT-TABLE {HOLD, LANE,
   LIVING-ROOM, ENTRY-BAY, LAIR, SPEEDBOAT, **INSIDE-WHALE**, WAR-CHAMBER}
   (globals.zil:1036-1040) and MISSING? is always true. `feel darkness` answers
   "cold" on LIVING-ROOM and "warm" on INSIDE-WHALE (globals.zil:964-976);
   `taste liquid` while warm exits into the whale. This is the ONLY way into the
   whale (WHALE-PROB is permanently 0).
6. **Tree of Foreknowledge** — EAT FRUIT rerolls `<PICK-ONE ,TOOL-LIST>` while
   the pick is IN-HEART?, up to 50 draws (heart.zil:474-480); with all ten tools
   aboard the 51st draw stands and the vision names a tool you can actually hold.
   TOOL-LIST (globals.zil:1320-1331): screwdriver, wrench (toolbox), chisel
   (Pantry), awl (war chamber), pliers + rasp (engine room), tweezers (handbag),
   pincer (Bridge), chipper (lair), toothbrush. Marvin's own pick (I-MARVIN,
   heart.zil:280-284) deliberately rerolls **while you hold the pick** — the
   fruit pre-empts that gag by fixing TOOL-REQUIRED first.
7. Ambient consumers riding the stream: Marvin's PROB-8 wander (heart.zil:330),
   I-THING's `4+RANDOM(4)` returns of the Thing (earth.zil:391-409), the dark
   litany variant PROBs (globals.zil:1043-1054), Galley PROB-3 Zaphod cameo
   (heart.zil:514-522), sauna `MOVES += 10+RANDOM 12` (heart.zil:980),
   hors-d'oeuvre taste PROBs, screening-door PROB-50 quips.

## Timed events (queues/interrupts)

* I-GROGGY every turn from Hold entry; **death at counter 4** — eat the peanuts
  (vogon.zil:52,103-130).
* I-FORD 6 (Ford naps, drops satchel + Guide), I-ANNOUNCEMENT 18, I-GUARDS 36
  (vogon.zil:53-55); a caught babel fish accelerates the guards to 4
  (vogon.zil:240-245). I-CAPTAIN every turn: counters 1-5 = first verse (ENJOY
  POETRY window is counter ≥2 and <6, else airlocked unenjoyed), 7-9 = second
  verse, 11 = guards to airlock (vogon.zil:645-715). AIRLOCK-F: spaced on the
  4th airlock turn, rescued 29 s later, HEART-PROB←100 (vogon.zil:858-886).
* Eddie's Engine-Room gauntlet: five consecutive `s` from Aft End (sure? /
  absolutely? / fake-out / reconsider / enter).
* Bugblatter: towel-on-head only works with the Beast present and re-queues
  I-BEAST at 11 (earth.zil:1408-1419); carving (towel worn + name told) MUNGs
  the Beast and queues the Beasthunter dream-end at 9 (unearth.zil:131-139,
  315-334 — this also hands over the chipper). Removing the towel before the
  carve = death (earth.zil:1424-1442).
* Ford-on-Earth: I-VOGONS 38-turn limit (earth.zil:1538); `give towel to arthur`
  → answer `idiot` → `go to prosser` → `prosser, lie down`; `buy beer` then the
  first `drink beer` pays FORD-POINT; the second triggers the house crash;
  `give fluff to arthur` requires HOUSE-DEMOLISHED and sets FLUFF-TO-GOWN
  (earth.zil:2332-2338) — LEAVE-DARK later moves the satchel fluff into the gown
  (globals.zil:1095-1097).
* Speedboat: I-SPEEDBOAT crashes at BOAT-COUNTER 7 unless DESTINATION is the
  cliff/spire, whose CRASH-COUNTER 4 wakes the autopilot (unearth.zil:1060-1093).
  Dais: DAIS-COUNTER 4 brings Trillian + guards, I-GUARDS 8-turn fuse
  (unearth.zil:1387-1401, vogon.zil:572-575): `guards, drop the rifles`,
  `trillian, shoot the rifles`, then `e`.
* War chamber: I-DOG counts 13 turns; DOG-FED (the Act-1 sandwich) turns the
  fleet peaceful and beams you into the MAZE (earth.zil:1565-1592).
* **I-BRAIN-DEATH**: if the drive rolls WAR-CHAMBER again after the particle is
  taken, LEAVE-DARK materialises you "inside your own brain" and 6 turns later
  you die for real (globals.zil:1098-1113, 1206-1212). The route makes this
  impossible by arming careless words (and hence FLEET-PROB) only after the
  other four scenarios are done, and taking no uncontrolled trip after the war
  chamber.
* I-TEA: interface in Nutrimat + touch pad (tea cup sits in the PAD) →
  counters 1-6 = overload signs, 7 = **missiles launched**, death at 15
  (heart.zil:895-948). Push the generator switch (DRIVE-TO-PLOTTER +
  DRIVE-TO-CONTROLS + brownian source) while 6 < counter < 15 → missiles become
  the whale, tea lands in the slot, I-LANDING 24 (heart.zil:1654-1696).
* I-WHALE: 11 turns inside the whale, then SPLAT (unearth.zil:1544-1552) — the
  flowerpot survives only inside the Thing (verbs.zil:2713-2717).
* I-PLANT: sprout 10 turns after the 4th fluff is planted (heart.zil:396-398).
* I-MARVIN: after `marvin, open the hatch` (needs LANDED), Marvin reaches the
  Access Space in 12 turns; be there when he arrives and when he asks, or he
  huffs off permanently (MARVIN-COUNTER 3) (heart.zil:204-214, 268-300).
* Access Space admits at most ONE carried item (worn gown — emptied — and the
  babel fish are exempt; the gown's contents are counted!) (heart.zil:1856-1881).

## Tea / no tea

`take tea` drops "no tea"; `take no tea` while holding tea only works once the
common-sense particle is MUNGED (NO-TEA-F, globals.zil:1424-1434). The screening
door opens on OPEN/KNOCK iff tea is held AND no tea is held (heart.zil:136-143)
— no SHOW needed (showing just burns PROB-50 quips). Drink the tea after the
door opens and before stepping into the Pantry.

## Walker-specific notes

* GameWalker's blocked-move rollback would eat the next command on outputs like
  "The screening door is closed." — the route never walks into a closed door
  (`open door` precedes `w`), never walks west in the Vogon Hold ("locked (from
  the outside)"), and Eddie's refusals don't match the blocked patterns.
* Dream deaths ("Everything becomes... Dark") match none of replay_solve's
  DEATH_MARKERS; the transcript was scanned — zero marker hits.
* The final ramp turn prints the score directly and falls into the
  RESTART/RESTORE/QUIT prompt; one trailing `z` answers it harmlessly.

## Deliverables

* `scripts/solve_hhgg_adaptive.py` — adaptive recorder (8/8 wins on seeds 1-8).
* `walkthroughs/hhgg_verified_400.txt` — seed-1 recording, 466 commands.
* `solutions/hhgg_verified.json` — replay_solve output: VERIFIED 400/400 at
  seed 1, died=False, won=True (run twice, identical).

# Leather Goddesses of Phobos (Release 59 / Serial 860730, V3) — solve notes

Authority: official ZIL in `logs/lgop_zil/` (github.com/historicalsource/leathergoddesses).
The repo's `COMPILED/x1.z3` is byte-identical to `games/zcode/lgop.z3`, so the source is
exact for our build. Detailed line-by-line dump is in `logs/lgop_zil_analysis.md`.
Third-party walkthroughs (route skeletons only) in `logs/lgop_source_walkthrough1.txt`
(Gunness), `logs/lgop_source_walkthrough2.txt` (detailed male solution), and
`logs/lgop_source_invisiclues.txt` (Infocom InvisiClues incl. the point table).

## The scoring is RANDOMIZED — "316" is not fixed

`INCREMENT-SCORE BASE VAR` (globals.zil:31-38) adds `BASE + RANDOM(VAR)` (1..VAR) each
time. There are 17 scoring events; `INT-MAX` starts at 429 = Σ(BASE+VAR). After each
award `INT-MAX -= (BASE+VAR - CHANGE)`, so once all 17 are earned `INT-MAX == SCORE`, and
at the win `EXT-MAX` is set to `INT-MAX` (phobos.zil:1384) — the game always prints
"N out of N". So a *win* can total anywhere in **188..429** (Σbase+17 .. Σ(base+var)),
≈308 typical. `zwalker.get_max_score()` hard-codes 316 for this serial, and
`replay_solve` declares a win only when `vm.get_score() == 316`, so the solve must land
the random total on **exactly 316**.

### The 17 events (BASE VAR → range, file:line)  [Σbase=171, Σ(base+var)=429]
1. wake in cell — 1 7 (2-8) — earth.zil:516
2. kiss frog → blender — 17 17 (18-34) — mars.zil:414
3. take mouse (frozen, <11 items) — 14 9 (15-23) — mars.zil:582
4. give coin to Donald-Dock proprietor → exit tube — 5 12 (6-17) — mars.zil:1749
5. answer Sultan riddle ("riddle") — 8 11 (9-19) — mars.zil:2364
6. take Cleveland phone book (catacombs directory) — 13 26 (14-39) — mars.zil:3106
7. take raft (catacombs) — 8 3 (9-11) — mars.zil:3264
8. enter Icy Dock un-radiated — 4 14 (5-18) — mars.zil:3628
9. take cotton balls (igloo) — 16 29 (17-45) — mars.zil:4168
10. give Thorbast his sword → suicide — 5 15 (6-20) — spaceship.zil:729
11. photo from Elysia (Space Yacht) — 17 13 (18-30) — spaceship.zil:947
12. flytrap trapped **or** hissed (one event) — 2 15 (3-17) — venus.zil:171 / verbs.zil:1205
13. un-angling cream on Theta → 82° angle — 16 10 (17-26) — venus.zil:252
14. give flashlight to salesman → TEE remover — 3 7 (4-10) — venus.zil:555
15. power switch → back in own body — 19 24 (20-43) — venus.zil:985
16. headlight (ceiling collapse w/ Trent) — 14 33 (15-47) — cleveland.zil:657
17. Plaza arrival (dumped from Boudoir) — 9 13 (10-22) — phobos.zil:1093
Rank hits Interplanetary Emperor (RANK 9) at the win (phobos.zil:1383).

## How we make it reproducible AND hit 316 exactly: `#RANDOM <k>`

The debug verb `#RANDOM <n>` (syntax.zil:89 → V-$RANDOM verbs.zil:298) calls
`RANDOM(-n)`, which in zwalker (`zmachine.py` op 0x07) does `rng.seed(n)`. Issued as the
first real turn it **reseeds the interpreter PRNG deterministically, overriding whatever
seed replay_solve pinned**, and it is turn-free (verified: turns stay 0). So the whole run
becomes a pure function of `k`; a walkthrough that begins `look / #random k / ...` verifies
identically at every replay_solve seed. We sweep `k` until the 17 random awards sum to 316.
(Use k>0; `#random 0` → RANDOM(0) → `rng.seed(None)` = non-deterministic — avoid.)

## Per-run randomness the recorder adapts to
- **Wife number** = 100+RANDOM(8270), rolled on first entry to Among the Dunes
  (mars.zil:1431-1439). The coded message prints it Caesar+3 and DIGIT-REVERSED
  (REVERSE-NUMBER, mars.zil:1524). We read the message, strip the digits, reverse them,
  and feed the number to the harem guard and the "NNNN, kiss my kneecaps" line. A wrong
  number yields no map/torch → no win, so it MUST come from this run.
- **Thorbast duel** (spaceship.zil:509-620): disarm is PROB(DISARM-PROB), +12%/attack.
  Attack until "knocking the sword out of", then take his sword and give it back
  (he impales himself, +pts). Bounded by a ≤24-turn fatigue clock and an ~11-turn monster
  (BEM) clock; if the monster carries the woman off first there is no photo → that k is a
  desync and skipped.
- **Spaceship exit circle** (HOLE-F globals.zil:1259) drops you at a RANDOM Mars room:
  My Kind of Dock (60%), Oasis (16%), or Ruined Castle 2 (24%). My Kind of Dock is in the
  palace and CANNOT reach the Throne Room by land (the raft only drifts downstream), so
  those k are skipped. From Oasis: w,nw,w,n,n. From Ruined Castle 2: w,n,n.

## Key mechanics / gotchas confirmed empirically
- Gender = male (enter NW = Gents' in Joe's Bar); cosmetic, no score difference. Default
  naughtiness is SUGGESTIVE; no puzzle needs another mode (frog/gorilla scenes score in any
  mode — the gorilla kiss even prints a "we normally wouldn't allow this in TAME mode" line).
- Must relieve yourself in a restroom by ~turn 5 or you are captured wrong and lose
  (I-URGE, earth.zil:425-467). Carry the stool at capture (robbed into the Cell with
  everything else, earth.zil ROB). Sequence: nw / wee / take stool / wait / wait → Cell.
- Wicker basket: reach it via "stand on trent" in the Closet (no stool needed).
- CCOUNT (direct inventory) is capped at 10 (verbs.zil:2731); stash into the basket/sack
  before "take can" / "take mouse" / "take baby". Trent's matchbook gift is turn-based and
  can arrive early, so we `put all in basket` before `take can`.
- Gorilla lab: chocolate into cage BEFORE the mind-transfer; as the gorilla, `kiss female`
  (makes the scientist leave immediately) then `eat food`, `bend bars`, exit, untie both
  bodies, `pull switch` (+pts back in own body).
- Flytrap: `hiss` kills it in one turn (verbs.zil:1205) — same event/points as the trellis
  trap, far simpler.
- Barge (mars.zil:722-800, I-CANAL 1160-1230, BARGE-DOCKS 1351): docks at BARGE-LOC-NUM
  ∈ {1,6,7,10,15} only while MOORING-ON. Position is a LOCAL turn count since leaving a
  dock, so a maneuver's docking is independent of global turns. "press orange" toggles
  mooring; to reach the next dock: press orange (leave), wait 1 (advance past origin),
  press orange (moor), then wait — it auto-docks and parks (extra waits are harmless).
  Ion-beam is at CANAL-LOC 31 (I-ION-DEATH, mars.zil:1188): send the barge EMPTY past it
  by pressing purple while you're on the RAFT (BARGE-FORGES-AHEAD, mars.zil:788), re-board
  via the Oriental Garden well (→ Well Bottom circle → barge at Icy Dock).
- Sultan: enter Audience Chamber (NE from Main Hall), `yes`, Trent guesses wrong (led
  away, rejoins later), then `say "riddle"` (+pts). Move W → guard, `say "<wife>"`, W →
  Harem, `wait` (veiled figure beckons → Inner Harem), `<wife>, kiss my kneecaps` → map,
  torch, catacombs open (down). Do NOT carry the map out via the harem (instant death,
  mars.zil INNER-HAREM-EXIT-F).
- Catacombs (mars.zil:2928+): CLAP ≤ every 6 / HOP ≤ every 10 / KWEEPA ≤ every 12 turns to
  avoid the beetles' random relocation; the fixed route (from the game's map) collects the
  phone-book "directory" and the raft, exits up to the Laundry Room.
- Endgame: land near/reach Throne Room; the dropped TEE-remover un-T's the "untangling
  cream" → "unangling", smear on Theta (the golden-haired 45° angle) → she gives the 82°
  angle. Raft from Royal Docks to Donald Dock; `buy exit` / give coin / `rake dust` → tube
  with a flexible circle → Boudoir → `search divan` / `wait` → Plaza. Give the 8 parts as
  Trent asks (PARTS-LIST phobos.zil:975: blender, rubber hose, cotton balls, 82° angle,
  headlight, mouse, photo, phone book); one `z` flushes the finale → win.

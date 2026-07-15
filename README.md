# ZWalker - Automated Z-Machine Walkthrough Generator

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**ZWalker** is an automated walkthrough generator for Z-machine interactive fiction games. It combines a CZECH-compliant Z-machine interpreter, AI-assisted solvers, and a deterministic replay harness to produce and verify game walkthroughs, primarily as regression tests for the [z2js](https://github.com/avwohl/z2js) compiler.

## 📚 Documentation

**[→ View Full Documentation & Game Index](https://avwohl.github.io/zwalker/)**

- [Verified Solves & AI Walkthroughs](https://avwohl.github.io/zwalker/WALKTHROUGHS.html)
- [100+ Game Sources with Download URLs](https://avwohl.github.io/zwalker/GAME_SOURCES.html)
- [Test Suite Results](https://avwohl.github.io/zwalker/#testing)

## Verified Results

The headline result is a corpus of **50 verified complete solves** spanning
Z-machine versions V1 through V8. It covers a large slice of the Infocom
catalogue — both Zork-era trilogies and Mini-Zork, the Planetfall series,
Trinity, A Mind Forever Voyaging, The Hitchhiker's Guide to the Galaxy,
Starcross, the three mysteries (Deadline, Suspect, Witness), Suspended,
Ballyhoo, Hollywood Hijinx, Cutthroats, Infidel, Plundered Hearts, Moonmist,
Leather Goddesses of Phobos, The Lurking Horror — alongside modern classics
(Photopia, Shade, Lost Pig, The Dreamhold) and IF-Comp games. Every game is
played start to finish and reproducibly won, verified by deterministic replay
against a fixed RNG seed:

| Game | Z-ver | Score | Won | Turns | Commands | Seed | Solution | Walkthrough |
|------|-------|-------|-----|-------|----------|------|----------|-------------|
| 9:05 | V5 | Win (unscored) | ✅ | 0 | 20 | 1 | [JSON](solutions/905_verified.json) | [Text](walkthroughs/905_verified_win.txt) |
| A Mind Forever Voyaging | V4 | Win (unscored) | ✅ | 0 | 623 | 1 | [JSON](solutions/amfv_verified.json) | [Text](walkthroughs/amfv_verified_win.txt) |
| Adventure (Colossal Cave) | V3 | 350/350 | ✅ | 290 | 289 | 3 | [JSON](solutions/advent_verified.json) | [Text](walkthroughs/advent_verified_350.txt) |
| Adventureland | V5 | 100/100 | ✅ | 146 | 146 | 3 | [JSON](solutions/adventureland_verified.json) | [Text](walkthroughs/adventureland_verified_100.txt) |
| All Quiet on the Library Front | V5 | Win (unscored) | ✅ | 1 | 37 | 1 | [JSON](solutions/library_verified.json) | [Text](walkthroughs/library_verified_win.txt) |
| All Roads | V5 | Win (unscored) | ✅ | 0 | 185 | 1 | [JSON](solutions/allroads_verified.json) | [Text](walkthroughs/allroads_verified_win.txt) |
| Balances | V5 | 51/51 | ✅ | 123 | 124 | 1 | [JSON](solutions/balances_verified.json) | [Text](walkthroughs/balances_verified_51.txt) |
| Ballyhoo | V3 | 200/200 | ✅ | 413 | 415 | 1 | [JSON](solutions/ballyhoo_verified.json) | [Text](walkthroughs/ballyhoo_verified_200.txt) |
| Castle Adventure! | V8 | Win (unscored) | ✅ | 67 | 277 | 1 | [JSON](solutions/castle_adventure_verified.json) | [Text](walkthroughs/castle_adventure_verified_win.txt) |
| Cloak of Darkness | V3 | Win (unscored) | ✅ | 4 | 5 | 1 | [JSON](solutions/cloak_verified.json) | [Text](walkthroughs/cloak_verified_win.txt) |
| Cold Iron | V8 | Win (unscored) | ✅ | 89 | 30 | 1 | [JSON](solutions/coldiron_verified.json) | [Text](walkthroughs/coldiron_verified_win.txt) |
| Cutthroats | V3 | 250/250 | ✅ | 416 (clock) | 264 | 1 | [JSON](solutions/cutthroats_verified.json) | [Text](walkthroughs/cutthroats_verified_250.txt) |
| Deadline | V3 | Win (unscored) | ✅ | 10 (clock) | 129 | 1 | [JSON](solutions/deadline_verified.json) | [Text](walkthroughs/deadline_verified_win.txt) |
| Deephome | V5 | Win (unscored) | ✅ | 11 | 315 | 1 | [JSON](solutions/deephome_verified.json) | [Text](walkthroughs/deephome_verified_300.txt) |
| Detective | V5 | 360/360 | ✅ | 45 | 45 | 1 | [JSON](solutions/detective_verified.json) | [Text](walkthroughs/detective_verified_360.txt) |
| Enchanter | V3 | 400/400 | ✅ | 300 | 206 | 1 | [JSON](solutions/enchanter_verified.json) | [Text](walkthroughs/enchanter_verified_400.txt) |
| Hollywood Hijinx | V3 | 150/150 | ✅ | 395 | 394 | 1 | [JSON](solutions/hollywood_verified.json) | [Text](walkthroughs/hollywood_verified_150.txt) |
| Infidel | V3 | 400/400 | ✅ | 305 | 306 | 1 | [JSON](solutions/infidel_verified.json) | [Text](walkthroughs/infidel_verified_400.txt) |
| Leather Goddesses of Phobos | V3 | Win (unscored) | ✅ | 395 | 373 | 1 | [JSON](solutions/lgop_verified.json) | [Text](walkthroughs/lgop_verified_win.txt) |
| Lost Pig | V8 | 7/7 | ✅ | 173 | 173 | 1 | [JSON](solutions/lostpig_verified.json) | [Text](walkthroughs/lostpig_verified_7.txt) |
| Mini-Zork I | V3 | 350/350 | ✅ | 440 | 405 | 1 | [JSON](solutions/minizork_verified.json) | [Text](walkthroughs/minizork_verified_350.txt) |
| Moonmist | V3 | Win (unscored) | ✅ | 26 | 86 | 1 | [JSON](solutions/moonmist_verified.json) | [Text](walkthroughs/moonmist_verified_win.txt) |
| Pentari | V5 | 70/70 | ✅ | 35 | 35 | 3 | [JSON](solutions/pentari_verified.json) | [Text](walkthroughs/pentari_verified_70.txt) |
| Photopia | V5 | Win (unscored) | ✅ | 80 | 110 | 1 | [JSON](solutions/photopia_verified.json) | [Text](walkthroughs/photopia_verified_win.txt) |
| Planetfall | V3 | 80/80 | ✅ | 5165 (GST) | 444 | 1 | [JSON](solutions/planetfall_verified.json) | [Text](walkthroughs/planetfall_verified_80.txt) |
| Plundered Hearts | V3 | 25/25 | ✅ | 192 | 186 | 1 | [JSON](solutions/plundered_verified.json) | [Text](walkthroughs/plundered_verified_25.txt) |
| Reverberations | V5 | Win (unscored) | ✅ | 4 | 72 | 1 | [JSON](solutions/reverb_verified.json) | [Text](walkthroughs/reverb_verified_50.txt) |
| Shade | V5 | Win (unscored) | ✅ | 124 | 126 | 1 | [JSON](solutions/shade_verified.json) | [Text](walkthroughs/shade_verified_win.txt) |
| Sorcerer | V3 | 400/400 | ✅ | 390 | 234 | 2 | [JSON](solutions/sorcerer_verified.json) | [Text](walkthroughs/sorcerer_verified_400.txt) |
| Spellbreaker | V3 | 600/600 | ✅ | 531 | 422 | 1 | [JSON](solutions/spellbreaker_verified.json) | [Text](walkthroughs/spellbreaker_verified_600.txt) |
| Starcross | V3 | 400/400 | ✅ | 265 | 240 | 1 | [JSON](solutions/starcross_verified.json) | [Text](walkthroughs/starcross_verified_400.txt) |
| Stationfall | V3 | 80/80 | ✅ | 5700 (GST) | 375 | 1 | [JSON](solutions/stationfall_verified.json) | [Text](walkthroughs/stationfall_verified_80.txt) |
| Suspect | V3 | Win (unscored) | ✅ | 29 (clock) | 110 | 1 | [JSON](solutions/suspect_verified.json) | [Text](walkthroughs/suspect_verified_win.txt) |
| Suspended | V3 | Win (unscored) | ✅ | 71 | 72 | 1 | [JSON](solutions/suspended_verified.json) | [Text](walkthroughs/suspended_verified_win.txt) |
| Suveh Nux | V5 | Win (unscored) | ✅ | 0 | 102 | 1 | [JSON](solutions/suveh_nux_verified.json) | [Text](walkthroughs/suveh_nux_verified_win.txt) |
| The Acorn Court | V5 | 30/30 | ✅ | 18 | 18 | 1 | [JSON](solutions/acorncourt_verified.json) | [Text](walkthroughs/acorncourt_verified_30.txt) |
| The Dreamhold | V8 | Win (unscored) | ✅ | 0 | 438 | 1 | [JSON](solutions/dreamhold_verified.json) | [Text](walkthroughs/dreamhold_verified_win.txt) |
| The Edifice | V5 | Win (unscored) | ✅ | 136 | 142 | 1 | [JSON](solutions/edifice_verified.json) | [Text](walkthroughs/edifice_verified_win.txt) |
| The Hitchhiker's Guide to the Galaxy | V3 | 400/400 | ✅ | 521 | 466 | 1 | [JSON](solutions/hhgg_verified.json) | [Text](walkthroughs/hhgg_verified_400.txt) |
| The Jewel of Knowledge | V5 | 90/90 | ✅ | 246 | 248 | 1 | [JSON](solutions/jewel_verified.json) | [Text](walkthroughs/jewel_verified_90.txt) |
| The Lurking Horror | V3 | 100/100 | ✅ | 310 | 306 | 1 | [JSON](solutions/lurking_verified.json) | [Text](walkthroughs/lurking_verified_100.txt) |
| The Witness | V3 | Win (unscored) | ✅ | 42 | 56 | 1 | [JSON](solutions/witness_verified.json) | [Text](walkthroughs/witness_verified_win.txt) |
| Theatre | V5 | 50/50 | ✅ | 295 | 357 | 1 | [JSON](solutions/theatre_verified.json) | [Text](walkthroughs/theatre_verified_50.txt) |
| Trinity | V4 | 100/100 | ✅ | 485 | 473 | 1 | [JSON](solutions/trinity_verified.json) | [Text](walkthroughs/trinity_verified_100.txt) |
| Wearing the Claw | V5 | Win (unscored) | ✅ | 159 | 160 | 1 | [JSON](solutions/wearing_the_claw_verified.json) | [Text](walkthroughs/wearing_the_claw_verified_win.txt) |
| Wishbringer | V3 | 100/100 | ✅ | 162 | 179 | 1 | [JSON](solutions/wishbringer_verified.json) | [Text](walkthroughs/wishbringer_verified_100.txt) |
| Zork I | V3 | 350/350 | ✅ | 499 | 431 | 3 | [JSON](solutions/zork1_verified.json) | [Text](walkthroughs/zork1_verified_350.txt) |
| Zork I (Release 5) | V1 | 350/350 | ✅ | 416 | 418 | 4 | [JSON](solutions/zork1-r5_verified.json) | [Text](walkthroughs/zork1-r5_verified_350.txt) |
| Zork II | V3 | 400/400 | ✅ | 416 | 386 | 2 | [JSON](solutions/zork2_verified.json) | [Text](walkthroughs/zork2_verified_400.txt) |
| Zork III | V3 | 7/7 | ✅ | 241 | 216 | 1 | [JSON](solutions/zork3_verified.json) | [Text](walkthroughs/zork3_verified_7.txt) |

Notes on the odd columns: Zork III scores "potential" out of 7; the win is
entering the Treasury of Zork and becoming the Dungeon Master. Planetfall's
and Stationfall's move counters are their in-game Galactic Standard Time
clocks, and the Cutthroats/Deadline/Suspect "clock" turns are their real-time
game clocks (the arrest in Deadline/Suspect happens at that hour). Wishbringer
and Cutthroats are V3 "time" games — the status line shows a clock, so the
interpreter reads their true score from the games' own globals (GSCORE,
RATING). Trinity is V4+, which has no status-line score convention at all,
so its SCORE/MOVES globals are mapped per build.

The `#% WIN_TEXT:` verification path (assert the game's true ending text
instead of a score) covers two kinds of "Win (unscored)" rows. Some games are
genuinely scoreless (9:05, Photopia, Shade, A Mind Forever Voyaging, The
Witness, Moonmist, Suspended, Wearing the Claw, ...). Others *are* internally
scored and their walkthroughs reach the documented maximum — Deephome 300/300,
Reverberations 50/50, All Quiet on the Library Front 30/30, Leather Goddesses
of Phobos (which deliberately randomizes its own score and prints "N out of
N") — but those particular builds keep the score in a global the interpreter
doesn't sample, so the run is verified by the ending text rather than the
number (the winning ending prints the real score, and the walkthrough header
documents it). A few games (Suveh Nux, The Dreamhold, 9:05) also show 0 turns
for the same reason: no move counter in the sampled global. Stationfall's and
Suspect's recordings open with a restart, which re-rolls the game's boot-time
clock on the pinned seed to make the run reproducible. Reproduce any of them
locally:

```bash
python3 scripts/replay_solve.py games/zcode/905.z5 walkthroughs/905_verified_win.txt --seeds 2
# -> 905_verified_win.txt: VERIFIED 0/None at seed 1 | 20 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/amfv.z4 walkthroughs/amfv_verified_win.txt --seeds 2
# -> amfv_verified_win.txt: VERIFIED -4134/None at seed 1 | 623 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/advent.z3 walkthroughs/advent_verified_350.txt --seeds 4
# -> advent_verified_350.txt: VERIFIED 350/350 at seed 3 | 289 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/adventureland.z5 walkthroughs/adventureland_verified_100.txt --seeds 4
# -> adventureland_verified_100.txt: VERIFIED 100/100 at seed 3 | 146 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/library.z5 walkthroughs/library_verified_win.txt --seeds 2
# -> library_verified_win.txt: VERIFIED 1/None at seed 1 | 37 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/allroads.z5 walkthroughs/allroads_verified_win.txt --seeds 2
# -> allroads_verified_win.txt: VERIFIED 36/None at seed 1 | 185 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/balances.z5 walkthroughs/balances_verified_51.txt --seeds 2
# -> balances_verified_51.txt: VERIFIED 51/51 at seed 1 | 124 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/ballyhoo.z3 walkthroughs/ballyhoo_verified_200.txt --seeds 2
# -> ballyhoo_verified_200.txt: VERIFIED 200/200 at seed 1 | 415 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/castle_adventure.z8 walkthroughs/castle_adventure_verified_win.txt --seeds 2
# -> castle_adventure_verified_win.txt: VERIFIED 0/None at seed 1 | 277 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/cloak.z3 walkthroughs/cloak_verified_win.txt --seeds 2
# -> cloak_verified_win.txt: VERIFIED 0/None at seed 1 | 5 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/coldiron.z8 walkthroughs/coldiron_verified_win.txt --seeds 2
# -> coldiron_verified_win.txt: VERIFIED 0/None at seed 1 | 30 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/cutthroats.z3 walkthroughs/cutthroats_verified_250.txt --seeds 2
# -> cutthroats_verified_250.txt: VERIFIED 250/250 at seed 1 | 264 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/deadline.z3 walkthroughs/deadline_verified_win.txt --seeds 2
# -> deadline_verified_win.txt: VERIFIED 13/None at seed 1 | 129 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/deephome.z5 walkthroughs/deephome_verified_300.txt --seeds 2
# -> deephome_verified_300.txt: VERIFIED 10/None at seed 1 | 315 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/detective.z5 walkthroughs/detective_verified_360.txt --seeds 2
# -> detective_verified_360.txt: VERIFIED 360/360 at seed 1 | 45 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/enchanter.z3 walkthroughs/enchanter_verified_400.txt --seeds 2
# -> enchanter_verified_400.txt: VERIFIED 400/400 at seed 1 | 206 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/hollywood.z3 walkthroughs/hollywood_verified_150.txt --seeds 2
# -> hollywood_verified_150.txt: VERIFIED 150/150 at seed 1 | 394 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/infidel.z3 walkthroughs/infidel_verified_400.txt --seeds 2
# -> infidel_verified_400.txt: VERIFIED 400/400 at seed 1 | 306 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/lgop.z3 walkthroughs/lgop_verified_win.txt --seeds 2
# -> lgop_verified_win.txt: VERIFIED 321/None at seed 1 | 373 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/lostpig.z8 walkthroughs/lostpig_verified_7.txt --seeds 2
# -> lostpig_verified_7.txt: VERIFIED 7/7 at seed 1 | 173 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/minizork.z3 walkthroughs/minizork_verified_350.txt --seeds 2
# -> minizork_verified_350.txt: VERIFIED 350/350 at seed 1 | 405 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/moonmist.z3 walkthroughs/moonmist_verified_win.txt --seeds 2
# -> moonmist_verified_win.txt: VERIFIED 21/None at seed 1 | 86 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/pentari.z5 walkthroughs/pentari_verified_70.txt --seeds 4
# -> pentari_verified_70.txt: VERIFIED 70/70 at seed 3 | 35 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/photopia.z5 walkthroughs/photopia_verified_win.txt --seeds 2
# -> photopia_verified_win.txt: VERIFIED 2/None at seed 1 | 110 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/planetfall.z3 walkthroughs/planetfall_verified_80.txt --seeds 2
# -> planetfall_verified_80.txt: VERIFIED 80/80 at seed 1 | 444 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/plundered.z3 walkthroughs/plundered_verified_25.txt --seeds 2
# -> plundered_verified_25.txt: VERIFIED 25/25 at seed 1 | 186 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/reverb.z5 walkthroughs/reverb_verified_50.txt --seeds 2
# -> reverb_verified_50.txt: VERIFIED 3/None at seed 1 | 72 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/shade.z5 walkthroughs/shade_verified_win.txt --seeds 2
# -> shade_verified_win.txt: VERIFIED 0/None at seed 1 | 126 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/sorcerer.z3 walkthroughs/sorcerer_verified_400.txt --seeds 3
# -> sorcerer_verified_400.txt: VERIFIED 400/400 at seed 2 | 234 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/spellbreaker.z3 walkthroughs/spellbreaker_verified_600.txt --seeds 2
# -> spellbreaker_verified_600.txt: VERIFIED 600/600 at seed 1 | 422 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/starcross.z3 walkthroughs/starcross_verified_400.txt --seeds 2
# -> starcross_verified_400.txt: VERIFIED 400/400 at seed 1 | 240 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/stationfall.z3 walkthroughs/stationfall_verified_80.txt --seeds 2
# -> stationfall_verified_80.txt: VERIFIED 80/80 at seed 1 | 375 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/suspect.z3 walkthroughs/suspect_verified_win.txt --seeds 2
# -> suspect_verified_win.txt: VERIFIED 23/None at seed 1 | 110 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/suspended.z3 walkthroughs/suspended_verified_win.txt --seeds 2
# -> suspended_verified_win.txt: VERIFIED 0/None at seed 1 | 72 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/suveh_nux.z5 walkthroughs/suveh_nux_verified_win.txt --seeds 2
# -> suveh_nux_verified_win.txt: VERIFIED 0/None at seed 1 | 102 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/acorncourt.z5 walkthroughs/acorncourt_verified_30.txt --seeds 2
# -> acorncourt_verified_30.txt: VERIFIED 30/30 at seed 1 | 18 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/dreamhold.z8 walkthroughs/dreamhold_verified_win.txt --seeds 2
# -> dreamhold_verified_win.txt: VERIFIED 0/None at seed 1 | 438 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/edifice.z5 walkthroughs/edifice_verified_win.txt --seeds 2
# -> edifice_verified_win.txt: VERIFIED 0/None at seed 1 | 142 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/hhgg.z3 walkthroughs/hhgg_verified_400.txt --seeds 2
# -> hhgg_verified_400.txt: VERIFIED 400/400 at seed 1 | 466 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/jewel.z5 walkthroughs/jewel_verified_90.txt --seeds 2
# -> jewel_verified_90.txt: VERIFIED 90/90 at seed 1 | 248 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/lurking.z3 walkthroughs/lurking_verified_100.txt --seeds 2
# -> lurking_verified_100.txt: VERIFIED 100/100 at seed 1 | 306 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/witness.z3 walkthroughs/witness_verified_win.txt --seeds 2
# -> witness_verified_win.txt: VERIFIED 0/None at seed 1 | 56 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/theatre.z5 walkthroughs/theatre_verified_50.txt --seeds 2
# -> theatre_verified_50.txt: VERIFIED 50/50 at seed 1 | 357 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/trinity.z4 walkthroughs/trinity_verified_100.txt --seeds 2
# -> trinity_verified_100.txt: VERIFIED 100/100 at seed 1 | 473 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/wearing_the_claw.z5 walkthroughs/wearing_the_claw_verified_win.txt --seeds 2
# -> wearing_the_claw_verified_win.txt: VERIFIED 0/None at seed 1 | 160 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/wishbringer.z3 walkthroughs/wishbringer_verified_100.txt --seeds 2
# -> wishbringer_verified_100.txt: VERIFIED 100/100 at seed 1 | 179 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/zork1.z3 walkthroughs/zork1_verified_350.txt --seeds 4
# -> zork1_verified_350.txt: VERIFIED 350/350 at seed 3 | 431 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/zork1-r5.z1 walkthroughs/zork1-r5_verified_350.txt --seeds 5
# -> zork1-r5_verified_350.txt: VERIFIED 350/350 at seed 4 | 418 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/zork2.z3 walkthroughs/zork2_verified_400.txt --seeds 3
# -> zork2_verified_400.txt: VERIFIED 400/400 at seed 2 | 386 cmds | died=False | won=True

python3 scripts/replay_solve.py games/zcode/zork_iii.z3 walkthroughs/zork3_verified_7.txt --seeds 2
# -> zork3_verified_7.txt: VERIFIED 7/7 at seed 1 | 216 cmds | died=False | won=True
```

Beyond the verified solves, the repo carries exploration-grade coverage data: 43 room-mapping
walkthrough dumps in `games/results/` and 73 batch solver runs in `solutions/`. These map
rooms and exercise the parser for compiler regression testing — they are **not** complete
solutions and are labeled accordingly.

## Features

- 🎮 **Z-Machine Interpreter**: 100% CZECH compliance — 1,604/1,604 tests passing
  across versions 3, 4, 5, and 8 (v3: 368, v4: 386, v5: 425, v8: 425)
  - Plays Z-machine versions 1–5 and 8 (v6/v7 screen model not supported); CZECH-verified on 3, 4, 5, 8
  - Accurate opcode implementation, full state save/restore

- ✅ **Deterministic Replay Verification**: `scripts/replay_solve.py` replays a walkthrough
  with a pinned RNG seed and searches seeds until random events (combat, thief, wizard)
  line up — making "did we really win?" a reproducible yes/no

- 🤖 **AI-Assisted Solving**: multiple solver generations
  - Agentic solver (`zwalker/agentic_solver.py`): perceive→decide→act→verify loop with
    BFS navigation, world model, and checkpoint backtracking; runs free with a local
    decider or with Claude via API
  - Strategic LLM solver (`zwalker/advanced_solver.py`) and assist layer (`zwalker/ai_assist.py`)
  - Persistent cross-run knowledge base (`zwalker/knowledge.py`)

- 🧪 **Compiler Testing**: validate z2js and other compilers
  - Convert solutions into Node.js replay test scripts (155 tracked, including 73 "smart"
    tests that tolerate random events)
  - Compare outputs between interpreters, detect regressions automatically

- 📊 **Game Exploration**: automated mapping and analysis
  - Room discovery and mapping, object detection and tracking
  - Command success/failure analysis

## Installation

Not yet published to PyPI — install from source:

```bash
git clone https://github.com/avwohl/zwalker.git
cd zwalker
pip install -e .

# with AI backends (anthropic, openai)
pip install -e ".[ai]"
```

## Quick Start

### Basic Game Exploration

```bash
# Explore a game and generate a map
zwalker explore game.z5 --max-rooms 50 --json walkthrough.json

# Use AI assistance (requires ANTHROPIC_API_KEY)
zwalker explore game.z5 --ai --ai-backend anthropic --max-rooms 100

# Interactive play mode
zwalker play game.z5
```

### Verify a Walkthrough

```bash
python3 scripts/replay_solve.py games/zcode/zork1.z3 walkthroughs/zork1_verified_350.txt --seeds 4
```

### Python API

```python
from zwalker.zmachine import ZMachine
from zwalker.walker import GameWalker
from zwalker.ai_assist import AIAssistant

# Load and explore a game
game_data = open('game.z5', 'rb').read()
walker = GameWalker(game_data)

# Start game
output = walker.start()
print(output)

# Explore with AI
ai = AIAssistant(backend='anthropic')
results = walker.explore_with_ai(ai, max_commands=20)

# Save walkthrough
walkthrough = walker.get_walkthrough_json()
```

### Generate Walkthroughs for Testing

```bash
# Solve a game (iterations fixed at 50; add --real-ai for LLM assistance)
python scripts/solve_game.py game.z5 --real-ai

# Compare interpreter output against a recorded solution
python scripts/compare_outputs.py solutions/lostpig_solution.json
```

## Use Cases

### 1. Compiler Testing (Primary Use Case)

ZWalker was built to provide regression testing for the [z2js](https://github.com/avwohl/z2js) compiler (ZIL/ZILF to JavaScript).

**The Problem**: z2js was released with bugs that upset users due to lack of testing.

**The Solution**: ZWalker generates comprehensive test walkthroughs that can be:
- Generated from a known-good .z compile
- Replayed on new compiles to detect regressions
- Used to compare output between interpreters

```bash
# Generate JS test scripts from recorded solutions (smart tests handle random events)
python scripts/generate_all_smart_tests.py

# Run the z2js regression suite
./scripts/run_smart_tests.sh
```

See [docs/TEST_GENERATION.md](docs/TEST_GENERATION.md) for the full pipeline.

### 2. Game Analysis

Automatically map and analyze IF games:

```bash
zwalker explore game.z5 --thorough --commands
```

### 3. Automated QA

Generate test coverage for your IF game:

```bash
python scripts/solve_game.py your_game.z5 --real-ai
```

## Project Status

**Version**: 0.1.0 (Alpha)

**What Works**:
- ✅ Z-machine interpreter (1,604/1,604 CZECH tests across v3/v4/v5/v8)
- ✅ Verified complete solves: Zork I 350/350, Zork II 400/400, Zork III 7/7,
  Enchanter 400/400, Sorcerer 400/400, Spellbreaker 600/600,
  Planetfall 80/80, Wishbringer 100/100, Stationfall 80/80
  (deterministic replay)
- ✅ Replay/verification harness (`scripts/replay_solve.py`)
- ✅ Agentic solver with navigation, world model, and backtracking
- ✅ Walkthrough generation and z2js test-script generation
- ✅ Output comparison tools

**Current Limitations**:
- Most games beyond the 50 verified solves have exploration coverage only, not verified wins
- Menu-based IF and Y/N prompts need special handling
- Complex opening puzzles can stall the AI solvers

See [TODO.md](TODO.md) for current status and [docs/CHANGELOG.md](docs/CHANGELOG.md) for
interpreter fixes. Historical reports live in [docs/archive/](docs/archive/).

## Documentation

- [CHANGELOG.md](docs/CHANGELOG.md) - Z-machine bug fixes
- [TEST_GENERATION.md](docs/TEST_GENERATION.md) - z2js test pipeline
- [ADVANCED_SOLVER.md](docs/ADVANCED_SOLVER.md) - strategic solver design (Dec 2025)
- [PROJECT_NOTES.md](docs/PROJECT_NOTES.md) - project overview and approach
- [docs/archive/](docs/archive/) - historical status and progress reports

## Architecture

```
zwalker/
├── zmachine.py        # Z-machine interpreter (1,604/1,604 CZECH tests)
├── walker.py          # Game exploration engine
├── agentic_solver.py  # Agentic solver: perceive→act→verify + navigation + backtracking
├── advanced_solver.py # Strategic LLM solver (multi-turn planning)
├── ai_assist.py       # AI integration (Claude, GPT, local)
├── knowledge.py       # Persistent cross-run knowledge base
└── cli.py             # Command-line interface

scripts/               # (selection)
├── replay_solve.py       # Deterministic seed-search walkthrough verifier
├── solve_zork3_adaptive.py # Adaptive recorder that produced the Zork III solve
├── solve_enchanter_adaptive.py # Adaptive recorder for the Enchanter solve
├── solve_sorcerer_adaptive.py # Adaptive recorder for the Sorcerer solve
├── solve_spellbreaker_adaptive.py # Adaptive recorder for the Spellbreaker solve
├── solve_planetfall_adaptive.py # Adaptive recorder for the Planetfall solve
├── solve_wishbringer_adaptive.py # Adaptive recorder for the Wishbringer solve
├── solve_stationfall_adaptive.py # Adaptive recorder for the Stationfall solve
├── debug_replay.py       # Transcript-printing replayer for walkthrough debugging
├── solve_game.py         # Single game AI solver
├── generate_all_smart_tests.py  # z2js test generation (random-event tolerant)
├── compare_outputs.py    # Output comparison tool
└── generate_docs_pages.py # Regenerates docs/WALKTHROUGHS.html from repo data

docs/                # Documentation + GitHub Pages site
solutions/           # Solution JSONs (50 verified solves + exploration runs)
walkthroughs/        # Human + verified walkthroughs (text + JSON command lists)
games/zcode/         # Game corpus (155 story files)
games/results/       # Exploration walkthrough dumps (43 games)
tests/               # Interpreter regression tests
```

## Contributing

Contributions welcome! Areas needing improvement:

1. **More Verified Solves**: extend the adaptive-recorder treatment to other games
2. **Menu Detection**: better handling of menu-based IF and Y/N prompts
3. **Puzzle Solving**: improved AI strategies for complex puzzles
4. **More Games**: test coverage for additional IF games

## License

GPL v3 License - see [LICENSE](LICENSE) file.

## Credits

- **Z-Machine Spec**: Based on the [Z-Machine Standards Document](https://www.inform-fiction.org/zmachine/standards/)
- **CZECH Test Suite**: Compliance testing by Amir Karger
- **AI Assistance**: Powered by Anthropic Claude and OpenAI

## Links

- **Source**: https://github.com/avwohl/zwalker
- **Issues**: https://github.com/avwohl/zwalker/issues
- **z2js Compiler**: https://github.com/avwohl/z2js
- **IF Archive**: https://www.ifarchive.org/
- **IFDB**: https://ifdb.org/

## Acknowledgments

Built to prevent "pissing off users" by providing comprehensive testing for the z2js compiler. Thanks to the Interactive Fiction community for their feedback and patience.

---

**Note**: This is alpha software under active development. Use for testing and exploration. Bug reports and contributions welcome!

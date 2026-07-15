# Deadline (Infocom, 1982) — solve notes

Binary: `games/zcode/deadline.z3` — Release 28 / Serial 850129, Z-machine V3.
Authority: official ZIL in `logs/deadline_zil/` (cited below as file:line).

## Game shape
- **TIME game** (Flags-1 bit 1). Status line is a 12-hour clock, NOT a score.
  `clock.zil` comments it exactly: `"SCORE INDICATES HOURS / MOVES = MINUTES"`.
  - Global 17 = SCORE = **hours** (starts 8 → 8:00 AM), global 18 = MOVES =
    **minutes** (clock.zil:51-52,66-69). So `vm.get_score()` returns the HOUR
    (8 at start, 13 at the 1:10 PM arrest) and `vm.get_turns()` the minute.
  - `PRESENT-TIME` is the master minutes-since-midnight counter (480 at 8:00 AM),
    +1 each turn (clock.zil:57). Deadline at `PRESENT-TIME > 1199` = 7:59 PM →
    Inspector Klutz ends the game (clock.zil:58-65).
  - No numeric score, no max score → `vm.get_max_score()` is None → this is a
    **WIN_TEXT** solve.
- Player = Chief of Detectives. 12 in-game hours to prove the murder of Marshall
  Robner (officially ruled a suicide by his own medicine, Ebullion).

## The win gate — OBJECT-PAIR-F, ARREST branch (actions.zil:3899-3929)
`arrest baxter and dunbar` (the object PAIR, either order) prints the winning
Sept-5 Klutz letter (EPILOGUE) **iff**:
  - `PRESENT-TIME >= 700` (≈11:40 AM; earlier → "premature"), and
  - Dunbar is alive (not CORPSE-SEEN / DUNBAR-DEAD — Baxter murders her at a
    late unobserved shed meeting, so arrest promptly), and
  - all four evidence flags set (actions.zil:3914-3917):
    1. `NOTE-READ`               — actions.zil:1473 (PAD-READ), set by rubbing
       the pencil on the library notepad → the "Baxter … Focus" impression.
    2. `LAB-REPORT` has TOUCHBIT — actions.zil:2759-2760, set when Sgt Duffy
       returns the slip from `analyze fragment for loblo` (fragment == the buried
       teacup shard, ANALYSIS-GOAL == LoBlo).
    3. `BAXTER-PAPERS` TOUCHBIT  — take the Focus-embezzlement papers from
       George's hidden wall safe (dungeon.zil:1174-1184; INVISIBLE until
       `examine safe` clears it, actions.zil:4469-4470).
    4. `STUB-D`                  — actions.zil:3042, set by showing Dunbar the
       concert ticket stub she drops (her "seeing each other socially" confession).
Winning string (unique): "a jury **convicted** Mr. Baxter and Ms. Dunbar today of
the murder of Mr. Robner" (actions.zil:3922). Every losing arrest outcome says
"declined to **convict**…" (3958/3969) — grep of the ZIL shows the only
"convicted" is 3922, so the WIN_TEXT regex is unambiguous.

## NPC schedules (goal.zil:433-482, MOVEMENT-GOALS)
- GARDENER McNabb: North Lawn 9-10, East Lawn 10-11, **ROSE-GARDEN 11-1**,
  Orchard 1-2. Discovers the ladder holes; when you share his location in the
  Rose Garden his "holes" outburst fires 2+RANDOM(10) min after he arrives
  (I-G-I-G, goal.zil:494-509). "show me the holes" leads you to IN-ROSES where
  `examine ground` / `dig around holes` unearth the porcelain shard (~30%/turn).
- BAXTER: Living Room from 9:55 to 4 PM.
- DUNBAR: Dunbar-Bath 9-9:30, Dunbar-Room 9:30-11:30, **Living Room 11:30-2**.
- GEORGE: Kitchen/Dining until 11, George-Room 11-11:45, Living Room 11:45-12:30.
- Will read at noon in the Living Room (WILL-READING=720, actions.zil:1384,1635);
  it waits/holds until everyone (incl. you) is present, else proceeds ~12:40.

## George / hidden-safe timing (actions.zil:1719-1978)
- `show calendar to george` sets G-CALENDAR → GEORGE-HACK sends George to his
  room; **leaving** his room flips GEORGE-READY and he sneaks to the library via
  the master-bedroom hidden closet.
- Watch from the **Library Balcony**. I-GEORGE-HACK-3 runs each turn with a
  counter GEORGE-SEARCH (0 when he rotates the bookshelf away and enters the
  closet). While he is inside, GEORGE-SEARCH increments once per turn:
    - < 10 : pressing the library button catches him still *dialing* → he bolts
             (safe stays shut, papers unreachable). Too early.
    - 10-15: pressing the button catches him with the safe **OPEN**, he crumples;
             you enter the closet, `examine safe`, `get papers`. **The window.**
    - == 16: the shelves swing out and he escapes with/destroys the will. Too late.
  Reveal the button first with `examine bookshelf` (BOOKS-MOVED, actions.zil:2500).
  Route uses twelve fixed balcony `look` fillers so the button press lands
  GEORGE-SEARCH ≈ 12.

## Dunbar flee / ticket (actions.zil:3150-3469)
- `accuse dunbar` only triggers her flee sequence if `LOBLO-FLAG` is set, which
  requires first `show lab report to dunbar` (actions.zil:3141-3149) — otherwise
  she just deflects ("I thought he committed suicide").
- DUNBAR-SEQUENCE (3375): she goes to Baxter, they meet, then ~5 min later heads
  to the SHED via the front path. While you `follow` her on the OUTSIDE-LINE
  (front path) she drops a Hartford Philharmonic ticket stub (3445-3453).
  `get ticket`, `read ticket`, `show ticket to dunbar` → STUB-D. Baxter is sent
  to the North Lawn then the shed; wait until both are at the shed and arrest.

## Determinism / harness
- **Boot is byte-identical across runs** → pin `vm.rng.seed(seed)` immediately
  after `start()`, no restart prelude.
- Seed then fixes every randomized delay: Duffy's 15+RANDOM(15) min lab
  turnaround (actions.zil:2715), McNabb's outburst, the George window, Dunbar's
  timing. The recorded flat command list (each `y` answering a
  "keep waiting? (Y/N)" wait interrupt, each fixed filler `look`) replays
  verbatim under the same seed. Recorded & verified at **seed 1**.
- Quirks:
  - The front door auto-closes; `open door` before every foyer↔front-path pass.
  - `wait until T` / `wait for X` are one command line but interrupt on passing
    NPCs with a Y/N prompt; answer with `y` (bare `y` off-prompt is a harmless
    "You must supply a verb!" no-op).
  - `wait` (no arg) passes up to 3 minutes; use single-turn commands (`look`)
    when exact turn counting matters (George window).
  - "loblo" resolves to GLOBAL-LOBLO anywhere, so `analyze fragment for loblo`
    works without visiting Dunbar's bathroom.

## Verified result
`python3 scripts/replay_solve.py games/zcode/deadline.z3
walkthroughs/deadline_verified_win.txt --seeds 24 --out solutions/deadline_verified.json`
→ `VERIFIED 13/None at seed 1 | 129 cmds | died=False | won=True` (13 = 1 PM
clock hour, not a score). win_text_seen=True. Reproduced twice.
Recorder: `scripts/solve_deadline_adaptive.py` (emits the identical 129-cmd list).

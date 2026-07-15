# Ballyhoo (Infocom, 1986) — research notes for the verified solve

Binary: `games/zcode/ballyhoo.z3` — Release 97 / Serial 851218, Z-machine V3
score game; `vm.get_max_score()` = 200. Boots clean under GameWalker; two
boots are byte-identical (no boot-time RNG draw), so the seed is pinned right
after `start()` with no `restart` prelude.

Authority: official ZIL source, github.com/historicalsource/ballyhoo
(files cited below as `file:line`). Cross-checked against three independent
walkthroughs (verbatim copies in `logs/ballyhoo_source_{spoiler,eristic,wtking}.txt`,
gitignored):
- The Spoiler Centre solution (Futtrup/Lintermans 1992)
- eristic.net/games/infocom/ballyhoo.html (annotated, with points list)
- walkthroughking.com/text/ballyhoo.aspx

## Scoring: 20 awards x 10 points = 200

The source ships its own scoring key (`points.txt`). Every award is a
`<SETG SCORE <+ ,SCORE 10>>`; all 20 sites:

| # | Award (points.txt wording)                          | ZIL site |
|---|------------------------------------------------------|----------|
| 1 | walking all the way across the tightrope             | bigtop.zil:1690 (PLATFORM-RETURN, first touch of PLATFORM-2) |
| 2 | talking to Harry with helium in your lungs           | outside.zil:1808 (GUARD-F, requires `ENABLED? I-HELIUM`) |
| 3 | fooling Chuckles with the clown mask disguise        | outside.zil:4964 (knock on Clown Alley door, MASK worn, no shawl/dress) |
| 4 | walking through the canvas pleats into the prop tent | outside.zil:3331 (first pass, CANVAS not RMUNGBIT) |
| 5 | finding a circus ticket                              | bigtop.zil:84 (GARBAGE-F search under the bleachers) |
| 6 | completing the hypnosis scene as the granola bar falls | bigtop.zil:183 (STANDS-ROOM M-END: HAWKER RMUNGBIT and TLOC == LOST-MONEY-LOC → WON-STANDS) |
| 7 | getting the radio from Tina                          | verbs.zil:2259 (V-TAKE RADIO, RADIO-POINTS latch) |
| 8 | fishing the skeleton key off the cage wall           | way.zil:1440 (TAKE-WITH-POLE?, KEY not yet TOUCHBIT) |
| 9 | catching a live mouse                                | outside.zil:2535 (catch mouse with bucket) |
|10 | finding the cigarette case under the lion stand      | bigtop.zil:1986 (STAND-F search/move, grate closed) |
|11 | listening to Jenny recalling Andrew's part           | way.zil:3256 (SPILL-BEANS?: CASE RMUNGBIT + GUARD-FELT-CASE) |
|12 | soothing Mahler with classical music                 | way.zil:205 (APE-F GIVE HEADPHONES while tape plays segment 2) |
|13 | getting rid of Hannibal                              | way.zil:1149 (I-BULL with BULL RMUNGBIT) |
|14 | gaining access into the white wagon                  | outside.zil:1324 (OFFICE M-ENTER first time) |
|15 | using your ticket to get into the Blue Room          | way.zil:2476 (PUT-UNDER TICKET at NOOK; needs CLOWN-COUNTER == 7, BOUNCE-C == 0, room untouched) |
|16 | defeating your unseen opponent on the elephant tent  | way.zil:927 (PROD-F PUSH/MOVE/RAISE/SHAKE → WON-ON-TENT) |
|17 | scaring Chuckles away from Katzenjammer's trailer    | outside.zil:4528 (JOEY-SCARED?: all five evidence RMUNGBITs + name known) |
|18 | rescuing Chelsea from the crawl space                | outside.zil:3918 (TAKE GIRL with GIRL RMUNGBIT) |
|19 | ordering the roustabout to get the safety net        | way.zil:1481 (JIM-F "get net" after clap → FOLLOW-FLAG 5) |
|20 | making Mahler lose his grip on Chelsea               | bigtop.zil:1623 (ACROSS-ROPE ON-ROPE 5 win branch → GOTO LEFT-HANGING) |

## Timed events (all turn-counter clockwork, seed-independent)

- **Thumb at the fountain** (opening): entering Connection queues `I-BOOST -1`
  (outside.zil:44); BOOST-COUNTER 1..6 narrates his attempts; at 6 he gives up
  and waddles off (outside.zil:4268-4297). "help midget" (RAISE/PICK-UP,
  outside.zil:4123-4128) any time while I-BOOST runs sets HELPED-THUMB.
  HELPED-THUMB is load-bearing three times: Thumb does NOT rat you out in
  Clown Alley (I-CLOWN-ALLEY counter 3, outside.zil:4689), Thumb hides under
  the blackjack table for the forced bet (way.zil:3549-3556), and Thumb hoists
  Chelsea in the crawl space.
- **Munrab/detective meeting**: first entry to the prop tent queues `I-MEET 1`
  (outside.zil:2175). MEET-COUNTER: voluntary "hide behind Taft" jumps it to 6
  (outside.zil:2761-2775); they enter at 7, kidnap dialogue at 8, END-MEETING
  at 9 (full ransom-note dialogue only if never discovered). END-MEETING sets
  MEET-COUNTER=10, which is the gate for crawling under the bleachers
  (outside.zil:2833-2880).
- **Helium/turnstile**: "untie balloon; inhale helium" queues `I-HELIUM 2`
  (bigtop.zil:832) — the guard must be addressed on the very next turn.
  GUARD-F then sets SPEAK-HELIUM and queues `I-TURNSTILE 2` (outside.zil:1810)
  — walk south within 2 turns. Later turnstile passes come from
  "put ticket in slot" (outside.zil:2104, way.zil:3134), same 2-turn window.
- **Clown Alley**: knocking with the mask (+10) queues `I-CLOWN-ALLEY`;
  inside, CLOWN-COUNTER ticks 1/turn (outside.zil:4667-4712). Counter 2 =
  "close the door" request; counter 3 busts you if !HELPED-THUMB; counter 6
  with the door CLOSED sets **CLOWN-COUNTER=7** and prints the Annie Oakley
  hint — this value is *the* gate for sliding the ticket under the sideshow
  front (way.zil:2470). You are thrown out and unmasked the same turn. Budget:
  entry turn is counter 1, so exactly: take ash tray(2), close door(3),
  search ash(4), take scrap(5), filler(6). Chuckles snatches the tray back on
  exit (EXIT-CLOWN-ALLEY outside.zil:4621) — irrelevant, the scrap is what counts.
- **Hypnosis dream** (bigtop.zil:222-296, 440-497): "give ticket to rimshaw"
  (TELL-WHAT-NOW way.zil:2226: punches the ticket, hands it BACK, sets
  HYP-BOX), "rimshaw, hypnotize me" → DREAM (way.zil:2245: POCKET-CHANGE set
  to 1841 for the dream, real money 1281 saved). I-STANDS: growl(2), roar(3),
  stomach(4), hawker appears at STANDS-C 5; he leaves the NEXT turn (I-STANDS
  first branch) so "buy candy from hawker" must follow immediately (re-queues
  I-STANDS 2, giving one turn to pay). "give money to hawker" with $1.85 →
  LOST-MONEY-LOC = TLOC (bigtop.zil:473). The stands are one room with a
  virtual 12-seat grid (TLOC, moves via N/S/E/W-OOF bigtop.zil:530-600);
  exit at TLOC 12 → dream Connection. The concession line (outside.zil:108-345):
  entering the long line queues `I-BAD-LUCK 5`; short line forms; two waits in
  the short line bring Jerry's ballplayer team, who bump you to the long line
  (LINE-COUNTER 4); "stand in long line" with LINE-COUNTER > 3 → ENTER-LINE
  win: frozen banana + POCKET-CHANGE -= 375 (outside.zil:20-45 CON-AREA M-BEG,
  outside.zil:301-312). Bite banana + drop it → monkey off your back. At the
  Wings, "ask hawker about candy" needs POCKET-CHANGE == 1281 exactly (bought
  candy AND banana, bigtop.zil:355-380) → HAWKER RMUNGBIT. Return to
  LOST-MONEY-LOC seat → M-END fires +10, granola bar falls, WAKE-UP.
- **Tape deck** (in the HEADPHONES, way.zil:1593-1830): 16-minute tape,
  ON-TAPE starts at 6, all-rock (segment code 0); positions 3-4 carry the
  subliminal Rimshaw voice "At the clap of my hands you shall obey my every
  command" (way.zil:1770-1782) — the roustabout's trigger. REWIND/ADVANCE move
  5/turn, PLAY/RECORD 1/turn. RECORD writes segment 2 (classical) when
  CLASSICAL-PLAYING? (radio on, dial 1170, same room; way.zil:1717,1890).
- **Mahler's cage**: entering queues `I-APE -1`; APE-C 7 = death
  (way.zil:245-299). With the tape playing classical, holding the headphones,
  M-END makes Mahler snatch them (way.zil:358-366) → PERFORM GIVE → +10 and
  APE RMUNGBIT (soothed). I-APE thereafter: the moment the playing segment is
  not 2 (recording exhausted) Mahler screams; in-cage = death (way.zil:253-270).
  With classical recorded on positions 0-6 there are ~6 safe turns: play tape,
  search straw, open trap door, take ribbon, east, close cage.
- **White wagon**: knock on office door → Munrab steps out; I-OFFICE
  (outside.zil:4-... at 1490-1520): door swings open at OFFICE-C 1, footsteps
  at 4, tries the (locked) door at 5/7/9/11, barges at 12 or the moment it is
  unlocked. Enter, lock door, search desk, take spreadsheet, move desk, up —
  comfortably inside the budget. First entry +10 (outside.zil:1324).
- **Blue Room** (way.zil:2468-2560, 3474-3567; cards.zil): sliding the ticket
  needs CLOWN-COUNTER 7; first slide +10 and the spring panel opens
  (WIN-BLUE-DOOR; auto-closes in 3 turns). "open secret panel" from inside on
  visit 1 forces a $1 bet (BLUE-DOOR-F way.zil:2532-2541) and Thumb sneaks
  under the table (HELPED-THUMB); during PLAY-HAND he peeks and taps the
  dealer's hole-card value on your foot → THUMB-TAPPED (cards.zil:105-115).
  Afterwards "open secret panel" simply opens it (I-BLUE-DOOR 2 closes it).
- **Thumb points to the Blue Room**: entering Connection with THUMB-TAPPED &
  HYP-BOX & elephant gone queues `I-THUMB 1` (outside.zil:47-49,
  way.zil:1176-1218): turn 1 he appears babbling, turn 2 he taps his foot,
  points at the Blue Room, sets DEALER RMUNGBIT ("new dealer") and leaves.
- **Blue Room, second entry** (DEALER RMUNGBIT): ticket slides through and
  REAPPEARS once (way.zil:2479-2496) — slide it a second time to get in.
  Inside, I-CHASE (way.zil:3607-3667): 1 new dealer scrutinizes the ticket,
  2 he vanishes into the smoke, 3 he returns with Billy the con man, 4 the
  thugs wrestle the KIESTER away (you must be holding it: look under table →
  suitcase appears since DEALER RMUNGBIT, way.zil:3745-3752; take it) and bolt.
  Back at the Nook (CHASE-C < 8) you see the silhouette throw something bulky
  onto the tent and climb after it — cues the tent fight.
- **On the Tent**: I-POKE (way.zil:860-905): prod thrusts up at POKE-C 2,4,7,
  9,12; it LINGERS at 4 and 9 only; NOT-MOVED-C > 3 at a thrust = death (move
  around to reset). "take shaft" (POKE-C := 15) then "pull shaft"
  (PUSH/MOVE/RAISE/SHAKE branch) → +10 WON-ON-TENT, queues I-MOVE-DICK 10.
- **Drunk detective**: I-MOVE-DICK (way.zil:966-978, queued by the tent win
  and by the ape-soothing) puts DICK, RMUNGBIT drunk, at the Midway Entrance
  with the ransom NOTE and TRADE-CARD. Pour water on him (bucket filled at the
  Connection fountain), ask about Chelsea, take note and card.
- **Chuckles at Camp East**: I-JOEY (outside.zil:4491-4506): WIPE-C ticks on
  entering East Camp; at 8 he retreats into the trailer. JOEY-SCARED? needs
  JOEY-NAME-KNOWN ("eddie, hello") plus RMUNGBIT on NOTE, SHEET, SCRAP,
  TRADE-CARD, RIBBON (show each) → +10, he flees (6 turns, inside budget).
- **Katzenjammer trailer / crawl space**: wear veil+dress+jacket (from the
  gorilla-suit pocket after Chuckles flees), knock, enter, close door, take
  crowbar, move moose → hole. Break into Clown Alley with the crowbar
  (WARPED-DOOR-BROKEN outside.zil:4922), take Thumb, carry him in, put Thumb
  in hole; I-TAMER (outside.zil:3800-3860): Chelsea rises into the opening on
  a 2-turn cycle (GIRL RMUNGBIT); "take chelsea" while she is up → +10
  (outside.zil:3918).
- **Endgame** (I-GIRL outside.zil:3960-4010, I-END-GAME outside.zil:3716-3790,
  ACROSS-ROPE bigtop.zil:1528-1640): carrying Chelsea to Near White Wagon
  flushes Munrab through the fence; next turn you are walked to the Menagerie:
  END-GAME set, Mahler (APE-LOC 1) holds Chelsea on Platform-1. At the Ring:
  "clap" (the tape's trigger) then "roustabout, get net" → +10; the roustabout
  sprints off and returns with the net, which Munrab & co hold (NET in MUNRAB).
  Climbing the (tangled) rope ladder needs the lion stand as a step; the first
  climb spooks Mahler into the guy wires (APE-LOC 2, globals.zil:549-551) —
  fatal unless the net is being held. "up" from Platform-1 shakes the
  apparatus (GUY-WIRES-F) and flushes him to Platform-2 (APE-LOC 3) — the
  radio must NOT be lying on Platform-2 ("Crunch!"). With the radio in hand,
  dial 1170, radio on: walking east to ON-ROPE 3/4 with APE-LOC 3 triggers the
  WPDL Pledge Week announcement (sets DIAL RMUNGBIT, way.zil:2897-2904) — this
  is why the walkthroughs cross partway and turn around ("A daring turnaround"
  branch, END-GAME only). "call WPDL" from the office phone (V-PHONE
  verbs.zil:1600-1613, needs END-GAME + DIAL RMUNGBIT) sets CALLED-STATION,
  and I-END-GAME brings the whole gang in to hold the net. Final crossing
  east with radio held+on+1170+CALLED-STATION: Mahler loosens grip at
  ON-ROPE 4, drops Chelsea into the net at 5 → +10 (200/200) and GOTO
  LEFT-HANGING; I-END-GAME then counts to 4: at 4 your hands slip and the
  net catches you — FINISH (win). Waiting 3 turns is the natural end; any
  DROP/LEAP short-circuits END-GAME-C to 3.

## Randomness (RANDOM/PROB) that can touch the route

- **Blackjack** (cards.zil:24-35): PICK-CARD draws with `RANDOM 52`; the
  forced $1 hand is unavoidable. The number of "Do you want another card?"
  Y/N prompts consumed depends on the cards, so the recorded command list is
  seed-specific — the adaptive recorder answers the prompts at runtime
  (policy: stand immediately; a lost dollar is irrelevant, POCKET-CHANGE
  starts at 1281 and nothing downstream needs money).
- **Tightrope trembling** (bigtop.zil:1431, 1467): only queued when crossing
  WITHOUT the pole and not END-GAME — the route always carries the pole, and
  the endgame branch skips it. Never fires.
- **Concession-line color** (outside.zil:471-492, PLAYER-NUM): random flavor
  lines while queueing; the "line kicks into gear" message needs a 1-in-8
  roll but is pure flavor — the banana win only needs LINE-COUNTER > 3.
- **Monkey on your back** (outside.zil:73, PROB 60): flavor messages.
- **I-STANDS hawker re-appearance** (bigtop.zil:260, PROB 25): only after the
  scripted appearance; harmless.
- **Elephant fling direction** (way.zil:1127, PROB 50), **squirt** (way.zil:1165),
  **fountain squirt** (outside.zil:603), **hawker exit direction**
  (bigtop.zil:235), **Rimshaw soothsay phrasing** (way.zil:2196), **radio
  static content** (way.zil:2996): all flavor-only on this route.
- All of these still consume RNG draws, so the exact command list (including
  filler turns) must be replayed verbatim — which is what replay_solve does.

## Money ledger

Real POCKET-CHANGE starts at 1281 (globals.zil:103) and is untouched except
by blackjack (forced $1 bet; outcome irrelevant). Dream money is a separate
1841: -185 granola order, -375 banana; "ask hawker about candy" checks the
1281 result exactly (bigtop.zil:365).

## Interpreter/harness notes

- Boot is deterministic (verified: three boots byte-identical); seed pinned
  after `start()`; no restart prelude needed.
- The forced blackjack hand's "Do you want another card? (Y is affirmative):"
  is a mid-turn YES? read: the next command in the walkthrough is consumed as
  the answer ("n").
- Walker rollback hazard: all door-gated moves (cage doors, office door,
  trailer doors, Blue Room panel) are opened before moving, so
  `try_command`'s blocked-move rollback never falsely triggers on this route.
- The known "feel my head"/"slide ticket" parser bug (eristic notes, GitHub
  issue) is avoided by using the exact phrasings "slide ticket under front"
  and never asking Rimshaw to read the head.

## Unavoidable joke death (replay_solve died=True is a FALSE POSITIVE here)

This is the one thing about Ballyhoo that the standard replay pipeline cannot
score cleanly, and it is a game-design fact, not a route error.

- **Award #16** ("defeating your unseen opponent on the elephant tent",
  points.txt) is scored by PROD-F (`take shaft` / `pull shaft`) in the room
  **On the Tent** (way.zil:812, PROD-F way.zil:924-930). On the Tent is
  reachable by exactly one route: `up` from **Top of Cage** (UP-LADDER
  globals.zil:586-599, ON-TENT way.zil:638 `UP PER UP-LADDER`). Top of Cage
  itself is reached only from the Menagerie Nook (`up`, UP-DOWN-CAGE
  way.zil:654-673). There is no other way in and no other way down: On the
  Tent's only exit is `down` -> POKE-EXIT -> DOWN-LADDER -> Top of Cage
  (way.zil:848-853, globals.zil:602-614), and Top of Cage's only ground exit
  is `down` -> Nook.
- The FIRST time you descend from Top of Cage, UP-DOWN-CAGE runs a scripted
  **non-fatal gag** (way.zil:660-668): `<COND (<NOT ,DIED> ... <SETG DIED T>
  <TELL-DIED> <MOVE ,PROTAGONIST ,NOOK>)>`. It prints
  `You fall awkwardly down from the cage.` then `**** You have died ****`
  (TELL-DIED, verbs.zil:3510-3512) and, two turns later via I-DEMISE
  (verbs.zil:3514-3518), `(The reports of your demise have been grossly
  exaggerated. You suffer little more than injured pride.)`. Play continues;
  the score is untouched. Every later cage descent just "clambers"
  (`<NOT ,DIED>` is now false).
- `SETG DIED T` at way.zil:667 is the ONLY writer of the DIED global, and DIED
  is read only inside that same fall routine (way.zil:660,665) -- it has zero
  downstream effect. So the gag is completely harmless in-game AND unavoidable
  in any 200/200 solve (award #16 forces at least one Top-of-Cage descent).
- **The problem for replay_solve.py**: a REAL Ballyhoo death (JIGS-UP,
  verbs.zil:3482-3499) prints the SAME `**** You have died ****` via the same
  TELL-DIED routine, then continues into "sell you to the circus" and
  `<FINISH>`. So the gag and a real death are textually identical at the
  `you have died` marker. scripts/replay_solve.py flags any output containing
  `"you have died"` as `died = True` (never reset), and `is_won` returns False
  whenever `died` -- so the pipeline reports **200/200, win_text_seen=True,
  won=False, died=True**. Verified: exactly ONE such line appears in the whole
  415-command transcript (command index 216, `down`), and it carries the
  gag's tell-tale `from the cage` phrasing.
- **Consequence**: `died=False` is NOT achievable through the unmodified
  scripts/replay_solve.py. The route genuinely reaches 200/200 and the winning
  ending; the `died=True` is a heuristic false-positive on this single gag.
  The clean fix is a one-line DEATH_MARKERS refinement in replay_solve.py --
  the same kind of per-game curation already recorded there for Enchanter,
  Plundered Hearts and Zork (see its DEATH_MARKERS comment block) -- e.g. make
  the `you have died` marker require the game-over prompt/JIGS-UP context, or
  exempt the `from the cage` gag. Per the task's hard rules I did NOT modify
  replay_solve.py. The recorder (scripts/solve_ballyhoo_adaptive.py) and the
  walkthrough header both flag this gag explicitly; the recorder's own death
  check ignores any `you have died` that also says `from the cage`.

# The Lurking Horror — verified-solve research notes

Game: games/zcode/lurking.z3 (Infocom, Release 221 / Serial 870918, Z-machine V3).
Authority: official ZIL source, github.com/historicalsource/lurkinghorror
(files cited below as file:line; local copies fetched to logs/lurking_zil/,
gitignored). Cross-checked against three independent walkthroughs and the
InvisiClues (verbatim copies in logs/lurking_source_*.txt, gitignored).

Standard V3 SCORE game: score/turn globals are the normal pair, SCORE verb
prints "Your score is N of a possible 100" (verbs.zil:281);
vm.get_max_score(boot_banner) returns 100.

## Scoring model (sums to 100)

Two mechanisms:

1. `SCORE-OBJECT` (verbs.zil:1743-1751): adds the object's `VALUE` property
   and zeroes it. Called from ITAKE for anything you pick up
   (verbs.zil:1737), from GOTO for each lit room you enter
   (verbs.zil:1842), and explicitly for a few event objects.
2. Inline `<SETG SCORE <+ ,SCORE ...>>` awards for events, each guarded by
   a one-shot global.

19 incremental awards of 5 points = 95; the endgame kill then does
`<SETG SCORE 100>` outright (frob.zil:1598), absorbing the last 5. (The
slime CURTAIN also carries `(VALUE 5)` at frob.zil:742, but no reachable
code path ever calls SCORE-OBJECT on it — it is not takeable and rooms
score only themselves — so its 5 points are exactly the gap the final
`SETG SCORE 100` closes. FLASK-SCORE, CHINESE-FOOD and FOOD-SCORE awards
are commented out in the shipped source: cs.zil:2848/2966-2969,
hacker.zil:271, hacker.zil:861.)

Rooms with (VALUE 5), scored on first lit entry:
- STORAGE-ROOM "Ancient Storage"           cs.zil:610
- TUNNEL "Steam Tunnel" (below the Tomb)   cs.zil:2814
- ELEVATOR-PIT "Concrete Box"              cs.zil:3334
- TOP-OF-DOME (catwalk, via the tentacle)  cs.zil:6716

Objects with (VALUE 5), scored via ITAKE or explicit SCORE-OBJECT:
- SMOOTH-STONE (take, dream sequence)      yuggoth.zil:116
- MASTER-KEY (hacker loans it)             hacker.zil:429, awarded in
  HACKER-LOANS-KEY hacker.zil:322-325
- NOTE (suicide note under the roof plug)  cs.zil:7086
- HAND (take the mummified hand)           green.zil:573
- FLIER (stone thrown off Brown roof)      green.zil:449, awarded in
  OBJ-OFF-ROOF yuggoth.zil:225
- PROFESSOR (survive his summoning)        cs.zil:5280, awarded at
  TIED-UP?=8 when you are NOT in the lab/pentagram, cs.zil:4839-4853
- BOLT-CUTTER (dropped by scared urchin)   frob.zil:444
- PRESSURE-VALVE (scald the rats)          cs.zil:3921, awarded in
  OPEN-VALVE only if RATS-HERE, cs.zil:3979-3994
- URCHIN-WIRE (cut with bolt cutter)       frob.zil:461, awarded at
  frob.zil:475-477

Inline event awards (5 each):
- MANHOLE-SCORE: first descent through the opened manhole
  (MANHOLE-EXIT, cs.zil:619-623; global cs.zil:786)
- MAINT-SCORE: maintenance man caught standing in floor wax
  (I-MAINT-ATTACK, cs.zil:6249-6252; global cs.zil:6244)
- HAND-ANIMATED-SCORE: pulling the animated hand from the vat
  (cs.zil:5483-5486; global cs.zil:5570)
- BRICK-WALL-SCORE: elevator rips the reinforcing rod out
  (I-ELEVATOR-MOVES, cs.zil:1758-1766; global cs.zil:1695)
- Curtain destroyed by liquid nitrogen (frob.zil:751-768, +5 at 763 when
  NITROGEN-CNT >= 3)
- The frob materializes after the line is plugged in
  (I-FROB-APPEARS END-CNT=1, frob.zil:1609-1616)

Win: throw the smooth stone at the frob when END-CNT=2 → creature destroyed,
`SETG SCORE 100` (frob.zil:1582-1598). Taking the dropped stone afterward
prints the epilogue ("Can I have my key back?") and calls FINISH
(yuggoth.zil:156-176).

## Timed events / interrupts (the clock hazards)

- I-COMPULSION (pc.zil:471-485): after reading page 1 of the corrupted
  paper, pages 2-4 display one per turn, then you faint into the Yuggoth
  dream. No input needed beyond waiting.
- I-LURKER-APPEARS (yuggoth.zil:256-287): fires every turn after taking
  the stone; 3 ticks then you wake in the Terminal Room. Inventory is
  preserved across the dream (ROB PLAYER FROB / ROB FROB PLAYER,
  cs.zil/pc.zil I-COMPULSION and yuggoth.zil:286).
- I-HACKER-HELPS (cs.zil:295+): 4 ticks (counted only while you are in the
  Terminal Room) for the hacker to fix your login and return to his desk.
- I-MICROWAVE (hacker.zil:866+): each turn = 1 minute; adds MICROWAVE-TEMP
  to each content's HEAT (HI = 4/min). Chinese food must reach HEAT >= 12
  and not exceed 20 (RMUNGBIT = overcooked, hacker.zil:263+857-860).
  5:00 on HI = exactly 20. I-COOL (hacker.zil:814) drains 1 heat per ~4
  turns afterward, so ~30 turns of slack to deliver.
- I-TIRED (interrupts.zil:12-27): first fires at turn 200 (misc.zil:320),
  then every 25 turns; each tick -10 LOAD-ALLOWED, -1 FUMBLE-NUMBER; at
  AWAKE>8 you collapse. Drinking Coke adds +200 to the timer and undoes one
  tick (hacker.zil:553-561). One preemptive sip around turn ~180 pushes the
  first tick past the end of the route.
- I-WAXER-MOVES (cs.zil:5916): the floor waxer ping-pongs INF-1..INF-5
  every 5 turns; purely turn-based, no RNG. WAXER-EXIT (cs.zil:5689)
  blocks moving east out of the waxer's room until it moves on.
- I-MAINT-ATTACK (cs.zil:6246): queued 2 turns after the cord is cut
  (cs.zil:6199-6206), then every turn: man descends at the waxer, moves one
  corridor room per turn toward you; 5th tick in your room without wax is
  death (MAINT-ATTACK-COUNT > 4, cs.zil:6330-6338). If FLOOR-WAX is in his
  room: +5 and I-MAINT-DISSOLVES 4 (cs.zil:6249-6252, dissolve 6361).
- I-FREEZE-TO-DEATH (cs.zil:83-93): queued 2 turns after stepping outside
  (EXIT-TO-COLD cs.zil:4419+), refires every 4; death at count > 5 (~22
  turns). EXIT-FROM-COLD resets the count each time you get back inside.
- Darkness is instantly fatal: turning the flashlight off (or losing light)
  in a dark room = "Something just grabbed you from behind" (verified
  empirically in the Temporary Lab; keep the light on until back in a lit
  room). Flashlight battery is finite (I-FLASHLIGHT, cs.zil:1384-1418) but
  ample for this route (~60 turns of use).
- I-RATS (cs.zil:3339+): rats stage room-by-room toward you in the steam
  tunnel (RATS-WAITING > 3 per hop); once with you, RATS-HERE increments
  each turn — 1 approach, 2 attack, 3 swarm, 4 = death. OPEN-VALVE with
  rats present scalds them: +5, rats gone for good.
- I-PROFESSOR (cs.zil:4739+): TIED-UP? increments each turn you are in the
  lab/under-lab/brick-tunnel. 1 = pushed into pentagram; cutting the chalk
  line before TIED-UP? > 2 makes him redraw it and CONFISCATE YOUR ENTIRE
  INVENTORY (PROF-REACTS, cs.zil:5001-5013); at 8: death if you are still
  in the lab or pentagram, +5 (professor eaten) if you escaped below
  (cs.zil:4839-4857).
- I-NITROGEN-GOES (cs.zil:1286-1292): once the flask is open, NITROGEN-CNT
  (starts 5, cs.zil:1284) drops by 1 every 3 turns; the curtain pour only
  fully destroys the curtain while NITROGEN-CNT >= 3 (frob.zil:758), i.e.
  pour within ~8 turns of opening. Route opens the flask at the curtain.
- Inner Lair countdown (frob.zil:939-1053): entering locks the door,
  queues I-HAND-DIVES -1 (unconditionally — the hand itself is optional
  for finding the line) and I-HACKER-RETURNS 2. Hacker: noises (t+2),
  enters (t+3), then LAIR-CNT 1..9, death at 9 (~12 turns). Plugging the
  live line in dequeues him and queues I-FROB-APPEARS -1: END-CNT 1 (+5,
  same turn), 2 "tenses" (next turn), 3 = death if the frob still lives
  (frob.zil:1638-1648). So: plug, wait 1 turn, throw stone = the only
  window.
- HV line (frob.zil:1360-1487): SEARCH POOL finds it only while
  I-HAND-DIVES is queued; TAKE needs gloves once cut; 3 axe blows to cut
  (HV-CNT > 2); after cutting, I-LINE-IN-WATER 2 — retake it within 2
  turns; plugging in without gloves drops it, without boots kills you.

## Randomness (PROB / RANDOM) — why a pinned seed suffices

Exactly two pieces of state-relevant RNG:

- I-URCHIN (frob.zil:346-436): every 10 turns the urchin either stays put
  (PROB 80 if you are with him) or moves through a random open exit
  (RANDOM-ELEMENT over legal non-outside exits, avoiding the Tomb and the
  maintenance man). When he moves into a player-less room he ROBs it —
  every takeable object in the room goes under his parka (frob.zil:430-433),
  so stashed tools can vanish on unlucky seeds. Showing him the ANIMATED
  hand (PERSON flag required) makes him flee and drop everything he
  carries, including the bolt cutter (URCHIN-F, frob.zil:265-280).
- RANDOM-ELEVATOR-MOTION (cs.zil:3460-3464): entering the ELEVATOR-PIT or
  STEAM-TUNNEL-EAST (cs.zil:3424, cs.zil:2966) presses a random elevator
  floor button with PROB 25, which can park the car away from floor 1 and
  hide the underside hook the chain gag needs (the adaptive harness
  recovers by re-calling the car to floor 1 from the lobby).

Flavor-only: LOOK-BEHIND texts (globals.zil:482-487, PROB 80),
PICK-ONE/RANDOM-ELEMENT description shufflers (misc.zil:281-296),
GOTO's PROB 80/PROB 90 ambience (verbs.zil:832,1830). None alter state.
- Boot draws no randomness: two boots produce identical banners and the
  seed pinned after start() fully determines the run (verified
  empirically), so no `restart` prelude is needed.

## Copy-protection / feelies

Login on the whiz-bang pc: `login 872325412` (the student-ID number from
the packaged GUE ID card), `password uhlersoth` (from the packaged
student handbook). The parser turns unrecognized words/numbers into
INTNAME and V-LOGIN/V-PASSWORD (pc.zil:311-347) accept the pair.

## Map/mechanics notes not obvious from walkthroughs

- The Tomb crack (TOMB-SQUEEZE cs.zil:2476-2490 + HEAVY-JUNK?
  cs.zil:2466-2474) blocks any carried object with SIZE > 5 except the
  crowbar and the animated hand. Axe (10), bolt cutter (10) and flask (50)
  must be stashed before the hatch trip; default-size items (key,
  flashlight, stone, knife, padlock) pass.
- Elevator chain gag: wedge the basement doors with the crowbar
  (ELEVATOR-DOORS-F PRY + PUT crowbar IN doors → V-WEDGE, cs.zil:2067+),
  drop into the Concrete Box (+5), chain around rod (too thick to tie —
  lock the loop with the Tomb padlock), climb out, hook the chain onto the
  elevator underside machinery, unwedge, ride the car from floor 1 to 2:
  I-ELEVATOR-MOVES rips rod + wall (cs.zil:1745-1775, +5, sets
  BRICK-WALL-FLAG which opens ELEVATOR-PIT north → STEAM-TUNNEL-EAST).
- The wet-tunnel maze (LAIR-1..LAIR-11, frob.zil:573-686) is FIXED, not
  randomized: Large Chamber d → LAIR-1, then n, d, s, s, d → OUTER-LAIR.
  The animated hand + brass hyrax ring pointing gimmick (LAIR-F END rarg,
  HAND-POINTS frob.zil:715-731) is a hint device only; the ring is not
  needed for anything.
- The valve needs two "open valve with crowbar" attempts (VALVE-OPENED?
  must exceed 1, cs.zil:3979-3990); do the first before the rats arrive,
  the second while they are in the room for the +5.
- Great Dome: the "rope" is a tentacle; climbing it with gloves lands you
  on the catwalk (TOP-OF-DOME +5); the creature flees, leaving the wooden
  ladder, which you LOWER (no need to lift it) to get back down.
- Weather dome (green.zil:297-430): entering with the stone queues I-FLIER;
  count 1 puts the flier on the Brown roof. Dig in the dirt (tub), take
  hand (+5), go down to the roof and THROW STONE AT CREATURE before count 6
  (or it eats the hand): OBJ-OFF-ROOF sends stone to the Small Courtyard,
  flier follows (+5). Retrieve the stone from the courtyard (outside).
- Hand animation: put hand in vat, I-ANIMATE-HAND sets PERSON after 2
  ticks (cs.zil:5572-5599); taking it then = +5 and it rides your shoulder.
- Endgame order that works: open cover, unplug coaxial cable (frees
  INPUT-SOCKET, frob.zil:1439-1441 "already a coaxial cable in the
  socket"), search pool, take line, cut line with axe ×3, take line,
  put line in socket, wait 1 turn, throw stone at creature, take stone.

## Verified result

Route recorded under interpreter RNG seed 1 (pinned after start()):
306 commands, score 100/100, turn counter 310, no deaths, epilogue
"Can I have my key back?" + "Your score is 100 of a possible 100 ...
President of the Institute" + FINISH. Verified twice by
scripts/replay_solve.py --seeds 24 (converges at seed 1, won=True,
died=False, win_text_seen=True). The adaptive harness
(scripts/solve_lurking_adaptive.py) also wins 6/8 on a 1-8 sweep: seeds
1,3,4,5 replay the base route verbatim; 2 and 7 win via the urchin-hunt
and elevator-recall recoveries; 6 and 8 desync on deeper urchin/elevator
rolls (stash robbed / car repeatedly mis-parked) and are simply skipped —
the verifier needs only the one pinned seed.

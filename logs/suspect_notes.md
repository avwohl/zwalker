# Suspect (Infocom, 1984) — verified-solve synthesis notes

Binary: `games/zcode/suspect.z3` — Release 14 / Serial 841005, Z-machine V3.
ZIL authority: github.com/historicalsource/suspect (cloned to `logs/suspect_zil/`, gitignored).
Two walkthroughs cross-referenced (verbatim in `logs/suspect_source_*.txt`, gitignored):
the-spoiler.com and walkthroughking.com. All prose below is my own.

## What kind of game this is
Suspect inverts Deadline/Witness: **you are the prime suspect**, framed for the
murder of your host Veronica Ashcroft at her Halloween masquerade. It is a race
to gather the *real* evidence and convince the detective to arrest the true
killers before he arrests you.

It is a V3 **time game** (header flags1 bit 1). The status line is a clock, not
a score. The game's own globals are `SCORE` = hours and `MOVES` = minutes
("SCORE INDICATES HOURS / MOVES = MINUTES", events.zil:4); `PRESENT-TIME` is the
master minutes counter and starts at 540 = 9:00 p.m. (events.zil:9). So
`vm.get_score()` returns the clock HOUR (23 at the winning arrest = 11 p.m.) and
`vm.get_max_score()` is None. No `_SCORE_VAR_OVERRIDES` entry is needed or wanted
— this is a WIN_TEXT solve. The SCORE verb prints only prose.

## The twist (spoiler)
The real Veronica was strangled with your rented cowboy lariat *before* the game
proper; the "Veronica" who circulates and spills her drink is Alicia Barron
wearing Veronica's over-the-head fairy mask, faking an alibi for the real
murderer, Michael Wellman (Veronica's husband and Alicia's lover). Michael and
Colonel Marston had been embezzling from the Ashcroft family Trust; Veronica
found out, so Michael killed her and planted evidence (the lariat, a silver
bullet from your gunbelt) to frame you.
NB: R14's binary names the husband **Michael Wellman** (the design memo m3.txt
calls him "Wellman"); some summaries say "Wembleton". The WIN_TEXT keys on the
first name "Michael" only.

## Boot RNG — restart/yes prelude
Two fresh GameWalker boots are byte-different, so Suspect draws randomness during
GO before a seed can be pinned. Fix (proven on Stationfall): begin the recording
with `restart`/`yes`. replay_solve pins `vm.rng.seed(seed)` right after `start()`;
the RESTART opcode then re-runs GO with the RNG already seeded, so the boot draw
and the entire party schedule become reproducible.

## The clock and the wait verbs
`CLOCKER` (clock.zil:39) advances `PRESENT-TIME` and rolls MOVES/SCORE every turn.
Bare `wait`/`z` is an interactive loop that asks "Do you want to keep waiting?".
The useful primitives are single command lines that advance many minutes:
* `wait for <person>` (V-WAIT-FOR, verbs.zil:2289) → `V-WAIT 10000 WHO`: burns
  minutes until WHO enters your room, or you leave, or a fatal event.
* `wait until <time>` / `wait until midnight`.
Crucially, when a scripted event prints during a wait, V-WAIT stops to ask
"keep waiting?" (verbs.zil:2252). So a `wait for` is followed by exactly the
number of `yes` answers the seed needs (seed 1: 2 after `wait for marston`, 1
after `wait for detective`). These `yes` lines are part of the recording.

## Autonomous event chain (the backbone)
NPC movement is goal-driven (goal.zil) with RNG variation once PRESENT-TIME > 540,
so exact minutes drift per seed — hence `wait for`. The murder-discovery chain,
in order, all firing on their own without the player:
1. 9:02 — I-SPILL (events.zil:55): "Veronica" (Alicia) spills her drink and
   leaves for the office "to clean up"; she is murdered there off-stage.
2. The three-way bar argument (I-ARGUMENT, people.zil:834) once Michael, Marston
   and Cochrane converge at the bar; it marches them to the office
   (GANGS-ALL-HERE, people.zil:729) where they find the body and Michael phones
   the police → I-POLICE-ARRIVE +25 (people.zil:1435).
3. Michael slips to the garage and hides the Trust folder in his BMW trunk
   (I-MICHAEL-HIDES-FOLDER, people.zil:638). **This happens whether or not you
   watch** (the "you're not in the garage" branch still stows the folder), so a
   stake-out is unnecessary — just crowbar the trunk after he leaves.
4. Michael + Marston hold a locked-door library meeting (I-LIBRARY-MEETING,
   people.zil:691); Michael hands Marston the investor list (MOVE INVESTOR-LIST
   COL-MARSTON, people.zil:802). I-END-MEETING (+2) walks both to the ballroom
   fireplace, where Marston drops the list into the fire (G-COL-MARSTON,
   people.zil:2363; it burns over ~2 turns then is consumed to POLICE-LAB).
5. The detective arrives (I-POLICE-ARRIVE), searches the office, then walks his
   script (OFFICE→MEDIA-ROOM→HALLWAY-7→LIVING-ROOM→BALLROOM-8, goal.zil:456).

## The win condition — twelve clues, exactly
`CASE-OVER` (events.zil:307) prints the winning "Congratulations!" ending only
when: the arrest names Michael **with** Alicia (CORRECT?), `DETECTIVE-SEEN` ==
`DETECTIVE-CONVINCED` = 12 (people.zil:3669), and Michael is not dead. Miss any
clue → jury acquits (events.zil:342) → loss.

Clue bookkeeping (people.zil:3655-3667 flags; increments in DETECTIVE-F /
CHECK-GLASS):
* 1 corpse, 2 lariat/rope — AUTO +2 when the detective searches the office
  (people.zil:4287). This is why you must LEAVE the lariat in place.
* 3 business card `show card to detective` (+1)
* 4 sale agreement `show manila folder to detective` (+1)
* 5 trust documents `show trust folder to detective` (+1)
* 6 investor list `show paper to detective` (+1)
* 7 dark hair (in the fairy mask, revealed by `look in fairy mask`)
  `show hair to detective` (+1)
* 8/9/10 broken glass → `detective, analyze glass for fingerprints` gives +3 at
  once (glass-seen + analyzed + printed, CHECK-GLASS people.zil:4069)
* 11/12 Alicia's soaked coat + the rain timing: `show wet overcoat to detective`
  then `tell detective about rain` gives +2 together (each is +0 alone; the
  second one of the pair pays out, people.zil:3916/3999). Requires
  SAW-RAIN-SLACK-OFF? (set by noting the drizzle, things.zil:225).
= 12 → `detective, arrest michael and alicia`.

## The two hard constraints (why order matters)
* **The detective arrests YOU** the moment he reaches the ballroom fireplace
  (BALLROOM-8) if `DETECTIVE-SEEN <= 4` (I-START-ARREST, people.zil:4290/4373;
  cancelled while DETECTIVE-SEEN > 4, people.zil:4374). So intercept him while he
  is ROAMING the hallways, never at the fireplace. Once you show the first item,
  GRAB-ATTENTION (goal.zil:611) freezes him so you can dump the rest in place.
* **Never be caught holding / standing over the body** (PLAYER-SEEN-WITH-BODY?),
  and never take the lariat (DONT-TAKE-EVIDENCE, people.zil:1810). Do all office
  looting before the body is discovered.

## Address-the-detective grammar
`analyze glass ...` as the player → "You don't have the equipment"; you must
address him: `detective, analyze glass for fingerprints`. Likewise the arrest is
`detective, arrest michael and alicia` (bare `arrest ...` → "citizen's arrest ...
only in the movies"). Diagonals must be abbreviations (`sw`, not `southwest`,
which is not in the vocabulary); n/s/e/w full words are fine.

## Determinism / verification
Machine-validated on the GameWalker pathway at seed 1: won=True, died=False,
win_text_seen=True, 110 commands, murderers arrested at the 23:29 clock tick.
`scripts/solve_suspect_adaptive.py --seed 1` reproduces the exact command list;
`scripts/replay_solve.py ... --seeds 24` verifies it (stops at the seed-1 win).

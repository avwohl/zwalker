# Pentari (Howard A. Sherman, 1998) — research notes

Binary: `games/zcode/pentari.z5` — Release 6 / Serial 030206 / Inform v6.21
Library 6/10, Z-machine V5. Boots cleanly to "Your Quarters"; two boots are
byte-identical (no boot-time RNG), so the RNG seed is pinned right after
`start()` with no `restart` prelude.

Title/author confirmed from the boot banner:
> Pentari — An Interactive Prequel To First Light — Copyright 1998 (C)
> Howard A. Sherman.

Max score: the SCORE verb reports "out of a possible 70"; `get_max_score`
returns None for this post-Infocom V5 title, so the walkthrough header declares
`#% MAX_SCORE: 70`.

## Premise
You are the Captain of Charlie Company. The wizard Morden transports you (via a
Pentarian Transporter + the word of bringing `covert`) into the abandoned
castle of the former Duke of Bostwin, now occupied by the ancient Dark Elf
**Vamvevmew**. Morden has sealed magic inside the castle; you must break his
ward, then stop Vamvevmew. The "Empirical Emerald" and its freed "daughter"
stone hold the essence of the imprisoned Duke **Galin**; crowning the platinum
box in the summoning circle frees Galin, who finishes the elf.

## Spells (cast by typing the word)
- `CITY` — the transporter's word; instead of the Bank it drops you in the
  guild's Entrance Hall (Library is E, Morden is there). +5.
- `COVERT` — Morden's "word of bringing"; teleports you into Vamvevmew's castle
  and makes you covert, so the elf wanders "looking for something" (you) but
  can't attack — until you carry the freed emerald.
- `FWOOSH` — "summon a fireball", taught by the dirty scroll. In the Treasury it
  blasts the oaken chest open; cast with the elf present it hits HIM (fatal to
  you); cast in an empty room it just washes over you.

## Castle map (all reachable via `covert`)
```
                 Barracks
                    |
   Treasury ---- (N) ---- [oaken chest -> emerald]
      | S
   Armory [dagger] --E-- Main Hall --N-- Main Hall by Fireplace --IN-- [scroll]
      (N Treasury)          |S                  (fireplace)
                          Castle (hub: N Main Hall, S Entrance, E Sitting,
                          W Audience)
                            |S
                       Castle Entrance [Magical Seal]
   Spiral Stairway (E of Main Hall): N Dining[towel]->N Kitchen ;
                                     U Upper Level[platinum box, ash circle];
                                     D Dungeon -> N Cell[Galin's note]
```
Sitting Room, Audience Chamber, Kitchen, Barracks, Dungeon Cell are essentially
atmosphere / red herrings (no points).

## Scoring (max 70) — verified by the score timeline
| action | pts | cum |
|---|---|---|
| `CITY` (transport to guild) | 5 | 5 |
| `SMASH SEAL` (shatter the ward) | 10 | 15 |
| `GET SCROLL` (fireplace; learns Fwoosh) | 10 | 25 |
| `GET DAGGER` (Galin's blade, in the Armory) | 5 | 30 |
| `FWOOSH` (fireball opens the chest) | 10 | 40 |
| `GET SMALL EMERALD` (free the daughter stone) | 5 | 45 |
| `KILL ELF` (run him through while Morden holds him) | 10 | 55 |
| crown the box / summon Galin (the final `LOOK`) | 15 | 70 |

## Three endings (from the game's own strings + IF Archive note)
Freeing the daughter emerald shatters the anti-magic ward; Morden detects this
and teleports in to duel the elf. When you then carry the emerald and the elf
finds you, he steals it and drags you into the duel room (Upper Level).
1. **Kill the elf yourself, then crown the box (MAX, 70).** While Vamvevmew is
   distracted fighting Morden you `kill elf` and run him through from behind;
   placing the emerald summons Galin, who finds "the corpse of his ancient
   nemesis" ("Damn it, I wanted the privilege."). This is the ending recorded.
2. **Crown the box while the elf is alive & duelling (variant).** Galin throws
   the dagger through Vamvevmew's shield into his throat.
3. **Crown the box with no one in the room (60).** Galin takes the dagger,
   dashes out, kills the elf offstage (the "THUD of a dead body"). This is what
   the IF Archive walkthrough does — it stops at 60/70, missing the two combat
   points (+10 KILL) and reaching only the +15 "no one present" ending.
Attacking the elf when he is NOT distracted by Morden = instant decapitation
death (`13fda`). FWOOSH-ing the elf = enraged, he cuts you down (`1490a`).

## The one source of randomness: the Dark Elf's wander
The elf random-walks the castle each turn (seed-dependent). Two consequences:
1. FWOOSH in the Treasury opens the chest only if the elf is absent that turn;
   otherwise the fireball hits him and he kills you. The adaptive recorder waits
   (`Z`) for him to leave the Treasury before FWOOSH.
2. You must MEET the elf while holding the freed emerald to trigger the duel.
   The recorder walks to the Main Hall (the four-exit hub the elf passes through
   often) and waits until the "senses your aura of power" encounter fires, then
   `kill elf`. Under seed 7 two hub waits suffice; the fixed 35-command list
   this produced is verified by replay_solve at seed 3 (it wins at many seeds —
   3, 7, 9, 11, 12, ...; the harness reports the first, seed 3).

## Harness quirks learned here
- `EMERALD` is ambiguous (the small emerald vs. the jewels on the dagger) —
  always say `SMALL EMERALD`.
- Multi-word commands ("SMASH SEAL", "GET SMALL EMERALD", "PUT SMALL EMERALD ON
  BOX") must be kept as single command strings; the game is lenient enough that
  a bare "SMASH"/"GET"/"OPEN" also acts, which can mask a split-command bug.
- No walker rollback issues on the winning route (all directions succeed); the
  route uses no blocked moves.
- `#% WIN_TEXT: \*\*\*\s*You have won\s*\*\*\*` plus `#% MAX_SCORE: 70` gate the
  win; only the 70-point kill-it-yourself ending reaches score 70.

## Sources
- IF Archive `solutions/pentari.sol` (Howard Sherman's own direct walkthrough;
  reaches 60/70, lists the three endings) — verbatim copy in
  `logs/pentari_source_ifarchive.txt` (gitignored).
- The game binary itself — decoded Z-strings for the ending/lore/scoring text
  (Morden's briefing, Galin & Vamvevmew lore, the three ending narratives, the
  combat/kill messages). The binary is the authority for the 70-point path.

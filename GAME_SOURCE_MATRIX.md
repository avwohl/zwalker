# ZIL / ZILF game source ↔ Z-machine version matrix

Purpose: enumerate every game whose **ZIL or ZILF source is available**, tag each
with its Z-machine story-file version, and track how many zwalker "finished
tests" exist per version. Two independent test tracks count:

- **from-source** — zorkie compiles the ZIL/ZILF source and zwalker replays a
  walkthrough to a verified win (the L2 suite, `scripts/test_zorkie_game.py`).
  This is the column that matters for the zorkie compiler.
- **binary-solved** — zwalker solved the *released* `.z` binary (no compile).
  These are the 50 verified solves / broader binary corpus in `games/zcode/`.

Legend for the **from-source** column: ✅ win · ⚙️ compiles (no win yet) ·
🚧 code-generates but blocked · ✋ source-blocked · — not attempted.

Last updated: 2026-07-20. Source data: local `historicalsource` ZIL submodules
(`../zorkie/tests/test-games/infocom-zil/`), the ZILF distribution, the
Obsessively Complete Infocom Catalog (eblong.com/infocom), and IFDB/IFWiki.

---

## 1. Infocom ZIL source (the `historicalsource` corpus)

40 game sources are mirrored as submodules under
`../zorkie/tests/test-games/infocom-zil/`. Version = the `<VERSION …>` directive
/ the release `.z` in each source tree (ZIP=v3, EZIP=v4, XZIP=v5, YZIP=v6).

### Z-machine V3 (ZIP) — 27 sources

| Game | source dir | from-source | note |
|------|-----------|:-----------:|------|
| Zork I | zork1 | ✅ 350/350 | |
| Zork II | zork2 | ✅ 400/400 | route re-derived (PROPDEF/carry limits) |
| Zork III | zork3 | ✅ 7/7 | lockstep-identical to R25 |
| Mini-Zork I | minizork-1987 | ✅ 350/350 | matches official binary post-PROPDEF |
| Mini-Zork II | minizork-1982 | ⚙️ boots | "West of House"; 12-file build, trimmed 1982 source |
| Deadline | deadline | ✅ win | |
| Starcross | starcross | ✅ 400/400 | lockstep-identical to R18 |
| Suspended | suspended | ✅ win | |
| The Witness | witness | ✅ win | |
| Planetfall | planetfall | ✅ 80/80 | fixed by repointing submodule to the-infocom-files (complete source) |
| Enchanter | enchanter | ✅ 400/400 | |
| Infidel | infidel | ✅ 400/400 | |
| Sorcerer | sorcerer | ✅ 400/400 | |
| Seastalker | seastalker | ⚙️ boots | seastalker.zil; name-entry flow + "lab center" |
| Cutthroats | cutthroats | ✅ 250/250 | |
| Hitchhiker's Guide | hitchhikersguide | ✅ 400/400 | |
| Suspect | suspect | ✅ win | conviction ending; route re-derived |
| Wishbringer | wishbringer | ✅ 100/100 | time-game; WIN_TEXT_SUFFICIENT |
| Spellbreaker | spellbreaker | ✅ 600/600 | |
| Ballyhoo | ballyhoo | ✅ 200/200 | |
| Leather Goddesses of Phobos | leathergoddesses | ✅ win | self-randomized score |
| Moonmist | moonmist | ✅ win | |
| Hollywood Hijinx | hollywoodhijinx | ✅ 150/150 | |
| Plundered Hearts | plunderedhearts | ✅ 25/25 | |
| Stationfall | stationfall | ✅ 80/80 | |
| The Lurking Horror | lurkinghorror | ✅ 100/100 | |
| Infocom Sampler | infocom-sampler | ⚙️ boots | sampler.zil; demo menu (Zork/Planetfall/Infidel/Witness) |

### Z-machine V4 (EZIP) — 4 sources

| Game | source dir | from-source | note |
|------|-----------|:-----------:|------|
| A Mind Forever Voyaging | amfv | ✅ win | scoreless; first V4 game |
| Trinity | trinity | ✅ 100/100 | first V4 game |
| Bureaucracy | bureaucracy | ⚙️ boots | b.zil; MDL-ZIL dialect; 1987 banner + license form |
| Nord and Bert | nordandbert | ✋ | source-incomplete (PICK-NEXT defined nowhere) |

### Z-machine V5 (XZIP) — 4 sources

| Game | source dir | from-source | note |
|------|-----------|:-----------:|------|
| Beyond Zork | beyondzork | — | needs a V5 target |
| Border Zone | borderzone | — | needs a V5 target |
| Border Zone (prototype "spy") | checkpoint | — | spy.z5 |
| Sherlock | sherlock | — | needs a V5 target |

### Z-machine V6 (YZIP) — 5 sources

| Game | source dir | from-source | note |
|------|-----------|:-----------:|------|
| Zork Zero | zorkzero | — | V6 graphical; needs a V6 target |
| Journey | journey | — | V6 |
| Arthur | arthur | — | V6 |
| Restaurant at the End of the Universe (HHGG 2, unreleased) | restaurant | — | h2.z6 |
| Abyss (demo) | abyss | — | abyss.z6 |

**Infocom ZIL source NOT in the local corpus** (source not public / not mirrored):
Shogun (v6). Everything else Infocom shipped has source here.

---

## 2. ZILF source (modern ZIL, compiled by ZILF/zorkie)

ZILF (Tara McGrew's open-source ZIL compiler, 2010–) targets V3/V4/V5/V8.
"Source" here means hand-written ZIL that is not Infocom's.

| Game | source | .z version | from-source | note |
|------|--------|:----------:|:-----------:|------|
| Cloak of Darkness (ZILF sample) | cloak.zil | v3 | ⚙️ runs | parser+movement work; blocked on the ZILF scope engine (#10) for object resolution |
| Cloak of Darkness (extended) | cloak_plus.zil | v5 | — | ZILF sample; needs V5 target |
| Colossal Cave / Advent (ZILF port) | advent.zil | v3 | — | ZILF sample (Jesse McGrew port) |
| zil_test (ZILF sample) | zil_test.zil | v3 | — | ZILF test game |
| microquest (zorkie toy) | microquest.zil | v3 | ✅ win | self-contained ZIL toy |
| mazekey (zorkie toy) | mazekey.zil | v3 | ✅ win | self-contained ZIL toy |
| reactor (zorkie toy) | reactor.zil | v3 | ✅ win | self-contained ZIL toy |
| Milliways: Restaurant at the End of the Universe (Max Fog, IFComp 2023) | (community) | v5/v8 | — | first IFComp entry in ZIL |
| Thread Unlocked (Max Fog) | (community) | ? | — | minimal ZIL choice game |
| Method in my Madness (Max Fog) | (community) | ? | — | minimal ZIL choice game |

Note: the ZILF standard library's parser uses a VERBS/syntax-table layout the
zorkie codegen does not yet emit (`_is_classic_parser=False`), so ZILF-library
games (cloak, advent, Milliways) compile but don't yet play — this is the next
frontier and would unlock the whole ZILF-library corpus at once.

---

## 3. Finished-tests-per-version summary

"From-source wins" (the precise zorkie metric) = games whose **ZIL/ZILF source**
zorkie compiles and zwalker drives to a verified win — the L2 registry, exact.
The last two columns are context, not the deliverable: "binaries present" is a
raw count of `.z` files in `games/zcode/` (an inventory, mostly Inform-era
downloads, NOT all solved); "verified solves" ≈ the released-binary wins on
record (`solutions/*_verified.json` with won=true; a mix of tracks, so
approximate). See `TODO.md` for the binary-solve history.

| Z-ver | known ZIL src | known ZILF src | **from-source wins** | binaries present | verified solves (≈) |
|:-----:|:-------------:|:--------------:|:--------------------:|:----------------:|:-------------------:|
| v1 | 0¹ | 0 | 0 | 2 | 1 |
| v2 | 0¹ | 0 | 0 | 0 | 0 |
| **v3** | 27 | 6² | **27** (24 Infocom + 3 toys) | 33 | 32 |
| **v4** | 4 | 0 | **2** (trinity, amfv) | 4 | 2 |
| v5 | 4 | 1 (cloak_plus) | 0 | 83 | 17 |
| v6 | 5 | 0 | 0 | 2 | 0 |
| v7 | 0 | 0 | 0 | 0 | 0 |
| v8 | 0 | 0³ | 0 | 21 | 4 |
| **total** | **40** | **~7** | **29** | **~145** | **~56** |

¹ Zork I's earliest revisions are v1/v2 but only the v3 ZIL source is in the corpus.
² 3 zorkie toys (microquest/mazekey/reactor) + the ZILF samples cloak/advent/zil_test.
³ Milliways (Max Fog, IFComp 2023) is likely v5 or v8 but its source isn't in the corpus.

### Headline

- **29 from-source wins** — 27 V3 + 2 V4 — every V3 Infocom source with a
  verified route, plus the first two V4 games (Trinity, AMFV). Registered and
  green in `scripts/test_zorkie_game.py`.
- **4 more compile+boot** (Phase 1): seastalker, bureaucracy (V4 MDL-ZIL),
  minizork2, sampler — no counted win only because they lack a
  locally-distributable published binary for route derivation; they are the
  binary/solve track's next route-derivation candidates.
- **V5/V6 Infocom sources (9)** are un-attempted: they need a zorkie V5/V6 target.
- **cloak** compiles as V3 but the ZILF-library parser-table format blocks a win.
- **planetfall** now WINS 80/80: its historicalsource `comptwo.zil` was
  truncated, but the-infocom-files has the complete source (submodule repointed).

## Sources

- [The Obsessively Complete Infocom Catalog (eblong.com)](https://eblong.com/infocom/)
- [Z-machine versions — IFWiki](https://www.ifwiki.org/Z-machine_versions)
- [ZILF — IFWiki](https://www.ifwiki.org/ZILF) · [ZIL — IFWiki](https://www.ifwiki.org/ZIL)
- [historicalsource org (Infocom ZIL, Jason Scott 2019)](https://github.com/historicalsource)
- [taradinoc/zilf (ZILF mirror)](https://github.com/taradinoc/zilf)
- [Milliways / Max Fog — first ZIL IFComp entry (2023)](https://www.ifwiki.org/ZIL)

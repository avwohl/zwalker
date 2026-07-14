# ZWalker - TODO & Status

**Last Updated**: 2026-07-14

## Current Status

- **Verified complete solves: both classic trilogies plus the complete
  Planetfall series and Wishbringer — Zork I 350/350, Zork II 400/400,
  Zork III 7/7, Enchanter 400/400, Sorcerer 400/400, Spellbreaker 600/600,
  Planetfall 80/80, Wishbringer 100/100, Stationfall 80/80**
  (won, replay-verified with `scripts/replay_solve.py` at fixed RNG seeds;
  `solutions/{zork1,zork2,zork3,enchanter,sorcerer,spellbreaker,planetfall,wishbringer,stationfall}_verified.json`)
- **82 solution files tracked in git** (73 `*_solution.json` exploration runs + 9 verified
  solves); the 2026-02-05 batch run produced ~58 more exploration runs that are local-only
  (`.gitignore` excludes new `solutions/*_solution.json`)
- **155 test scripts** tracked (73 smart tests that tolerate random events)
- **Z-machine interpreter**: 100% CZECH compliance (1,604/1,604 tests across v3/v4/v5/v8;
  re-verified 2026-07-13)
- **Z2JS tests**: 7/7 passing as of 2026-02-05
- **Zorkie tests**: 43/64 passing (67%) as of 2026-02-05

Note: the batch "solves" are exploration/coverage runs (room mapping + command exercise),
not completed games. The only verified end-to-end wins are the Zork and
Enchanter trilogies, the Planetfall series, and Wishbringer.

## Unsolved Games

| Game | Reason |
|------|--------|
| czech (z3/z4/z5/z8) | Test suite, not playable |
| gntests (z5) | Test suite, not playable |
| Some IFDB/IF Archive games | Broken download links (HTTP 404) |

Note: failsafe and plundered got exploration runs in the 2026-02-05 batch (local output,
not tracked in git); neither has a verified win.

## TODO

### High Priority

1. **Handle Y/N and menu prompts** - Games like failsafe use `(Y/N)?>` prompts
   - Detect prompt patterns: `(Y/N)?`, `Select an option`, numbered menus
   - Add Y/N/number responses to solver

2. **More verified solves** - Extend the replay-verified treatment
   (`scripts/replay_solve.py` + per-game adaptive recorders like
   `scripts/solve_{zork3,enchanter,sorcerer,spellbreaker,planetfall,wishbringer,stationfall}_adaptive.py`)
   to other games (e.g. The Lurking Horror, Hitchhiker's Guide)

3. **Compile more games with z2js** - many games pending compilation
   (24 `scripts/*_z2js.js` compiled-game scripts tracked vs. a 155-story-file corpus)
   - Use `scripts/compile_games_for_testing.sh`
   - Or manually: `cd ~/src/z2js && python -m jsgen /path/to/game.z5`

### Medium Priority

4. **Implement hints system** - Use human walkthrough files to guide AI
   - See `docs/HINTS_ENHANCEMENT.md` for design
   - Parse hint files from `walkthroughs/` directory
   - Add to advanced solver context

5. **Improve AI solver for hard games**
   - Better maze handling
   - Timing puzzle support
   - Multi-step dependency planning

6. **Output comparison tool** - Compare z2js output with zwalker
   - Extend `scripts/compare_outputs.py`
   - Detect regressions automatically

### Low Priority

7. **CI/CD integration** - GitHub Actions for automated testing
8. **Performance benchmarks** - z2js vs native execution time
9. **More IF Archive games** - Expand game collection

## Architecture

```
zwalker/
├── zmachine.py      # Z-machine interpreter (1,604/1,604 CZECH across v3/v4/v5/v8)
├── walker.py        # Game exploration engine
├── agentic_solver.py # Agentic solver: perceive→act→verify + nav + backtracking
├── ai_assist.py     # Basic AI integration
├── advanced_solver.py # Strategic AI solver (Opus)
├── knowledge.py     # Persistent cross-run knowledge base
└── cli.py           # Command-line interface

scripts/
├── replay_solve.py     # Deterministic seed-search walkthrough verifier
├── solve_game.py       # Single game AI solver
├── solve_with_opus.py  # Advanced Opus solver
├── generate_test_script.py  # Test generator
├── generate_all_tests.py    # Batch test generator
├── run_all_tests.sh         # Test runner
└── test_zorkie_compilation.py  # Zorkie tester

solutions/           # 9 verified solves + 73 exploration runs (JSON, tracked)
scripts/test_*.js    # 155 generated test scripts (73 smart)
```

## Key Tools

| Tool | Purpose |
|------|---------|
| `solve_game.py` | AI-solve a single game |
| `solve_with_opus.py` | Advanced Opus solver with strategy |
| `replay_solve.py` | Deterministic seed-search walkthrough verifier |
| `generate_test_script.py` | Generate JS test from solution |
| `generate_all_tests.py` | Batch generate all tests |
| `run_all_tests.sh` | Run all z2js tests |
| `test_zorkie_compilation.py` | Test Zorkie compiler |
| `analyze_coverage.py` | Solution statistics |

## Test Commands

```bash
# Solve a game
python scripts/solve_game.py games/zcode/zork1.z3 --real-ai

# Verify a walkthrough deterministically (seed search)
python3 scripts/replay_solve.py games/zcode/zork1.z3 walkthroughs/zork1_verified_350.txt --seeds 4

# Advanced solving with Opus
python scripts/solve_with_opus.py games/zcode/zork1.z3

# Generate test scripts (basic - no random event handling)
python scripts/generate_all_tests.py

# Generate smart tests (handles random events like combat/thief/grue)
python scripts/generate_all_smart_tests.py --force

# Run z2js tests (basic)
./scripts/run_all_tests.sh

# Run smart z2js tests (recommended - handles random events)
./scripts/run_smart_tests.sh

# Test Zorkie compiler
python scripts/test_zorkie_compilation.py
```

## Smart Tests

The smart test system (`generate_smart_test.py`) handles random events during playback:
- **Thief encounters** - fights with sword or drops valuables
- **Troll encounters** - fights or flees
- **Grue warnings** - lights lamp or retreats
- **Combat attacks** - fights or flees
- **Cyclops** - gives lunch or says "odysseus"

This allows solutions to work even when random events occur at different times.

## Notes

- Test suites (czech, gntests) are not playable games - excluded from coverage
- Exploration runs: 131 solution files locally (73 tracked in git); roughly 120 distinct
  playable games after deduplicating variants and excluding test suites
- Human walkthroughs available in `walkthroughs/` for ~12 games
- Verified wins come from the agentic solver + `scripts/replay_solve.py` replay verification
- Batch solver completed 2026-02-05: 56 new exploration runs (local-only, gitignored)

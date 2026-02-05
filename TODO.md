# ZWalker - TODO & Status

**Last Updated**: 2026-02-05

## Current Status

- **130+ games solved** (exceeds target of 130)
- **74 test scripts** generated (107 games pending test generation)
- **24,488 total commands** across solutions
- **Z-machine interpreter**: 100% CZECH compliance (425/425 tests)
- **Z2JS tests**: 7/7 passing (100%)
- **Zorkie tests**: 43/64 passing (67%)

## Unsolved Games

| Game | Reason |
|------|--------|
| czech (z3/z4/z5/z8) | Test suite, not playable |
| gntests (z5) | Test suite, not playable |
| Some IFDB/IF Archive games | Broken download links (HTTP 404) |

Note: failsafe and plundered are now solved as of 2026-02-05.

## TODO

### High Priority

1. **Handle Y/N and menu prompts** - Games like failsafe use `(Y/N)?>` prompts
   - Detect prompt patterns: `(Y/N)?`, `Select an option`, numbered menus
   - Add Y/N/number responses to solver

2. **Solve plundered** - Manual intervention or improved solver needed

3. **Compile more games with z2js** - 61 games pending compilation
   - Use `scripts/compile_games_for_testing.sh`
   - Or manually: `cd ~/src/z2js && python -m jsgen /path/to/game.z5`

### Medium Priority

4. **Implement hints system** - Use human walkthrough files to guide AI
   - See archived `docs/HINTS_ENHANCEMENT.md` for design
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
├── zmachine.py      # Z-machine interpreter (425/425 CZECH)
├── walker.py        # Game exploration engine
├── ai_assist.py     # Basic AI integration
├── advanced_solver.py # Strategic AI solver (Opus)
└── cli.py           # Command-line interface

scripts/
├── solve_game.py       # Single game AI solver
├── solve_with_opus.py  # Advanced Opus solver
├── generate_test_script.py  # Test generator
├── generate_all_tests.py    # Batch test generator
├── run_all_tests.sh         # Test runner
└── test_zorkie_compilation.py  # Zorkie tester

solutions/           # 130+ game solutions (JSON)
scripts/test_*.js    # 74 generated test scripts
```

## Key Tools

| Tool | Purpose |
|------|---------|
| `solve_game.py` | AI-solve a single game |
| `solve_with_opus.py` | Advanced Opus solver with strategy |
| `generate_test_script.py` | Generate JS test from solution |
| `generate_all_tests.py` | Batch generate all tests |
| `run_all_tests.sh` | Run all z2js tests |
| `test_zorkie_compilation.py` | Test Zorkie compiler |
| `analyze_coverage.py` | Solution statistics |

## Test Commands

```bash
# Solve a game
python scripts/solve_game.py games/zcode/zork1.z3 --real-ai

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
- Effective coverage of playable games: 130+ (target met: 130 games)
- Human walkthroughs available in `walkthroughs/` for ~12 games
- Advanced solver uses Claude Opus for better puzzle solving
- Batch solver completed 2026-02-05: 56 new games solved, 135 total solutions

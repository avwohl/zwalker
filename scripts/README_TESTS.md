# Z2JS Test Scripts

This directory contains automatically generated test scripts for validating z2js-compiled games.

## Overview

We have generated **28 test scripts** from solution JSON files. These scripts can run commands through z2js-compiled games and verify correct execution.

## Current Status

### Test Scripts Generated
- **28** JavaScript test scripts created from solution files
- Located in: `scripts/test_*_solution.js`

### Available Z2JS Files
Currently, we have z2js-compiled versions for:
- ✓ **905** (9:05 game)
- ✓ **amfv** (A Mind Forever Voyaging)
- ✓ **lostpig** (Lost Pig)
- ✓ **trinity** (Trinity)
- ✓ **zork1** (Zork I)

### Pending Compilation
23 more games have test scripts ready but need z2js compilation:
- acheton, advent, adv440, adv550, adverbum, aisle, allroads, anchor, animals
- bedlam, bluechairs, booth, bunny, candy, catseye, dreamhold, enchanter
- jigsaw, lists, planetfa, zork2, zork3, and more

## Quick Start

### Generate all test scripts
```bash
python scripts/generate_all_tests.py
```

### Run a specific test
```bash
cd scripts
node test_zork1_solution.js
```

### Run all available tests
```bash
./scripts/run_all_tests.sh
```

## How It Works

1. **Solution files** (`solutions/*.json`) contain game commands
2. **Generator script** (`generate_test_script.py`) creates JavaScript test files
3. **Test scripts** (`test_*_solution.js`) run commands through z2js games
4. **Test runner** (`run_all_tests.sh`) executes all tests with z2js files

## Test Script Structure

Each generated test script:
- Loads the z2js-compiled game
- Executes all commands from the solution
- Shows progress every 30 commands
- Captures and displays final output
- Detects victory conditions and scores
- Returns exit code 0 on success

## Example Test Run

```bash
$ node test_zork1_solution.js
============================================================
 ZORK1: Z2JS ENGINE TEST
============================================================
Running 800 commands

--- Progress: 30/800 commands ---
--- Progress: 60/800 commands ---
...
--- All commands executed ---

FINAL OUTPUT:
[Last 2000 characters]

Final Score: 350/350 points
✓ VICTORY: Game completed!

============================================================
 TEST COMPLETE
============================================================
```

## Adding More Tests

To add tests for more games:

1. **Get a solution file**: Create or find a `{game}_solution.json` in `solutions/`
2. **Generate test script**: Run `python scripts/generate_test_script.py solutions/{game}_solution.json`
3. **Compile with z2js**: Use z2js to create `{game}_z2js.js` in the scripts directory
4. **Run the test**: `node test_{game}_solution.js`

## Next Steps

To achieve full test coverage:

1. **Compile remaining games** with z2js (23 games ready for testing)
2. **Generate more solutions** for untested games
3. **Integrate into CI/CD** for automated regression testing
4. **Add output comparison** between zwalker and z2js

## Compilation Instructions

To compile a game with z2js:

```bash
cd ~/src/z2js
python -m jsgen /path/to/game.z5
mv game.js /path/to/zwalker/scripts/game_z2js.js
```

Then run the test:
```bash
cd /path/to/zwalker/scripts
node test_game_solution.js
```

## Tools

- `generate_test_script.py` - Generate single test script
- `generate_all_tests.py` - Generate all test scripts from solutions/
- `run_all_tests.sh` - Run all tests (requires z2js files)
- `test_*_solution.js` - Generated test scripts (28 total)

## Documentation

See `docs/TEST_GENERATION.md` for detailed documentation on:
- Command-line options
- Solution file formats
- CI/CD integration
- Troubleshooting

## Test Coverage Goals

- ✅ **Current**: 5 games fully testable
- 🎯 **Next**: 23 games with test scripts (need z2js compilation)
- 🎯 **Target**: 50+ games with comprehensive test coverage

## Files in This Directory

### Generated Test Scripts (28)
- `test_905_solution.js` - 9:05 game (0 commands)
- `test_acheton_solution.js` - Acheton (2444 commands)
- `test_advent_solution.js` - Colossal Cave Adventure (800 commands)
- `test_zork1_solution.js` - Zork I (800 commands)
- ... and 24 more

### Z2JS Compiled Games (5 working)
- `905_z2js.js`
- `amfv_z2js.js`
- `lostpig_z2js.js`
- `trinity_z2js.js`
- `zork1_z2js.js`

### Tools
- `generate_test_script.py` - Test generator
- `generate_all_tests.py` - Batch generator
- `run_all_tests.sh` - Test runner

---

**Last updated**: 2026-01-26
**Test scripts**: 28 generated, 5 runnable
**Coverage**: 5/28 games (18%), 23 pending z2js compilation

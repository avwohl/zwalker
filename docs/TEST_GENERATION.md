# Test Script Generation for z2js

This document explains how to generate and run JavaScript test scripts for z2js-compiled games.

## Overview

The test script generator creates Node.js test scripts from solution JSON files. These scripts can be run against z2js-compiled games to verify correct execution and detect regressions.

## Quick Start

### Generate a single test script

```bash
python scripts/generate_test_script.py solutions/zork1_solution.json
```

This will create `scripts/test_zork1_solution.js`.

### Generate all test scripts

```bash
python scripts/generate_all_tests.py
```

This scans the `solutions/` directory and generates test scripts for all games.

### Run a single test

```bash
cd scripts
node test_zork1_solution.js
```

Note: This requires `zork1_z2js.js` to exist in the same directory.

### Run all tests

```bash
./scripts/run_all_tests.sh
```

This runs all generated test scripts that have corresponding z2js files.

## Generated Test Scripts

Each generated test script:

1. Loads the z2js-compiled game using `require()`
2. Executes commands from the solution file
3. Captures and displays game output
4. Reports progress every 30 commands
5. Detects victory conditions and final scores
6. Exits with code 0 on success, 1 on failure

### Example Output

```
============================================================
 ZORK1: Z2JS ENGINE TEST
============================================================
Running 800 commands

--- Progress: 30/800 commands ---
--- Progress: 60/800 commands ---
...
--- All commands executed ---

FINAL OUTPUT:
[Last 2000 characters of game output]

Final Score: 350/350 points

✓ VICTORY: Game completed!

============================================================
 TEST COMPLETE
============================================================
```

## Command-Line Options

### generate_test_script.py

```bash
python scripts/generate_test_script.py [OPTIONS] SOLUTION_FILE

Arguments:
  SOLUTION_FILE         Solution JSON file (e.g., solutions/zork1_solution.json)

Options:
  -o, --output PATH     Output test script path (default: scripts/test_{game}_solution.js)
  -z, --z2js-file PATH  Path to z2js compiled file (default: ./{game}_z2js.js)
  --no-progress         Disable progress reporting during test
  --final-output N      Number of characters to show in final output (default: 2000)
```

### generate_all_tests.py

```bash
python scripts/generate_all_tests.py [OPTIONS]

Options:
  --solutions-dir DIR   Directory containing solution JSON files (default: solutions/)
  --output-dir DIR      Directory to write test scripts (default: scripts/)
  --force               Overwrite existing test scripts
  --no-progress         Disable progress reporting in generated tests
```

## Solution File Format

The generator supports two JSON formats:

### Format 1: commands field

```json
{
  "game": "zork1",
  "commands": [
    "n",
    "open window",
    "go in",
    "take lamp"
  ]
}
```

### Format 2: solution_commands field

```json
{
  "game": "games/zcode/lists.z5",
  "solution_commands": [
    "look",
    "take box"
  ]
}
```

The generator automatically detects which format is used.

## Z2JS Compilation

Before running tests, you need to compile games to JavaScript using z2js:

```bash
cd ~/src/z2js
python -m jsgen path/to/game.z5
```

This creates `game.js` which should be renamed to `game_z2js.js` and placed in the `scripts/` directory.

## Integration with CI/CD

The test scripts can be integrated into continuous integration:

```bash
# Generate tests
python scripts/generate_all_tests.py --force

# Run tests
./scripts/run_all_tests.sh

# Exit code indicates success/failure
```

## Current Status

As of 2026-01-26, we have:

- **26 solution files** in the `solutions/` directory
- **26 test scripts** generated successfully
- Test scripts for: zork1, zork2, zork3, lostpig, lists, acheton, advent, enchanter, and 18 more games

## Troubleshooting

### "No commands found"

The solution file might be using a different field name. The generator supports both `commands` and `solution_commands` fields.

### "Cannot find module './game_z2js.js'"

The z2js-compiled file doesn't exist. You need to:
1. Compile the game with z2js: `python -m jsgen game.z5`
2. Rename the output to `game_z2js.js`
3. Place it in the `scripts/` directory

### Test times out

Some games with 800+ commands may take longer than 60 seconds. Edit `run_all_tests.sh` to increase the timeout value.

### Victory not detected

The victory detection looks for common patterns like:
- `*** You have won ***`
- `You have won`
- `Victory`
- `Congratulations`

If your game uses different text, the test will still pass but won't show the victory message.

## Future Enhancements

Possible improvements:

1. **Parallel test execution** - Run multiple tests concurrently
2. **Output comparison** - Compare z2js output with native zwalker output
3. **Coverage reports** - Track which game features are tested
4. **Regression detection** - Automatically detect changes in game output
5. **Performance benchmarks** - Measure execution time and memory usage

## Related Files

- `scripts/generate_test_script.py` - Single test generator
- `scripts/generate_all_tests.py` - Batch test generator
- `scripts/run_all_tests.sh` - Test runner
- `scripts/test_z2js.py` - Original integration test (deprecated)
- `solutions/` - Solution JSON files
- `scripts/test_*_solution.js` - Generated test scripts

## See Also

- [README.md](../README.md) - Project overview
- [STATUS.md](STATUS.md) - Project status
- [TEST_SUITES.md](TEST_SUITES.md) - Z-machine test suites

#!/bin/bash
#
# Compile games with z2js for testing
#
# This script compiles all games that have solution files but no z2js version yet.
# Requires z2js to be installed at ~/src/z2js
#

ZWALKER_DIR="$(cd "$(dirname "$0")/.." && pwd)"
Z2JS_DIR="${HOME}/src/z2js"
GAMES_DIR="${ZWALKER_DIR}/games/zcode"
SCRIPTS_DIR="${ZWALKER_DIR}/scripts"

echo "========================================"
echo "  Z2JS Game Compiler"
echo "========================================"
echo

# Check if z2js exists
if [ ! -d "$Z2JS_DIR" ]; then
    echo "Error: z2js not found at $Z2JS_DIR"
    echo "Please clone z2js first:"
    echo "  git clone https://github.com/yourrepo/z2js ~/src/z2js"
    exit 1
fi

# Check if jsgen module exists
if [ ! -f "$Z2JS_DIR/jsgen/__main__.py" ]; then
    echo "Error: z2js jsgen module not found"
    echo "Expected: $Z2JS_DIR/jsgen/__main__.py"
    exit 1
fi

echo "Z2JS directory: $Z2JS_DIR"
echo "Games directory: $GAMES_DIR"
echo "Output directory: $SCRIPTS_DIR"
echo

# Find games that need compilation
# (have test scripts but no z2js files)
games_to_compile=()

for test_script in "$SCRIPTS_DIR"/test_*_solution.js; do
    if [ ! -f "$test_script" ]; then
        continue
    fi

    game_name=$(basename "$test_script" | sed 's/test_\(.*\)_solution\.js/\1/')
    z2js_file="$SCRIPTS_DIR/${game_name}_z2js.js"

    if [ ! -f "$z2js_file" ]; then
        # Find the game file
        game_file=$(find "$GAMES_DIR" -name "${game_name}.z*" -type f | head -1)

        if [ -n "$game_file" ]; then
            games_to_compile+=("$game_name:$game_file")
        fi
    fi
done

if [ ${#games_to_compile[@]} -eq 0 ]; then
    echo "✓ All games are already compiled!"
    exit 0
fi

echo "Found ${#games_to_compile[@]} games to compile:"
for entry in "${games_to_compile[@]}"; do
    game_name="${entry%%:*}"
    echo "  - $game_name"
done
echo

read -p "Compile all these games? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo
compiled=0
failed=0

for entry in "${games_to_compile[@]}"; do
    game_name="${entry%%:*}"
    game_file="${entry#*:}"
    output_file="$SCRIPTS_DIR/${game_name}_z2js.js"

    echo -n "Compiling $game_name ... "

    # Run z2js compilation
    if (cd "$Z2JS_DIR" && python -m jsgen "$game_file") > /tmp/z2js_${game_name}.log 2>&1; then
        # Find the generated file
        generated_file=$(find "$Z2JS_DIR" -name "$(basename "$game_file" | sed 's/\.[^.]*$/.js/')" -type f -newer /tmp/z2js_start_${game_name} 2>/dev/null | head -1)

        if [ -z "$generated_file" ]; then
            # Try default location
            generated_file="$Z2JS_DIR/$(basename "$game_file" .z*)_$(basename "$game_file" | sed 's/.*\.\(z[0-9]\)/\1/').js"
        fi

        if [ -f "$generated_file" ]; then
            mv "$generated_file" "$output_file"
            echo "✓ done"
            ((compiled++))
        else
            echo "✗ generated file not found"
            echo "  Log: /tmp/z2js_${game_name}.log"
            ((failed++))
        fi
    else
        echo "✗ compilation failed"
        echo "  Log: /tmp/z2js_${game_name}.log"
        ((failed++))
    fi
done

echo
echo "========================================"
echo "  Compilation Summary"
echo "========================================"
echo "  Compiled: $compiled"
echo "  Failed:   $failed"
echo

if [ $compiled -gt 0 ]; then
    echo "✓ $compiled games compiled successfully"
    echo
    echo "Run tests with:"
    echo "  ./scripts/run_all_tests.sh"
fi

exit $failed

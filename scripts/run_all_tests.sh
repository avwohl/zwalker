#!/bin/bash
#
# Run all generated z2js test scripts
#
# This script runs all test_*_solution.js files in the scripts directory.
# Each test requires a corresponding *_z2js.js file to exist.
#

cd "$(dirname "$0")"

echo "========================================"
echo "  Running Z2JS Test Suite"
echo "========================================"
echo

# Find all test solution scripts
test_files=(test_*_solution.js)

if [ ${#test_files[@]} -eq 0 ]; then
    echo "No test files found!"
    exit 1
fi

echo "Found ${#test_files[@]} test files"
echo

passed=0
failed=0
skipped=0

for test_file in "${test_files[@]}"; do
    # Extract game name
    game_name=$(basename "$test_file" | sed 's/test_\(.*\)_solution\.js/\1/')
    z2js_file="${game_name}_z2js.js"

    # Check if z2js file exists
    if [ ! -f "$z2js_file" ]; then
        echo "⊙ $game_name - SKIPPED (no $z2js_file)"
        ((skipped++))
        continue
    fi

    echo -n "⟳ Testing $game_name ... "

    # Run test with timeout
    if timeout 60s node "$test_file" > "/tmp/test_${game_name}.log" 2>&1; then
        echo "✓ PASS"
        ((passed++))
    else
        exit_code=$?
        if [ $exit_code -eq 124 ]; then
            echo "✗ FAIL (timeout)"
        else
            echo "✗ FAIL (exit $exit_code)"
        fi
        echo "  Log: /tmp/test_${game_name}.log"
        ((failed++))
    fi
done

echo
echo "========================================"
echo "  Test Results"
echo "========================================"
echo "  Passed:  $passed"
echo "  Failed:  $failed"
echo "  Skipped: $skipped"
echo "  Total:   ${#test_files[@]}"
echo

if [ $failed -eq 0 ] && [ $passed -gt 0 ]; then
    echo "✓ All tests passed!"
    exit 0
else
    echo "✗ Some tests failed"
    exit 1
fi

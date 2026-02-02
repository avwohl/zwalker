#!/bin/bash
# Run smart z2js tests that handle random events

cd "$(dirname "$0")"

echo "========================================"
echo "  Running Smart Z2JS Test Suite"
echo "========================================"
echo ""

# Count files
SMART_TESTS=(test_*_smart.js)
echo "Found ${#SMART_TESTS[@]} smart test files"
echo ""

PASSED=0
FAILED=0
SKIPPED=0
EVENTS_TOTAL=0

for test_file in "${SMART_TESTS[@]}"; do
    game_name=$(echo "$test_file" | sed 's/test_\(.*\)_smart\.js/\1/')
    z2js_file="${game_name}_z2js.js"

    if [[ ! -f "$z2js_file" ]]; then
        echo "⊙ $game_name - SKIPPED (no $z2js_file)"
        ((SKIPPED++))
        continue
    fi

    echo -n "⟳ Testing $game_name ... "

    # Run test with timeout
    output=$(timeout 120 node "$test_file" 2>&1)
    exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        # Extract events count
        events=$(echo "$output" | grep -oP 'Events: \K\d+' | tail -1)
        events=${events:-0}
        ((EVENTS_TOTAL += events))
        echo "✓ PASS (events: $events)"
        ((PASSED++))
    elif [[ $exit_code -eq 124 ]]; then
        echo "✗ TIMEOUT"
        ((FAILED++))
    else
        echo "✗ FAIL"
        ((FAILED++))
        # Show last few lines on failure
        echo "$output" | tail -10
    fi
done

echo ""
echo "========================================"
echo "  Smart Test Results"
echo "========================================"
echo "  Passed:  $PASSED"
echo "  Failed:  $FAILED"
echo "  Skipped: $SKIPPED"
echo "  Total:   ${#SMART_TESTS[@]}"
echo ""
echo "  Random events handled: $EVENTS_TOTAL"
echo ""

if [[ $FAILED -eq 0 ]]; then
    echo "✓ All tests passed!"
    exit 0
else
    echo "✗ Some tests failed"
    exit 1
fi

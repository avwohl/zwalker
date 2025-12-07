#!/bin/bash
# Monitor the completion solver progress

echo "=== AI Game Completion Solver Status ==="
echo ""

# Check if running
if ps aux | grep 1059581 | grep -v grep > /dev/null; then
    echo "✓ Solver is RUNNING (PID: 1059581)"
else
    echo "✗ Solver is NOT running"
fi

echo ""
echo "=== Solutions Generated ==="
total=$(ls solutions/*.json 2>/dev/null | wc -l)
echo "Total solutions: $total"

if [ $total -gt 0 ]; then
    complete=$(grep -l '"completed": true' solutions/*.json 2>/dev/null | wc -l)
    incomplete=$(grep -l '"completed": false' solutions/*.json 2>/dev/null | wc -l)

    echo "  ✓ COMPLETE: $complete"
    echo "  ⚠ INCOMPLETE: $incomplete"
fi

echo ""
echo "=== Latest Log Output (last 30 lines) ==="
tail -30 logs/completion_solver.log 2>/dev/null || echo "(Log not yet written)"

echo ""
echo "=== Monitor Commands ==="
echo "Watch log:      tail -f logs/completion_solver.log"
echo "Count complete: grep -l '\"completed\": true' solutions/*.json | wc -l"
echo "Check process:  ps aux | grep 1059581"

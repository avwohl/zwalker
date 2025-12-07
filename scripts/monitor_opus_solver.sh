#!/bin/bash
# Monitor Opus solver progress on Zork I

LOG_FILE="logs/zork1_opus_solve.log"

echo "==================================================================="
echo "OPUS SOLVER - ZORK I - LIVE MONITOR"
echo "==================================================================="
echo ""

# Check if solver is running
if pgrep -f "solve_with_opus.py.*zork1" > /dev/null; then
    echo "✓ Solver is RUNNING"
    PID=$(pgrep -f "solve_with_opus.py.*zork1")
    echo "  PID: $PID"
else
    echo "⚠ Solver is NOT running"
fi

echo ""
echo "-------------------------------------------------------------------"
echo "RECENT ACTIVITY (last 30 lines):"
echo "-------------------------------------------------------------------"
tail -30 "$LOG_FILE"

echo ""
echo "-------------------------------------------------------------------"
echo "STATISTICS:"
echo "-------------------------------------------------------------------"

# Count strategies
STRATEGIES=$(grep -c "Strategy:" "$LOG_FILE" 2>/dev/null || echo "0")
echo "Strategies planned: $STRATEGIES"

# Count new rooms
ROOMS=$(grep -c "Entered new room" "$LOG_FILE" 2>/dev/null || echo "0")
echo "New rooms discovered: $ROOMS"

# Count commands
COMMANDS=$(grep -c "Step [0-9]" "$LOG_FILE" 2>/dev/null || echo "0")
echo "Commands executed: $COMMANDS"

# Check for win
if grep -q "GAME WON" "$LOG_FILE" 2>/dev/null; then
    echo ""
    echo "🎉 GAME WON!"
    grep "GAME WON" "$LOG_FILE"
fi

# Check for errors
if grep -q "ERROR" "$LOG_FILE" 2>/dev/null; then
    echo ""
    echo "⚠ ERRORS DETECTED:"
    grep "ERROR" "$LOG_FILE" | tail -3
fi

echo ""
echo "-------------------------------------------------------------------"
echo "To watch live: tail -f $LOG_FILE"
echo "To check if still running: pgrep -f solve_with_opus"
echo "-------------------------------------------------------------------"

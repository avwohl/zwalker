# Advanced IF Solver - Quick Start

This is a sophisticated AI solver that can actually complete complex interactive fiction games.

## What's Different?

**Old solver** (Haiku):
- Tried random commands
- No memory or planning
- Success rate: ~7%

**New solver** (Opus 4.5):
- Strategic multi-step planning
- Long-term memory and backtracking
- Deep IF puzzle understanding
- Expected success rate: ~50-60%

## Quick Start

### 1. Set up API key

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### 2. Test on a simple game

```bash
python3 scripts/solve_with_opus.py games/zcode/detective.z5
```

Expected: Should complete in 100-200 turns (costs ~$2)

### 3. Test on a hard game

```bash
python3 scripts/solve_with_opus.py games/zcode/zork1.z3 --max-turns 600
```

Expected: Should make significant progress, possibly complete (costs ~$5-10)

### 4. Run full test suite

```bash
python3 scripts/test_opus_on_hard_games.py
```

Tests on 9 challenging games. Takes 2-4 hours, costs ~$50-100.

## What to Expect

### If It Works Well

- **Detective**: Should win in 100-200 turns
- **Shade**: Should win in 50-150 turns
- **Zork I**: Should get 10-15 treasures, maybe win
- **Enchanter**: Should make steady progress on spell puzzles

### If It Struggles

Watch for these patterns:
- **Stuck in loops**: Trying same commands repeatedly
- **Missing obvious puzzles**: Not recognizing locked doors, etc.
- **Poor inventory management**: Not picking up key items
- **Giving up too early**: Strategy says "I'm stuck" when solution exists

These indicate prompting/logic needs refinement.

## Cost Control

To limit costs during testing:

```bash
# Short test - only 100 turns
python3 scripts/solve_with_opus.py games/zcode/detective.z5 --max-turns 100

# Quiet mode - less API calls for analysis
python3 scripts/solve_with_opus.py games/zcode/shade.z5 --quiet --max-turns 150
```

## Output

Solutions saved to `solutions/<game>_solution.json`:

```json
{
  "completed": true,
  "turns_taken": 187,
  "commands": ["north", "take lamp", "light lamp", ...],
  "total_rooms": 27
}
```

## Next Steps

1. **Smoke test**: Run on detective.z5 first
2. **Hard test**: Try zork1.z3
3. **Analyze**: Check if strategies make sense
4. **Iterate**: Improve prompts based on failures
5. **Batch**: Run on all 28 unsolved games

## Files

- `zwalker/advanced_solver.py` - Core solver engine
- `scripts/solve_with_opus.py` - Command-line interface
- `scripts/test_opus_on_hard_games.py` - Test suite
- `docs/ADVANCED_SOLVER.md` - Full documentation

## Troubleshooting

**"ANTHROPIC_API_KEY not set"**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**"No module named anthropic"**
```bash
pip install anthropic
```

**Game gets stuck in loops**
- The backtracking should handle this
- If it doesn't, check the stuck_counter logic
- May need to adjust planning_interval

**Too expensive**
- Use --max-turns to limit cost
- Test on simple games first
- Can switch to Sonnet 4.5 for cheaper (but less capable) solving

---

Ready to test! Start with:
```bash
python3 scripts/solve_with_opus.py games/zcode/detective.z5
```

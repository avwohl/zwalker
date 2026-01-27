# ZWalker Project Notes

Related tools: `~/src/z2js`, `~/z2pdf`, `~/zorkie`

## Primary Use Case: Compiler Testing

The IF community was not happy with z2js due to lack of testing. ZWalker provides:

1. Automatically verify games can be played from start to finish
2. Generate walkthroughs with a known-good .z compile
3. Replay solutions on new compiles to verify correctness

This enables regression testing of the z2js compiler.

**See [TODO.md](/TODO.md) for current status and tasks.**

## Approach

### Automatic Exploration
- Start game and preserve state
- Try every vocabulary word
- Try multiple words parsed from game
- For each room, note exits and connections
- Pick up objects and try using them

### AI-Assisted Solving
The `ai_assist.py` module provides:
- `analyze(context)` - Get suggestions for current room
- `suggest_for_puzzle()` - Solve specific obstacles
- `create_context_from_walker()` - Build context from game state

Use Claude/GPT to:
- Read room descriptions and identify puzzles
- Suggest commands based on IF game knowledge
- Recognize common puzzle patterns
- Detect when stuck and suggest creative solutions
- Build multi-step solution sequences

### Advanced Solver (Opus)
See [ADVANCED_SOLVER.md](ADVANCED_SOLVER.md) for the strategic solver design:
- Multi-turn planning (5-15 step strategies)
- Long-term memory (map, puzzles, inventory history)
- Backtracking system (checkpoints every 10 turns)
- Deep IF understanding built into prompts
- Win detection after every command

## Output Format

Walkthrough JSON contains:
- Command sequence (for replay)
- Room mapping (ID -> name, exits, objects)
- Object tracking (ID -> name, location, takeable)
- Stats (rooms found, commands tried, etc)

This allows:
- Replay on new compile
- Diff against expected behavior
- Identify compiler regressions

## Future: Hints System

Human walkthrough/hint files can guide the AI solver:
- Parse hint files from `walkthroughs/` directory
- Add to solver context to improve success rate
- See [HINTS_ENHANCEMENT.md](HINTS_ENHANCEMENT.md) for design

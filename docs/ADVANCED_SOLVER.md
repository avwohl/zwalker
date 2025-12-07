# Advanced AI Solver - Claude Opus 4.5

A sophisticated IF game solver designed to actually complete complex games, not just explore them.

## Philosophy

The previous solvers failed because they treated IF games like random exploration. Real IF games require:

1. **Understanding puzzle patterns** - Recognizing locked doors, inventory puzzles, NPCs, etc.
2. **Multi-step planning** - "To get key, I need lamp. To get lamp, I need to unlock chest."
3. **Backtracking** - Recognizing dead ends and trying different paths
4. **Long-term memory** - Remembering what was tried, what failed, what clues exist
5. **Strategic thinking** - Having goals beyond "try next command"

## Architecture

### Core Components

#### 1. Multi-Turn Strategic Planning

Instead of asking AI for one command at a time, we ask for a **comprehensive strategy**:

```
"What is blocking progress? → locked door
What puzzle pattern? → inventory_combination
What's needed? → key (location unknown)
Plan: 1) Search unexplored rooms
      2) Find key
      3) Return and unlock door
      4) Continue"
```

The AI creates plans of 5-15 steps, then we execute them.

#### 2. Long-Term Memory

The solver maintains:
- **Map of explored rooms** with exits
- **Puzzle tracking** - What puzzles exist, what was tried, what failed
- **Inventory history** - What items were acquired when
- **Strategy history** - What plans were attempted

This gives Opus context beyond just the last few commands.

#### 3. Backtracking System

Game state is checkpointed every 10 turns. When stuck:
- Detect: "No progress in 20 turns"
- Action: Restore checkpoint from 50 turns ago
- Reason: Try different branch of game tree

This allows exploration of multiple solution paths.

#### 4. Deep IF Understanding

The prompt teaches Opus about IF conventions:
- Objects must be examined before use
- Doors must be unlocked before opening
- NPCs often need specific conversation sequences
- Mazes require mapping
- Timing puzzles need careful sequencing

#### 5. Win Detection

Actively checks for win phrases after every command:
- "you have won"
- "congratulations"
- "victory"
- etc.

Stops immediately when game is won.

### Prompting Strategy

The key is the **strategic planning prompt**. It asks Opus to:

1. **Analyze deeply**: What's the current situation?
2. **Identify puzzles**: What patterns (locked door, maze, NPC, etc.)?
3. **Plan multi-step**: Create 5-15 specific commands
4. **Explain reasoning**: Why this strategy should work
5. **Assess confidence**: How likely is success?

Example prompt structure:
```
GAME STATE: [comprehensive current state]
MAP: [all explored rooms and connections]
PUZZLES: [active puzzles and attempts]
HISTORY: [recent actions and results]

YOUR TASK: Create a strategic plan to WIN this game.

Consider:
- IF puzzle patterns
- Dependencies (what's needed for what)
- Unexplored areas
- Failed approaches to avoid

Output: JSON with analysis, goal, steps, reasoning
```

### Why Opus 4.5?

| Model | Reasoning | Planning | IF Knowledge | Cost |
|-------|-----------|----------|--------------|------|
| Haiku | Weak | Minimal | Generic | $0.25/M |
| Sonnet | Good | Decent | Some | $3/M |
| **Opus 4.5** | **Excellent** | **Strategic** | **Deep** | **$15/M** |

For complex puzzle solving, Opus's superior reasoning is essential. A game might cost $5-10 to solve but generates reusable complete walkthroughs.

## Usage

### Solve a Single Game

```bash
python3 scripts/solve_with_opus.py games/zcode/zork1.z3
```

Options:
- `--max-turns N` - Maximum turns (default: 500)
- `--quiet` - Minimal output
- `--verbose` - Detailed output (default)

### Test on Hard Games

```bash
python3 scripts/test_opus_on_hard_games.py
```

This runs the solver on 9 challenging games:
- Detective (simple mystery)
- Shade (psychological puzzle)
- Zork I (classic adventure)
- Enchanter (magic system)
- Photopia (narrative)
- Trinity (time travel)
- Curses (very hard)
- Anchorhead (horror)
- Zork II (harder than I)

### Expected Performance

**Conservative estimate**:
- Simple games (Detective, Shade): 80-90% success
- Medium games (Zork I, Enchanter): 60-70% success
- Hard games (Curses, Trinity): 30-50% success
- Very hard (Zork II, Anchorhead): 20-30% success

**Overall**: Should complete 50-60% of attempted games, versus ~7% with the basic solver.

## Output Format

Solutions are saved as JSON:

```json
{
  "game": "games/zcode/zork1.z3",
  "source": "advanced_ai_opus",
  "completed": true,
  "total_commands": 187,
  "total_rooms": 27,
  "turns_taken": 245,
  "commands": ["north", "open mailbox", "read leaflet", ...],
  "final_inventory": ["brass lantern", "sword", "rusty knife"],
  "strategies_used": 12,
  "model": "claude-opus-4-20250514"
}
```

## Cost Estimates

Per game (rough):
- **Simple** (50-100 turns): $0.50 - $2
- **Medium** (200-300 turns): $3 - $7
- **Hard** (400-600 turns): $8 - $15

Batch solving 50 games: **$200-400 total**

This is acceptable because:
1. One-time cost to generate reusable walkthroughs
2. Walkthroughs enable unlimited z2js testing
3. Cheaper than manual walkthrough creation
4. Much faster than human solving

## Improvements Over Basic Solver

| Feature | Basic Solver | Advanced Solver |
|---------|-------------|-----------------|
| Model | Haiku | Opus 4.5 |
| Context | 5 commands | 30+ commands + full map |
| Planning | Single command | 5-15 step strategies |
| Memory | None | Puzzles, map, history |
| Backtracking | No | Yes (20 checkpoints) |
| IF Knowledge | Generic | Deep understanding |
| Win Detection | After batch | After every turn |
| Success Rate | ~7% | ~50-60% (estimated) |

## Limitations

Even Opus has limits:

1. **Maze games** - Pure topology puzzles are hard for LLMs
2. **Precise timing** - Games requiring exact turn sequences
3. **Obscure puzzles** - Requiring outside knowledge or leaps of intuition
4. **Very long games** - 1000+ turn epics may hit context limits
5. **Bugs** - Games with implementation bugs confuse the AI

For these, human walkthroughs remain necessary.

## Future Enhancements

Possible improvements:

1. **Multi-agent approach** - Planner AI + Executor AI + Critic AI
2. **Learning from examples** - Show Opus solved puzzles as examples
3. **Ensemble solving** - Run 3 strategies in parallel, pick best
4. **Human-in-the-loop** - Ask for hints when truly stuck
5. **Puzzle pattern library** - Pre-coded solutions for common patterns
6. **Monte Carlo tree search** - Explore multiple solution branches
7. **Reinforcement learning** - Fine-tune on IF games

## Testing Plan

1. **Smoke test** - Run on 3-4 simple games to verify it works
2. **Hard games test** - Run full test suite (9 challenging games)
3. **Batch solve** - Run on all 28 unsolved games
4. **Analysis** - Compare success rates, identify failure patterns
5. **Iteration** - Improve prompts/strategy based on failures

## Running the Tests

```bash
# Quick smoke test on one game
python3 scripts/solve_with_opus.py games/zcode/detective.z5

# Full hard games test (takes 2-4 hours)
python3 scripts/test_opus_on_hard_games.py

# Individual challenging game
python3 scripts/solve_with_opus.py games/zcode/curses.z5 --max-turns 800
```

---

**Status**: Implementation complete, ready for testing
**Next**: Run smoke tests then full evaluation

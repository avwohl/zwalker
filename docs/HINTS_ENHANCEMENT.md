# Hints Enhancement for AI Solver

## Concept

Use human-written hint files to guide the AI solver's strategic planning, significantly improving success rates while still having the AI play the game and generate full transcripts.

## Current Walkthroughs Are Actually Hints!

The downloaded "walkthrough" files are actually **hint files**:

```
* * *  Zork I Hints  * * *

1. The Timber Room
   Consider the uses of a basket, as well as alternate light sources.

2. Hades
   First, get the spirits' attention. Read any good books lately?

3. The Platinum Bar
   Consider the outstanding quality of the room, and make an order of it.
```

## How It Would Work

### 1. Parse Hint Files
Extract hints into structured format:
```python
{
  "game": "zork1",
  "puzzles": [
    {
      "name": "The Timber Room",
      "hints": [
        "Consider the uses of a basket",
        "Remember alternate light sources",
        "Solution may not be in the same room"
      ]
    },
    {
      "name": "Hades",
      "hints": [
        "Get the spirits' attention",
        "Read any good books lately?"
      ]
    }
  ]
}
```

### 2. Add to AI Context
Modify `advanced_solver.py` to include hints in strategic planning:

```python
def get_strategic_plan(self, context: Dict[str, Any]) -> Strategy:
    # Current context: room, inventory, map, etc.

    # NEW: Add hints
    hints_context = self._get_relevant_hints(context)

    prompt = f"""
    ... existing context ...

    HINTS AVAILABLE:
    {hints_context}

    Use these hints to guide your strategy, but you must still
    discover and execute the actual solution yourself.
    """
```

### 3. Hint Matching
Match hints to current game state:
- Location-based: "In Hades? Show Hades hints"
- Item-based: "Have egg? Show egg-opening hints"
- Progress-based: "Early game? Show early hints"

### 4. AI Still Solves
The AI reads the hints but must:
- Interpret what they mean
- Figure out the actual commands
- Execute them in the right order
- Handle unexpected situations

**Result**: Full game transcript with responses, just like before!

## Implementation Plan

### Phase 1: Parse Hints
```python
# scripts/parse_hints.py
def parse_hint_file(filepath: str) -> Dict[str, Any]:
    """Extract hints from human walkthrough files"""
    hints = []
    current_puzzle = None

    for line in file:
        if is_puzzle_header(line):
            current_puzzle = extract_puzzle_name(line)
        elif is_hint_line(line):
            hints.append({
                "puzzle": current_puzzle,
                "hint": clean_hint_text(line)
            })

    return {"game": game_name, "hints": hints}
```

### Phase 2: Add to Solver
```python
# zwalker/advanced_solver.py
class AdvancedAISolver:
    def __init__(self, game_data: bytes, hints_file: Optional[str] = None):
        self.walker = GameWalker(game_data)
        self.hints = load_hints(hints_file) if hints_file else None

    def _get_relevant_hints(self, context: Dict) -> str:
        if not self.hints:
            return ""

        # Match hints to current room/items/progress
        relevant = filter_hints(
            self.hints,
            current_room=context['current_room'],
            inventory=context['inventory'],
            progress=context['progress']
        )

        return format_hints_for_prompt(relevant)
```

### Phase 3: Update Prompt
Add hints section to strategic planning prompt:

```python
prompt = f"""
... existing context ...

PUZZLE HINTS (OPTIONAL GUIDANCE):
{hints_context}

Note: These are optional hints from experienced players. Use them
to guide your thinking, but you must still determine the actual
commands and execute them yourself.

... rest of prompt ...
```

## Benefits

### Improved Success Rate
- **Without hints**: 20-40% success on hard games
- **With hints**: 60-80% success estimated
- **Cost**: Same ($8-15 per game)
- **Quality**: Better solutions, fewer dead ends

### Still Generates Valid Solutions
- AI plays the game (not just copying commands)
- Full transcripts with game responses
- Handles unexpected situations
- Validates z2js compiler correctly

### Better Strategy
Hints help AI:
- Avoid red herrings (boarded front door in Zork)
- Know which items are important
- Understand puzzle dependencies
- Focus exploration on productive areas

## Example: Zork I with Hints

### Current Behavior (No Hints)
```
Turn 15: try to open front door (blocked)
Turn 16-20: try various ways to remove boards
Turn 25: give up, try window (works!)
```

### With Hints
```
Hint: "The boarded front door is a red herring"
Turn 15: check for alternate entrances
Turn 16: find window, enter successfully
```

**Saves ~10 turns**, reduces cost, increases success rate.

## Files Available

We already have hint files for:
- ✅ zork1_human_walkthrough.txt (has Zork I & II hints)
- ✅ zork2_human_walkthrough.txt
- ✅ zork3_human_walkthrough.txt
- ✅ enchanter_human_walkthrough.txt
- ✅ curses_human_walkthrough.txt
- ✅ trinity_human_walkthrough.txt
- ✅ And 6 more...

## Next Steps

### Option 1: Wait for Current Test
Let Zork I finish without hints to establish baseline, then add hints for comparison.

### Option 2: Implement Now
Add hints system before running batch solver on all 28 games.

### Option 3: Hybrid Approach
- Run Zork I without hints (in progress)
- Implement hints system
- Run Zork II with hints for comparison
- Use whichever works better for batch solving

## Code Changes Needed

### New Files
- `scripts/parse_hints.py` - Parse hint files to JSON
- `zwalker/hints.py` - Hint matching and formatting logic

### Modified Files
- `zwalker/advanced_solver.py` - Add hints loading and context
- `scripts/solve_with_opus.py` - Accept --hints parameter

### Estimated Effort
- Parsing hints: 1-2 hours
- Integration: 2-3 hours
- Testing: 1 hour
- **Total**: Half a day of work

## Expected Impact

### Success Rate Improvement
| Game Difficulty | Without Hints | With Hints |
|-----------------|---------------|------------|
| Simple          | 80%           | 95%        |
| Medium          | 40%           | 70%        |
| Hard            | 20%           | 50%        |

### Solutions Generated
- **28 unsolved games** × **50% avg success** = **~14 solutions**
- **Plus 12 human walkthroughs** (after replay) = **~26 total**
- **Goal**: 25-35 solutions for z2js testing ✅

### Cost Savings
- Fewer failed attempts
- Faster solutions (less turns)
- Better first-run success
- Potentially save 30-40% on API costs

---

**Recommendation**: Implement hints system after current Zork I test completes. This gives us baseline comparison and maximizes success for batch solving.

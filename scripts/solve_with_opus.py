#!/usr/bin/env python3
"""
Advanced solver using Claude Sonnet 4 for complex IF games.

This solver is designed to actually solve difficult games like:
- Zork I, II, III
- Curses
- Trinity
- Anchorhead
- Spider and Web

It uses sophisticated reasoning, planning, and backtracking.
Can optionally use a walkthrough/hints file to guide the AI.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.advanced_solver import AdvancedAISolver


def solve_game(game_path: str, max_turns: int = 500, verbose: bool = True, hints_file: str = None, state_file: str = None, log_file: str = None):
    """
    Solve a game using the advanced AI solver.

    Args:
        game_path: Path to .z file
        max_turns: Maximum turns to attempt
        verbose: Print detailed progress
        hints_file: Optional path to walkthrough/hints file
        state_file: Optional path to save/load learned state (for resuming)
        log_file: Optional path to write log output
    """
    # Set up logging to file if specified
    log_handle = None
    if log_file:
        import sys
        log_handle = open(log_file, 'w')
        # Tee output to both stdout and log file
        class Tee:
            def __init__(self, *files):
                self.files = files
            def write(self, obj):
                for f in self.files:
                    f.write(obj)
                    f.flush()
            def flush(self):
                for f in self.files:
                    f.flush()
        sys.stdout = Tee(sys.stdout, log_handle)
    print("="*80)
    print(f"ADVANCED IF SOLVER - Claude Opus 4")
    print("="*80)
    print(f"Game: {game_path}")
    print(f"Max turns: {max_turns}")
    print(f"Model: claude-opus-4-20250514")
    if hints_file:
        print(f"Hints: {hints_file}")
    if state_file:
        print(f"State file: {state_file}")
    print("="*80)
    print()

    # Load game
    game_file = Path(game_path)
    if not game_file.exists():
        print(f"❌ Error: Game file not found: {game_path}")
        return None

    game_data = game_file.read_bytes()
    print(f"✓ Loaded {len(game_data):,} bytes")
    print()

    # Create solver with optional hints
    solver = AdvancedAISolver(game_data, verbose=verbose, hints_file=hints_file)

    # Load previous learned state if available
    if state_file:
        solver.load_learned_state(state_file)

    # Solve
    try:
        result = solver.solve(max_turns=max_turns)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        result = {
            "game_won": False,
            "turns_taken": solver.turn_number,
            "interrupted": True
        }
    except Exception as e:
        print(f"\n\n❌ Error during solving: {e}")
        import traceback
        traceback.print_exc()
        result = {
            "game_won": False,
            "error": str(e)
        }

    # Print results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    if result.get("game_won"):
        print(f"🎉 SUCCESS - Game completed!")
        print(f"   Turns taken: {result['turns_taken']}")
        print(f"   Won at turn: {result['win_turn']}")
    else:
        print(f"⚠️  Game not completed")
        print(f"   Turns attempted: {result.get('turns_taken', 0)}")

    print(f"   Rooms explored: {result.get('rooms_explored', 0)}")
    print(f"   Strategies tried: {result.get('strategies_tried', 0)}")
    print(f"   Commands executed: {len(result.get('commands', []))}")

    if result.get('final_inventory'):
        print(f"   Final inventory: {', '.join(result['final_inventory'])}")

    # Save solution
    game_name = game_file.stem
    output_file = Path("solutions") / f"{game_name}_solution.json"
    output_file.parent.mkdir(exist_ok=True)

    solution_data = {
        "game": str(game_path),
        "source": "advanced_ai_sonnet",
        "completed": result.get("game_won", False),
        "total_commands": len(result.get("commands", [])),
        "total_rooms": result.get("rooms_explored", 0),
        "turns_taken": result.get("turns_taken", 0),
        "commands": result.get("commands", []),
        "final_inventory": result.get("final_inventory", []),
        "strategies_used": result.get("strategies_tried", 0),
        "model": "claude-sonnet-4-20250514",
        "hints_file": hints_file
    }

    with open(output_file, 'w') as f:
        json.dump(solution_data, f, indent=2)

    print(f"\n✓ Solution saved to: {output_file}")

    return result


def main():
    if len(sys.argv) < 2:
        print("""
Usage: python solve_with_opus.py <game.z*> [options]

Options:
  --max-turns N    Maximum turns to attempt (default: 500)
  --hints FILE     Path to walkthrough/hints file to guide the AI
  --state FILE     Path to save/load learned state (maze maps, deaths) for resuming
  --log FILE       Path to write log output (also prints to stdout)
  --quiet          Minimal output
  --verbose        Detailed output (default)

Examples:
  # Solve Zork I
  python solve_with_opus.py games/zcode/zork1.z3

  # Solve Zork I with walkthrough hints
  python solve_with_opus.py games/zcode/zork1.z3 --hints walkthroughs/zork1_walkthrough.txt

  # Solve Zork I with state persistence (remembers maze, deaths between runs)
  python solve_with_opus.py games/zcode/zork1.z3 --hints walkthroughs/zork1_walkthrough.txt --state zork1_state.json

  # Solve Curses with more turns
  python solve_with_opus.py games/zcode/curses.z5 --max-turns 1000

  # Solve Trinity quietly
  python solve_with_opus.py games/zcode/trinity.z4 --quiet
        """)
        return 1

    game_path = sys.argv[1]
    max_turns = 500
    verbose = True
    hints_file = None
    state_file = None
    log_file = None

    # Parse options
    if "--max-turns" in sys.argv:
        idx = sys.argv.index("--max-turns")
        max_turns = int(sys.argv[idx + 1])

    if "--hints" in sys.argv:
        idx = sys.argv.index("--hints")
        hints_file = sys.argv[idx + 1]

    if "--state" in sys.argv:
        idx = sys.argv.index("--state")
        state_file = sys.argv[idx + 1]

    if "--log" in sys.argv:
        idx = sys.argv.index("--log")
        log_file = sys.argv[idx + 1]

    if "--quiet" in sys.argv:
        verbose = False

    # Solve
    result = solve_game(game_path, max_turns=max_turns, verbose=verbose, hints_file=hints_file, state_file=state_file, log_file=log_file)

    # Exit code
    if result and result.get("game_won"):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Batch solve all games using AI-assisted walkthroughs.
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Games to solve
GAMES = [
    ("games/zcode/zork1.z3", "walkthroughs/zork1_gameboomers.txt"),
    ("games/zcode/zork2.z3", "walkthroughs/zork2_human_walkthrough.txt"),
    ("games/zcode/zork3.z3", "walkthroughs/zork3_human_walkthrough.txt"),
    ("games/zcode/enchanter.z3", "walkthroughs/enchanter_human_walkthrough.txt"),
    ("games/zcode/trinity.z4", "walkthroughs/trinity_human_walkthrough.txt"),
    ("games/zcode/photopia.z5", "walkthroughs/photopia_human_walkthrough.txt"),
    ("games/zcode/curses.z5", "walkthroughs/curses_human_walkthrough.txt"),
    ("games/zcode/anchor.z8", "walkthroughs/anchor_human_walkthrough.txt"),
    ("games/zcode/dreamhold.z8", "walkthroughs/dreamhold_human_walkthrough.txt"),
    ("games/zcode/lostpig.z8", None),  # No walkthrough yet
    ("games/zcode/aisle.z5", "walkthroughs/aisle_human_walkthrough.txt"),
    ("games/zcode/shade.z5", None),
    ("games/zcode/photopia.z5", None),
    ("games/zcode/905.z5", None),
    ("games/zcode/lists.z5", None),
]

def run_solver(game_path, hints_path, max_turns=500):
    """Run the AI solver on a single game"""
    game_name = Path(game_path).stem
    solution_path = f"solutions/{game_name}_solution.json"
    log_path = f"logs/{game_name}_solve.log"

    print(f"\n{'='*60}")
    print(f"SOLVING: {game_name}")
    print(f"{'='*60}")

    cmd = [
        "python3", "scripts/solve_with_opus.py",
        game_path,
        "--max-turns", str(max_turns),
        "--log", log_path,
    ]

    if hints_path and Path(hints_path).exists():
        cmd.extend(["--hints", hints_path])
        print(f"Using hints: {hints_path}")
    else:
        print("No hints file - AI will explore freely")

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            cwd=str(Path(__file__).parent.parent)
        )

        print(f"Exit code: {result.returncode}")
        if result.stdout:
            # Print last 20 lines of output
            lines = result.stdout.strip().split('\n')
            for line in lines[-20:]:
                print(line)

        if result.returncode != 0 and result.stderr:
            print(f"STDERR: {result.stderr[-500:]}")

    except subprocess.TimeoutExpired:
        print(f"TIMEOUT after 600 seconds")
    except Exception as e:
        print(f"ERROR: {e}")

    # Check if solution was created
    if Path(solution_path).exists():
        with open(solution_path) as f:
            sol = json.load(f)
        completed = sol.get("completed", False)
        cmds = len(sol.get("commands", []))
        print(f"\nResult: completed={completed} commands={cmds}")
        return completed
    else:
        print(f"No solution file created")
        return False

def main():
    print("="*60)
    print("BATCH GAME SOLVER")
    print(f"Started: {datetime.now()}")
    print("="*60)

    # Filter to games that exist
    existing_games = []
    for game, hints in GAMES:
        if Path(game).exists():
            existing_games.append((game, hints))
        else:
            print(f"SKIP (not found): {game}")

    print(f"\nWill solve {len(existing_games)} games")

    results = {}
    for game, hints in existing_games:
        name = Path(game).stem
        success = run_solver(game, hints)
        results[name] = success

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    completed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"Completed: {completed}/{total}")
    print("\nResults:")
    for name, success in sorted(results.items()):
        status = "DONE" if success else "INCOMPLETE"
        print(f"  {name}: {status}")

    # Save summary
    summary = {
        "timestamp": str(datetime.now()),
        "total_games": total,
        "completed": completed,
        "results": results
    }
    Path("solutions/batch_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nSummary saved to solutions/batch_summary.json")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Run zwalker on all downloaded games and generate test results.
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add parent to path for zwalker imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.zmachine import ZMachine
from zwalker.walker import GameWalker


def test_game(game_path, output_dir, max_rooms=20, verbose=False):
    """
    Test a single game with zwalker.

    Returns a result dict with status and details.
    """
    result = {
        "game": game_path.name,
        "path": str(game_path),
        "status": "unknown",
        "error": None,
        "stats": {},
        "timestamp": datetime.now().isoformat(),
    }

    try:
        # Load game
        game_data = game_path.read_bytes()
        result["size"] = len(game_data)

        # Get header info
        vm = ZMachine(game_data)
        result["version"] = vm.header.version
        result["release"] = vm.header.release
        result["serial"] = vm.header.serial

        # Create walker and explore
        walker = GameWalker(game_data)
        initial_output = walker.start()

        if verbose:
            print(f"    Initial: {initial_output[:100]}...")

        # Explore
        walker.explore_breadth_first(max_rooms=max_rooms)

        # Get stats
        stats = walker.get_stats()
        result["stats"] = stats
        result["rooms_found"] = stats.get("rooms_found", 0)
        result["commands_tried"] = stats.get("commands_tried", 0)

        # Generate walkthrough JSON
        walkthrough = walker.get_walkthrough_json()
        result["walkthrough_moves"] = len(walkthrough.get("moves", []))

        # Save walkthrough
        walkthrough_path = output_dir / f"{game_path.stem}_walkthrough.json"
        walkthrough_path.write_text(json.dumps(walkthrough, indent=2))
        result["walkthrough_file"] = str(walkthrough_path)

        result["status"] = "pass"

    except Exception as e:
        result["status"] = "fail"
        result["error"] = str(e)
        if verbose:
            import traceback
            traceback.print_exc()

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run zwalker tests on Z-machine games")
    parser.add_argument("--games-dir", type=Path, default=Path(__file__).parent / "zcode",
                        help="Directory containing .z* game files")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "results",
                        help="Directory for test results and walkthroughs")
    parser.add_argument("--max-rooms", type=int, default=20,
                        help="Maximum rooms to explore per game")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")
    parser.add_argument("--game", type=str, help="Test a specific game only")
    args = parser.parse_args()

    # Setup directories
    games_dir = args.games_dir
    output_dir = args.output_dir
    output_dir.mkdir(exist_ok=True)

    if not games_dir.exists():
        print(f"Games directory not found: {games_dir}")
        print("Run download_games.py first")
        return 1

    # Find games
    if args.game:
        games = [games_dir / args.game]
        if not games[0].exists():
            # Try with extension
            for ext in ['.z3', '.z4', '.z5', '.z8', '.zblorb']:
                test_path = games_dir / f"{args.game}{ext}"
                if test_path.exists():
                    games = [test_path]
                    break
    else:
        games = sorted(games_dir.glob("*.z[3458]"))

    if not games:
        print(f"No games found in {games_dir}")
        return 1

    print(f"Testing {len(games)} games from {games_dir}")
    print(f"Results will be saved to {output_dir}")
    print()

    results = []
    passed = 0
    failed = 0

    for game_path in games:
        print(f"[TEST] {game_path.name}...", end=" ", flush=True)
        start_time = time.time()

        result = test_game(game_path, output_dir, max_rooms=args.max_rooms, verbose=args.verbose)
        elapsed = time.time() - start_time
        result["elapsed_seconds"] = round(elapsed, 2)

        results.append(result)

        if result["status"] == "pass":
            passed += 1
            rooms = result.get("rooms_found", 0)
            print(f"PASS ({rooms} rooms, {elapsed:.1f}s)")
        else:
            failed += 1
            error = result.get("error", "unknown error")[:50]
            print(f"FAIL: {error}")

    # Save summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "games_dir": str(games_dir),
        "total_games": len(games),
        "passed": passed,
        "failed": failed,
        "results": results
    }

    summary_path = output_dir / "test_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))

    print()
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(games)}")
    print(f"Summary saved to: {summary_path}")
    print()

    # List failures
    if failed > 0:
        print("Failed games:")
        for r in results:
            if r["status"] == "fail":
                print(f"  {r['game']}: {r.get('error', 'unknown')}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

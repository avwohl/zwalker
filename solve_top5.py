#!/usr/bin/env python3
"""
Generate AI walkthroughs for the top 5 IF games, then test in z2js.

This script:
1. Solves each game using AI assistance (Claude)
2. Generates walkthrough JSON files
3. Compiles each game with z2js
4. Compares outputs to find bugs

Usage: python solve_top5.py [--max-iterations N] [--no-ai]
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Import our solver
from solve_game import solve_game

# Top 5 games from our collection
TOP_5_GAMES = [
    ("games/zcode/anchor.z8", "Anchorhead", "#2 in 2023 Top 50"),
    ("games/zcode/photopia.z5", "Photopia", "#6 tie in 2023 Top 50"),
    ("games/zcode/lostpig.z8", "Lost Pig", "#8 tie in 2023 Top 50"),
    ("games/zcode/trinity.z4", "Trinity", "Classic Infocom"),
    ("games/zcode/curses.z5", "Curses", "Classic IF"),
]


def compile_with_z2js(game_path):
    """Compile a game with z2js"""
    game_name = Path(game_path).stem
    output_js = f"z2js_output/{game_name}.js"
    output_html = f"z2js_output/{game_name}.html"

    # Create output directory
    Path("z2js_output").mkdir(exist_ok=True)

    print(f"  Compiling {game_name} with z2js...")

    z2js_dir = Path.home() / "src" / "z2js"
    abs_game_path = Path(game_path).absolute()
    abs_output_js = Path(output_js).absolute()

    try:
        result = subprocess.run(
            ["python", "-m", "jsgen", str(abs_game_path), "-o", str(abs_output_js)],
            cwd=str(z2js_dir),
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            print(f"  ✗ Z2JS compilation failed:")
            print(f"    {result.stderr[:500]}")
            return None

        if Path(output_js).exists():
            size = Path(output_js).stat().st_size
            print(f"  ✓ Generated {output_js} ({size:,} bytes)")
            return output_js
        else:
            print(f"  ✗ Output file not created")
            return None

    except subprocess.TimeoutExpired:
        print(f"  ✗ Z2JS compilation timed out (>120s)")
        return None
    except Exception as e:
        print(f"  ✗ Z2JS error: {e}")
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Solve top 5 IF games and test with z2js")
    parser.add_argument("--max-iterations", type=int, default=100,
                       help="Max AI iterations per game (default: 100)")
    parser.add_argument("--no-ai", action="store_true",
                       help="Use local heuristics instead of Claude")
    parser.add_argument("--games", nargs="+", type=int, choices=[1,2,3,4,5],
                       help="Solve only specific games (1-5)")
    args = parser.parse_args()

    use_real_ai = not args.no_ai

    # Check for API key if using real AI
    if use_real_ai:
        import os
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("ERROR: ANTHROPIC_API_KEY not set. Use --no-ai for local heuristics.")
            return 1

    print("=" * 70)
    print("TOP 5 INTERACTIVE FICTION GAMES - WALKTHROUGH GENERATION")
    print("=" * 70)
    print(f"AI Mode: {'Claude (Anthropic)' if use_real_ai else 'Local Heuristics'}")
    print(f"Max iterations: {args.max_iterations}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    results = []

    # Filter games if specific ones requested
    games_to_solve = TOP_5_GAMES
    if args.games:
        games_to_solve = [TOP_5_GAMES[i-1] for i in args.games]

    for i, (game_path, name, rank) in enumerate(games_to_solve, 1):
        print(f"\n{'='*70}")
        print(f"GAME {i}/{len(games_to_solve)}: {name} ({rank})")
        print(f"File: {game_path}")
        print(f"{'='*70}\n")

        if not Path(game_path).exists():
            print(f"✗ Game file not found: {game_path}")
            results.append({
                "game": name,
                "path": game_path,
                "status": "not_found"
            })
            continue

        # Step 1: Solve with AI
        print(f"STEP 1: Generating walkthrough with AI...")
        print("-" * 70)

        try:
            walkthrough = solve_game(
                game_path,
                max_iterations=args.max_iterations,
                use_real_ai=use_real_ai
            )

            solution_file = Path(game_path).stem + "_solution.json"

            result_entry = {
                "game": name,
                "path": game_path,
                "rank": rank,
                "solution_file": solution_file,
                "rooms_visited": len(walkthrough.get("rooms_visited", [])),
                "commands": len(walkthrough.get("solution_commands", [])),
                "status": "walkthrough_generated"
            }

            print(f"\n✓ Walkthrough generated: {solution_file}")
            print(f"  Rooms visited: {result_entry['rooms_visited']}")
            print(f"  Commands: {result_entry['commands']}")

        except Exception as e:
            print(f"\n✗ Walkthrough generation failed: {e}")
            result_entry = {
                "game": name,
                "path": game_path,
                "status": "walkthrough_failed",
                "error": str(e)
            }

        # Step 2: Compile with z2js
        print(f"\nSTEP 2: Compiling with z2js...")
        print("-" * 70)

        try:
            js_file = compile_with_z2js(game_path)
            if js_file:
                result_entry["z2js_file"] = js_file
                result_entry["z2js_status"] = "compiled"
            else:
                result_entry["z2js_status"] = "failed"
        except Exception as e:
            print(f"  ✗ Z2JS compilation error: {e}")
            result_entry["z2js_status"] = "error"
            result_entry["z2js_error"] = str(e)

        results.append(result_entry)

        # Save progress after each game
        progress_file = "top5_progress.json"
        Path(progress_file).write_text(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "ai_mode": "claude" if use_real_ai else "local",
            "max_iterations": args.max_iterations,
            "results": results
        }, indent=2))

    # Final summary
    print(f"\n\n{'='*70}")
    print("FINAL SUMMARY")
    print(f"{'='*70}\n")

    for i, result in enumerate(results, 1):
        print(f"{i}. {result['game']}")
        print(f"   Status: {result['status']}")
        if result.get('rooms_visited'):
            print(f"   Rooms: {result['rooms_visited']}, Commands: {result['commands']}")
        if result.get('z2js_status'):
            print(f"   Z2JS: {result['z2js_status']}")
        print()

    # Statistics
    walkthroughs_generated = sum(1 for r in results if r['status'] == 'walkthrough_generated')
    z2js_compiled = sum(1 for r in results if r.get('z2js_status') == 'compiled')

    print(f"Walkthroughs generated: {walkthroughs_generated}/{len(results)}")
    print(f"Z2JS compilations: {z2js_compiled}/{len(results)}")
    print(f"\nResults saved to: top5_progress.json")

    return 0


if __name__ == '__main__':
    sys.exit(main())

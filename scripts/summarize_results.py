#!/usr/bin/env python3
"""
Summarize results from top 5 game solving and z2js testing.

Usage: python summarize_results.py [top5_progress.json]
"""

import sys
import json
from pathlib import Path


def summarize_results(progress_file="top5_progress.json"):
    """Create a summary report"""
    if not Path(progress_file).exists():
        print(f"ERROR: Progress file not found: {progress_file}")
        return 1

    with open(progress_file) as f:
        data = json.load(f)

    results = data.get("results", [])

    print("=" * 70)
    print("TOP 5 GAMES - WALKTHROUGH GENERATION SUMMARY")
    print("=" * 70)
    print(f"Timestamp: {data.get('timestamp', 'unknown')}")
    print(f"AI Mode: {data.get('ai_mode', 'unknown')}")
    print(f"Max iterations: {data.get('max_iterations', 'unknown')}")
    print()

    # Summary stats
    total = len(results)
    walkthroughs_ok = sum(1 for r in results if r.get('status') == 'walkthrough_generated')
    z2js_ok = sum(1 for r in results if r.get('z2js_status') == 'compiled')

    print(f"Games processed: {total}/5")
    print(f"Walkthroughs generated: {walkthroughs_ok}/{total}")
    print(f"Z2JS compilations: {z2js_ok}/{total}")
    print()

    # Individual results
    print("=" * 70)
    print("INDIVIDUAL RESULTS")
    print("=" * 70)
    print()

    for i, result in enumerate(results, 1):
        game = result.get('game', 'Unknown')
        rank = result.get('rank', '')
        status = result.get('status', 'unknown')
        rooms = result.get('rooms_visited', 0)
        commands = result.get('commands', 0)
        z2js_status = result.get('z2js_status', 'not attempted')

        print(f"{i}. {game} ({rank})")
        print(f"   Walkthrough: {status}")

        if status == 'walkthrough_generated':
            print(f"   Exploration: {rooms} rooms, {commands} commands")
            avg_commands = commands / max(1, rooms)
            print(f"   Efficiency: {avg_commands:.1f} commands/room")

            # Quality assessment
            if rooms == 1 and commands > 20:
                print(f"   ⚠ WARNING: Stuck in one room")
            elif rooms > 10:
                print(f"   ✓ Good exploration (10+ rooms)")
            elif rooms > 5:
                print(f"   ○ Moderate exploration (5+ rooms)")

        print(f"   Z2JS: {z2js_status}")

        if result.get('solution_file'):
            print(f"   File: {result['solution_file']}")

        if result.get('z2js_file'):
            js_size = Path(result['z2js_file']).stat().st_size if Path(result['z2js_file']).exists() else 0
            print(f"   JS: {result['z2js_file']} ({js_size:,} bytes)")

        if result.get('error'):
            print(f"   Error: {result['error']}")

        print()

    # Recommendations
    print("=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    print()

    stuck_games = [r for r in results
                   if r.get('rooms_visited', 0) == 1 and r.get('commands', 0) > 20]
    if stuck_games:
        print("Games that got stuck (1 room, 20+ commands):")
        for r in stuck_games:
            print(f"  - {r['game']}")
            print(f"    Try: Manual hints, different AI model, or hybrid approach")
        print()

    successful = [r for r in results if r.get('rooms_visited', 0) > 5]
    if successful:
        print(f"Successfully explored games ({len(successful)}):")
        for r in successful:
            print(f"  - {r['game']}: {r['rooms_visited']} rooms")
        print()

    if z2js_ok < total:
        failed_z2js = [r for r in results if r.get('z2js_status') != 'compiled']
        print("Z2JS compilation issues:")
        for r in failed_z2js:
            print(f"  - {r['game']}: {r.get('z2js_status', 'unknown')}")
            if r.get('z2js_error'):
                print(f"    Error: {r['z2js_error'][:100]}")
        print()

    # Next steps
    print("NEXT STEPS:")
    print("1. Review stuck games and add manual guidance")
    print("2. Test successful walkthroughs in z2js (compare outputs)")
    print("3. Document bugs found in zwalker or z2js")
    print("4. Iterate on unsuccessful games with more iterations")
    print()

    return 0


if __name__ == '__main__':
    progress_file = sys.argv[1] if len(sys.argv) > 1 else "top5_progress.json"
    sys.exit(summarize_results(progress_file))

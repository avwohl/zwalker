#!/usr/bin/env python3
"""
Generate walkthroughs for all top 100 IF games.
Skips games already solved and zblorb files (not supported yet).
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.zmachine import ZMachine
from zwalker.walker import GameWalker
from zwalker.ai_assist import AIAssistant, create_context_from_walker

# Top 100 games from IFDB (excluding zblorb which we don't support yet)
TOP_100_GAMES = [
    # Already done in top 5
    # ("photopia.z5", "Photopia"),
    # ("anchor.z8", "Anchorhead"),
    # ("lostpig.z8", "Lost Pig"),
    # ("trinity.z4", "Trinity"),
    # ("curses.z5", "Curses"),

    # Continue with rest of top 100
    ("Tangle.z5", "Spider and Web"),
    ("devours.z5", "All Things Devours"),
    ("bedlam.z5", "Slouching Towards Bedlam"),
    ("babel.z5", "Babel"),
    ("makeitgood.z8", "Make It Good"),
    ("WorldsApart.z8", "Worlds Apart"),
    ("905.z5", "9:05"),
    ("Aisle.z5", "Aisle"),
    ("adverbum.z5", "Ad Verbum"),
    ("AllRoads.z5", "All Roads"),
    ("savoir-faire.z8", "Savoir-Faire"),
    ("metamorphoses.z5", "Metamorphoses"),
    ("dreamhold.z8", "The Dreamhold"),
    ("coldiron.z8", "Cold Iron"),
    ("jigsaw.z8", "Jigsaw"),
    ("sofar.z8", "So Far"),
    ("shade.z5", "Shade"),
    ("theatre.z5", "Theatre"),
    ("edifice.z5", "The Edifice"),
    ("galatea.z5", "Galatea"),
    ("varicella.z8", "Varicella"),
    ("sentence.z8", "Suspended Sentence"),

    # Classic Infocom games
    ("zork1.z3", "Zork I"),
    ("zork2.z3", "Zork II"),
    ("zork3.z3", "Zork III"),
    ("enchanter.z3", "Enchanter"),
    ("sorcerer.z3", "Sorcerer"),
    ("spellbre.z3", "Spellbreaker"),
    ("planetfa.z3", "Planetfall"),
    ("stationfal.z3", "Stationfall"),
    ("lurking.z3", "The Lurking Horror"),
    ("infidel.z3", "Infidel"),
    ("suspend.z3", "Suspended"),
    ("deadline.z3", "Deadline"),
    ("witness.z3", "Witness"),
    ("suspect.z3", "Suspect"),
    ("cutthro.z3", "Cutthroats"),
    ("seastal.z3", "Seastalker"),
    ("wishbrin.z3", "Wishbringer"),
    ("ballyhoo.z3", "Ballyhoo"),
    ("hhgg.z3", "Hitchhiker's Guide"),
    ("lgop.z3", "Leather Goddesses"),
    ("moonmist.z3", "Moonmist"),
    ("plundere.z3", "Plundered Hearts"),
    ("nord.z4", "Nord and Bert"),
    ("amfv.z4", "A Mind Forever Voyaging"),
    ("bureaucr.z4", "Bureaucracy"),
    ("beyondzo.z5", "Beyond Zork"),
    ("borderzo.z5", "Border Zone"),
    ("sherlock.z5", "Sherlock"),

    # More modern IF
    ("advent.z3", "Adventure (Colossal Cave)"),
    ("Advent.z5", "Adventure (Graham Nelson)"),
    ("adv440.z8", "Adventure 440"),
    ("adv550.z8", "Adventure 550"),
    ("Acheton.z8", "Acheton"),
    ("catseye.z3", "Cat's Eye"),
    ("acorncourt.z5", "Acorn Court"),
    ("bluechairs.z5", "Blue Chairs"),
    ("cheeseshop.z5", "Cheeseshop"),
    ("detective.z5", "Detective"),
    ("FailSafe.z5", "FailSafe"),
    ("heroes.z5", "Heroes"),
    ("lists.z5", "Lists and Lists"),
    ("spur.z5", "Spur"),
    ("toonesia.z5", "Toonesia"),
    ("winter.z5", "Winter Wonderland"),
    ("zombies.z5", "Zombies"),
    ("dracula.z8", "Dracula"),
    ("Enemies.z8", "Enemies"),
    ("Fairyland.z8", "Fairyland"),
    ("booth.z5", "Pick Up the Phone Booth and Die"),
    ("rematch.z5", "Rematch"),
    ("plant.z5", "The Plant"),
    ("tattoo.z5", "Tattoo Parlour"),
    ("misdirect.z5", "The Act of Misdirection"),
    ("uncle.z5", "Uncle Zebulon's Will"),
    ("oprobing.z5", "Offensive Probing"),
]


def solve_game(game_file, game_name, max_iterations=100):
    """Solve a single game and return results."""
    print(f"\n{'='*60}")
    print(f"GAME: {game_name}")
    print(f"FILE: {game_file}")
    print(f"{'='*60}\n")

    game_path = Path("games/zcode") / game_file
    if not game_path.exists():
        print(f"⚠ SKIP: File not found: {game_path}")
        return None

    # Check if already solved
    output_name = game_file.replace('.z3', '').replace('.z4', '').replace('.z5', '').replace('.z8', '')
    output_file = Path("solutions") / f"{output_name}_solution.json"

    if output_file.exists():
        print(f"✓ SKIP: Already solved (found {output_file})")
        return None

    try:
        # Load game
        with open(game_path, 'rb') as f:
            game_data = f.read()

        print(f"Loaded {len(game_data)} bytes")

        # Create walker
        walker = GameWalker(game_data)

        # Start game
        output = walker.start()
        print(f"Starting: {output[:100]}...")

        # Create AI assistant
        ai = AIAssistant(backend="anthropic", use_real_ai=True)

        # Solve iteratively
        print(f"Running AI solver (max {max_iterations} iterations)...")
        for iteration in range(max_iterations):
            # Get context
            context = create_context_from_walker(walker)

            # Get AI decision
            command = ai.suggest_next_command(context)

            if not command:
                print(f"AI gave up at iteration {iteration}")
                break

            # Try command
            result = walker.try_command(command)

            if iteration % 10 == 0:
                print(f"  Iteration {iteration}: {len(walker.rooms_visited)} rooms, {len(walker.command_history)} commands")

            # Check if stuck (repeating same room)
            if len(walker.command_history) > 20:
                recent_rooms = [cmd.get('room') for cmd in walker.command_history[-20:]]
                if len(set(recent_rooms)) <= 2:
                    print(f"Stuck in same rooms, stopping at iteration {iteration}")
                    break

        # Save results
        result = {
            'game': str(game_path),
            'total_rooms': len(walker.rooms_visited),
            'total_commands': len(walker.command_history),
            'rooms_visited': list(walker.rooms_visited),
            'commands': [cmd['command'] for cmd in walker.command_history],
        }

        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"\n✓ SUCCESS: Saved to {output_file}")
        print(f"  Rooms: {result['total_rooms']}")
        print(f"  Commands: {result['total_commands']}")

        return result

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("="*60)
    print("ZWalker - Top 100 Games Walkthrough Generator")
    print("="*60)
    print(f"Total games to process: {len(TOP_100_GAMES)}")
    print(f"Using AI: Anthropic Claude")
    print(f"Max iterations per game: 100")
    print("="*60)

    results = []
    completed = 0
    skipped = 0
    failed = 0

    for i, (game_file, game_name) in enumerate(TOP_100_GAMES, 1):
        print(f"\n[{i}/{len(TOP_100_GAMES)}] Processing: {game_name}")

        result = solve_game(game_file, game_name, max_iterations=100)

        if result is None:
            skipped += 1
        elif result:
            completed += 1
            results.append({
                'game': game_name,
                'file': game_file,
                'rooms': result['total_rooms'],
                'commands': result['total_commands'],
            })
        else:
            failed += 1

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total games: {len(TOP_100_GAMES)}")
    print(f"Completed: {completed}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print("="*60)

    # Save summary
    summary_file = Path("solutions/top100_summary.json")
    with open(summary_file, 'w') as f:
        json.dump({
            'total': len(TOP_100_GAMES),
            'completed': completed,
            'skipped': skipped,
            'failed': failed,
            'results': results,
        }, f, indent=2)

    print(f"\nSummary saved to: {summary_file}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

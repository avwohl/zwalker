#!/usr/bin/env python3
"""
Improved batch solver with better exploration strategy.

Key improvements:
1. Tries ALL AI suggestions, not just the first
2. Tracks tried commands to avoid repetition
3. Always explores all directions in each room
4. Detects when stuck and tries harder
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.walker import GameWalker, DIRECTIONS
from zwalker.ai_assist import AIAssistant, create_context_from_walker


def solve_one_game(game_path, max_iterations=100, verbose=False):
    """Solve one game with improved strategy."""
    game_name = game_path.stem
    output_path = Path("solutions") / f"{game_name}_solution.json"

    if output_path.exists():
        print(f"✓ SKIP {game_name} (already solved)")
        return None

    print(f"\n{'='*60}")
    print(f"Solving: {game_name}")
    print(f"{'='*60}")

    try:
        game_data = game_path.read_bytes()
        walker = GameWalker(game_data)
        output = walker.start()

        ai = AIAssistant(backend='anthropic')

        # Track what we've tried to avoid repetition
        tried_commands = set()
        tried_in_room = {}  # room_id -> set of commands
        last_room_count = 0
        stuck_counter = 0

        # Initial direction exploration
        current_room = walker.current_room_id
        if current_room not in tried_in_room:
            tried_in_room[current_room] = set()

        # Try all directions first
        for direction in ["n", "s", "e", "w", "u", "d", "ne", "nw", "se", "sw", "in", "out"]:
            if direction not in tried_in_room[current_room]:
                walker.try_command(direction)
                tried_in_room[current_room].add(direction)
                tried_commands.add(direction)

        for iteration in range(max_iterations):
            current_room = walker.current_room_id
            if current_room not in tried_in_room:
                tried_in_room[current_room] = set()
                # New room! Try all directions
                for direction in ["n", "s", "e", "w", "u", "d", "ne", "nw", "se", "sw", "in", "out"]:
                    if direction not in tried_in_room[current_room]:
                        result = walker.try_command(direction)
                        tried_in_room[current_room].add(direction)

            # Check progress
            room_count = len(walker.rooms)
            if room_count > last_room_count:
                last_room_count = room_count
                stuck_counter = 0
                if verbose:
                    print(f"  [{iteration}] Found room #{room_count}: {walker.known_room_names}")
            else:
                stuck_counter += 1

            # Progress report
            if iteration % 20 == 0:
                print(f"  [{iteration}/{max_iterations}] {room_count} rooms, {len(walker.full_transcript)} cmds, stuck={stuck_counter}")

            # Get AI suggestions
            context = create_context_from_walker(walker)
            response = ai.analyze(context)

            # Try ALL suggested commands that we haven't tried in this room
            commands_executed = 0
            for cmd in response.suggested_commands[:10]:
                cmd_lower = cmd.lower().strip()

                # Skip if tried globally for simple commands
                if cmd_lower in tried_commands and cmd_lower in DIRECTIONS:
                    continue

                # Skip if tried in this specific room
                if cmd_lower in tried_in_room.get(current_room, set()):
                    continue

                # Execute it
                walker.try_command(cmd)
                tried_commands.add(cmd_lower)
                tried_in_room[current_room].add(cmd_lower)
                commands_executed += 1

                # Check if we moved to a new room
                new_room = walker.current_room_id
                if new_room != current_room:
                    current_room = new_room
                    if current_room not in tried_in_room:
                        tried_in_room[current_room] = set()
                        # Explore directions in new room
                        for direction in ["n", "s", "e", "w", "u", "d"]:
                            walker.try_command(direction)
                            tried_in_room[current_room].add(direction)

            # If we executed nothing new, try common IF actions
            if commands_executed == 0:
                # Extract nouns from room description for targeted actions
                desc_words = set(w.lower().strip('.,!?;:"\'()')
                                for w in context.room_description.split()
                                if len(w) > 3 and w[0].islower())

                # Common IF interaction patterns
                common_actions = [
                    "look", "inventory", "take all", "get all",
                    # Light sources
                    "light lamp", "turn on lamp", "turn on lantern", "light lantern",
                    # Common openables
                    "open door", "open window", "open mailbox", "open box", "open gate",
                    # Common enterables
                    "enter", "enter door", "enter building", "enter house", "go inside",
                    "enter window", "climb window", "go window",
                    # Reading
                    "read sign", "read note", "read book", "read letter",
                    # Keys and locks
                    "unlock door", "unlock gate",
                ]

                # Add actions for words found in description
                for word in desc_words:
                    if word in ['door', 'window', 'gate', 'mailbox', 'box', 'chest', 'container']:
                        common_actions.extend([f"open {word}", f"enter {word}", f"examine {word}"])
                    elif word in ['lamp', 'lantern', 'torch', 'light']:
                        common_actions.extend([f"take {word}", f"light {word}", f"turn on {word}"])
                    elif word in ['key', 'keys']:
                        common_actions.extend([f"take {word}", f"get {word}"])

                for cmd in common_actions:
                    if cmd not in tried_in_room.get(current_room, set()):
                        result = walker.try_command(cmd)
                        tried_in_room[current_room].add(cmd)
                        # Check if we moved
                        if walker.current_room_id != current_room:
                            break

            # If truly stuck for many iterations, try harder
            if stuck_counter > 20:
                if verbose:
                    print(f"  Stuck! Trying harder exploration...")
                # Try examining objects mentioned in description
                for word in context.room_description.lower().split():
                    if len(word) > 3 and word.isalpha():
                        cmd = f"examine {word}"
                        if cmd not in tried_in_room.get(current_room, set()):
                            walker.try_command(cmd)
                            tried_in_room[current_room].add(cmd)
                stuck_counter = 0  # Reset to avoid infinite loop

        # Collect unique rooms
        unique_rooms = list(walker.known_room_names) if walker.known_room_names else []

        # Save result
        result = {
            'game': game_name,
            'total_rooms': len(walker.rooms),
            'total_commands': len(walker.full_transcript),
            'rooms_visited': unique_rooms,
            'unique_commands': len(tried_commands),
            'commands': [cmd for cmd, _ in walker.full_transcript],
        }

        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2))

        print(f"✓ DONE {game_name}: {result['total_rooms']} rooms, {len(unique_rooms)} unique, {result['total_commands']} commands")
        return result

    except Exception as e:
        print(f"✗ ERROR {game_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Improved batch solver")
    parser.add_argument("--game", help="Solve a specific game")
    parser.add_argument("--max-iter", type=int, default=100, help="Max iterations per game")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--force", "-f", action="store_true", help="Re-solve even if solution exists")
    args = parser.parse_args()

    if args.game:
        game_path = Path(f"games/zcode/{args.game}")
        if not game_path.exists():
            # Try with extension
            for ext in [".z3", ".z4", ".z5", ".z8"]:
                if Path(f"games/zcode/{args.game}{ext}").exists():
                    game_path = Path(f"games/zcode/{args.game}{ext}")
                    break

        if args.force:
            sol_path = Path("solutions") / f"{game_path.stem}_solution.json"
            if sol_path.exists():
                sol_path.unlink()

        solve_one_game(game_path, args.max_iter, args.verbose)
    else:
        games = sorted(Path("games/zcode").glob("*.z[3458]"))
        print(f"Found {len(games)} games")

        completed = 0
        skipped = 0
        failed = 0

        for i, game in enumerate(games, 1):
            print(f"\n[{i}/{len(games)}] {game.name}")

            if args.force:
                sol_path = Path("solutions") / f"{game.stem}_solution.json"
                if sol_path.exists():
                    sol_path.unlink()

            result = solve_one_game(game, args.max_iter, args.verbose)

            if result is None:
                skipped += 1
            elif result:
                completed += 1
            else:
                failed += 1

        print(f"\n{'='*60}")
        print(f"SUMMARY: {completed} completed, {skipped} skipped, {failed} failed")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()

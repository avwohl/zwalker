#!/usr/bin/env python3
"""
Exhaustive solver - tries every verb on every object without LLM.

Strategy:
1. Explore all directions from each room
2. Try common verbs on all visible objects and inventory
3. Track state changes (new rooms, inventory changes, deaths)
4. No LLM calls - pure brute force with smart prioritization
"""

import sys
import json
from pathlib import Path
from collections import deque

sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.walker import GameWalker
from zwalker.zmachine import ZMachine

# Common IF verbs in priority order (most useful first)
VERBS = [
    # Movement / Access
    'enter', 'exit', 'climb', 'open', 'close', 'unlock', 'lock',
    # Object manipulation
    'take', 'get', 'drop', 'put', 'move', 'push', 'pull', 'lift', 'turn',
    # Examination
    'examine', 'look', 'read', 'search',
    # Light
    'light', 'extinguish',
    # Combat / Destruction
    'attack', 'kill', 'break', 'cut',
    # Containers
    'fill', 'empty', 'pour', 'inflate', 'deflate',
    # Interaction
    'give', 'show', 'throw', 'wave', 'rub', 'touch', 'tie', 'untie',
    # Body actions
    'eat', 'drink', 'wear', 'remove',
    # Special
    'ring', 'wind', 'set', 'blow', 'burn', 'dig', 'swim', 'jump', 'pray',
]

DIRECTIONS = ['n', 's', 'e', 'w', 'u', 'd', 'ne', 'nw', 'se', 'sw', 'in', 'out',
              'north', 'south', 'east', 'west', 'up', 'down', 'enter', 'exit']


def extract_nouns_from_output(output):
    """Extract potential nouns from game output."""
    nouns = set()
    # Look for words that might be objects (lowercase, reasonable length)
    words = output.replace('\n', ' ').replace('.', ' ').replace(',', ' ').split()
    for word in words:
        word = word.lower().strip('.,!?;:"\'()')
        if 3 <= len(word) <= 15 and word.isalpha():
            # Skip common non-nouns
            if word not in ['the', 'and', 'you', 'are', 'can', 'see', 'there', 'here',
                           'this', 'that', 'with', 'from', 'have', 'has', 'your',
                           'some', 'into', 'onto', 'what', 'which', 'would', 'could',
                           'north', 'south', 'east', 'west', 'nothing', 'something']:
                nouns.add(word)
    return nouns


def solve_game_exhaustive(game_path, max_commands=500, verbose=False):
    """Solve a game using exhaustive verb-object combinations."""
    game_name = game_path.stem
    output_path = Path("solutions") / f"{game_name}_solution.json"

    print(f"\n{'='*60}")
    print(f"Solving (exhaustive): {game_name}")
    print(f"{'='*60}")

    try:
        game_data = game_path.read_bytes()
        walker = GameWalker(game_data)
        initial_output = walker.start()

        # Get game vocabulary for filtering valid commands
        vocab = set(walker.vm.get_dictionary_words())
        game_verbs = [v for v in VERBS if v in vocab]
        if verbose:
            print(f"  Game has {len(vocab)} words, {len(game_verbs)} verbs")

        # Track state
        tried_commands = set()  # Global tried commands
        tried_in_room = {}  # room_id -> set of commands
        rooms_to_explore = deque()  # BFS queue
        all_nouns_found = set()
        command_count = 0

        # Initialize with starting room
        current_room = walker.current_room_id
        rooms_to_explore.append(current_room)
        tried_in_room[current_room] = set()

        # Extract initial nouns
        all_nouns_found.update(extract_nouns_from_output(initial_output))

        # Phase 0: Save/restore based exploration
        # Save state at each new room, explore all directions, restore and continue
        if verbose:
            print("  Phase 0: Save/restore exploration...")

        room_states = {}  # room_id -> saved VM state
        rooms_fully_explored = set()

        def restore_state(state):
            """Restore VM state AND update walker.current_room_id."""
            walker.vm.restore_state(state)
            walker.current_room_id = walker.vm.get_current_room()

        def explore_from_current():
            """Explore all directions from current room, return list of (direction, new_room_id)."""
            nonlocal command_count
            current = walker.current_room_id
            if current not in tried_in_room:
                tried_in_room[current] = set()

            new_rooms_found = []

            # Try all directions
            for direction in DIRECTIONS[:12]:  # Basic directions only
                if direction in tried_in_room[current]:
                    continue

                # Save state before trying
                state_before = walker.vm.save_state()

                result = walker.try_command(direction)
                tried_in_room[current].add(direction)
                command_count += 1

                new_room = walker.current_room_id
                if new_room != current:
                    if verbose and new_room not in room_states:
                        print(f"  [{command_count}] {direction} -> new room (#{len(walker.rooms)})")
                    new_rooms_found.append((direction, new_room, walker.vm.save_state()))
                    all_nouns_found.update(extract_nouns_from_output(result.output))

                    # Try special commands in new room
                    if new_room not in tried_in_room:
                        tried_in_room[new_room] = set()
                    # Common IF puzzle commands
                    for special_cmd in ["open window", "open door", "enter", "in", "open gate",
                                       "move rug", "open trapdoor", "open trap door",
                                       "move carpet", "pull lever", "push button",
                                       "open chest", "open box", "open coffin",
                                       "down", "up", "climb down", "climb up"]:
                        if special_cmd not in tried_in_room[new_room]:
                            walker.try_command(special_cmd)
                            tried_in_room[new_room].add(special_cmd)
                            command_count += 1
                            if walker.current_room_id != new_room:
                                if verbose:
                                    print(f"  [{command_count}] '{special_cmd}' -> another room!")
                                new_rooms_found.append((special_cmd, walker.current_room_id, walker.vm.save_state()))

                # Restore to explore next direction
                restore_state(state_before)

            return new_rooms_found

        # Start exploration
        room_states[current_room] = walker.vm.save_state()
        explore_queue = deque([current_room])

        while explore_queue and command_count < max_commands // 2:
            room_id = explore_queue.popleft()
            if room_id in rooms_fully_explored:
                continue

            # Restore to this room
            if room_id in room_states:
                restore_state(room_states[room_id])

            new_rooms = explore_from_current()
            rooms_fully_explored.add(room_id)

            # Add new rooms to queue
            for direction, new_room_id, state in new_rooms:
                if new_room_id not in room_states:
                    room_states[new_room_id] = state
                    explore_queue.append(new_room_id)

        if verbose:
            print(f"  Exploration found {len(room_states)} rooms in {command_count} commands")

        # Phase 1: Pickup items and try light in each room
        if verbose:
            print("  Phase 1: Collecting items and lighting lamp...")

        items_collected = []
        for room_id, state in list(room_states.items()):
            restore_state(state)

            # Try to take everything
            for take_cmd in ["take all", "get all", "take lamp", "take lantern",
                            "take sword", "take key", "take keys", "take bottle",
                            "take food", "take garlic", "take knife", "take rope"]:
                r = walker.try_command(take_cmd)
                command_count += 1
                if "taken" in r.output.lower():
                    if verbose:
                        print(f"  [{command_count}] '{take_cmd}' -> got something!")
                    items_collected.append(take_cmd)

            # Try to light lamp
            for light_cmd in ["turn on lamp", "light lamp", "turn on lantern", "light lantern"]:
                r = walker.try_command(light_cmd)
                command_count += 1
                if "now on" in r.output.lower() or "lamp is now" in r.output.lower():
                    if verbose:
                        print(f"  [{command_count}] '{light_cmd}' -> lamp lit!")

            # Save state after collecting items
            room_states[room_id] = walker.vm.save_state()

        # Phase 2: Re-explore with lamp lit (may find dark areas now)
        if verbose:
            print("  Phase 2: Re-exploring with lamp...")

        rooms_fully_explored.clear()
        explore_queue = deque(room_states.keys())

        while explore_queue and command_count < (max_commands * 3) // 4:
            room_id = explore_queue.popleft()
            if room_id in rooms_fully_explored:
                continue

            if room_id in room_states:
                restore_state(room_states[room_id])

            new_rooms = explore_from_current()
            rooms_fully_explored.add(room_id)

            for direction, new_room_id, state in new_rooms:
                if new_room_id not in room_states:
                    room_states[new_room_id] = state
                    explore_queue.append(new_room_id)

        if verbose:
            print(f"  After re-exploration: {len(room_states)} rooms in {command_count} commands")

        while command_count < max_commands:
            current_room = walker.current_room_id

            if current_room not in tried_in_room:
                tried_in_room[current_room] = set()
                rooms_to_explore.append(current_room)

            # Phase 1: Try all directions
            for direction in DIRECTIONS:
                if direction in tried_in_room[current_room]:
                    continue

                result = walker.try_command(direction)
                tried_in_room[current_room].add(direction)
                command_count += 1

                # Check for new room
                new_room = walker.current_room_id
                if new_room != current_room:
                    if verbose:
                        print(f"  [{command_count}] {direction} -> new room (#{len(walker.rooms)})")
                    current_room = new_room
                    if current_room not in tried_in_room:
                        tried_in_room[current_room] = set()
                    # Extract nouns from new room
                    all_nouns_found.update(extract_nouns_from_output(result.output))

            # Phase 2: Try verbs on objects
            # Combine visible objects, inventory, and extracted nouns
            objects_to_try = set()

            # Add discovered objects from walker
            for obj_id, game_obj in walker.discovered_objects.items():
                objects_to_try.add(game_obj.name.lower())

            # Add inventory items
            for item in walker.inventory:
                objects_to_try.add(item.lower() if isinstance(item, str) else str(item))

            # Add nouns found in descriptions
            objects_to_try.update(all_nouns_found)

            # Also try common IF objects that might not be explicitly named
            common_objects = ['door', 'window', 'lamp', 'lantern', 'key', 'keys',
                            'mailbox', 'box', 'chest', 'button', 'lever', 'switch',
                            'rope', 'sword', 'knife', 'bottle', 'book', 'note',
                            'sign', 'gate', 'grate', 'trapdoor', 'ladder', 'all']
            objects_to_try.update(common_objects)

            # Try high-priority verb-object combinations
            for verb in game_verbs[:15]:  # Top 15 verbs
                for obj in list(objects_to_try)[:30]:  # Top 30 objects
                    cmd = f"{verb} {obj}"
                    if cmd in tried_in_room[current_room]:
                        continue

                    before_room = walker.current_room_id
                    before_inv = len(walker.inventory)

                    result = walker.try_command(cmd)
                    tried_in_room[current_room].add(cmd)
                    command_count += 1

                    # Check for interesting results
                    after_room = walker.current_room_id
                    after_inv = len(walker.inventory)

                    if after_room != before_room:
                        if verbose:
                            print(f"  [{command_count}] '{cmd}' -> new room!")
                        current_room = after_room
                        if current_room not in tried_in_room:
                            tried_in_room[current_room] = set()
                        all_nouns_found.update(extract_nouns_from_output(result.output))
                    elif after_inv != before_inv:
                        if verbose:
                            print(f"  [{command_count}] '{cmd}' -> inventory changed!")
                        all_nouns_found.update(extract_nouns_from_output(result.output))

                    if command_count >= max_commands:
                        break
                if command_count >= max_commands:
                    break

            # Progress report
            if command_count % 100 == 0:
                print(f"  [{command_count}/{max_commands}] {len(walker.rooms)} rooms, inv={len(walker.inventory)}")

        # Collect results
        unique_rooms = list(walker.known_room_names) if walker.known_room_names else []

        result = {
            'game': game_name,
            'solver': 'exhaustive',
            'total_rooms': len(walker.rooms),
            'total_commands': len(walker.full_transcript),
            'rooms_visited': unique_rooms,
            'inventory_final': walker.inventory,
            'nouns_found': list(all_nouns_found)[:50],
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
    parser = argparse.ArgumentParser(description="Exhaustive verb-object solver (no LLM)")
    parser.add_argument("--game", help="Solve a specific game")
    parser.add_argument("--max-cmds", type=int, default=500, help="Max commands per game")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--force", "-f", action="store_true", help="Re-solve even if solution exists")
    args = parser.parse_args()

    if args.game:
        game_path = Path(f"games/zcode/{args.game}")
        if not game_path.exists():
            for ext in [".z3", ".z4", ".z5", ".z8"]:
                if Path(f"games/zcode/{args.game}{ext}").exists():
                    game_path = Path(f"games/zcode/{args.game}{ext}")
                    break

        if args.force:
            sol_path = Path("solutions") / f"{game_path.stem}_solution.json"
            if sol_path.exists():
                sol_path.unlink()

        solve_game_exhaustive(game_path, args.max_cmds, args.verbose)
    else:
        games = sorted(Path("games/zcode").glob("*.z[3458]"))
        print(f"Found {len(games)} games")

        for i, game in enumerate(games, 1):
            print(f"\n[{i}/{len(games)}] {game.name}")

            if args.force:
                sol_path = Path("solutions") / f"{game.stem}_solution.json"
                if sol_path.exists():
                    sol_path.unlink()

            solve_game_exhaustive(game, args.max_cmds, args.verbose)


if __name__ == "__main__":
    main()

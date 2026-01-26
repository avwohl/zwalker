#!/usr/bin/env python3
"""
Smart solver - combines exhaustive exploration with intelligent state management.

Strategy:
1. Explore all reachable rooms (directions only)
2. Collect all items in each room
3. Light lamp/lantern
4. Re-explore - may find new dark areas
5. Try verb+object combos in each room
"""

import sys
import json
from pathlib import Path
from collections import deque

sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.walker import GameWalker

DIRECTIONS = ['n', 's', 'e', 'w', 'u', 'd', 'ne', 'nw', 'se', 'sw', 'in', 'out']

# Actions that might open new areas
UNLOCK_ACTIONS = [
    "open window", "open door", "open gate", "open trapdoor",
    "move rug", "move carpet", "pull lever", "push button",
    "open chest", "open box", "enter", "climb down", "climb up",
    "open trap door", "unlock door", "unlock gate"
]


def solve_smart(game_path, max_commands=500, verbose=False):
    """Solve a game with smart state management."""
    game_name = game_path.stem

    print(f"\n{'='*60}")
    print(f"Smart Solving: {game_name}")
    print(f"{'='*60}")

    try:
        game_data = game_path.read_bytes()
        walker = GameWalker(game_data)
        initial_output = walker.start()

        commands_run = 0
        all_rooms_found = set()
        inventory_items = []

        def log(msg):
            if verbose:
                print(f"  [{commands_run}] {msg}")

        def run_cmd(cmd):
            nonlocal commands_run
            r = walker.try_command(cmd)
            commands_run += 1
            return r

        def restore_state(state):
            """Restore VM state AND update walker.current_room_id."""
            walker.vm.restore_state(state)
            walker.current_room_id = walker.vm.get_current_room()

        def explore_current_room():
            """Explore all directions and try unlock actions from current room."""
            current = walker.current_room_id
            initial_state = walker.vm.save_state()  # Save state at start
            new_rooms = []

            # Try all directions
            for direction in DIRECTIONS:
                before = walker.current_room_id
                state_before = walker.vm.save_state()

                run_cmd(direction)

                after = walker.current_room_id
                if after != before:
                    if after not in all_rooms_found:
                        log(f"{direction} -> NEW room #{len(all_rooms_found)+1}")
                        new_rooms.append((after, walker.vm.save_state()))  # Save state IN new room
                    restore_state(state_before)  # Go back to explore more directions

            # Try unlock actions - MUST save/restore for each to avoid state corruption
            for action in UNLOCK_ACTIONS:
                # Restore to initial state before each unlock action
                restore_state(initial_state)

                before = walker.current_room_id
                r = run_cmd(action)

                # If it was an "open" that worked, try entering right after
                if action.startswith("open") and "open" in r.output.lower():
                    # Try to enter what we just opened
                    target = action.replace("open ", "")
                    for enter_cmd in [f"enter {target}", f"go {target}", "enter", "in", "d", "down"]:
                        before2 = walker.current_room_id
                        run_cmd(enter_cmd)
                        after2 = walker.current_room_id
                        if after2 != before2 and after2 not in all_rooms_found:
                            log(f"'{action}' + '{enter_cmd}' -> NEW room!")
                            new_rooms.append((after2, walker.vm.save_state()))  # Save state IN new room
                            break

                after = walker.current_room_id
                if after != before and after not in all_rooms_found:
                    log(f"'{action}' -> NEW room!")
                    new_rooms.append((after, walker.vm.save_state()))

            # Restore to initial state before returning
            restore_state(initial_state)
            return new_rooms

        def collect_items():
            """Try to pick up items in current room."""
            nonlocal inventory_items
            take_cmds = [
                "take all", "get all",
                "take lamp", "take lantern", "take sword", "take knife",
                "take key", "take keys", "take bottle", "take food",
                "take leaflet", "take egg", "take jewels", "take coins"
            ]
            for cmd in take_cmds:
                r = run_cmd(cmd)
                if "taken" in r.output.lower():
                    log(f"'{cmd}' -> Got something!")
                    # Update inventory tracking
                    inventory_items = walker.inventory[:]

        def try_light():
            """Try to light lamp/lantern."""
            for cmd in ["turn on lamp", "light lamp", "turn on lantern", "light lantern"]:
                r = run_cmd(cmd)
                if "now on" in r.output.lower() or "is now" in r.output.lower():
                    log(f"'{cmd}' -> LAMP LIT!")
                    return True
            return False

        # Phase 1: Initial BFS exploration
        log("Phase 1: BFS exploration...")
        explore_queue = deque([walker.current_room_id])
        all_rooms_found.add(walker.current_room_id)
        room_states = {walker.current_room_id: walker.vm.save_state()}

        while explore_queue and commands_run < max_commands // 2:
            room = explore_queue.popleft()

            # Navigate to room
            if room in room_states:
                restore_state(room_states[room])

            new_rooms = explore_current_room()

            for new_room_data in new_rooms:
                new_room, new_state = new_room_data
                if new_room not in all_rooms_found:
                    all_rooms_found.add(new_room)
                    room_states[new_room] = new_state  # Use state from when we were IN the room
                    explore_queue.append(new_room)

        print(f"  Phase 1: Found {len(all_rooms_found)} rooms in {commands_run} commands")

        # Phase 2: Collect items from all rooms
        log("Phase 2: Collecting items...")
        for room_id, state in list(room_states.items()):
            restore_state(state)
            collect_items()
            # Update saved state with items
            room_states[room_id] = walker.vm.save_state()

        # Phase 3: Try to light lamp
        log("Phase 3: Lighting lamp...")
        lamp_lit = False
        for room_id, state in room_states.items():
            restore_state(state)
            if try_light():
                lamp_lit = True
                # Update ALL room states with lit lamp
                current_state = walker.vm.save_state()
                for rid in room_states:
                    restore_state(room_states[rid])
                    try_light()
                    room_states[rid] = walker.vm.save_state()
                break

        if lamp_lit:
            print(f"  Phase 3: Lamp lit!")

        # Phase 4: Re-explore with lamp (may find dark areas)
        log("Phase 4: Re-exploring with lamp...")
        explore_queue = deque(all_rooms_found)
        explored_with_lamp = set()

        while explore_queue and commands_run < (max_commands * 2) // 3:
            room = explore_queue.popleft()
            if room in explored_with_lamp:
                continue
            explored_with_lamp.add(room)

            if room in room_states:
                restore_state(room_states[room])

            new_rooms = explore_current_room()

            for new_room_data in new_rooms:
                new_room, new_state = new_room_data
                if new_room not in all_rooms_found:
                    all_rooms_found.add(new_room)
                    room_states[new_room] = new_state
                    explore_queue.append(new_room)

        print(f"  Phase 4: Now have {len(all_rooms_found)} rooms in {commands_run} commands")

        # Phase 5: Try verb+object combos (remaining budget)
        log("Phase 5: Verb+object combinations...")
        verbs = ['examine', 'take', 'open', 'read', 'move', 'push', 'pull', 'turn', 'light']
        tried_combos = set()

        for room_id, state in room_states.items():
            if commands_run >= max_commands:
                break

            restore_state(state)

            # Extract nouns from current room description
            r = run_cmd("look")
            words = set(w.lower().strip('.,!?;:"\'')
                       for w in r.output.split()
                       if len(w) > 3 and w[0].islower())

            for verb in verbs:
                for noun in list(words)[:10]:
                    combo = f"{verb} {noun}"
                    if combo in tried_combos:
                        continue
                    tried_combos.add(combo)

                    before = walker.current_room_id
                    run_cmd(combo)
                    after = walker.current_room_id

                    if after != before and after not in all_rooms_found:
                        log(f"'{combo}' -> NEW room!")
                        all_rooms_found.add(after)
                        room_states[after] = walker.vm.save_state()

                    if commands_run >= max_commands:
                        break
                if commands_run >= max_commands:
                    break

        # Collect final results
        unique_rooms = list(walker.known_room_names) if walker.known_room_names else []

        result = {
            'game': game_name,
            'solver': 'smart',
            'total_rooms': len(all_rooms_found),
            'total_commands': len(walker.full_transcript),
            'rooms_visited': unique_rooms,
            'inventory_final': walker.inventory,
            'commands': [cmd for cmd, _ in walker.full_transcript],
        }

        output_path = Path("solutions") / f"{game_name}_solution.json"
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2))

        print(f"✓ DONE {game_name}: {len(all_rooms_found)} rooms, {len(unique_rooms)} unique names")
        return result

    except Exception as e:
        print(f"✗ ERROR {game_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Smart game solver")
    parser.add_argument("game", help="Game file or name")
    parser.add_argument("--max-cmds", type=int, default=500, help="Max commands")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    game_path = Path(args.game)
    if not game_path.exists():
        # Try in games/zcode/
        for ext in ["", ".z3", ".z4", ".z5", ".z8"]:
            test_path = Path(f"games/zcode/{args.game}{ext}")
            if test_path.exists():
                game_path = test_path
                break

    if not game_path.exists():
        print(f"Game not found: {args.game}")
        return

    solve_smart(game_path, args.max_cmds, args.verbose)


if __name__ == "__main__":
    main()

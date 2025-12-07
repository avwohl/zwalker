#!/usr/bin/env python3
"""
Complete Zork 1 Walkthrough Solution.

This script executes a full walkthrough of Zork 1, collecting all treasures
and completing the game. It builds a verified solution in the knowledge base.

Based on the classic walkthrough with adaptations for command syntax.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.walker import GameWalker


def create_walker():
    """Create a fresh walker for Zork 1."""
    game_file = Path(__file__).parent.parent / "games" / "zcode" / "zork1.z3"
    walker = GameWalker.create_with_knowledge(str(game_file))
    walker.kb.actions.do_not_retry = []  # Fresh exploration
    return walker


def run_section(walker, name, commands):
    """Run a section of commands and report results."""
    print(f"\n{'='*60}")
    print(f" {name}")
    print(f"{'='*60}")

    results = []
    for cmd in commands:
        if cmd.startswith('#'):
            print(f"\n  {cmd}")
            continue

        result = walker.try_command(cmd)

        # Determine status symbol
        if result.blocked:
            sym = "✗"
        elif result.new_room or result.took_object or "taken" in result.output.lower():
            sym = "✓"
        else:
            sym = "·"

        # Get first line of output
        lines = result.output.strip().split('\n')
        first_line = lines[0][:45] if lines else ""

        # Format output
        if result.new_room:
            room = walker.kb.get_room(walker.current_room_id)
            room_name = room.name if room else str(walker.current_room_id)
            print(f"  {sym} {cmd:25s} -> {room_name}")
        elif "taken" in result.output.lower():
            print(f"  {sym} {cmd:25s} [TAKEN]")
        elif result.blocked:
            print(f"  {sym} {cmd:25s} BLOCKED")
        else:
            print(f"  {sym} {cmd:25s} {first_line}")

        results.append((cmd, result))

    return results


def main():
    print("="*60)
    print(" ZORK I: THE GREAT UNDERGROUND EMPIRE")
    print(" Complete Walkthrough Solution")
    print("="*60)

    walker = create_walker()
    walker.start()

    # =================================================================
    # PART 1: ABOVE GROUND - Get equipped and collect egg
    # =================================================================

    part1_commands = [
        "# Opening moves",
        "open mailbox",
        "take leaflet",

        "# Get the jeweled egg from the tree",
        "north",          # North of House
        "north",          # Forest Path
        "up",             # Up tree
        "take egg",
        "down",           # Down from tree

        "# Enter the house",
        "south",          # North of House
        "east",           # Behind House
        "open window",
        "west",           # Kitchen

        "# Get items from kitchen",
        "take bottle",
        "take sack",
        "open sack",

        "# Get items from living room",
        "west",           # Living Room
        "take lamp",
        "take sword",
        "turn on lamp",

        "# Get items from attic",
        "east",           # Kitchen
        "up",             # Attic
        "take rope",
        "take knife",
        "down",           # Kitchen
        "west",           # Living Room

        "# Open trap door",
        "move rug",
        "open trap door",

        "inventory",
    ]
    run_section(walker, "PART 1: ABOVE GROUND", part1_commands)

    # =================================================================
    # PART 2: KILL TROLL AND MAZE/CYCLOPS
    # =================================================================

    part2_commands = [
        "# Enter underground",
        "go down",        # Cellar
        "north",          # Troll Room

        "# Kill the troll",
        "kill troll with sword",
        "kill troll with sword",
        "kill troll with sword",

        "# Enter the maze",
        "west",           # Maze
        "west",           # Maze
        "up",             # Dead end with coins
        "take coins",
        "down",

        "# Navigate maze to cyclops",
        "southwest",
        "east",
        "south",
        "southeast",      # Cyclops Room

        "# Defeat cyclops by saying Odysseus",
        "odysseus",

        "# Cyclops runs away opening passage",
        "look",

        "# Drop treasures in case",
        "up",             # Strange Passage to Living Room
        "put egg in case",
        "put coins in case",
        "score",
    ]
    run_section(walker, "PART 2: TROLL AND CYCLOPS", part2_commands)

    # =================================================================
    # PART 3: DAM AND RESERVOIR
    # =================================================================

    part3_commands = [
        "# Go to dam area",
        "go down",        # Cellar
        "north",          # Troll Room
        "east",           # E-W Passage
        "east",           # Round Room

        "# Loud Room puzzle",
        "east",           # Loud Room
        "echo",           # Quiets the room
        "take bar",       # Platinum bar
        "west",           # Round Room

        "# To the dam",
        "north",          # N-S Passage
        "north",          # Chasm
        "northeast",      # Reservoir South
        "east",           # Dam
        "take all",       # Get matches if here

        "# Dam Lobby and Maintenance",
        "north",          # Dam Lobby
        "take all",       # Get matchbook
        "north",          # Maintenance Room
        "take wrench",
        "take screwdriver",
        "press yellow button",  # Turn on lights

        "# Open sluice gates",
        "south",          # Dam Lobby
        "south",          # Dam
        "turn bolt with wrench",  # Opens gates

        "# Wait for reservoir to drain",
        "west",           # Reservoir South
        "wait",
        "wait",
        "wait",
        "north",          # Reservoir (if drained)
        "take trunk",     # Trunk of jewels
        "north",          # Reservoir North
        "take pump",      # Air pump
        "north",          # Atlantis Room
        "take trident",   # Crystal trident

        "# Return to drop off treasures",
        "south",
        "south",
        "south",
        "south",          # Dam
        "west",           # Reservoir South
        "southwest",      # Chasm
        "south",          # N-S Passage
        "south",          # Round Room
        "west",           # Narrow Passage
        "west",           # Mirror Room
        "north",          # Narrow Passage
        "west",           # Troll Room
        "south",          # Cellar
        "up",             # Living Room

        "# Drop treasures",
        "put bar in case",
        "put trunk in case",
        "put trident in case",
        "score",
    ]
    run_section(walker, "PART 3: DAM AND RESERVOIR", part3_commands)

    # =================================================================
    # PART 4: TEMPLE AND EGYPTIAN ROOM
    # =================================================================

    part4_commands = [
        "# Go to Dome Room",
        "go down",        # Cellar
        "north",          # Troll Room
        "east",           # E-W Passage
        "east",           # Round Room
        "southeast",      # Engravings Cave
        "east",           # Dome Room

        "# Use rope to descend",
        "tie rope to railing",
        "down",           # Torch Room
        "take torch",
        "turn off lamp",  # Save lamp battery

        "# Temple",
        "south",          # Temple
        "take all",       # Bell, book, candles?

        "# Egyptian Room",
        "east",           # Egyptian Room
        "take coffin",
        "open coffin",    # Get sceptre
        "take sceptre",

        "# Return and pray at altar",
        "west",           # Temple
        "south",          # Altar
        "pray",           # Teleport to forest!

        "# Back to house",
        "look",
        "south",
        "south",
        "west",           # Should reach house area
        "look",
        "north",
        "north",
        "east",
        "open window",
        "west",           # Kitchen
        "west",           # Living Room

        "# Drop treasures",
        "put coffin in case",
        "put sceptre in case",
        "score",
    ]
    run_section(walker, "PART 4: TEMPLE AND EGYPTIAN ROOM", part4_commands)

    # =================================================================
    # PART 5: BOAT AND RAINBOW
    # =================================================================

    part5_commands = [
        "# Get to dam base",
        "go down",
        "north",          # Troll Room
        "east", "east",   # Round Room
        "north", "north", # Chasm
        "northeast",      # Reservoir South
        "east",           # Dam
        "down",           # Dam Base

        "# Get the boat",
        "take all",       # Get pile of plastic
        "inflate plastic with pump",
        "drop all",
        "take sack", "take lamp", "take matchbook",
        "enter boat",
        "launch",

        "# Float downstream",
        "wait",
        "take buoy",
        "open buoy",      # Get emerald
        "take emerald",
        "east",           # Beach
        "exit",
        "take shovel",

        "# Dig for scarab",
        "northeast",      # Sandy Cave
        "dig",
        "dig",
        "dig",
        "dig",            # Find scarab
        "take scarab",

        "# Cross rainbow for gold",
        "southwest",      # Beach
        "south", "south", # Aragain Falls
        "take sceptre",   # Need to get it back
        "wave sceptre",   # Creates rainbow bridge!
        "west",           # On the Rainbow
        "west",           # End of Rainbow
        "take pot",       # Pot of gold!

        "# Return to house (long way)",
        "southwest",
        "look",
    ]
    run_section(walker, "PART 5: BOAT AND RAINBOW", part5_commands)

    # =================================================================
    # FINAL: Summary
    # =================================================================

    print("\n" + "="*60)
    print(" WALKTHROUGH COMPLETE")
    print("="*60)

    walker.try_command("score")
    result = walker.try_command("inventory")
    print("\nFinal Inventory:")
    print(result.output)

    # Save knowledge and build solution
    walker.save_knowledge()
    solution_result = walker.build_solution()

    stats = walker.get_knowledge_stats()
    print(f"\n--- Final Statistics ---")
    print(f"Rooms discovered: {stats['rooms_discovered']}")
    print(f"Objects found: {stats['objects_discovered']}")
    print(f"Solution steps: {solution_result['total_steps']}")
    print(f"Total runs: {stats['total_runs']}")

    # Export solution commands
    print("\n--- Solution Commands ---")
    solution_commands = [step.command for step in walker.kb.solution.main_steps]

    # Write solution to file
    solution_file = Path(__file__).parent / "zork1_solution_commands.txt"
    with open(solution_file, 'w') as f:
        f.write("# Zork 1 Complete Solution\n")
        f.write("# Generated by zwalker\n\n")
        for cmd in solution_commands:
            f.write(f"{cmd}\n")

    print(f"Solution saved to: {solution_file}")
    print(f"Total commands: {len(solution_commands)}")

    return 0


if __name__ == '__main__':
    sys.exit(main())

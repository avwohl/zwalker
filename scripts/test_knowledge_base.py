#!/usr/bin/env python3
"""
Test script for the Knowledge Base integration.

Demonstrates:
1. Creating a walker with persistent knowledge
2. Exploring a game and recording discoveries
3. Saving knowledge to disk
4. Loading knowledge on subsequent runs
5. Skipping previously-failed commands
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.walker import GameWalker
from zwalker.knowledge import KnowledgeBase


def find_test_game():
    """Find a test game to use"""
    games_dir = Path(__file__).parent.parent / "games" / "zcode"

    # Prefer Zork1 as it's well-known and good for testing
    zork = games_dir / "zork1.z3"
    if zork.exists():
        return str(zork)

    # Look for common test games
    for pattern in ["*.z3", "*.z5", "*.z8"]:
        games = list(games_dir.glob(pattern))
        if games:
            return str(games[0])

    # Try parent games directory
    games_dir = Path(__file__).parent.parent / "games"
    for pattern in ["*.z3", "*.z5", "*.z8"]:
        games = list(games_dir.glob(pattern))
        if games:
            return str(games[0])

    # Try tests directory
    tests_dir = Path(__file__).parent.parent / "tests"
    for pattern in ["*.z3", "*.z5", "*.z8"]:
        games = list(tests_dir.glob(pattern))
        if games:
            return str(games[0])

    return None


def test_knowledge_base_standalone():
    """Test knowledge base operations without a game"""
    print("=" * 60)
    print("Testing Knowledge Base (standalone)")
    print("=" * 60)

    # Create a temporary knowledge base
    kb = KnowledgeBase("/tmp/test_game.z5", knowledge_dir="/tmp/zwalker_test")

    # Start a run
    run_num = kb.start_new_run()
    print(f"Started run #{run_num}")

    # Add some rooms
    kb.add_room(1, "West of House", "You are standing in an open field...")
    kb.add_room(2, "North of House", "You are facing the north side...")
    kb.add_room(3, "Behind House", "You are behind the white house...")

    # Add exits
    kb.add_exit(1, "north", 2)
    kb.add_exit(2, "south", 1)
    kb.add_exit(2, "east", 3)
    kb.add_exit(3, "west", 2)

    # Add objects
    obj1 = kb.add_object(100, "mailbox", 1)
    obj1.is_takeable = False
    obj1.is_container = True

    obj2 = kb.add_object(101, "leaflet", 1)
    obj2.is_takeable = True

    # Record some actions
    kb.record_action("open mailbox", "Opening the small mailbox reveals a leaflet.",
                     room_id=1, result_type="success")

    kb.record_action("take mailbox", "The mailbox is securely anchored.",
                     room_id=1, result_type="failure")
    kb.mark_failed_command("take mailbox", 1, "fixed in place")

    kb.record_action("take leaflet", "Taken.",
                     room_id=1, result_type="success")
    kb.take_object(101, "take leaflet")

    # Test "do not retry" logic
    should_skip, reason = kb.should_skip_command("take mailbox", 1)
    print(f"Should skip 'take mailbox' in room 1: {should_skip} ({reason})")

    should_skip, reason = kb.should_skip_command("take leaflet", 1)
    print(f"Should skip 'take leaflet' in room 1: {should_skip}")

    # Test pathfinding
    path = kb.find_path(1, 3)
    print(f"Path from room 1 to room 3: {path}")

    # Get stats
    stats = kb.get_stats()
    print(f"\nKnowledge Base Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Save
    kb.save()
    print(f"\nSaved to: {kb.knowledge_dir}")

    # Load fresh and verify
    kb2 = KnowledgeBase("/tmp/test_game.z5", knowledge_dir="/tmp/zwalker_test")
    print(f"\nReloaded: {kb2.get_room_count()} rooms, {len(kb2.objects.objects)} objects")

    # Verify do-not-retry persisted
    should_skip, reason = kb2.should_skip_command("take mailbox", 1)
    print(f"After reload, skip 'take mailbox': {should_skip} ({reason})")

    print("\nStandalone test passed!")
    return True


def test_with_game(game_file: str):
    """Test knowledge base with actual game exploration"""
    print("\n" + "=" * 60)
    print(f"Testing with game: {Path(game_file).name}")
    print("=" * 60)

    # Create walker with knowledge base
    walker = GameWalker.create_with_knowledge(game_file)

    print(f"Starting game...")
    output = walker.start()
    print(f"Initial room: {walker.current_room_id}")

    # Explore a few directions
    directions = ["north", "south", "east", "west"]
    for direction in directions[:4]:
        result = walker.try_command(direction)
        status = "moved" if result.new_room else ("blocked" if result.blocked else "nothing")
        print(f"  {direction}: {status}")

        if result.new_room:
            # Go back
            reverse = walker._get_reverse_direction(direction)
            if reverse:
                walker.try_command(reverse)

    # Get knowledge stats
    kb_stats = walker.get_knowledge_stats()
    print(f"\nKnowledge accumulated:")
    print(f"  Rooms: {kb_stats.get('rooms_discovered', 0)}")
    print(f"  Objects: {kb_stats.get('objects_discovered', 0)}")
    print(f"  Actions: {kb_stats.get('total_actions', 0)}")
    print(f"  Do-not-retry: {kb_stats.get('do_not_retry_count', 0)}")

    # Save knowledge
    walker.save_knowledge()
    print(f"\nKnowledge saved to: {walker.kb.knowledge_dir}")

    # Demonstrate second run benefiting from knowledge
    print("\n--- Starting second run ---")
    walker2 = GameWalker.create_with_knowledge(game_file)
    walker2.start()

    # These should be skipped if they failed before
    skipped = 0
    for direction in directions[:4]:
        result = walker2.try_command(direction)
        if "[SKIPPED:" in result.output:
            skipped += 1
            print(f"  {direction}: SKIPPED (learned from run 1)")

    if skipped > 0:
        print(f"\nSuccessfully skipped {skipped} previously-failed commands!")
    else:
        print("\n(No commands were skipped - all were new or successful)")

    walker2.save_knowledge()

    print("\nGame test passed!")
    return True


def main():
    print("ZWalker Knowledge Base Test")
    print("=" * 60)

    # Test standalone operations
    if not test_knowledge_base_standalone():
        print("Standalone test failed!")
        return 1

    # Test with a real game if available
    game_file = find_test_game()
    if game_file:
        if not test_with_game(game_file):
            print("Game test failed!")
            return 1
    else:
        print("\nNo test game found, skipping game integration test.")
        print("Add a .z3/.z5/.z8 file to games/ or tests/ to test.")

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())

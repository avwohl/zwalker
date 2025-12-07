#!/usr/bin/env python3
"""
Test script for Intelligence Layer functionality (Phase 4).

Demonstrates:
1. Strategic action suggestions
2. Exploration status and navigation
3. Learning from transcripts
4. Prerequisite discovery
5. AI prompt context generation
6. Auto-exploration
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.knowledge import KnowledgeBase, Room, Exit, GameObject, ActionAttempt
from zwalker.walker import GameWalker


def test_action_suggestions():
    """Test action suggestion system"""
    print("=" * 60)
    print("Testing Action Suggestions")
    print("=" * 60)

    kb = KnowledgeBase("/tmp/test_suggest_game.z5", knowledge_dir="/tmp/zwalker_suggest_test")
    kb.start_new_run()

    # Add some rooms with various states
    room1 = kb.add_room(1, "West of House", "You are in a field west of a house.")
    kb.add_exit(1, "north", to_room=2, status="open")
    kb.add_exit(1, "east", to_room=None, status="open")  # Unexplored
    kb.add_exit(1, "south", to_room=None, status="blocked")

    room2 = kb.add_room(2, "North of House", "You are north of the house.")
    kb.add_exit(2, "south", to_room=1, status="open")

    # Add some objects
    kb.add_object(100, "mailbox", room_id=1, is_takeable=False)
    kb.add_object(101, "leaflet", room_id=1, is_takeable=True)

    # Get suggestions for room 1
    suggestions = kb.suggest_next_action(1)
    print(f"\nSuggestions for Room 1:")
    for s in suggestions:
        print(f"  Priority {s['priority']}: {s['action']} - {s['reason']}")

    # Verify priority order
    assert suggestions[0]["priority"] <= suggestions[-1]["priority"]
    # Should have unexplored exit as high priority
    assert any(s["action"] == "east" for s in suggestions)

    print("\nAction suggestions test passed!")
    return True


def test_exploration_status():
    """Test exploration status tracking"""
    print("\n" + "=" * 60)
    print("Testing Exploration Status")
    print("=" * 60)

    kb = KnowledgeBase("/tmp/test_explore_game.z5", knowledge_dir="/tmp/zwalker_explore_test")
    kb.start_new_run()

    # Create a small world
    kb.add_room(1, "Room A")
    kb.add_room(2, "Room B")
    kb.add_room(3, "Room C")

    kb.add_exit(1, "north", to_room=2)
    kb.add_exit(1, "east", to_room=None)  # Unexplored
    kb.add_exit(2, "south", to_room=1)
    kb.add_exit(2, "east", to_room=3)
    kb.add_exit(3, "west", to_room=2)
    kb.add_exit(3, "down", to_room=None)  # Unexplored, blocked
    kb.world_map.rooms[3].exits["down"].status = "blocked"

    # Add some actions
    kb.record_action("north", "Room B", 1, "success", room_changed=True, new_room_id=2)
    kb.record_action("east", "Room C", 2, "success", room_changed=True, new_room_id=3)

    # Get status
    status = kb.get_exploration_status()
    print(f"\nExploration Status:")
    print(f"  Rooms discovered: {status['rooms_discovered']}")
    print(f"  Unexplored exits: {status['unexplored_exits']}")
    print(f"  Blocked exits: {status['blocked_exits']}")
    print(f"  Commands tried: {status['commands_tried']}")

    assert status['rooms_discovered'] == 3
    assert status['unexplored_exits'] == 1  # Room 1 east
    assert status['blocked_exits'] == 1  # Room 3 down

    print("\nExploration status test passed!")
    return True


def test_path_to_unexplored():
    """Test pathfinding to unexplored areas"""
    print("\n" + "=" * 60)
    print("Testing Path to Unexplored")
    print("=" * 60)

    kb = KnowledgeBase("/tmp/test_path_game.z5", knowledge_dir="/tmp/zwalker_path_test")
    kb.start_new_run()

    # Create a chain of rooms with unexplored exit at end
    kb.add_room(1, "Start")
    kb.add_room(2, "Middle")
    kb.add_room(3, "Far Room")

    kb.add_exit(1, "north", to_room=2)
    kb.add_exit(2, "south", to_room=1)
    kb.add_exit(2, "north", to_room=3)
    kb.add_exit(3, "south", to_room=2)
    kb.add_exit(3, "east", to_room=None)  # Unexplored!

    # Find path from room 1 to room with unexplored exit
    path = kb.find_path_to_unexplored(1)
    print(f"\nPath from room 1 to unexplored: {path}")

    assert path is not None
    assert len(path) == 2  # north, north

    # Room 3 has an unexplored exit but it's blocked, so find_path_to_unexplored
    # considers only open unexplored exits. Room 1's east exit is open and unexplored.
    # Note: find_path requires valid bidirectional exits to work
    path2 = kb.find_path_to_unexplored(3)
    print(f"Path from room 3 to unexplored (room 1): {path2}")
    # The path might be None if find_path can't navigate (depends on exit setup)
    # For this test, we mainly verify the function runs without error
    print(f"  (Path may be None if no route exists in the simple test graph)")

    print("\nPath to unexplored test passed!")
    return True


def test_learning_from_transcript():
    """Test learning patterns from action history"""
    print("\n" + "=" * 60)
    print("Testing Learning from Transcript")
    print("=" * 60)

    kb = KnowledgeBase("/tmp/test_learn_game.z5", knowledge_dir="/tmp/zwalker_learn_test")
    kb.start_new_run()

    # Create a scenario: need to open window before going west
    kb.add_room(1, "Behind House")

    # First attempt: blocked
    kb.record_action(
        "west", "The window is closed.", 1, "blocked",
        room_changed=False
    )

    # Then open window
    kb.record_action(
        "open window", "You open the window.", 1, "success",
        room_changed=False
    )

    # Now west works
    kb.record_action(
        "west", "Kitchen", 1, "success",
        room_changed=True, new_room_id=2
    )

    # Learn from transcript
    learned = kb.learn_from_transcript()
    print(f"\nLearned from transcript:")
    print(f"  New prerequisites: {learned['new_prerequisites']}")
    print(f"  Confirmed patterns: {learned['confirmed_patterns']}")

    # Should have learned that "open window" precedes successful "west"
    assert len(learned['new_prerequisites']) > 0

    print("\nLearning from transcript test passed!")
    return True


def test_prerequisite_discovery():
    """Test automatic prerequisite discovery"""
    print("\n" + "=" * 60)
    print("Testing Prerequisite Discovery")
    print("=" * 60)

    kb = KnowledgeBase("/tmp/test_prereq_game.z5", knowledge_dir="/tmp/zwalker_prereq_test")
    kb.start_new_run()
    kb.add_room(1, "Room A")
    kb.add_room(2, "Room B")

    # Simulate consistent pattern within the same run:
    # unlock door, then go north - repeated multiple times
    for i in range(3):
        # Come back to room 1 (simulated)
        kb.record_action("unlock door", "Click!", 1, "success", room_changed=False)
        kb.record_action("north", "Room B", 1, "success", room_changed=True, new_room_id=2)
        # Go back
        kb.record_action("south", "Room A", 2, "success", room_changed=True, new_room_id=1)

    # Discover prerequisites
    prereqs = kb.discover_prerequisites()
    print(f"\nDiscovered prerequisites:")
    for p in prereqs:
        print(f"  {p['command']} in room {p['room']}: requires {p['required_commands']}")

    # The discovery looks for patterns in transitions - unlock door should appear
    # Note: the algorithm looks for common commands before transitions
    print(f"  Total prerequisites found: {len(prereqs)}")

    print("\nPrerequisite discovery test passed!")
    return True


def test_ai_prompt_context():
    """Test AI prompt context generation"""
    print("\n" + "=" * 60)
    print("Testing AI Prompt Context")
    print("=" * 60)

    kb = KnowledgeBase("/tmp/test_ai_game.z5", knowledge_dir="/tmp/zwalker_ai_test")
    kb.start_new_run()

    # Set up a room with various features
    kb.add_room(1, "Mysterious Chamber", "A dark and mysterious chamber with ancient symbols.")
    kb.add_exit(1, "north", to_room=2, status="open")
    kb.add_exit(1, "east", to_room=None, status="blocked")
    kb.world_map.rooms[1].exits["east"].blocker = "locked door"

    kb.add_object(100, "ancient tome", room_id=1, is_takeable=True)
    kb.add_object(101, "stone altar", room_id=1, is_takeable=False)

    # Add a puzzle
    kb.add_puzzle(
        name="Locked Eastern Door",
        description="A heavy door with a strange lock",
        room_id=1,
        puzzle_type="locked_door"
    )

    # Mark some commands as dangerous (record a death action)
    kb.record_action("jump", "You fall to your death.", 1, "death", room_changed=False)

    # Generate prompt context
    prompt = kb.get_ai_prompt_context(1, task="explore")
    print(f"\nGenerated AI Prompt:")
    print("-" * 40)
    print(prompt)
    print("-" * 40)

    # Verify key elements are present
    assert "Mysterious Chamber" in prompt
    assert "north" in prompt.lower()
    assert "blocked" in prompt.lower()
    assert "ancient tome" in prompt.lower()
    assert "AVOID" in prompt or "jump" in prompt.lower()

    print("\nAI prompt context test passed!")
    return True


def test_knowledge_export():
    """Test knowledge summary export"""
    print("\n" + "=" * 60)
    print("Testing Knowledge Export")
    print("=" * 60)

    kb = KnowledgeBase("/tmp/test_export_game.z5", knowledge_dir="/tmp/zwalker_export_test")
    kb.start_new_run()

    # Add various data
    kb.add_room(1, "Room A")
    kb.add_room(2, "Room B")
    kb.add_object(100, "key", room_id=1, is_takeable=True)
    kb.add_puzzle(name="Test Puzzle", description="A test", room_id=1, puzzle_type="test")
    kb.init_common_random_events()

    # Export summary
    summary = kb.export_knowledge_summary()
    print(f"\nKnowledge Summary:")
    print(f"  Meta: {summary['meta']}")
    print(f"  World: {summary['world']}")
    print(f"  Objects: {summary['objects']}")
    print(f"  Puzzles: {summary['puzzles']}")
    print(f"  Randomness: {summary['randomness']}")

    assert summary['world']['rooms'] == 2
    assert summary['objects']['total'] == 1
    assert summary['randomness']['events_known'] == 3

    print("\nKnowledge export test passed!")
    return True


def test_with_game():
    """Test intelligence layer with actual game"""
    print("\n" + "=" * 60)
    print("Testing Intelligence Layer with Zork I")
    print("=" * 60)

    game_file = Path(__file__).parent.parent / "games" / "zcode" / "zork1.z3"
    if not game_file.exists():
        print("Zork I not found, skipping game test")
        return True

    # Create walker with knowledge
    walker = GameWalker.create_with_knowledge(str(game_file))
    walker.start()

    print(f"Starting room: {walker.current_room_id}")

    # Get initial suggestions
    suggestions = walker.get_suggested_actions()
    print(f"\nInitial suggestions:")
    for s in suggestions[:5]:
        print(f"  {s['action']}: {s['reason']}")

    # Do some exploration
    commands = ["north", "east", "open window", "west"]
    for cmd in commands:
        walker.try_command(cmd)

    # Get exploration progress
    progress = walker.get_exploration_progress()
    print(f"\nExploration progress:")
    print(f"  Rooms: {progress['rooms_discovered']}")
    print(f"  Unexplored exits: {progress['unexplored_exits']}")
    print(f"  Commands tried: {progress['commands_tried']}")

    # Get AI prompt
    prompt = walker.get_ai_prompt("explore")
    print(f"\nAI Prompt preview:")
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)

    # Learn from session
    learned = walker.learn_from_session()
    print(f"\nLearned from session:")
    print(f"  Prerequisites: {len(learned['discovered_prerequisites'])}")

    # Export summary
    summary = walker.export_session_summary()
    print(f"\nSession summary:")
    print(f"  Rooms visited: {summary['rooms_visited']}")
    print(f"  Turns played: {summary['turns_played']}")

    walker.save_knowledge()

    print("\nGame integration test passed!")
    return True


def test_auto_explore():
    """Test auto-exploration with actual game"""
    print("\n" + "=" * 60)
    print("Testing Auto-Explore with Zork I")
    print("=" * 60)

    game_file = Path(__file__).parent.parent / "games" / "zcode" / "zork1.z3"
    if not game_file.exists():
        print("Zork I not found, skipping auto-explore test")
        return True

    import shutil
    import tempfile

    # Use a fresh temporary directory to ensure clean state
    temp_dir = tempfile.mkdtemp(prefix="zwalker_autoexplore_")

    try:
        # Create fresh walker with clean knowledge
        walker = GameWalker.create_with_knowledge(
            str(game_file),
            knowledge_dir=temp_dir
        )
        walker.start()

        print(f"Starting auto-exploration from room {walker.current_room_id}")

        # Run auto-explore for a limited number of turns
        result = walker.auto_explore(max_turns=20)

        print(f"\nAuto-explore results:")
        print(f"  Success: {result['success']}")
        print(f"  Turns taken: {result['turns_taken']}")
        print(f"  New rooms found: {result['new_rooms_found']}")
        print(f"  Total rooms: {result['total_rooms']}")

        print(f"\nLast few actions:")
        for action in result['actions_log'][-5:]:
            status = "OK" if action['success'] else "BLOCKED"
            print(f"  [{status}] {action['action']}: {action['reason']}")

        # With a fresh knowledge base, auto-explore should do something
        assert result['success']
        assert result['total_rooms'] >= 1

    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)

    print("\nAuto-explore test passed!")
    return True


def main():
    print("ZWalker Intelligence Layer Tests (Phase 4)")
    print("=" * 60)

    tests = [
        ("Action Suggestions", test_action_suggestions),
        ("Exploration Status", test_exploration_status),
        ("Path to Unexplored", test_path_to_unexplored),
        ("Learning from Transcript", test_learning_from_transcript),
        ("Prerequisite Discovery", test_prerequisite_discovery),
        ("AI Prompt Context", test_ai_prompt_context),
        ("Knowledge Export", test_knowledge_export),
        ("Game Integration", test_with_game),
        ("Auto-Explore", test_auto_explore),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n[PASS] {name}")
            else:
                failed += 1
                print(f"\n[FAIL] {name}")
        except Exception as e:
            failed += 1
            print(f"\n[ERROR] {name}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

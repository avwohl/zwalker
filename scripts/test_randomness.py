#!/usr/bin/env python3
"""
Test script for Randomness Handling functionality.

Demonstrates:
1. Random event detection from game output
2. Run snapshots for variance detection
3. Cross-run comparison to identify random elements
4. Response handling for random events
5. Integration with GameWalker
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.knowledge import (
    KnowledgeBase, RandomEvent, RunSnapshot, VarianceRecord,
    RandomnessTracker, create_common_random_events
)
from zwalker.walker import GameWalker


def test_random_event_standalone():
    """Test random event detection without a game"""
    print("=" * 60)
    print("Testing Random Event Detection (standalone)")
    print("=" * 60)

    import tempfile
    temp_dir = tempfile.mkdtemp(prefix="zwalker_random_")
    kb = KnowledgeBase("/tmp/test_random_game.z5", knowledge_dir=temp_dir)
    kb.start_new_run()

    # Initialize common random events
    kb.init_common_random_events()
    print(f"Initialized {len(kb.randomness.events)} common random events")

    # Test detection patterns
    test_outputs = [
        ("Someone carrying a large bag is approaching!", "thief_encounter"),
        ("The thief appears from the shadows.", "thief_encounter"),
        ("It is pitch black. You are likely to be eaten by a grue.", "grue_warning"),
        ("The troll attacks you with his axe!", "combat_start"),
        ("You are in a forest clearing.", None),  # No random event
    ]

    print("\nTesting detection patterns:")
    for output, expected_event in test_outputs:
        event = kb.check_for_random_event(output, room_id=1)
        if event:
            print(f"  Detected: {event.id} - '{output[:40]}...'")
            if expected_event:
                assert event.id == expected_event, f"Expected {expected_event}, got {event.id}"
        else:
            print(f"  No event: '{output[:40]}...'")
            assert expected_event is None

    # Record some events
    kb.record_random_event(
        event_id="thief_encounter",
        room_id=10,
        turn=5,
        output="The thief appears from the shadows.",
        response_used=["drop valuables"],
    )
    print("\nRecorded thief encounter")

    # Check occurrences
    thief_event = kb.randomness.events["thief_encounter"]
    print(f"Thief occurrences: {len(thief_event.occurrences)}")
    assert len(thief_event.occurrences) == 1

    kb.save()
    print(f"\nSaved to: {kb.knowledge_dir}")

    # Reload and verify
    kb2 = KnowledgeBase("/tmp/test_random_game.z5", knowledge_dir=temp_dir)
    print(f"Reloaded: {len(kb2.randomness.events)} events")

    return True


def test_snapshot_and_variance():
    """Test run snapshots and variance detection"""
    print("\n" + "=" * 60)
    print("Testing Snapshots and Variance Detection")
    print("=" * 60)

    import tempfile
    temp_dir = tempfile.mkdtemp(prefix="zwalker_variance_")
    kb = KnowledgeBase("/tmp/test_variance_game.z5", knowledge_dir=temp_dir)

    # Simulate run 1
    kb.start_new_run()
    print(f"Run {kb.current_run}")

    kb.take_snapshot(
        room_id=1,
        room_name="West of House",
        object_locations={100: 1, 101: 5, 102: 10}  # lamp in room 1, sword in 5, etc.
    )
    kb.take_snapshot(
        room_id=5,
        room_name="Behind House",
        object_locations={100: 1, 101: 5, 102: 10}
    )

    # Simulate run 2 with different object locations
    kb.start_new_run()
    print(f"Run {kb.current_run}")

    kb.take_snapshot(
        room_id=1,
        room_name="West of House",
        object_locations={100: 1, 101: 7, 102: 10}  # sword moved to room 7!
    )
    kb.take_snapshot(
        room_id=5,
        room_name="Behind House",
        object_locations={100: 1, 101: 7, 102: 12}  # obj 102 also moved!
    )

    # Compare runs
    variances = kb.compare_runs(run1=1, run2=2)
    print(f"\nVariances detected: {len(variances)}")
    for v in variances:
        print(f"  - {v.variance_type}: object {v.subject_id}")

    # Check random objects
    random_objs = kb.get_random_objects()
    print(f"\nRandom objects: {random_objs}")
    assert 101 in random_objs, "Object 101 should be detected as random"
    assert 102 in random_objs, "Object 102 should be detected as random"

    # Check specific object
    assert kb.is_random_object(101), "Object 101 should be random"
    assert not kb.is_random_object(100), "Object 100 should not be random"

    kb.save()
    print(f"\nSaved to: {kb.knowledge_dir}")

    return True


def test_response_handling():
    """Test response handling for random events"""
    print("\n" + "=" * 60)
    print("Testing Random Event Response Handling")
    print("=" * 60)

    kb = KnowledgeBase("/tmp/test_response_game.z5", knowledge_dir="/tmp/zwalker_response_test")
    kb.start_new_run()
    kb.init_common_random_events()

    thief_event = kb.randomness.events["thief_encounter"]

    # Test response without sword
    response = kb.get_random_response(thief_event, inventory_names=["lamp", "key"])
    print(f"Response without sword: {response}")
    assert response == ["drop valuables", "wait", "wait", "take valuables"]

    # Test response with sword
    response = kb.get_random_response(thief_event, inventory_names=["sword", "lamp"])
    print(f"Response with sword: {response}")
    assert response == ["kill thief with sword"]

    # Test grue response without lamp
    grue_event = kb.randomness.events["grue_warning"]
    response = kb.get_random_response(grue_event, inventory_names=["key"])
    print(f"Grue response without lamp: {response}")
    assert response == ["go back"]

    # Test grue response with lamp
    response = kb.get_random_response(grue_event, inventory_names=["lamp"])
    print(f"Grue response with lamp: {response}")
    assert response == ["light lamp"]

    print("\nAll response tests passed!")
    return True


def test_custom_random_events():
    """Test adding custom random events"""
    print("\n" + "=" * 60)
    print("Testing Custom Random Events")
    print("=" * 60)

    kb = KnowledgeBase("/tmp/test_custom_game.z5", knowledge_dir="/tmp/zwalker_custom_test")
    kb.start_new_run()

    # Add a custom random event
    event = kb.add_custom_random_event(
        event_id="cyclops_encounter",
        name="Cyclops Encounter",
        event_type="wandering_npc",
        detection_pattern=r"cyclops|one-eyed giant",
        detection_rooms=[50, 51, 52]  # Only in certain rooms
    )
    event.add_response("has lunch", ["give lunch to cyclops"])
    event.add_response("default", ["flee", "run"])

    print(f"Added custom event: {event.name}")
    print(f"  Detection rooms: {event.detection_rooms}")
    print(f"  Responses: {list(event.responses.keys())}")

    # Test detection in valid room
    result = kb.check_for_random_event("A huge cyclops blocks your path!", room_id=50)
    assert result is not None
    print(f"  Detected in room 50: {result.id}")

    # Test no detection in invalid room
    result = kb.check_for_random_event("A huge cyclops blocks your path!", room_id=100)
    assert result is None
    print(f"  Not detected in room 100 (expected)")

    # Test response
    response = kb.get_random_response(event, inventory_names=["sword", "lunch"])
    print(f"  Response with lunch: {response}")
    assert response == ["give lunch to cyclops"]

    kb.save()
    return True


def test_stats():
    """Test randomness statistics"""
    print("\n" + "=" * 60)
    print("Testing Randomness Statistics")
    print("=" * 60)

    kb = KnowledgeBase("/tmp/test_stats_game.z5", knowledge_dir="/tmp/zwalker_stats_test")
    kb.start_new_run()
    kb.init_common_random_events()

    # Record some events
    kb.record_random_event("thief_encounter", 10, 5, "Thief appears!")
    kb.record_random_event("thief_encounter", 15, 10, "Thief again!")
    kb.record_random_event("grue_warning", 20, 15, "Grue warning!")

    # Add some variance
    kb.take_snapshot(1, "Room A", {100: 1, 101: 2})
    kb.start_new_run()
    kb.take_snapshot(1, "Room A", {100: 1, 101: 5})  # 101 moved
    kb.compare_runs(1, 2)

    stats = kb.get_stats()
    print(f"Knowledge base stats:")
    print(f"  random_events_known: {stats['random_events_known']}")
    print(f"  random_events_observed: {stats['random_events_observed']}")
    print(f"  variance_records: {stats['variance_records']}")
    print(f"  random_objects: {stats['random_objects']}")

    assert stats['random_events_known'] == 3  # thief, grue, combat
    assert stats['random_events_observed'] == 3  # 2 thief + 1 grue
    assert stats['variance_records'] == 1  # object 101
    assert stats['random_objects'] == 1

    return True


def test_with_game():
    """Test randomness tracking with actual game"""
    print("\n" + "=" * 60)
    print("Testing Randomness with Zork I")
    print("=" * 60)

    game_file = Path(__file__).parent.parent / "games" / "zcode" / "zork1.z3"
    if not game_file.exists():
        print("Zork I not found, skipping game test")
        return True

    # Create walker with knowledge
    walker = GameWalker.create_with_knowledge(str(game_file))
    walker.start()

    print(f"Starting room: {walker.current_room_id}")
    print(f"Random events initialized: {len(walker.kb.randomness.events)}")

    # Take initial snapshot
    snapshot = walker.take_snapshot()
    print(f"Initial snapshot taken: room {snapshot['room_id']}")

    # Explore a bit
    commands = ["north", "east", "open window", "west"]
    for cmd in commands:
        result = walker.try_command(cmd)
        status = "success" if not result.blocked else "blocked"
        random_event = f" [RANDOM: {result.random_event}]" if result.random_event else ""
        print(f"  {cmd}: {status}{random_event}")

    # Check stats
    stats = walker.get_knowledge_stats()
    print(f"\nRandomness tracking stats:")
    print(f"  Events known: {stats['random_events_known']}")
    print(f"  Events observed: {stats['random_events_observed']}")

    # Save and check
    walker.save_knowledge()

    return True


def main():
    print("ZWalker Randomness Handling Tests")
    print("=" * 60)

    tests = [
        ("Random Event Detection", test_random_event_standalone),
        ("Snapshots and Variance", test_snapshot_and_variance),
        ("Response Handling", test_response_handling),
        ("Custom Random Events", test_custom_random_events),
        ("Statistics", test_stats),
        ("Game Integration", test_with_game),
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

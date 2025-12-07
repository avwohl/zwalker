#!/usr/bin/env python3
"""
Test script for Puzzle and Solution functionality.

Demonstrates:
1. Puzzle detection from blocked actions
2. Adding clues to puzzles
3. Building solutions from transcripts
4. Solution execution with branches
5. Prerequisites checking
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.knowledge import (
    KnowledgeBase, Puzzle, PuzzleTracker, PuzzleStatus,
    Solution, SolutionStep, SolutionBranch, Prerequisites,
    SolutionExecutor
)
from zwalker.walker import GameWalker


def test_puzzle_standalone():
    """Test puzzle creation and tracking without a game"""
    print("=" * 60)
    print("Testing Puzzle Tracking (standalone)")
    print("=" * 60)

    kb = KnowledgeBase("/tmp/test_puzzle_game.z5", knowledge_dir="/tmp/zwalker_puzzle_test")
    kb.start_new_run()

    # Create puzzles
    puzzle1 = kb.add_puzzle(
        name="Locked Grate",
        description="A grate blocks the way down",
        room_id=10,
        puzzle_type="locked_door"
    )
    print(f"Created puzzle: {puzzle1.name} ({puzzle1.id})")

    puzzle2 = kb.add_puzzle(
        name="Dark Cellar",
        description="It's too dark to see",
        room_id=20,
        puzzle_type="darkness"
    )
    print(f"Created puzzle: {puzzle2.name} ({puzzle2.id})")

    # Add clues
    kb.add_clue_to_puzzle(puzzle1.id, "The grate has a keyhole", "room_desc", "high")
    kb.add_clue_to_puzzle(puzzle1.id, "A rusty key is nearby", "object_examine", "high")
    print(f"Added 2 clues to {puzzle1.name}")

    # Record attempts
    kb.record_puzzle_attempt(
        puzzle1.id,
        commands=["open grate", "pull grate"],
        result="The grate won't budge",
        success=False
    )
    print(f"Recorded failed attempt on {puzzle1.name}")

    # Mark solved
    kb.mark_puzzle_solved(puzzle1.id, ["unlock grate with key", "open grate"])
    print(f"Marked {puzzle1.name} as solved")

    # Check status
    unsolved = kb.puzzles.get_unsolved_puzzles()
    print(f"\nUnsolved puzzles: {len(unsolved)}")
    for p in unsolved:
        print(f"  - {p.name}: {p.status}")

    solved = [p for p in kb.puzzles.puzzles.values() if p.status == PuzzleStatus.SOLVED.value]
    print(f"Solved puzzles: {len(solved)}")
    for p in solved:
        print(f"  - {p.name}: {p.solution_commands}")

    kb.save()
    print(f"\nSaved to: {kb.knowledge_dir}")

    # Reload and verify
    kb2 = KnowledgeBase("/tmp/test_puzzle_game.z5", knowledge_dir="/tmp/zwalker_puzzle_test")
    print(f"Reloaded: {len(kb2.puzzles.puzzles)} puzzles")

    return True


def test_solution_standalone():
    """Test solution creation and execution without a game"""
    print("\n" + "=" * 60)
    print("Testing Solution Building (standalone)")
    print("=" * 60)

    kb = KnowledgeBase("/tmp/test_solution_game.z5", knowledge_dir="/tmp/zwalker_solution_test")
    kb.start_new_run()

    # Build a solution manually
    kb.add_solution_step("north", room_id=1, success_indicators=["North of House"])
    kb.add_solution_step("take lamp", room_id=2, success_indicators=["Taken"])
    kb.add_solution_step("light lamp", room_id=2, success_indicators=["lamp is now lit"])
    kb.add_solution_step("down", room_id=2, success_indicators=["Cellar"])

    print(f"Created solution with {len(kb.solution.main_steps)} steps:")
    for step in kb.solution.main_steps:
        print(f"  {step.id}: {step.command}")

    # Add a branch for random event
    branch = kb.add_solution_branch(
        branch_id="handle_thief",
        name="Thief Encounter",
        trigger_pattern="thief|Someone carrying a large bag"
    )
    branch.steps.append(SolutionStep(
        id="thief_001",
        command="kill thief with sword"
    ))
    branch.rejoin_at = "step_004"  # Continue after dealing with thief
    print(f"\nAdded branch: {branch.name}")

    # Test prerequisites
    prereq = Prerequisites(
        in_room=2,
        has_item_names=["lamp"],
        state_flags={"lamp_lit": True}
    )

    # Check prerequisites (should fail - no lamp, not in room 2)
    ok, reason = prereq.check(
        current_room=1,
        inventory=[],
        inventory_names=[],
        solved_puzzles=[],
        flags={}
    )
    print(f"\nPrerequisites check (should fail): {ok}, reason: {reason}")

    # Check with correct state
    ok, reason = prereq.check(
        current_room=2,
        inventory=[100],
        inventory_names=["lamp"],
        solved_puzzles=[],
        flags={"lamp_lit": True}
    )
    print(f"Prerequisites check (should pass): {ok}")

    # Validate solution
    executor = SolutionExecutor(kb)
    issues = executor.validate_solution()
    if issues:
        print(f"\nSolution validation issues: {issues}")
    else:
        print("\nSolution validated successfully")

    kb.save()
    print(f"Saved to: {kb.knowledge_dir}")

    # Reload and verify
    kb2 = KnowledgeBase("/tmp/test_solution_game.z5", knowledge_dir="/tmp/zwalker_solution_test")
    print(f"Reloaded: {len(kb2.solution.main_steps)} steps, {len(kb2.solution.branches)} branches")

    return True


def test_puzzle_detection():
    """Test automatic puzzle detection from game output"""
    print("\n" + "=" * 60)
    print("Testing Puzzle Detection Heuristics")
    print("=" * 60)

    kb = KnowledgeBase("/tmp/test_detect_game.z5", knowledge_dir="/tmp/zwalker_detect_test")
    kb.start_new_run()

    # Test various outputs that should trigger puzzle detection
    test_cases = [
        ("The door is locked.", "locked_door"),
        ("It's too dark to see. You might fall into a pit.", "darkness"),
        ("A troll blocks your way, waving a large axe.", "combat"),
        ("You push the button, but nothing happens. Maybe there's a sequence.", "sequence"),
        ("The window won't open - it seems stuck.", None),  # Not a puzzle
    ]

    for output, expected_type in test_cases:
        puzzle = kb.detect_puzzle(room_id=1, output=output, command="test")
        if puzzle:
            print(f"  Detected: {puzzle.puzzle_type} - '{output[:40]}...'")
            assert expected_type is None or puzzle.puzzle_type == expected_type
        else:
            print(f"  No puzzle: '{output[:40]}...'")
            assert expected_type is None

    print(f"\nTotal puzzles detected: {len(kb.puzzles.puzzles)}")
    return True


def test_with_game():
    """Test puzzle and solution with actual game"""
    print("\n" + "=" * 60)
    print("Testing with Zork I")
    print("=" * 60)

    game_file = Path(__file__).parent.parent / "games" / "zcode" / "zork1.z3"
    if not game_file.exists():
        print("Zork I not found, skipping game test")
        return True

    # Create walker with knowledge
    walker = GameWalker.create_with_knowledge(str(game_file))
    walker.start()

    print(f"Starting room: {walker.current_room_id}")

    # Explore a bit
    commands = ["north", "east", "open window", "west", "down"]
    for cmd in commands:
        result = walker.try_command(cmd)
        status = "success" if not result.blocked else "blocked"
        print(f"  {cmd}: {status}")

    # Check for detected puzzles
    puzzles = walker.kb.puzzles.puzzles
    print(f"\nPuzzles detected: {len(puzzles)}")
    for pid, puzzle in puzzles.items():
        print(f"  - {puzzle.name} ({puzzle.puzzle_type})")

    # Build solution from what we've done
    result = walker.build_solution()
    print(f"\nBuilt solution with {result['total_steps']} steps")

    # Save and show stats
    walker.save_knowledge()
    stats = walker.kb.get_stats()
    print(f"\nKnowledge Base Stats:")
    print(f"  Rooms: {stats['rooms_discovered']}")
    print(f"  Puzzles: {stats['puzzles_discovered']}")
    print(f"  Solution steps: {stats['solution_steps']}")

    return True


def main():
    print("ZWalker Puzzle and Solution Tests")
    print("=" * 60)

    tests = [
        ("Puzzle Tracking", test_puzzle_standalone),
        ("Solution Building", test_solution_standalone),
        ("Puzzle Detection", test_puzzle_detection),
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

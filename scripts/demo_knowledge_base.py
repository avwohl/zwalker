#!/usr/bin/env python3
"""
Comprehensive demonstration of the ZWalker Knowledge Base system.

This script demonstrates all major features:
1. Persistent knowledge across runs
2. Automatic puzzle detection
3. Random event handling
4. AI-powered suggestions
5. Solution building and replay
6. Cross-run learning
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.walker import GameWalker
from zwalker.knowledge import KnowledgeBase


def section(title):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}\n")


def demo_basic_exploration():
    """Demonstrate basic exploration with knowledge persistence."""
    section("PART 1: Basic Exploration with Knowledge Persistence")

    game_file = Path(__file__).parent.parent / "games" / "zcode" / "zork1.z3"

    print("Creating walker with knowledge base...")
    walker = GameWalker.create_with_knowledge(str(game_file))

    print(f"Game: {walker.kb.game_name}")
    print(f"Previous runs: {walker.kb.world_map.total_runs}")

    # Start game
    output = walker.start()
    print(f"\nStarting room: {walker.current_room_id}")
    print(f"Room name: {walker.rooms[walker.current_room_id].name}")

    # Explore the opening area
    print("\n--- Exploring the opening area ---")
    commands = [
        "look",
        "open mailbox",
        "take leaflet",
        "read leaflet",
        "north",
        "east",
        "open window",
        "west",  # Enter house through window
    ]

    for cmd in commands:
        print(f"\n> {cmd}")
        result = walker.try_command(cmd)

        # Show abbreviated output
        output_lines = result.output.strip().split('\n')
        for line in output_lines[:4]:
            print(f"  {line}")
        if len(output_lines) > 4:
            print(f"  ...")

        if result.blocked:
            print(f"  [BLOCKED]")
        elif result.new_room:
            print(f"  [NEW ROOM: {walker.current_room_id}]")
        elif result.took_object:
            print(f"  [TOOK OBJECT]")

    # Show what we learned
    print("\n--- Knowledge Acquired ---")
    stats = walker.get_knowledge_stats()
    print(f"Rooms discovered: {stats['rooms_discovered']}")
    print(f"Objects found: {stats['objects_discovered']}")
    print(f"Commands tried: {stats['total_actions']}")
    print(f"Do-not-retry commands: {stats['do_not_retry_count']}")

    walker.save_knowledge()
    print(f"\nKnowledge saved. Run: {walker.kb.current_run}")

    return walker


def demo_knowledge_persistence(walker):
    """Demonstrate that knowledge persists across runs."""
    section("PART 2: Knowledge Persistence Across Runs")

    game_file = Path(__file__).parent.parent / "games" / "zcode" / "zork1.z3"

    print("Creating NEW walker instance (simulating restart)...")
    walker2 = GameWalker.create_with_knowledge(str(game_file))
    walker2.start()

    print(f"Previous runs loaded: {walker2.kb.world_map.total_runs}")
    print(f"Rooms already known: {len(walker2.kb.world_map.rooms)}")

    # Show known rooms
    print("\n--- Previously Discovered Rooms ---")
    for room_id, room in walker2.kb.world_map.rooms.items():
        exits = ", ".join(room.exits.keys())
        print(f"  [{room_id}] {room.name} -> {exits}")

    # Try a command that was previously blocked
    print("\n--- Testing Do-Not-Retry ---")
    blocked_cmds = walker2.kb.actions.do_not_retry
    if blocked_cmds:
        for dnr in blocked_cmds[:3]:
            print(f"  Will skip: '{dnr.command}' in room {dnr.room_id} ({dnr.reason})")

    return walker2


def demo_ai_suggestions(walker):
    """Demonstrate AI-powered suggestions."""
    section("PART 3: AI-Powered Suggestions")

    # Navigate to kitchen if possible
    print("Navigating to explore more...")
    walker.try_command("north")
    walker.try_command("east")
    walker.try_command("open window")
    walker.try_command("west")

    print(f"\nCurrent room: {walker.current_room_id}")

    # Get suggestions
    suggestions = walker.get_suggested_actions()
    print("\n--- Knowledge-Based Suggestions ---")
    for s in suggestions[:8]:
        print(f"  [{s['priority']}] {s['type']:12s} | {s['action']:20s} | {s['reason']}")

    # Get AI prompt context
    print("\n--- AI Prompt Context ---")
    prompt = walker.get_ai_prompt(task="explore")
    # Show first part
    lines = prompt.split('\n')
    for line in lines[:25]:
        print(f"  {line}")
    if len(lines) > 25:
        print(f"  ... ({len(lines) - 25} more lines)")

    return walker


def demo_deeper_exploration(walker):
    """Explore deeper into the game."""
    section("PART 4: Deeper Exploration")

    # If we're in the kitchen, explore more
    print("Continuing exploration...")

    explore_commands = [
        "look",
        "take all",
        "inventory",
        "west",
        "take lamp",
        "turn on lamp",
        "down",  # To cellar
        "north",
        "east",
        "south",
    ]

    for cmd in explore_commands:
        result = walker.try_command(cmd)
        status = "OK" if not result.blocked else "BLOCKED"
        room_change = f" -> room {walker.current_room_id}" if result.new_room else ""

        # Check for random events
        random = f" [RANDOM: {result.random_event}]" if result.random_event else ""

        print(f"  [{status}] {cmd:20s}{room_change}{random}")

        if result.random_event:
            # Handle random event
            responses = walker.handle_random_event(result.random_event)
            for r in responses:
                print(f"       Response: {r.command}")

    # Show exploration progress
    progress = walker.get_exploration_progress()
    print(f"\n--- Exploration Progress ---")
    print(f"Rooms discovered: {progress['rooms_discovered']}")
    print(f"Unexplored exits: {progress['unexplored_exits']}")
    print(f"Blocked exits: {progress['blocked_exits']}")
    print(f"Objects found: {progress['objects_found']}")

    walker.save_knowledge()
    return walker


def demo_puzzle_detection(walker):
    """Show automatic puzzle detection."""
    section("PART 5: Automatic Puzzle Detection")

    puzzles = walker.kb.puzzles.puzzles
    print(f"Puzzles detected: {len(puzzles)}")

    for pid, puzzle in puzzles.items():
        print(f"\n  Puzzle: {puzzle.name}")
        print(f"    Type: {puzzle.puzzle_type}")
        print(f"    Room: {puzzle.room_id}")
        print(f"    Status: {puzzle.status}")
        if puzzle.clues:
            print(f"    Clues:")
            for clue in puzzle.clues[:3]:
                print(f"      - {clue.text[:60]}...")

    return walker


def demo_solution_building(walker):
    """Demonstrate solution building and export."""
    section("PART 6: Solution Building")

    # Build solution from transcript
    result = walker.build_solution()

    print(f"Solution built with {result['total_steps']} steps")
    print(f"Completeness: {walker.kb.solution.completeness}")

    # Show first few steps
    print("\n--- Solution Steps (first 15) ---")
    for i, step in enumerate(walker.kb.solution.main_steps[:15], 1):
        room_info = f" (room {step.prerequisites.in_room})" if step.prerequisites.in_room else ""
        print(f"  {i:2d}. {step.command}{room_info}")

    if len(walker.kb.solution.main_steps) > 15:
        print(f"  ... ({len(walker.kb.solution.main_steps) - 15} more steps)")

    return walker


def demo_learning(walker):
    """Demonstrate pattern learning."""
    section("PART 7: Learning from Experience")

    # Learn from transcript
    learned = walker.learn_from_session()

    print("--- Learned Prerequisites ---")
    prereqs = learned['learned_patterns']['new_prerequisites']
    if prereqs:
        for p in prereqs[:5]:
            print(f"  '{p['for_command']}' may require '{p['prerequisite']}' in room {p['room']}")
    else:
        print("  (none detected yet)")

    print("\n--- Discovered Prerequisites ---")
    discovered = learned['discovered_prerequisites']
    if discovered:
        for d in discovered[:5]:
            print(f"  '{d['command']}' requires: {d['required_commands']}")
    else:
        print("  (need more runs to discover patterns)")

    # Show confirmed patterns
    patterns = learned['learned_patterns']['confirmed_patterns']
    if patterns:
        print("\n--- Confirmed Patterns ---")
        for p in patterns[:5]:
            print(f"  '{p['command']}': requires items {p['required_items']}")

    return walker


def demo_randomness_tracking(walker):
    """Demonstrate randomness tracking."""
    section("PART 8: Randomness Tracking")

    print("--- Known Random Events ---")
    for eid, event in walker.kb.randomness.events.items():
        occurrences = len(event.occurrences)
        print(f"  {event.name}: {occurrences} occurrences")
        if event.responses:
            for condition, cmds in list(event.responses.items())[:2]:
                print(f"    Response ({condition}): {cmds}")

    print("\n--- Variance Records ---")
    if walker.kb.randomness.variances:
        for vid, variance in walker.kb.randomness.variances.items():
            print(f"  {variance.variance_type}: object {variance.subject_id}")
    else:
        print("  (none detected - need multiple runs)")

    # Take a snapshot for future comparison
    walker.take_snapshot()
    print("\n  Snapshot taken for future variance detection")

    return walker


def demo_final_stats(walker):
    """Show final statistics."""
    section("FINAL STATISTICS")

    stats = walker.get_knowledge_stats()
    summary = walker.kb.export_knowledge_summary()

    print(f"Game: {stats['game_name']}")
    print(f"Total runs: {stats['total_runs']}")
    print(f"Current run: {stats['current_run']}")

    print(f"\n--- World ---")
    print(f"  Rooms: {stats['rooms_discovered']}")
    print(f"  Objects: {stats['objects_discovered']}")

    print(f"\n--- Actions ---")
    print(f"  Total attempts: {stats['total_actions']}")
    print(f"  Do-not-retry: {stats['do_not_retry_count']}")
    print(f"  Death commands: {stats['death_records']}")

    print(f"\n--- Puzzles ---")
    print(f"  Discovered: {stats['puzzles_discovered']}")
    print(f"  Solved: {stats['puzzles_solved']}")

    print(f"\n--- Solution ---")
    print(f"  Steps: {stats['solution_steps']}")
    print(f"  Branches: {stats['solution_branches']}")

    print(f"\n--- Randomness ---")
    print(f"  Events known: {stats['random_events_known']}")
    print(f"  Events observed: {stats['random_events_observed']}")

    walker.save_knowledge()
    print(f"\nKnowledge saved to: {walker.kb.knowledge_dir}")


def main():
    print("=" * 70)
    print(" ZWalker Knowledge Base - Comprehensive Demonstration")
    print("=" * 70)

    game_file = Path(__file__).parent.parent / "games" / "zcode" / "zork1.z3"
    if not game_file.exists():
        print(f"Error: Zork I not found at {game_file}")
        return 1

    try:
        # Run all demonstrations
        walker = demo_basic_exploration()
        walker = demo_knowledge_persistence(walker)
        walker = demo_ai_suggestions(walker)
        walker = demo_deeper_exploration(walker)
        walker = demo_puzzle_detection(walker)
        walker = demo_solution_building(walker)
        walker = demo_learning(walker)
        walker = demo_randomness_tracking(walker)
        demo_final_stats(walker)

        print("\n" + "=" * 70)
        print(" Demonstration Complete!")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

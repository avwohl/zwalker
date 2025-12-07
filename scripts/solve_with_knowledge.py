#!/usr/bin/env python3
"""
Enhanced game solver with persistent knowledge base.

This solver uses the KnowledgeBase to:
- Persist knowledge across multiple runs
- Skip commands that previously failed
- Detect and track puzzles automatically
- Handle random events (thief, grue, etc.)
- Build proper replayable solutions
- Use AI-powered suggestions based on accumulated knowledge

Usage:
    python solve_with_knowledge.py <game.z5> [--real-ai] [--max-turns 100]
    python solve_with_knowledge.py <game.z5> --auto-explore
    python solve_with_knowledge.py <game.z5> --status
"""

import sys
import json
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.walker import GameWalker
from zwalker.knowledge import KnowledgeBase, SolutionExecutor


def show_status(game_path: str):
    """Show current knowledge base status for a game."""
    kb = KnowledgeBase(game_path)

    print(f"Knowledge Base Status: {kb.game_name}")
    print("=" * 60)

    stats = kb.get_stats()
    summary = kb.export_knowledge_summary()

    print(f"\nWorld Knowledge:")
    print(f"  Total runs: {stats['total_runs']}")
    print(f"  Rooms discovered: {stats['rooms_discovered']}")
    print(f"  Objects found: {stats['objects_discovered']}")

    print(f"\nAction History:")
    print(f"  Commands tried: {stats['total_actions']}")
    print(f"  Do-not-retry: {stats['do_not_retry_count']}")
    print(f"  Death commands: {stats['death_records']}")

    print(f"\nPuzzles:")
    print(f"  Discovered: {stats['puzzles_discovered']}")
    print(f"  Solved: {stats['puzzles_solved']}")

    print(f"\nSolution:")
    print(f"  Steps: {stats['solution_steps']}")
    print(f"  Branches: {stats['solution_branches']}")

    print(f"\nRandomness:")
    print(f"  Events known: {stats['random_events_known']}")
    print(f"  Events observed: {stats['random_events_observed']}")
    print(f"  Random objects: {stats['random_objects']}")

    # Show exploration status
    exploration = kb.get_exploration_status()
    print(f"\nExploration Status:")
    print(f"  Unexplored exits: {exploration['unexplored_exits']}")
    print(f"  Blocked exits: {exploration['blocked_exits']}")

    if exploration['unexplored_details']:
        print(f"  Unexplored locations:")
        for room_id, direction in exploration['unexplored_details'][:10]:
            room = kb.get_room(room_id)
            name = room.name if room else f"Room {room_id}"
            print(f"    - {name}: {direction}")


def auto_explore(game_path: str, max_turns: int = 100):
    """Auto-explore the game using knowledge-based suggestions."""
    print(f"Auto-exploring: {game_path}")
    print("=" * 60)

    walker = GameWalker.create_with_knowledge(game_path)
    output = walker.start()

    print(f"Starting room: {walker.current_room_id}")
    print(f"Previous knowledge: {walker.kb.world_map.total_runs} runs")
    print()

    # Run auto-exploration
    result = walker.auto_explore(max_turns=max_turns)

    print(f"\nAuto-Explore Results:")
    print(f"  Success: {result['success']}")
    print(f"  Turns taken: {result['turns_taken']}")
    print(f"  New rooms found: {result['new_rooms_found']}")
    print(f"  Total rooms: {result['total_rooms']}")

    # Show action log
    print(f"\nAction Log (last 20):")
    for action in result['actions_log']:
        status = "OK" if action['success'] else "BLOCKED"
        room_info = " -> NEW ROOM" if action.get('new_room') else ""
        print(f"  [{status}] {action['action']}: {action['reason']}{room_info}")

    # Build and save solution
    solution_result = walker.build_solution()
    print(f"\nSolution built with {solution_result['total_steps']} steps")

    walker.save_knowledge()
    print(f"\nKnowledge saved to: {walker.kb.knowledge_dir}")

    return result


def solve_with_ai(game_path: str, max_iterations: int = 50, use_real_ai: bool = False):
    """Solve game with AI assistance and knowledge base."""
    print(f"Solving with knowledge: {game_path}")
    print("=" * 60)

    # Create walker with knowledge base
    walker = GameWalker.create_with_knowledge(game_path)

    # Start game
    output = walker.start()
    print(f"Starting room: {walker.current_room_id}")
    print(f"Previous knowledge: {walker.kb.world_map.total_runs} runs")

    # Get exploration status
    exploration = walker.get_exploration_progress()
    print(f"Rooms known: {exploration['rooms_discovered']}")
    print(f"Unexplored exits: {exploration['unexplored_exits']}")
    print()

    # Initialize AI if using real AI
    ai = None
    if use_real_ai:
        try:
            from zwalker.ai_assist import AIAssistant, create_context_from_walker
            ai = AIAssistant(backend='anthropic')
            print("Using Anthropic Claude for AI assistance")
        except ImportError:
            print("AI assistant not available, using knowledge-based suggestions")

    # Track solution
    rooms_visited = set()
    successful_commands = []

    for iteration in range(max_iterations):
        print(f"\n{'='*60}")
        print(f"ITERATION {iteration + 1}")
        print(f"{'='*60}")

        room_id = walker.current_room_id
        rooms_visited.add(room_id)

        # Show current state
        room = walker.kb.get_room(room_id)
        if room:
            print(f"Room: {room.name} (ID: {room_id})")

        inventory = walker.kb.get_inventory()
        print(f"Inventory: {', '.join(o.name for o in inventory) if inventory else 'empty'}")

        # Check for random events in recent output
        if walker.full_transcript:
            last_output = walker.full_transcript[-1][1]
            event = walker.kb.check_for_random_event(last_output, room_id)
            if event:
                print(f"\n⚠️  Random event detected: {event.name}")
                responses = walker.handle_random_event(event.id)
                for r in responses:
                    print(f"  Response: {r.command} -> {'OK' if not r.blocked else 'BLOCKED'}")
                continue

        # Get suggestions from knowledge base
        suggestions = walker.get_suggested_actions()

        if suggestions:
            print(f"\nKnowledge-based suggestions:")
            for s in suggestions[:5]:
                print(f"  [{s['priority']}] {s['action']}: {s['reason']}")

        # If using real AI, get AI suggestions too
        if ai:
            from zwalker.ai_assist import create_context_from_walker
            context = create_context_from_walker(walker)
            response = ai.analyze(context)
            print(f"\nAI suggestions: {response.suggested_commands[:5]}")

        # Try commands in priority order
        command_worked = False

        # First try knowledge-based suggestions
        for suggestion in suggestions[:5]:
            cmd = suggestion['action']

            # Skip meta-actions
            if cmd.startswith('['):
                continue

            print(f"\n> {cmd}")
            result = walker.try_command(cmd)

            output_preview = result.output[:200] + "..." if len(result.output) > 200 else result.output
            print(output_preview)

            if result.new_room:
                print(f"✓ Moved to new room!")
                successful_commands.append(cmd)
                command_worked = True
                break
            elif result.interesting or result.took_object:
                print(f"✓ Something happened!")
                successful_commands.append(cmd)
                command_worked = True
            elif result.random_event:
                print(f"⚠️  Random event: {result.random_event}")

        if not command_worked and not suggestions:
            print("No more suggestions, exploration may be complete.")

            # Check if there are unexplored areas
            exploration = walker.get_exploration_progress()
            if exploration['unexplored_exits'] == 0:
                print("All exits explored!")
                break
            else:
                # Try to navigate to unexplored area
                nav_result = walker.navigate_to_unexplored()
                if nav_result['success']:
                    print(f"Navigated to unexplored area")
                else:
                    print(f"Cannot reach unexplored areas: {nav_result.get('error')}")
                    break

        # Check for game end
        if walker.full_transcript:
            last_output = walker.full_transcript[-1][1].lower()
            if any(marker in last_output for marker in
                   ['you have died', 'you have won', '*** you have', 'congratulations']):
                print(f"\n🎉 GAME ENDED!")
                break

    # Results
    print(f"\n{'='*60}")
    print("SOLUTION SUMMARY")
    print(f"{'='*60}")

    final_stats = walker.get_knowledge_stats()
    print(f"Rooms discovered: {final_stats['rooms_discovered']}")
    print(f"Commands in solution: {len(successful_commands)}")
    print(f"Puzzles found: {final_stats['puzzles_discovered']}")
    print(f"Puzzles solved: {final_stats['puzzles_solved']}")

    # Learn from session
    learned = walker.learn_from_session()
    if learned['learned_patterns']['new_prerequisites']:
        print(f"\nLearned prerequisites:")
        for p in learned['learned_patterns']['new_prerequisites'][:5]:
            print(f"  {p['for_command']} requires {p['prerequisite']}")

    # Build and save solution
    solution_result = walker.build_solution()
    print(f"\nSolution steps: {solution_result['total_steps']}")

    walker.save_knowledge()
    print(f"\nKnowledge saved to: {walker.kb.knowledge_dir}")

    # Export solution
    game_name = Path(game_path).stem
    solution_file = f"{game_name}_solution.json"

    export = {
        'game': str(game_path),
        'rooms_visited': list(rooms_visited),
        'successful_commands': successful_commands,
        'solution': solution_result['solution'],
        'stats': final_stats,
        'learned': learned,
    }

    Path(solution_file).write_text(json.dumps(export, indent=2))
    print(f"Solution exported to: {solution_file}")

    return export


def replay_solution(game_path: str):
    """Replay the saved solution for a game."""
    print(f"Replaying solution: {game_path}")
    print("=" * 60)

    walker = GameWalker.create_with_knowledge(game_path)

    if not walker.kb.solution.main_steps:
        print("No solution saved for this game.")
        return

    print(f"Solution has {len(walker.kb.solution.main_steps)} steps")

    # Execute solution
    result = walker.execute_solution(max_steps=500)

    print(f"\nReplay Results:")
    print(f"  Success: {result['success']}")
    print(f"  Steps executed: {result['steps_executed']}")

    if result['progress']['failed_steps']:
        print(f"  Failed steps: {result['progress']['failed_steps']}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Solve Z-machine games with persistent knowledge base'
    )
    parser.add_argument('game', help='Path to Z-machine game file (.z3, .z5, .z8)')
    parser.add_argument('--status', action='store_true',
                        help='Show knowledge base status')
    parser.add_argument('--auto-explore', action='store_true',
                        help='Auto-explore using knowledge-based suggestions')
    parser.add_argument('--replay', action='store_true',
                        help='Replay saved solution')
    parser.add_argument('--real-ai', action='store_true',
                        help='Use Anthropic Claude for AI assistance')
    parser.add_argument('--max-turns', type=int, default=100,
                        help='Maximum turns for exploration (default: 100)')

    args = parser.parse_args()

    if not Path(args.game).exists():
        print(f"Error: Game file not found: {args.game}")
        sys.exit(1)

    if args.status:
        show_status(args.game)
    elif args.auto_explore:
        auto_explore(args.game, max_turns=args.max_turns)
    elif args.replay:
        replay_solution(args.game)
    else:
        solve_with_ai(args.game, max_iterations=args.max_turns, use_real_ai=args.real_ai)


if __name__ == '__main__':
    main()

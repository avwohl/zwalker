#!/usr/bin/env python3
"""
Quick test script to solve a game with AI assistance
"""

import sys
import json
from pathlib import Path
from zwalker.zmachine import ZMachine
from zwalker.walker import GameWalker
from zwalker.ai_assist import AIAssistant, create_context_from_walker


def solve_game(game_path, max_iterations=50, use_real_ai=False):
    """
    Attempt to solve a game using AI assistance.

    Args:
        game_path: Path to .z file
        max_iterations: Maximum number of AI iterations
        use_real_ai: If True, use Anthropic Claude. If False, use local heuristics.
    """
    print(f"Loading {game_path}...")
    game_data = Path(game_path).read_bytes()

    walker = GameWalker(game_data)

    # Start game
    output = walker.start()
    print("=" * 60)
    print("GAME START")
    print("=" * 60)
    print(output)
    print()

    # Initialize AI
    if use_real_ai:
        print("Using Anthropic Claude for AI assistance...")
        ai = AIAssistant(backend='anthropic')
    else:
        print("Using local heuristics (no API needed)...")
        ai = AIAssistant(backend='local')

    # Track solution
    solution_commands = []
    rooms_visited = set()

    # Solve iteratively
    for iteration in range(max_iterations):
        print(f"\n{'='*60}")
        print(f"ITERATION {iteration + 1}")
        print(f"{'='*60}")

        # Get current context
        context = create_context_from_walker(walker)
        print(f"Room: {context.room_name} (ID: {context.room_id})")
        print(f"Inventory: {', '.join(context.inventory) if context.inventory else 'empty'}")
        print(f"Exits: {', '.join(context.exits.keys()) if context.exits else 'none'}")
        print(f"Objects: {', '.join(context.visible_objects) if context.visible_objects else 'none'}")

        rooms_visited.add(context.room_id)

        # Check for game over/completion
        recent_output = context.recent_outputs[-1] if context.recent_outputs else ""
        if any(marker in recent_output.lower() for marker in
               ['you have died', 'you have won', 'the end', '*** you have', 'congratulations']):
            print(f"\n🎉 GAME COMPLETE! Ending detected.")
            break

        # Get AI analysis
        print(f"\nAI analyzing...")
        response = ai.analyze(context)
        print(f"Priority: {response.exploration_priority}")
        if response.possible_puzzles:
            print(f"Puzzles detected: {response.possible_puzzles}")
        print(f"Suggested commands: {response.suggested_commands[:10]}")

        # Try suggested commands
        command_tried = False
        for cmd in response.suggested_commands[:5]:
            print(f"\n> {cmd}")
            result = walker.try_command(cmd)

            output_text = result.output
            print(output_text[:300] + ("..." if len(output_text) > 300 else ""))

            # Track successful command
            if result.new_room or result.interesting or result.took_object:
                solution_commands.append({
                    'command': cmd,
                    'from_room': context.room_id,
                    'to_room': walker.current_room_id,
                    'result': 'moved' if result.new_room else 'interesting'
                })
                command_tried = True

                if result.new_room:
                    print(f"✓ Moved to new room!")
                    break
                elif result.interesting:
                    print(f"✓ Something interesting happened!")

        if not command_tried:
            # Try basic exploration
            print(f"\nNo interesting AI suggestions. Trying basic directions...")
            for direction in ['north', 'south', 'east', 'west', 'up', 'down']:
                result = walker.try_command(direction)
                if result.new_room:
                    solution_commands.append({
                        'command': direction,
                        'from_room': context.room_id,
                        'to_room': walker.current_room_id
                    })
                    print(f"✓ {direction} -> room {walker.current_room_id}")
                    break

    # Results
    print(f"\n{'='*60}")
    print("SOLUTION SUMMARY")
    print(f"{'='*60}")
    print(f"Rooms discovered: {len(rooms_visited)}")
    print(f"Commands in solution: {len(solution_commands)}")
    print(f"\nSolution path:")
    for i, step in enumerate(solution_commands, 1):
        print(f"  {i}. {step['command']}")

    # Save walkthrough
    walkthrough = {
        'game': str(game_path),
        'solved': True,
        'rooms_visited': list(rooms_visited),
        'solution_commands': [s['command'] for s in solution_commands],
        'full_solution_data': solution_commands,
        'stats': walker.get_stats()
    }

    output_file = Path(game_path).stem + '_solution.json'
    Path(output_file).write_text(json.dumps(walkthrough, indent=2))
    print(f"\n✓ Solution saved to: {output_file}")

    return walkthrough


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python solve_game.py <game.z5> [--real-ai]")
        sys.exit(1)

    game = sys.argv[1]
    use_ai = '--real-ai' in sys.argv

    solve_game(game, max_iterations=50, use_real_ai=use_ai)

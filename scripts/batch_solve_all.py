#!/usr/bin/env python3
"""
Batch solve all games in games/zcode/ - corrected version
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.walker import GameWalker
from zwalker.ai_assist import AIAssistant, create_context_from_walker


def solve_one_game(game_path, max_iterations=100):
    """Solve one game using AI."""
    game_name = game_path.stem
    output_path = Path("solutions") / f"{game_name}_solution.json"
    
    if output_path.exists():
        print(f"✓ SKIP {game_name} (already solved)")
        return None
    
    print(f"\n{'='*60}")
    print(f"Solving: {game_name}")
    print(f"{'='*60}")
    
    try:
        game_data = game_path.read_bytes()
        walker = GameWalker(game_data)
        output = walker.start()
        
        ai = AIAssistant(backend='anthropic')
        
        for iteration in range(max_iterations):
            context = create_context_from_walker(walker)
            
            if iteration % 20 == 0:
                print(f"  [{iteration}/{max_iterations}] {len(walker.rooms)} rooms, {len(walker.full_transcript)} commands")
            
            # Get AI suggestions
            response = ai.analyze(context)
            
            # Try commands
            command_tried = False
            for cmd in response.suggested_commands[:10]:
                walker.try_command(cmd)
                command_tried = True
                # Just try the first command and move on
                break

            if not command_tried:
                print(f"  AI gave up at iteration {iteration}")
                break
        
        # Save
        result = {
            'game': game_name,
            'total_rooms': len(walker.rooms),
            'total_commands': len(walker.full_transcript),
            'rooms_visited': list(walker.known_room_names),
            'commands': [cmd for cmd, _ in walker.full_transcript],
        }
        
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2))
        
        print(f"✓ DONE {game_name}: {result['total_rooms']} rooms, {result['total_commands']} commands")
        return result
        
    except Exception as e:
        print(f"✗ ERROR {game_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    games = sorted(Path("games/zcode").glob("*.z[3458]"))
    print(f"Found {len(games)} games")
    
    completed = 0
    skipped = 0
    failed = 0
    
    for i, game in enumerate(games, 1):
        print(f"\n[{i}/{len(games)}] {game.name}")
        result = solve_one_game(game)
        
        if result is None:
            skipped += 1
        elif result:
            completed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {completed} completed, {skipped} skipped, {failed} failed")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

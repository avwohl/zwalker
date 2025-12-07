#!/usr/bin/env python3
"""
Simplified batch solver - just run AI commands without result checking
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
        print(f"✓ SKIP {game_name}")
        return None
    
    print(f"\nSolving: {game_name}...")
    
    try:
        game_data = game_path.read_bytes()
        walker = GameWalker(game_data)
        walker.start()
        
        ai = AIAssistant(backend='anthropic')
        
        for iteration in range(max_iterations):
            if iteration % 20 == 0:
                print(f"  [{iteration}] {len(walker.rooms)} rooms, {len(walker.full_transcript)} cmds")
            
            context = create_context_from_walker(walker)
            response = ai.analyze(context)
            
            # Just try the first suggested command
            if response.suggested_commands:
                walker.try_command(response.suggested_commands[0])
        
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
        
        print(f"✓ {game_name}: {len(walker.rooms)} rooms, {len(walker.full_transcript)} commands")
        return result
        
    except Exception as e:
        print(f"✗ {game_name}: {e}")
        return False


def main():
    games = sorted(Path("games/zcode").glob("*.z[3458]"))
    print(f"Batch solving {len(games)} games\n")
    
    for i, game in enumerate(games, 1):
        print(f"[{i}/{len(games)}] ", end='')
        solve_one_game(game)


if __name__ == "__main__":
    main()

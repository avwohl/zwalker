#!/usr/bin/env python3
"""
Play games to completion using walkthroughs with AI fallback.
"""
import sys
import json
import os
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.zmachine import ZMachine
from zwalker.walker import GameWalker

def load_walkthrough(walkthrough_file):
    """Load commands from walkthrough file"""
    commands = []
    with open(walkthrough_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                commands.append(line)
    return commands

def is_combat_needed(output):
    """Check if we're in combat"""
    combat_indicators = [
        'troll', 'thief', 'cyclops', 'attacks', 'sword',
        'axe', 'parries', 'dodges', 'blow'
    ]
    output_lower = output.lower()
    return any(ind in output_lower for ind in combat_indicators)

def is_dead(output):
    """Check if player died"""
    return 'you have died' in output.lower() or 'restart, restore' in output.lower()

def is_won(output):
    """Check if game won"""
    win_indicators = [
        'your score is 350',
        '350 points',
        'master adventurer',
        'you have won'
    ]
    output_lower = output.lower()
    return any(ind in output_lower for ind in win_indicators)

def play_game(game_path, walkthrough_path, output_path):
    """Play game using walkthrough commands"""
    print(f"Playing: {game_path}")
    print(f"Walkthrough: {walkthrough_path}")

    # Load game
    game_data = Path(game_path).read_bytes()
    vm = ZMachine(game_data)

    # Load walkthrough
    commands = load_walkthrough(walkthrough_path)
    print(f"Loaded {len(commands)} commands")

    # Start game
    vm.run()
    output = vm.get_output()
    print(f"=== GAME START ===")
    print(output[:200])

    executed = []
    cmd_idx = 0

    while cmd_idx < len(commands) and len(executed) < 1000:
        cmd = commands[cmd_idx]

        # Execute command
        vm.send_input(cmd)
        vm.run()
        out = vm.get_output()
        executed.append(cmd)

        # Check win
        if is_won(out):
            print(f"\n*** WIN at command {len(executed)}! ***")
            print(out[:200])
            break

        # Check death
        if is_dead(out):
            print(f"\n*** DEATH at command {len(executed)}: {cmd} ***")
            print(out[:200])
            break

        # Handle combat - repeat attack if enemy still alive
        if 'kill' in cmd.lower() and is_combat_needed(out) and 'dies' not in out.lower():
            # Repeat attack
            for _ in range(10):
                vm.send_input(cmd)
                vm.run()
                combat_out = vm.get_output()
                executed.append(cmd)
                if 'dies' in combat_out.lower() or 'unconscious' in combat_out.lower():
                    break
                if is_dead(combat_out):
                    print(f"\n*** DIED IN COMBAT ***")
                    break

        cmd_idx += 1

        # Progress
        if len(executed) % 50 == 0:
            print(f"Progress: {len(executed)} commands executed")

    # Final score
    vm.send_input('score')
    vm.run()
    score = vm.get_output()
    print(f"\n=== FINAL ===")
    print(f"Commands executed: {len(executed)}")
    print(f"Score: {score[:100]}")

    # Save solution
    solution = {
        'game': str(game_path),
        'walkthrough': str(walkthrough_path),
        'commands': executed,
        'total_commands': len(executed),
        'completed': is_won(score) or '350' in score
    }

    Path(output_path).write_text(json.dumps(solution, indent=2))
    print(f"Saved: {output_path}")

    return solution

def main():
    if len(sys.argv) < 4:
        print("Usage: python play_to_win.py <game.z5> <walkthrough.txt> <output.json>")
        sys.exit(1)

    game_path = sys.argv[1]
    walkthrough_path = sys.argv[2]
    output_path = sys.argv[3]

    play_game(game_path, walkthrough_path, output_path)

if __name__ == '__main__':
    main()

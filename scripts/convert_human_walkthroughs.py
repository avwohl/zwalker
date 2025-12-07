#!/usr/bin/env python3
"""
Convert human walkthroughs to our solution JSON format
and optionally verify them by replaying in the Z-machine
"""

import sys
import json
import re
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.zmachine import ZMachine


def parse_walkthrough(text: str, game_name: str) -> list:
    """
    Parse a text walkthrough into command list

    Handles various formats:
    - Commands prefixed with >
    - Plain command lists
    - InvisiClues format
    - Hints format
    """
    commands = []
    in_solution = False

    for line in text.split('\n'):
        original_line = line
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Skip obvious headers/comments
        if line.startswith('===') or line.startswith('---'):
            continue
        if line.startswith('#') or line.startswith(';') or line.startswith('//'):
            continue
        if line.upper() == line and len(line) > 30:  # ALL CAPS header
            continue

        # Extract commands with > prefix
        if line.startswith('>'):
            cmd = line[1:].strip()
            if cmd and len(cmd) < 100:
                commands.append(cmd.lower())
            continue

        # Detect solution sections
        if 'solution' in line.lower() or 'walkthrough' in line.lower():
            in_solution = True
            continue

        # Skip lines that are clearly not commands
        if line.endswith(':') and len(line) < 40:  # Section headers
            continue
        if line.startswith('Note:') or line.startswith('Warning:'):
            continue
        if '©' in line or 'Copyright' in line:
            continue

        # Lines that look like commands (heuristic)
        if len(line) < 100 and not line.endswith('.') or line.endswith('!'):
            # Check if it contains common command words
            cmd_words = ['go', 'take', 'get', 'drop', 'open', 'close', 'read',
                        'examine', 'look', 'inventory', 'north', 'south', 'east',
                        'west', 'up', 'down', 'in', 'out', 'wait', 'z']

            lower_line = line.lower()
            if any(word in lower_line for word in cmd_words):
                commands.append(lower_line)
            elif in_solution and len(line.split()) <= 6:  # Short lines in solution section
                commands.append(lower_line)

    return commands


def verify_walkthrough(game_path: Path, commands: list, max_commands: int = None) -> dict:
    """
    Verify walkthrough by replaying in Z-machine
    Returns info about how far it got
    """
    try:
        with open(game_path, 'rb') as f:
            game_data = f.read()

        zm = ZMachine(game_data)
        zm.start()

        commands_to_try = commands[:max_commands] if max_commands else commands

        rooms_seen = set()
        last_output = ""

        for i, cmd in enumerate(commands_to_try):
            try:
                output = zm.execute_command(cmd)
                last_output = output

                # Try to detect room names (very basic)
                # Room names are often at the start, in title case
                lines = output.split('\n')
                for line in lines[:5]:
                    line = line.strip()
                    if line and line[0].isupper() and len(line) < 60:
                        rooms_seen.add(line)

            except Exception as e:
                return {
                    'verified': False,
                    'stopped_at': i,
                    'total_commands': len(commands),
                    'error': str(e),
                    'rooms_seen': len(rooms_seen)
                }

        # Check if won
        won = any(phrase in last_output.lower() for phrase in [
            'you have won',
            'congratulations',
            'victory',
            '*** you have won ***',
            'the end'
        ])

        return {
            'verified': True,
            'completed': won,
            'commands_executed': len(commands_to_try),
            'total_commands': len(commands),
            'rooms_seen': len(rooms_seen),
            'won_message': won
        }

    except Exception as e:
        return {
            'verified': False,
            'error': str(e),
            'total_commands': len(commands)
        }


def main():
    walkthroughs_dir = Path("walkthroughs")
    solutions_dir = Path("solutions")
    games_dir = Path("games/zcode")

    solutions_dir.mkdir(exist_ok=True)

    print("="*80)
    print("CONVERTING HUMAN WALKTHROUGHS TO JSON FORMAT")
    print("="*80)
    print()

    converted = 0
    verified = 0
    failed = 0

    for walkthrough_file in sorted(walkthroughs_dir.glob("*_human_walkthrough.txt")):
        game_name = walkthrough_file.stem.replace("_human_walkthrough", "")

        print(f"\n{game_name}:")
        print(f"  Reading: {walkthrough_file}")

        # Read and parse
        text = walkthrough_file.read_text(errors='ignore')
        commands = parse_walkthrough(text, game_name)

        print(f"  Parsed {len(commands)} commands")

        if len(commands) == 0:
            print(f"  ✗ No commands found - skipping")
            failed += 1
            continue

        # Find game file
        game_files = list(games_dir.glob(f"{game_name}.*"))
        if not game_files:
            # Try case-insensitive
            game_files = [f for f in games_dir.glob("*") if f.stem.lower() == game_name.lower()]

        # Verify if we have the game
        verify_info = {}
        if game_files:
            game_file = game_files[0]
            print(f"  Verifying with: {game_file.name}")
            verify_info = verify_walkthrough(game_file, commands, max_commands=50)

            if verify_info.get('verified'):
                print(f"  ✓ Verified: {verify_info.get('commands_executed')} commands executed")
                print(f"    Rooms seen: {verify_info.get('rooms_seen')}")
                if verify_info.get('completed'):
                    print(f"    ✓ GAME WON!")
                verified += 1
            else:
                print(f"  ⚠ Verification failed: {verify_info.get('error', 'unknown')}")
        else:
            print(f"  ⚠ No game file found - cannot verify")

        # Create solution JSON
        solution = {
            'game': game_name,
            'source': 'human_walkthrough',
            'source_file': str(walkthrough_file),
            'total_commands': len(commands),
            'commands': commands,
            'verified': verify_info.get('verified', False),
            'completed': verify_info.get('completed', False),
        }

        # Don't overwrite existing AI solutions unless this is better
        output_file = solutions_dir / f"{game_name}_solution.json"
        if output_file.exists():
            existing = json.loads(output_file.read_text())
            if existing.get('completed') and not solution['completed']:
                print(f"  ⚠ Skipping - existing solution is already complete")
                continue
            if existing.get('source') == 'AI' and len(existing.get('commands', [])) > len(commands):
                print(f"  ⚠ Skipping - existing AI solution has more exploration")
                continue

        # Save
        output_file.write_text(json.dumps(solution, indent=2))
        print(f"  ✓ Saved: {output_file}")
        converted += 1

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Converted: {converted}")
    print(f"Verified: {verified}")
    print(f"Failed: {failed}")
    print()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Debug script to understand Z-machine output behavior"""

from pathlib import Path
from zwalker.walker import GameWalker

game_data = Path("games/zcode/zork1.z3").read_bytes()
walker = GameWalker(game_data)

print("="*80)
print("STARTING GAME")
print("="*80)
output = walker.start()
print(output)
print()

commands = [
    "open mailbox",
    "read leaflet",
    "north",
    "east",
    "open window",
    "enter window",
    "west",
    "take all",
    "move rug",
    "look",
    "open trap door",
    "look",
]

for i, cmd in enumerate(commands, 1):
    print(f"\n{'='*80}")
    print(f"COMMAND {i}: {cmd}")
    print("="*80)

    # Try command
    result = walker.try_command(cmd)

    print(f"Output length: {len(result.output)}")
    print(f"New room: {result.new_room}")
    print(f"Interesting: {result.interesting}")
    print(f"Blocked: {result.blocked}")
    print()
    print("OUTPUT:")
    print(result.output)
    print()

    # Also check what's in output buffer directly
    print("VM output buffer check:")
    direct_output = walker.vm.get_output()
    if direct_output:
        print(f"  RESIDUAL OUTPUT: {direct_output[:200]}")
    else:
        print("  (empty)")

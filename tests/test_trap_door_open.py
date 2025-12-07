#!/usr/bin/env python3
"""Test opening trap door and descending"""

from pathlib import Path
from zwalker.walker import GameWalker

game_data = Path("games/zcode/zork1.z3").read_bytes()
walker = GameWalker(game_data)

walker.start()

# Get to trap door
setup_commands = [
    "east",
    "north",
    "open window",
    "enter window",
    "west",
    "take all",
    "turn on lantern",
    "move rug",
]

for cmd in setup_commands:
    result = walker.try_command(cmd)
    print(f"> {cmd}")
    print(f"  {result.output[:100]}")

print("\n" + "="*80)
print("Opening trap door...")
print("="*80)
result = walker.try_command("open trap door")
print(f"Output: {result.output}")
print(f"Blocked: {result.blocked}")

print("\n" + "="*80)
print("Looking...")
print("="*80)
result = walker.try_command("look")
print(f"Output: {result.output}")

print("\n" + "="*80)
print("Going down...")
print("="*80)
result = walker.try_command("down")
print(f"Output: {result.output}")
print(f"New room: {result.new_room}")
print(f"Blocked: {result.blocked}")

if not result.blocked:
    print("\n✓ Successfully entered cellar!")
    print("\nTrying 'look' in cellar...")
    result2 = walker.try_command("look")
    print(f"Output: {result2.output}")

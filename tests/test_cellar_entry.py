#!/usr/bin/env python3
"""Reproduce the exact sequence that causes the cellar bug"""

from pathlib import Path
from zwalker.walker import GameWalker

game_data = Path("games/zcode/zork1.z3").read_bytes()
walker = GameWalker(game_data)

print("="*80)
print("Reproducing exact Opus solver sequence to cellar")
print("="*80)

walker.start()

# These are the exact commands that the solver used to get to the cellar
commands = [
    "open mailbox",
    "east",
    "open window",
    "north",
    "open window",
    "enter window",
    "west",
    "take lantern",
    "turn on lantern",
    "move rug",
    "open trap door",
    "down",  # This works - enters cellar
    # Now try commands in cellar:
    "look",
    "inventory",
    "north",
]

for i, cmd in enumerate(commands, 1):
    print(f"\n{'='*80}")
    print(f"{i}. Command: {cmd}")
    print("="*80)

    result = walker.try_command(cmd)

    print(f"Blocked: {result.blocked}")
    print(f"New room: {result.new_room}")
    print(f"Output: {result.output[:300]}")

    if cmd == "down":
        print("\n*** ENTERED CELLAR - NEXT COMMANDS SHOULD WORK ***")

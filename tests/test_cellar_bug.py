#!/usr/bin/env python3
"""Test to debug why commands fail in the cellar"""

from pathlib import Path
from zwalker.walker import GameWalker

game_data = Path("games/zcode/zork1.z3").read_bytes()
walker = GameWalker(game_data)

print("="*80)
print("STARTING GAME")
print("="*80)
output = walker.start()
print(output[:200])
print()

# Get to the cellar
commands_to_cellar = [
    "open mailbox",
    "east", "open window", "enter window",
    "west", "take lantern", "move rug",
    "open trap door", "turn on lantern", "down",
]

print("Getting to cellar...")
for cmd in commands_to_cellar:
    result = walker.try_command(cmd)
    print(f"> {cmd}")
    if result.blocked:
        print(f"  BLOCKED: {result.output[:100]}")
    else:
        print(f"  OK: {result.output[:100]}")

print("\n" + "="*80)
print("NOW IN CELLAR - Testing commands")
print("="*80)

# Test commands in cellar using try_command
test_commands = ["look", "inventory", "north", "examine lantern"]

for cmd in test_commands:
    print(f"\n> {cmd}")
    result = walker.try_command(cmd)
    print(f"  Blocked: {result.blocked}")
    print(f"  New room: {result.new_room}")
    print(f"  Output: {result.output[:200]}")

    # Now check what _is_blocked thinks
    is_blocked = walker._is_blocked(result.output)
    print(f"  _is_blocked() says: {is_blocked}")

    # Check which pattern matched if blocked
    if is_blocked:
        from zwalker.walker import BLOCKED_PATTERNS
        import re
        print("  Matched patterns:")
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, result.output, re.IGNORECASE):
                print(f"    - {pattern}")

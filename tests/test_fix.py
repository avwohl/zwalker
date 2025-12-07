#!/usr/bin/env python3
"""Test that the restore_state fix works"""

from pathlib import Path
from zwalker.walker import GameWalker

game_data = Path("games/zcode/zork1.z3").read_bytes()
walker = GameWalker(game_data)

walker.start()

# Get to trap door (using correct path)
commands = [
    "north",  # North of House
    "east",   # Behind House
    "east",   # try going more east
]

# Actually, let me use a simpler test: just try a blocked command followed by a valid one

print("Test 1: Simple blocked command")
print("="*80)

# This will be blocked
result1 = walker.try_command("xyzzy")
print(f"1. 'xyzzy' → Blocked={result1.blocked}, Output: {result1.output[:80]}")

# This should work
result2 = walker.try_command("inventory")
print(f"2. 'inventory' → Blocked={result2.blocked}, Output: {result2.output[:80]}")

# This should work
result3 = walker.try_command("look")
print(f"3. 'look' → Blocked={result3.blocked}, Output: {result3.output[:80]}")

print("\nTest 2: Movement blocked then valid command")
print("="*80)

# Try invalid movement
result4 = walker.try_command("down")
print(f"4. 'down' → Blocked={result4.blocked}, Output: {result4.output[:80]}")

# Valid command
result5 = walker.try_command("north")
print(f"5. 'north' → Blocked={result5.blocked}, New room={result5.new_room}, Output: {result5.output[:80]}")

# Another valid command in new room
result6 = walker.try_command("look")
print(f"6. 'look' → Blocked={result6.blocked}, Output: {result6.output[:80]}")

print("\n✓ Test completed - if all outputs make sense, the fix works!")

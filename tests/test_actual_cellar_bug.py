#!/usr/bin/env python3
"""Reproduce the EXACT bug by loading the solver's checkpoint"""

from pathlib import Path
import json
from zwalker.walker import GameWalker

# Try to use the same path the solver used
game_data = Path("games/zcode/zork1.z3").read_bytes()
walker = GameWalker(game_data)

walker.start()

# Manually execute the known working path to get to trap door
# Based on the log, here's the sequence that worked:
commands = [
    "north",  # To North of House
    "east",   # To Behind House
    "enter window",  # Enter through window (after it's opened somehow)
]

# Actually, let me just try to create the exact game state
# by using save/restore. But we don't have the save file...

# Instead, let me try a DIFFERENT approach: send commands directly to VM
# and see if the output changes

print("Testing direct VM vs GameWalker output handling")
print("="*80)

# Simple sequence to test
test_cmds = ["north", "look", "south", "look"]

for cmd in test_cmds:
    print(f"\n> {cmd}")

    # Method 1: Direct VM
    walker.vm.send_input(cmd)
    walker.vm.run()
    direct_output = walker.vm.get_output()
    print(f"Direct VM output: {direct_output[:150]}")

    # Method 2: try_command
    result = walker.try_command(cmd)
    print(f"try_command output: {result.output[:150]}")

    if direct_output != result.output:
        print("⚠️  MISMATCH!")
        print(f"Direct: {repr(direct_output)}")
        print(f"Walker: {repr(result.output)}")

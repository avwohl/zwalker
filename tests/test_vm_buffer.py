#!/usr/bin/env python3
"""Test to see what's in the VM output buffer at each step"""

from pathlib import Path
from zwalker.walker import GameWalker

game_data = Path("games/zcode/zork1.z3").read_bytes()
walker = GameWalker(game_data)

walker.start()

# Get to trap door (simplified sequence)
setup_commands = [
    "east",
    "north",
    "open window",
    "enter window",
    "west",
    "take all",
    "turn on lantern",
    "move rug",
    "open trap door",
]

for cmd in setup_commands:
    walker.try_command(cmd)

print("="*80)
print("NOW AT TRAP DOOR - Testing descent to cellar")
print("="*80)

print("\nBEFORE down command:")
print(f"  VM waiting_for_input: {walker.vm.waiting_for_input}")
print(f"  VM output_buffer: {repr(walker.vm.output_buffer[:100])}")

print("\nExecuting: down")
result = walker.try_command("down")

print(f"\nAFTER down command:")
print(f"  result.output: {repr(result.output[:200])}")
print(f"  result.new_room: {result.new_room}")
print(f"  result.blocked: {result.blocked}")
print(f"  VM waiting_for_input: {walker.vm.waiting_for_input}")
print(f"  VM output_buffer: {repr(walker.vm.output_buffer[:100])}")

print("\nExecuting: look")
result2 = walker.try_command("look")

print(f"\nAFTER look command:")
print(f"  result.output: {repr(result2.output[:200])}")
print(f"  result.new_room: {result2.new_room}")
print(f"  result.blocked: {result2.blocked}")
print(f"  VM waiting_for_input: {walker.vm.waiting_for_input}")
print(f"  VM output_buffer: {repr(walker.vm.output_buffer[:100])}")

print("\nExecuting: inventory")
result3 = walker.try_command("inventory")

print(f"\nAFTER inventory command:")
print(f"  result.output: {repr(result3.output[:200])}")
print(f"  VM waiting_for_input: {walker.vm.waiting_for_input}")
print(f"  VM output_buffer: {repr(walker.vm.output_buffer[:100])}")

#!/usr/bin/env python3
"""Test exact output sequence to find the off-by-one bug"""

from pathlib import Path
from zwalker.zmachine import ZMachine

game_data = Path("games/zcode/zork1.z3").read_bytes()
vm = ZMachine(game_data)

print("="*80)
print("TEST 1: Direct Z-machine calls")
print("="*80)

# Start game
print("\n1. Starting game...")
vm.run()
output1 = vm.get_output()
print(f"Start output length: {len(output1)}")
print(f"Last 100 chars: ...{output1[-100:]}")
print()

# Send first command
print("2. Sending 'open mailbox'...")
vm.send_input("open mailbox")
vm.run()
output2 = vm.get_output()
print(f"Output: {output2}")
print()

# Send second command
print("3. Sending 'inventory'...")
vm.send_input("inventory")
vm.run()
output3 = vm.get_output()
print(f"Output: {output3}")
print()

# Send third command
print("4. Sending 'north'...")
vm.send_input("north")
vm.run()
output4 = vm.get_output()
print(f"Output: {output4}")
print()

print("="*80)
print("TEST 2: Using GameWalker")
print("="*80)

from zwalker.walker import GameWalker

walker = GameWalker(game_data)
print("\n1. Starting game...")
start_output = walker.start()
print(f"Start output length: {len(start_output)}")
print(f"Last 100 chars: ...{start_output[-100:]}")
print()

print("2. Trying 'open mailbox'...")
result = walker.try_command("open mailbox")
print(f"Output: {result.output}")
print()

print("3. Trying 'inventory'...")
result = walker.try_command("inventory")
print(f"Output: {result.output}")
print()

print("4. Trying 'north'...")
result = walker.try_command("north")
print(f"Output: {result.output}")
print()

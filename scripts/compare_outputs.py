#!/usr/bin/env python3
"""
Compare walkthrough outputs between zwalker and z2js.

This helps debug both programs by finding where they diverge.

Usage: python compare_outputs.py <solution.json>
"""

import sys
import json
import subprocess
from pathlib import Path
from difflib import unified_diff


def replay_in_zwalker(game_path, commands):
    """Replay commands in zwalker and capture detailed output"""
    from zwalker.zmachine import ZMachine

    print(f"Replaying in ZWALKER: {game_path}")
    print("-" * 60)

    game_data = Path(game_path).read_bytes()
    vm = ZMachine(game_data)

    # Initial output
    vm.run()
    initial = vm.get_output()
    print(f"[START]\n{initial[:300]}...\n")

    outputs = [{"command": None, "output": initial}]

    for i, cmd in enumerate(commands, 1):
        print(f"{i}. > {cmd}")
        vm.send_input(cmd)
        vm.run()
        output = vm.get_output()
        print(f"   {output[:200]}...\n")

        outputs.append({"command": cmd, "output": output})

    return outputs


def replay_in_z2js(js_file, commands):
    """
    Replay commands in z2js using Node.js.

    Note: This requires the JS file to have been modified to accept
    scripted input. For now, we just verify the file exists.
    """
    print(f"\nReplaying in Z2JS: {js_file}")
    print("-" * 60)

    if not Path(js_file).exists():
        print(f"ERROR: JS file not found: {js_file}")
        return None

    js_size = Path(js_file).stat().st_size
    print(f"✓ JS file exists ({js_size:,} bytes)")

    # TODO: Implement Node.js replay
    # For now, just return placeholder
    print("⚠ Node.js replay not yet implemented")
    print("  Need to modify generated JS to accept scripted input\n")

    return None


def compare_outputs(zwalker_outputs, z2js_outputs):
    """Compare outputs from both interpreters"""
    if not z2js_outputs:
        print("Cannot compare - z2js outputs not available yet")
        return

    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)

    for i, (zw, z2js) in enumerate(zip(zwalker_outputs, z2js_outputs)):
        cmd = zw.get("command", "[START]")
        zw_out = zw["output"]
        z2js_out = z2js["output"]

        if zw_out == z2js_out:
            print(f"✓ {i}. {cmd} - MATCH")
        else:
            print(f"✗ {i}. {cmd} - DIFFER")
            print(f"\n  Diff:")
            diff = list(unified_diff(
                zw_out.split('\n'),
                z2js_out.split('\n'),
                fromfile='zwalker',
                tofile='z2js',
                lineterm='',
                n=1
            ))
            for line in diff[:20]:
                print(f"  {line}")
            print()


def analyze_solution(solution_file):
    """Analyze a solution file and check quality"""
    with open(solution_file) as f:
        solution = json.load(f)

    print("\n" + "=" * 60)
    print("SOLUTION ANALYSIS")
    print("=" * 60)

    game_path = solution.get("game")
    commands = solution.get("solution_commands", [])
    rooms = solution.get("rooms_visited", [])

    print(f"Game: {game_path}")
    print(f"Rooms discovered: {len(rooms)}")
    print(f"Commands in solution: {len(commands)}")
    print(f"Commands per room: {len(commands)/max(1, len(rooms)):.1f}")

    # Check for stuck patterns
    if len(commands) > 10:
        last_10 = commands[-10:]
        if len(set(last_10)) < 5:
            print(f"\n⚠ WARNING: Repetitive commands at end")
            print(f"  Last 10: {last_10}")

    if len(rooms) == 1 and len(commands) > 20:
        print(f"\n⚠ WARNING: Stuck in one room with {len(commands)} commands")

    print(f"\nCommands:")
    for i, cmd in enumerate(commands[:20], 1):
        print(f"  {i}. {cmd}")
    if len(commands) > 20:
        print(f"  ... and {len(commands)-20} more")

    return game_path, commands


def main():
    if len(sys.argv) < 2:
        print("Usage: python compare_outputs.py <solution.json>")
        print("\nExample: python compare_outputs.py photopia_solution.json")
        sys.exit(1)

    solution_file = sys.argv[1]

    if not Path(solution_file).exists():
        print(f"ERROR: Solution file not found: {solution_file}")
        sys.exit(1)

    # Analyze the solution
    game_path, commands = analyze_solution(solution_file)

    if not game_path or not Path(game_path).exists():
        print(f"\nERROR: Game file not found: {game_path}")
        sys.exit(1)

    # Replay in zwalker
    print(f"\n{'='*60}")
    print("REPLAY IN ZWALKER")
    print(f"{'='*60}\n")
    zwalker_outputs = replay_in_zwalker(game_path, commands)

    # Check for z2js compiled version
    game_name = Path(game_path).stem
    js_file = f"z2js_output/{game_name}.js"

    if Path(js_file).exists():
        # Replay in z2js
        z2js_outputs = replay_in_z2js(js_file, commands)

        # Compare
        if z2js_outputs:
            compare_outputs(zwalker_outputs, z2js_outputs)
    else:
        print(f"\n⚠ Z2JS file not found: {js_file}")
        print("  Run: python solve_top5.py to compile with z2js first")

    return 0


if __name__ == '__main__':
    sys.exit(main())

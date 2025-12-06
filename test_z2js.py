#!/usr/bin/env python3
"""
Test script to validate z2js against zwalker.

Creates a simple walkthrough, runs it in zwalker, then runs it in z2js,
and compares the results.
"""

import sys
import json
import subprocess
from pathlib import Path

def create_simple_walkthrough(game_file):
    """Create a simple walkthrough for testing"""
    from zwalker.zmachine import ZMachine
    from zwalker.walker import GameWalker

    print(f"Creating walkthrough for {game_file}...")
    game_data = Path(game_file).read_bytes()
    walker = GameWalker(game_data)

    # Start game
    output = walker.start()
    print(f"\n=== GAME START ===")
    print(output[:300])

    # Try a sequence of commands
    commands = [
        "look",
        "inventory",
        "examine door",
        "north",
        "look",
        "inventory",
    ]

    transcript = [{"command": "", "output": output}]

    for cmd in commands:
        print(f"\n> {cmd}")
        result = walker.try_command(cmd)
        print(result.output[:200])
        transcript.append({
            "command": cmd,
            "output": result.output,
            "room_id": walker.current_room_id
        })

    # Save walkthrough
    walkthrough = {
        "game": str(game_file),
        "commands": commands,
        "transcript": transcript,
        "final_stats": walker.get_stats()
    }

    output_file = Path(game_file).stem + "_test_walkthrough.json"
    Path(output_file).write_text(json.dumps(walkthrough, indent=2))
    print(f"\n✓ Walkthrough saved to: {output_file}")

    return output_file, commands, transcript

def replay_in_zwalker(game_file, commands):
    """Replay commands in zwalker and capture output"""
    from zwalker.zmachine import ZMachine

    print(f"\n{'='*60}")
    print("REPLAYING IN ZWALKER")
    print(f"{'='*60}")

    game_data = Path(game_file).read_bytes()
    vm = ZMachine(game_data)

    # Initial run
    vm.run()
    output = vm.get_output()
    print(f"Start: {output[:200]}")

    outputs = [output]

    for cmd in commands:
        print(f"\n> {cmd}")
        vm.send_input(cmd)
        vm.run()
        output = vm.get_output()
        print(output[:200])
        outputs.append(output)

    return outputs

def replay_in_z2js(game_file, commands):
    """Replay commands in z2js and capture output"""
    print(f"\n{'='*60}")
    print("REPLAYING IN Z2JS")
    print(f"{'='*60}")

    z2js_dir = Path.home() / "src" / "z2js"
    if not z2js_dir.exists():
        print(f"ERROR: z2js not found at {z2js_dir}")
        return None

    # Convert .z file to .js using z2js
    game_path = Path(game_file).absolute()
    game_name = game_path.stem

    print(f"Converting {game_name} to JavaScript...")

    # Run z2js conversion
    result = subprocess.run(
        ["python", "-m", "jsgen", str(game_path)],
        cwd=str(z2js_dir),
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"ERROR converting game:")
        print(result.stderr)
        return None

    print(f"✓ Converted to JavaScript")

    # TODO: Run the JS version with Node.js and feed it commands
    # For now, just verify the conversion worked

    js_file = z2js_dir / f"{game_name}.js"
    if js_file.exists():
        print(f"✓ JavaScript file created: {js_file}")
        print(f"  Size: {js_file.stat().st_size} bytes")
        return {"status": "converted", "js_file": str(js_file)}
    else:
        print(f"ERROR: JavaScript file not created")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_z2js.py <game.z5>")
        print("\nExample: python test_z2js.py games/zcode/lists.z5")
        sys.exit(1)

    game_file = sys.argv[1]

    if not Path(game_file).exists():
        print(f"ERROR: Game file not found: {game_file}")
        sys.exit(1)

    # Step 1: Create walkthrough
    walkthrough_file, commands, transcript = create_simple_walkthrough(game_file)

    # Step 2: Replay in zwalker
    zwalker_outputs = replay_in_zwalker(game_file, commands)

    # Step 3: Test z2js conversion
    z2js_result = replay_in_z2js(game_file, commands)

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Game: {game_file}")
    print(f"Commands tested: {len(commands)}")
    print(f"Zwalker: ✓ Completed")
    print(f"Z2JS: {'✓ Converted' if z2js_result else '✗ Failed'}")

    if z2js_result:
        print(f"\nNext step: Run the JavaScript version and compare outputs")
        print(f"JS file: {z2js_result['js_file']}")

    return 0 if z2js_result else 1

if __name__ == '__main__':
    sys.exit(main())

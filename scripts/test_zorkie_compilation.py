#!/usr/bin/env python3
"""
Test zorkie ZIL compiler by compiling examples and testing with zwalker
"""

import subprocess
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.zmachine import ZMachine

ZORKIE_DIR = Path.home() / "src" / "zorkie"
OUTPUT_DIR = Path("/tmp/zorkie_tests")

def compile_zil(zil_file, output_file, version=3):
    """Compile a ZIL file with zorkie"""
    try:
        result = subprocess.run(
            [sys.executable, "zorkie", str(zil_file), "-o", str(output_file), "-v", str(version)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(ZORKIE_DIR),
            env={'PYTHONPATH': str(ZORKIE_DIR)}
        )

        if result.returncode == 0 and output_file.exists():
            return True, None
        else:
            return False, result.stderr or result.stdout
    except Exception as e:
        return False, str(e)

def test_z_file(z_file):
    """Test a compiled z-machine file with zwalker"""
    try:
        game_data = z_file.read_bytes()
        vm = ZMachine(game_data)
        vm.run()
        output = vm.get_output()

        return {
            'success': True,
            'output': output,
            'version': vm.header.version,
            'size': len(game_data)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    print("="*60)
    print("Testing Zorkie ZIL Compiler with ZWalker")
    print("="*60)
    print()

    if not ZORKIE_DIR.exists():
        print(f"Error: Zorkie not found at {ZORKIE_DIR}")
        return 1

    OUTPUT_DIR.mkdir(exist_ok=True)

    # Find ZIL examples
    examples = list((ZORKIE_DIR / "examples").glob("*.zil"))

    if not examples:
        print("No ZIL examples found!")
        return 1

    print(f"Found {len(examples)} ZIL examples")
    print()

    results = []
    compiled = 0
    failed_compile = 0
    passed_test = 0
    failed_test = 0

    for zil_file in sorted(examples):
        name = zil_file.stem
        output_file = OUTPUT_DIR / f"{name}.z3"

        print(f"Testing {name:30} ... ", end='', flush=True)

        # Compile
        success, error = compile_zil(zil_file, output_file)

        if not success:
            print(f"✗ COMPILE FAILED")
            if error and len(error) < 100:
                print(f"  Error: {error}")
            failed_compile += 1
            continue

        compiled += 1

        # Test with zwalker
        test_result = test_z_file(output_file)

        if test_result['success']:
            output_preview = test_result['output'][:60].replace('\n', ' ')
            print(f"✓ PASS ({test_result['size']} bytes)")
            if output_preview:
                print(f"  Output: {output_preview}...")
            passed_test += 1
        else:
            print(f"✗ TEST FAILED")
            print(f"  Error: {test_result['error']}")
            failed_test += 1

        results.append({
            'name': name,
            'compiled': success,
            'tested': test_result['success'],
            'size': test_result.get('size', 0),
            'output': test_result.get('output', '')[:200]
        })

    print()
    print("="*60)
    print("Results")
    print("="*60)
    print(f"  Total examples:    {len(examples)}")
    print(f"  Compiled:          {compiled}")
    print(f"  Failed compile:    {failed_compile}")
    print(f"  Passed test:       {passed_test}")
    print(f"  Failed test:       {failed_test}")
    print()

    if passed_test > 0:
        print(f"✓ Successfully tested {passed_test} zorkie-compiled games!")
        print(f"  Output directory: {OUTPUT_DIR}")
        return 0
    else:
        print("✗ No games passed testing")
        return 1

if __name__ == "__main__":
    sys.exit(main())

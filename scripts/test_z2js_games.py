#!/usr/bin/env python3
"""
Test all z2js-compiled games with their test scripts
"""

import subprocess
from pathlib import Path
import sys

def find_testable_games():
    """Find games that have both test scripts and z2js files"""
    scripts_dir = Path("scripts")
    testable = []

    test_scripts = list(scripts_dir.glob("test_*_solution.js"))

    for test_script in test_scripts:
        game_name = test_script.name.replace('test_', '').replace('_solution.js', '')
        z2js_file = scripts_dir / f"{game_name}_z2js.js"

        if z2js_file.exists():
            testable.append({
                'name': game_name,
                'test_script': test_script,
                'z2js_file': z2js_file
            })

    return testable

def run_test(game_info, timeout=60):
    """Run a single test"""
    try:
        # Run from scripts directory
        test_file = game_info['test_script'].name
        result = subprocess.run(
            ["node", test_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(game_info['test_script'].parent)
        )

        # Check for success indicators
        success = result.returncode == 0
        has_victory = 'VICTORY' in result.stdout or 'won' in result.stdout.lower()
        has_complete = 'TEST COMPLETE' in result.stdout
        has_error = 'Error' in result.stderr or 'error' in result.stdout.lower()

        return {
            'success': success and has_complete and not has_error,
            'returncode': result.returncode,
            'victory': has_victory,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'returncode': -1,
            'victory': False,
            'timeout': True
        }
    except Exception as e:
        return {
            'success': False,
            'returncode': -1,
            'victory': False,
            'error': str(e)
        }

def main():
    print("="*60)
    print("Z2JS Test Suite Runner")
    print("="*60)
    print()

    testable = find_testable_games()

    if not testable:
        print("No testable games found!")
        print("Need both test_*_solution.js and *_z2js.js files")
        return 1

    print(f"Found {len(testable)} testable games:")
    for game in testable:
        print(f"  - {game['name']}")
    print()

    passed = 0
    failed = 0
    timeout = 0

    print("Running tests...")
    print("-" * 60)

    for game_info in testable:
        game_name = game_info['name']
        print(f"Testing {game_name:20} ... ", end='', flush=True)

        result = run_test(game_info)

        if result.get('timeout'):
            print("✗ TIMEOUT")
            timeout += 1
        elif result['success']:
            status = "✓ PASS"
            if result['victory']:
                status += " (VICTORY)"
            print(status)
            passed += 1
        else:
            print(f"✗ FAIL (exit {result['returncode']})")
            failed += 1
            if result.get('error'):
                print(f"  Error: {result['error']}")

    print()
    print("="*60)
    print("Results")
    print("="*60)
    print(f"  Passed:  {passed}/{len(testable)}")
    print(f"  Failed:  {failed}/{len(testable)}")
    print(f"  Timeout: {timeout}/{len(testable)}")
    print()

    if passed == len(testable):
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {failed + timeout} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

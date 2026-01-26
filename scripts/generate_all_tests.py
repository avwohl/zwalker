#!/usr/bin/env python3
"""
Generate JavaScript test scripts for all solution files.

Scans the solutions directory and generates a test script for each game
that has a solution JSON file.
"""

import sys
from pathlib import Path
from generate_test_script import generate_test_script, load_solution


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate test scripts for all solution files'
    )
    parser.add_argument(
        '--solutions-dir',
        type=Path,
        default=Path('solutions'),
        help='Directory containing solution JSON files (default: solutions/)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('scripts'),
        help='Directory to write test scripts (default: scripts/)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing test scripts'
    )
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress reporting in generated tests'
    )

    args = parser.parse_args()

    # Find all solution files
    solution_files = sorted(args.solutions_dir.glob('*_solution.json'))

    # Filter out progress, state, test files
    solution_files = [
        f for f in solution_files
        if 'progress' not in f.name and 'state' not in f.name and 'test' not in f.name
    ]

    if not solution_files:
        print(f"No solution files found in {args.solutions_dir}")
        return 1

    print(f"Found {len(solution_files)} solution files")
    print()

    generated = 0
    skipped = 0
    errors = 0

    for solution_file in solution_files:
        try:
            game_name, commands = load_solution(solution_file)
            output_file = args.output_dir / f'test_{game_name}_solution.js'

            # Check if already exists
            if output_file.exists() and not args.force:
                print(f"⊙ {game_name:20} - skipped (exists, use --force to overwrite)")
                skipped += 1
                continue

            # Generate
            generate_test_script(
                game_name=game_name,
                commands=commands,
                output_path=output_file,
                z2js_file=None,
                show_progress=not args.no_progress,
                final_output_lines=2000
            )
            generated += 1

        except Exception as e:
            print(f"✗ {solution_file.stem:20} - error: {e}")
            errors += 1

    print()
    print("=" * 60)
    print(f"SUMMARY")
    print("=" * 60)
    print(f"  Generated: {generated}")
    print(f"  Skipped:   {skipped}")
    print(f"  Errors:    {errors}")
    print()

    if generated > 0:
        print(f"Test scripts written to: {args.output_dir}")
        print()
        print("To run a test:")
        print("  cd scripts")
        print("  node test_<game>_solution.js")

    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

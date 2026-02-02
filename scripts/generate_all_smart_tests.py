#!/usr/bin/env python3
"""
Generate smart test scripts for all solution files.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from generate_smart_test import generate_smart_test_script, load_solution


def main():
    solutions_dir = Path(__file__).parent.parent / 'solutions'
    scripts_dir = Path(__file__).parent

    if not solutions_dir.exists():
        print(f"Error: Solutions directory not found: {solutions_dir}")
        return 1

    solution_files = sorted(solutions_dir.glob('*_solution.json'))

    if not solution_files:
        print("No solution files found!")
        return 1

    print(f"Found {len(solution_files)} solution files\n")

    generated = 0
    skipped = 0
    errors = 0

    for sol_file in solution_files:
        try:
            game_name, commands, branches = load_solution(sol_file)
            output_path = scripts_dir / f'test_{game_name}_smart.js'

            # Skip if already exists and not forcing
            if output_path.exists() and '--force' not in sys.argv:
                print(f"⊙ {game_name} - exists (use --force to regenerate)")
                skipped += 1
                continue

            generate_smart_test_script(
                game_name=game_name,
                commands=commands,
                output_path=output_path,
                branches=branches
            )
            generated += 1

        except Exception as e:
            print(f"✗ {sol_file.name}: {e}")
            errors += 1

    print(f"\n{'='*40}")
    print(f"Generated: {generated}")
    print(f"Skipped:   {skipped}")
    print(f"Errors:    {errors}")
    print(f"Total:     {len(solution_files)}")

    return 0 if errors == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

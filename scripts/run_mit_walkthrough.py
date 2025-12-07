#!/usr/bin/env python3
"""
Run the MIT Zork 1 walkthrough with robust combat handling.

This script executes the verified MIT walkthrough, handling combat
RNG by retrying attacks and detecting death states.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.walker import GameWalker


def load_walkthrough():
    """Load and parse the MIT walkthrough."""
    walkthrough_file = Path(__file__).parent.parent / "walkthroughs" / "zork1_mit.txt"
    commands = []

    with open(walkthrough_file) as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            # Skip line numbers if present (from Read tool output)
            if '→' in line:
                line = line.split('→', 1)[1].strip()
            if line:
                commands.append(line)

    return commands


def run_command(walker, cmd, retry_combat=True):
    """Run a command with combat retry logic."""
    # Normalize command
    if cmd == "go up chimney":
        cmd = "up"

    result = walker.try_command(cmd, skip_if_tried=False)

    # Check for death
    if "you're dead" in result.output.lower() or "have died" in result.output.lower():
        return result, "dead"

    # Check for combat commands
    is_combat = cmd.startswith(('kill ', 'attack '))

    if is_combat and retry_combat:
        # Check if we won
        if 'dies' in result.output.lower() or 'dead' in result.output.lower():
            if "you're dead" not in result.output.lower():
                return result, "victory"

        # Check if we lost weapon
        if "don't have" in result.output.lower():
            return result, "disarmed"

        # Check if blocked
        if 'unconscious' in result.output.lower():
            return result, "victory"

        return result, "combat_ongoing"

    return result, "ok"


def main():
    print("=" * 60)
    print(" ZORK I: MIT WALKTHROUGH RUNNER")
    print("=" * 60)

    # Create walker
    game_file = Path(__file__).parent.parent / "games" / "zcode" / "zork1.z3"
    walker = GameWalker.create_with_knowledge(str(game_file))
    walker.kb.actions.do_not_retry = []  # Fresh start
    walker.start()

    commands = load_walkthrough()
    print(f"Loaded {len(commands)} commands from MIT walkthrough")

    cmd_index = 0
    deaths = 0
    max_deaths = 3
    checkpoint_scores = []

    while cmd_index < len(commands):
        cmd = commands[cmd_index]

        # Progress indicator every 50 commands
        if cmd_index % 50 == 0:
            result = walker.try_command("score", skip_if_tried=False)
            score_line = [l for l in result.output.split('\n') if 'score' in l.lower()]
            score_info = score_line[0] if score_line else "unknown"
            print(f"\n--- Progress: {cmd_index}/{len(commands)} commands ---")
            print(f"    {score_info}")

        result, status = run_command(walker, cmd)

        # Handle different statuses
        if status == "dead":
            deaths += 1
            print(f"\n!!! DEATH #{deaths} at command {cmd_index}: {cmd}")
            print(f"    Output: {result.output[:100]}")

            if deaths >= max_deaths:
                print(f"\nToo many deaths ({deaths}). Stopping.")
                break

            # Player resurrects in forest with reduced score
            # Try to continue from next command
            print("    Continuing after resurrection...")
            cmd_index += 1
            continue

        elif status == "victory":
            print(f"  ✓ Combat won: {cmd}")
            # Skip remaining combat commands for same target
            while cmd_index + 1 < len(commands):
                next_cmd = commands[cmd_index + 1]
                if next_cmd.startswith(('kill ', 'attack ')) and next_cmd == cmd:
                    cmd_index += 1
                else:
                    break

        elif status == "disarmed":
            print(f"  ! Disarmed during: {cmd}")
            # Try to pick up weapon
            if 'sword' in cmd:
                walker.try_command("take sword", skip_if_tried=False)
            elif 'knife' in cmd:
                walker.try_command("take knife", skip_if_tried=False)
            # Retry same command
            continue

        elif status == "combat_ongoing":
            # Combat not done, but command executed - continue to next
            pass

        # Check for blocked movement (might indicate wrong path)
        if result.blocked and not cmd.startswith(('kill ', 'attack ', 'take ', 'drop ', 'put ')):
            print(f"  ✗ Blocked: {cmd}")
            print(f"    Room: {walker.current_room_id}")

        cmd_index += 1

    # Final score
    print("\n" + "=" * 60)
    print(" FINAL RESULTS")
    print("=" * 60)

    result = walker.try_command("score", skip_if_tried=False)
    print(result.output)

    result = walker.try_command("inventory", skip_if_tried=False)
    print("\nInventory:")
    print(result.output)

    print(f"\nCommands executed: {cmd_index}/{len(commands)}")
    print(f"Deaths: {deaths}")

    # Save knowledge
    walker.save_knowledge()
    print("\nKnowledge saved.")

    return 0


if __name__ == '__main__':
    sys.exit(main())

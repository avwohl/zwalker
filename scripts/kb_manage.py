#!/usr/bin/env python3
"""
Knowledge Base Management CLI.

Manage and inspect the persistent knowledge base for Z-machine games.

Usage:
    kb_manage.py list                    - List all games with knowledge
    kb_manage.py status <game>           - Show detailed status
    kb_manage.py export <game> <file>    - Export knowledge to JSON
    kb_manage.py import <game> <file>    - Import knowledge from JSON
    kb_manage.py reset <game>            - Reset knowledge for a game
    kb_manage.py compare <game1> <game2> - Compare knowledge between games
    kb_manage.py prompt <game>           - Show AI prompt context
"""

import sys
import json
import argparse
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.knowledge import KnowledgeBase


def get_knowledge_dir():
    """Get the default knowledge directory."""
    return Path(__file__).parent.parent / "knowledge"


def cmd_list(args):
    """List all games with knowledge."""
    kb_dir = get_knowledge_dir()

    if not kb_dir.exists():
        print("No knowledge directory found.")
        return

    games = [d.name for d in kb_dir.iterdir() if d.is_dir()]

    if not games:
        print("No games with knowledge found.")
        return

    print(f"Games with knowledge ({len(games)}):")
    print("-" * 60)

    for game in sorted(games):
        game_dir = kb_dir / game
        world_file = game_dir / "world.json"

        if world_file.exists():
            with open(world_file) as f:
                world = json.load(f)
                runs = world.get('total_runs', 0)
                rooms = len(world.get('rooms', {}))
                print(f"  {game:30s} | {runs:3d} runs | {rooms:3d} rooms")
        else:
            print(f"  {game:30s} | (incomplete)")


def cmd_status(args):
    """Show detailed status for a game."""
    game_path = find_game_file(args.game)
    if not game_path:
        print(f"Error: Could not find game file for '{args.game}'")
        return

    kb = KnowledgeBase(game_path)
    stats = kb.get_stats()
    summary = kb.export_knowledge_summary()

    print(f"Knowledge Base: {kb.game_name}")
    print("=" * 60)

    print(f"\nMeta:")
    print(f"  Game file: {kb.game_file}")
    print(f"  Checksum: {kb.game_checksum}")
    print(f"  Total runs: {stats['total_runs']}")

    print(f"\nWorld Map:")
    print(f"  Rooms: {stats['rooms_discovered']}")
    print(f"  Starting room: {summary['world']['starting_room']}")
    print(f"  Has darkness: {summary['world']['has_darkness']}")
    print(f"  Has maze: {summary['world']['has_maze']}")
    print(f"  Has wandering NPC: {summary['world']['has_wandering_npc']}")

    print(f"\nObjects:")
    print(f"  Total: {stats['objects_discovered']}")
    print(f"  Takeable: {summary['objects']['takeable']}")
    print(f"  In inventory: {summary['objects']['in_inventory']}")

    print(f"\nActions:")
    print(f"  Total attempts: {stats['total_actions']}")
    print(f"  Unique commands: {len(kb.actions.by_command)}")
    print(f"  Do-not-retry: {stats['do_not_retry_count']}")
    print(f"  Death commands: {stats['death_records']}")

    print(f"\nPuzzles:")
    print(f"  Discovered: {stats['puzzles_discovered']}")
    print(f"  Solved: {stats['puzzles_solved']}")

    if kb.puzzles.puzzles:
        print(f"  Details:")
        for pid, puzzle in kb.puzzles.puzzles.items():
            print(f"    - {puzzle.name} ({puzzle.status})")

    print(f"\nSolution:")
    print(f"  Steps: {stats['solution_steps']}")
    print(f"  Branches: {stats['solution_branches']}")
    print(f"  Completeness: {kb.solution.completeness}")

    print(f"\nRandomness:")
    print(f"  Events known: {stats['random_events_known']}")
    print(f"  Events observed: {stats['random_events_observed']}")
    print(f"  Random objects: {stats['random_objects']}")

    # Exploration status
    exploration = kb.get_exploration_status()
    print(f"\nExploration:")
    print(f"  Unexplored exits: {exploration['unexplored_exits']}")
    print(f"  Blocked exits: {exploration['blocked_exits']}")

    if exploration['unexplored_details']:
        print(f"  Unexplored locations:")
        for room_id, direction in exploration['unexplored_details'][:5]:
            room = kb.get_room(room_id)
            name = room.name if room else f"Room {room_id}"
            print(f"    {name}: {direction}")


def cmd_export(args):
    """Export knowledge to JSON file."""
    game_path = find_game_file(args.game)
    if not game_path:
        print(f"Error: Could not find game file for '{args.game}'")
        return

    kb = KnowledgeBase(game_path)

    export = {
        'meta': {
            'game_name': kb.game_name,
            'game_file': str(kb.game_file),
            'checksum': kb.game_checksum,
        },
        'world': kb.world_map.to_dict(),
        'objects': kb.objects.to_dict(),
        'actions': kb.actions.to_dict(),
        'puzzles': kb.puzzles.to_dict(),
        'solution': kb.solution.to_dict(),
        'randomness': kb.randomness.to_dict(),
        'summary': kb.export_knowledge_summary(),
    }

    output_file = Path(args.output)
    output_file.write_text(json.dumps(export, indent=2))
    print(f"Exported knowledge to: {output_file}")
    print(f"  Rooms: {len(export['world'].get('rooms', {}))}")
    print(f"  Actions: {len(export['actions'].get('attempts', []))}")
    print(f"  Solution steps: {len(export['solution'].get('main_steps', []))}")


def cmd_import(args):
    """Import knowledge from JSON file."""
    input_file = Path(args.input)
    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        return

    game_path = find_game_file(args.game)
    if not game_path:
        print(f"Error: Could not find game file for '{args.game}'")
        return

    # Load import data
    with open(input_file) as f:
        import_data = json.load(f)

    # Create/update knowledge base
    kb = KnowledgeBase(game_path)

    # Import solution if present
    if 'solution' in import_data:
        kb.import_solution(import_data['solution'])
        print(f"Imported solution with {len(kb.solution.main_steps)} steps")

    kb.save()
    print(f"Knowledge imported to: {kb.knowledge_dir}")


def cmd_reset(args):
    """Reset knowledge for a game."""
    kb_dir = get_knowledge_dir() / args.game

    if not kb_dir.exists():
        print(f"No knowledge found for: {args.game}")
        return

    if not args.force:
        confirm = input(f"Reset all knowledge for '{args.game}'? [y/N]: ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return

    shutil.rmtree(kb_dir)
    print(f"Knowledge reset for: {args.game}")


def cmd_compare(args):
    """Compare knowledge between two games."""
    game1_path = find_game_file(args.game1)
    game2_path = find_game_file(args.game2)

    if not game1_path:
        print(f"Error: Could not find game file for '{args.game1}'")
        return
    if not game2_path:
        print(f"Error: Could not find game file for '{args.game2}'")
        return

    kb1 = KnowledgeBase(game1_path)
    kb2 = KnowledgeBase(game2_path)

    stats1 = kb1.get_stats()
    stats2 = kb2.get_stats()

    print(f"Comparing: {kb1.game_name} vs {kb2.game_name}")
    print("=" * 60)

    metrics = [
        ('Total runs', 'total_runs'),
        ('Rooms discovered', 'rooms_discovered'),
        ('Objects found', 'objects_discovered'),
        ('Actions tried', 'total_actions'),
        ('Do-not-retry', 'do_not_retry_count'),
        ('Puzzles discovered', 'puzzles_discovered'),
        ('Puzzles solved', 'puzzles_solved'),
        ('Solution steps', 'solution_steps'),
    ]

    print(f"\n{'Metric':<25} {kb1.game_name:>15} {kb2.game_name:>15}")
    print("-" * 60)

    for label, key in metrics:
        v1 = stats1.get(key, 0)
        v2 = stats2.get(key, 0)
        print(f"{label:<25} {v1:>15} {v2:>15}")


def cmd_prompt(args):
    """Show AI prompt context for current state."""
    game_path = find_game_file(args.game)
    if not game_path:
        print(f"Error: Could not find game file for '{args.game}'")
        return

    kb = KnowledgeBase(game_path)

    # Get starting room or specified room
    room_id = args.room if args.room else kb.world_map.starting_room_id

    if not room_id:
        print("No rooms in knowledge base yet.")
        return

    prompt = kb.get_ai_prompt_context(room_id, task=args.task)
    print(prompt)


def cmd_rooms(args):
    """List all known rooms."""
    game_path = find_game_file(args.game)
    if not game_path:
        print(f"Error: Could not find game file for '{args.game}'")
        return

    kb = KnowledgeBase(game_path)

    print(f"Rooms in {kb.game_name}:")
    print("-" * 60)

    for room_id, room in sorted(kb.world_map.rooms.items()):
        exits = ", ".join(f"{d}->{e.destination_id}" for d, e in room.exits.items())
        status = "dark" if room.is_dark else ""
        status += " deadly" if room.is_deadly else ""
        print(f"  [{room_id:3d}] {room.name}")
        if exits:
            print(f"        Exits: {exits}")
        if status.strip():
            print(f"        Status: {status.strip()}")


def cmd_solution(args):
    """Show saved solution."""
    game_path = find_game_file(args.game)
    if not game_path:
        print(f"Error: Could not find game file for '{args.game}'")
        return

    kb = KnowledgeBase(game_path)

    if not kb.solution.main_steps:
        print("No solution saved.")
        return

    print(f"Solution for {kb.game_name}")
    print(f"Completeness: {kb.solution.completeness}")
    print(f"Total commands: {kb.solution.total_commands}")
    print("-" * 60)

    for i, step in enumerate(kb.solution.main_steps, 1):
        room_info = f" (room {step.prerequisites.in_room})" if step.prerequisites and step.prerequisites.in_room else ""
        verified = f" [{step.verified_runs}x]" if step.verified_runs > 0 else ""
        print(f"{i:3d}. {step.command}{room_info}{verified}")

    if kb.solution.branches:
        print(f"\nBranches ({len(kb.solution.branches)}):")
        for bid, branch in kb.solution.branches.items():
            print(f"  {branch.name}: {len(branch.steps)} steps")


def find_game_file(game_spec: str) -> str:
    """Find a game file by name or path."""
    # Direct path
    if Path(game_spec).exists():
        return game_spec

    # Check in games directory
    games_dir = Path(__file__).parent.parent / "games" / "zcode"
    for ext in ['.z3', '.z4', '.z5', '.z8', '']:
        candidate = games_dir / f"{game_spec}{ext}"
        if candidate.exists():
            return str(candidate)

    # Check if it's just a knowledge base name
    kb_dir = get_knowledge_dir() / game_spec
    if kb_dir.exists():
        # Try to find original game file from world.json
        world_file = kb_dir / "world.json"
        if world_file.exists():
            with open(world_file) as f:
                world = json.load(f)
                game_file = world.get('game_file')
                if game_file and Path(game_file).exists():
                    return game_file

    return None


def main():
    parser = argparse.ArgumentParser(
        description='Manage ZWalker knowledge bases',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # list
    sub = subparsers.add_parser('list', help='List all games with knowledge')

    # status
    sub = subparsers.add_parser('status', help='Show detailed status')
    sub.add_argument('game', help='Game name or path')

    # export
    sub = subparsers.add_parser('export', help='Export knowledge to JSON')
    sub.add_argument('game', help='Game name or path')
    sub.add_argument('output', help='Output JSON file')

    # import
    sub = subparsers.add_parser('import', help='Import knowledge from JSON')
    sub.add_argument('game', help='Game name or path')
    sub.add_argument('input', help='Input JSON file')

    # reset
    sub = subparsers.add_parser('reset', help='Reset knowledge for a game')
    sub.add_argument('game', help='Game name')
    sub.add_argument('--force', '-f', action='store_true', help='Skip confirmation')

    # compare
    sub = subparsers.add_parser('compare', help='Compare two games')
    sub.add_argument('game1', help='First game')
    sub.add_argument('game2', help='Second game')

    # prompt
    sub = subparsers.add_parser('prompt', help='Show AI prompt context')
    sub.add_argument('game', help='Game name or path')
    sub.add_argument('--room', type=int, help='Room ID (default: starting room)')
    sub.add_argument('--task', default='explore', help='Task type (explore, solve_puzzle)')

    # rooms
    sub = subparsers.add_parser('rooms', help='List known rooms')
    sub.add_argument('game', help='Game name or path')

    # solution
    sub = subparsers.add_parser('solution', help='Show saved solution')
    sub.add_argument('game', help='Game name or path')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Dispatch to command
    commands = {
        'list': cmd_list,
        'status': cmd_status,
        'export': cmd_export,
        'import': cmd_import,
        'reset': cmd_reset,
        'compare': cmd_compare,
        'prompt': cmd_prompt,
        'rooms': cmd_rooms,
        'solution': cmd_solution,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args)
    else:
        print(f"Unknown command: {args.command}")


if __name__ == '__main__':
    main()

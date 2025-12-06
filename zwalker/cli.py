#!/usr/bin/env python3
"""
zwalker CLI - Automated walkthrough generator for Z-machine games
"""

import argparse
import sys
from pathlib import Path
from .zmachine import ZMachine
from .walker import GameWalker


def cmd_explore(args):
    """Explore a game and generate a map"""
    game_path = Path(args.game)
    if not game_path.exists():
        print(f"Error: Game file not found: {game_path}", file=sys.stderr)
        return 1

    print(f"Loading {game_path.name}...")
    game_data = game_path.read_bytes()

    walker = GameWalker(game_data)

    print("Starting game...")
    initial_output = walker.start()
    print(initial_output)
    print("-" * 60)

    # Show detected room info
    room_obj = walker.vm.get_current_room()
    player_obj = walker.vm.detect_player_object()
    if room_obj:
        room_name = walker.vm.get_current_room_name()
        print(f"Current room: #{room_obj} ({room_name})")
    if player_obj:
        player_name = walker.vm.get_object_name(player_obj)
        print(f"Player object: #{player_obj} ({player_name})")
    print()

    # Show word categories
    word_cats = walker.get_word_categories()
    print(f"Vocabulary: {len(walker.vocabulary)} words")
    print(f"  Verbs: {len(word_cats.get('verbs', []))}")
    print(f"  Nouns: {len(word_cats.get('nouns', []))}")
    print(f"Exploring up to {args.max_rooms} rooms...")
    print()

    walker.explore_breadth_first(max_rooms=args.max_rooms)

    # Try verb-noun commands if requested
    if hasattr(args, 'commands') and args.commands:
        print("Trying verb-noun combinations in each room...")
        for room_id in list(walker.rooms.keys()):
            room = walker.rooms[room_id]
            if room.state_snapshot:
                walker.vm.restore_state(room.state_snapshot)
                walker.current_room_id = room_id
                results = walker.try_verb_noun_commands(max_commands=100)
                interesting = [r for r in results if r.interesting]
                if interesting:
                    print(f"  Room {room_id}: {len(interesting)} interesting responses")

    # Try all vocabulary if thorough mode
    if hasattr(args, 'thorough') and args.thorough:
        print("Trying all vocabulary words...")
        results = walker.try_single_words(max_words=500)
        interesting = [r for r in results if r.interesting]
        print(f"  Found {len(interesting)} interesting responses")

    # AI-assisted exploration
    if hasattr(args, 'ai') and args.ai:
        print(f"AI-assisted exploration (backend: {args.ai_backend})...")
        try:
            from zwalker.ai_assist import AIAssistant
            ai = AIAssistant(backend=args.ai_backend)

            for room_id in list(walker.rooms.keys()):
                room = walker.rooms[room_id]
                if room.state_snapshot:
                    walker.vm.restore_state(room.state_snapshot)
                    walker.current_room_id = room_id

                    # Get AI analysis
                    analysis = walker.get_ai_analysis(ai)
                    print(f"  Room {room_id} ({room.name}):")
                    print(f"    Priority: {analysis['exploration_priority']}")
                    print(f"    Objects of interest: {analysis['objects_of_interest']}")
                    print(f"    Suggested: {analysis['suggested_commands'][:5]}")

                    # Try AI-suggested commands
                    results = walker.explore_with_ai(ai, max_commands=10)
                    interesting = [r for r in results if r.interesting]
                    if interesting:
                        print(f"    Found {len(interesting)} interesting responses")
        except Exception as e:
            print(f"  AI error: {e}")

    # Print results
    print(walker.get_map_text())

    stats = walker.get_stats()
    print("=" * 60)
    print("STATISTICS")
    print("=" * 60)
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Save transcript if requested
    if args.transcript:
        transcript_path = Path(args.transcript)
        transcript_path.write_text(walker.get_transcript())
        print(f"\nTranscript saved to: {transcript_path}")

    # Save JSON walkthrough if requested
    if args.json:
        import json
        json_path = Path(args.json)
        walkthrough_data = walker.get_walkthrough_json()
        json_path.write_text(json.dumps(walkthrough_data, indent=2))
        print(f"JSON walkthrough saved to: {json_path}")

    return 0


def cmd_info(args):
    """Show information about a Z-machine game file"""
    game_path = Path(args.game)
    if not game_path.exists():
        print(f"Error: Game file not found: {game_path}", file=sys.stderr)
        return 1

    game_data = game_path.read_bytes()
    vm = ZMachine(game_data)
    h = vm.header

    print(f"File: {game_path.name}")
    print(f"Size: {len(game_data)} bytes")
    print()
    print("Z-Machine Header:")
    print(f"  Version: {h.version}")
    print(f"  Release: {h.release}")
    print(f"  Serial: {h.serial}")
    print(f"  File length: {h.file_length}")
    print(f"  Checksum: 0x{h.checksum:04X}")
    print()
    print("Memory Layout:")
    print(f"  Initial PC: 0x{h.initial_pc:04X}")
    print(f"  High memory: 0x{h.high_memory:04X}")
    print(f"  Static memory: 0x{h.static_memory:04X}")
    print(f"  Dictionary: 0x{h.dictionary:04X}")
    print(f"  Object table: 0x{h.object_table:04X}")
    print(f"  Globals: 0x{h.globals:04X}")
    print(f"  Abbreviations: 0x{h.abbreviations:04X}")

    if h.version in (6, 7):
        print(f"  Routines offset: 0x{h.routines_offset:04X}")
        print(f"  Strings offset: 0x{h.strings_offset:04X}")

    # Show dictionary sample
    words = vm.get_dictionary_words()
    print()
    print(f"Dictionary: {len(words)} words")
    if words:
        sample = words[:20]
        print(f"  Sample: {', '.join(sample)}...")

    return 0


def cmd_vocab(args):
    """List vocabulary words from a game"""
    game_path = Path(args.game)
    if not game_path.exists():
        print(f"Error: Game file not found: {game_path}", file=sys.stderr)
        return 1

    game_data = game_path.read_bytes()
    vm = ZMachine(game_data)
    words = vm.get_dictionary_words()

    if args.sort:
        words = sorted(words)

    for word in words:
        print(word)

    print(f"\nTotal: {len(words)} words", file=sys.stderr)
    return 0


def cmd_play(args):
    """Interactive play session (for testing)"""
    game_path = Path(args.game)
    if not game_path.exists():
        print(f"Error: Game file not found: {game_path}", file=sys.stderr)
        return 1

    game_data = game_path.read_bytes()
    vm = ZMachine(game_data)
    vm.debug = args.debug

    # Initial run
    vm.run()
    print(vm.get_output())

    # Interactive loop
    try:
        while not vm.finished:
            try:
                cmd = input("> ")
            except EOFError:
                break

            if cmd.lower() in ('quit', 'q'):
                break

            vm.send_input(cmd)
            vm.run()
            print(vm.get_output())
    except KeyboardInterrupt:
        print("\nInterrupted")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="zwalker - Automated walkthrough generator for Z-machine games"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # explore command
    explore_parser = subparsers.add_parser(
        "explore", help="Explore a game and generate a map"
    )
    explore_parser.add_argument("game", help="Z-machine game file (.z3, .z5, etc)")
    explore_parser.add_argument(
        "-m", "--max-rooms", type=int, default=50,
        help="Maximum number of rooms to explore (default: 50)"
    )
    explore_parser.add_argument(
        "-t", "--transcript", help="Save transcript to file"
    )
    explore_parser.add_argument(
        "-j", "--json", help="Save JSON walkthrough for replay testing"
    )
    explore_parser.add_argument(
        "--thorough", action="store_true",
        help="Try all vocabulary words (slower but more thorough)"
    )
    explore_parser.add_argument(
        "--commands", action="store_true",
        help="Try verb-noun combinations in each room"
    )
    explore_parser.add_argument(
        "--ai", action="store_true",
        help="Use AI to suggest commands (uses local heuristics by default)"
    )
    explore_parser.add_argument(
        "--ai-backend", choices=["local", "anthropic", "openai"],
        default="local",
        help="AI backend to use (default: local heuristics)"
    )
    explore_parser.set_defaults(func=cmd_explore)

    # info command
    info_parser = subparsers.add_parser(
        "info", help="Show information about a game file"
    )
    info_parser.add_argument("game", help="Z-machine game file")
    info_parser.set_defaults(func=cmd_info)

    # vocab command
    vocab_parser = subparsers.add_parser(
        "vocab", help="List vocabulary words from a game"
    )
    vocab_parser.add_argument("game", help="Z-machine game file")
    vocab_parser.add_argument(
        "-s", "--sort", action="store_true", help="Sort alphabetically"
    )
    vocab_parser.set_defaults(func=cmd_vocab)

    # play command
    play_parser = subparsers.add_parser(
        "play", help="Interactive play session (for testing)"
    )
    play_parser.add_argument("game", help="Z-machine game file")
    play_parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug output"
    )
    play_parser.set_defaults(func=cmd_play)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

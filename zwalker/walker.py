"""
Game walker/explorer for Z-machine games

Systematically explores a game by trying commands and mapping rooms.
"""

from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from .zmachine import ZMachine, GameState
import re


@dataclass
class Room:
    """A discovered room in the game"""
    id: int  # Z-machine object number for this room
    name: str  # Room name from object name
    description: str  # Full description from game output
    exits: Dict[str, int] = field(default_factory=dict)  # direction -> room object number
    objects: List[Tuple[int, str]] = field(default_factory=list)  # (obj_num, name) of objects found
    takeable_objects: List[Tuple[int, str]] = field(default_factory=list)  # Objects that can be taken
    visited_from: Optional[Tuple[int, str]] = None  # (room_id, direction) we came from
    state_snapshot: Optional[GameState] = None


@dataclass
class GameObject:
    """A game object discovered during exploration"""
    id: int  # Z-machine object number
    name: str
    found_in_room: int  # Room where it was first found
    is_takeable: bool
    taken: bool = False  # Have we picked it up?


@dataclass
class ExplorationResult:
    """Result of trying a command"""
    command: str
    output: str
    new_room: bool = False
    room_id: Optional[int] = None
    blocked: bool = False  # "You can't go that way"
    interesting: bool = False  # Something notable happened
    took_object: bool = False  # Successfully took an object
    object_id: Optional[int] = None  # Object involved


# Common direction commands
DIRECTIONS = [
    "north", "south", "east", "west",
    "northeast", "northwest", "southeast", "southwest",
    "up", "down", "in", "out",
    "n", "s", "e", "w", "ne", "nw", "se", "sw", "u", "d"
]

# Direction abbreviation mapping
DIR_ABBREV = {
    "n": "north", "s": "south", "e": "east", "w": "west",
    "ne": "northeast", "nw": "northwest", "se": "southeast", "sw": "southwest",
    "u": "up", "d": "down"
}

# Common movement blockers
# Note: Be specific to avoid false positives (e.g., "revealing a closed door" shouldn't block)
BLOCKED_PATTERNS = [
    r"can'?t go that way",
    r"cannot go that way",
    r"you can'?t go",
    r"there'?s no exit",
    r"no exit",
    r"nothing in that direction",
    r"wall blocks",
    r"door is (locked|closed)",  # Only if door is the subject
    r"window is (locked|closed)",
    r"(locked|closed)\s*\.",  # At end of sentence - usually "It is locked."
    r"way is blocked",
]

# Patterns suggesting we've entered a new room
NEW_ROOM_PATTERNS = [
    r"^[A-Z][A-Za-z\s,'-]+$",  # Room names are typically title case on their own line
]


class GameWalker:
    """
    Automated game explorer.

    Explores a Z-machine game by:
    1. Trying movement commands to map rooms
    2. Tracking which rooms connect to which
    3. Discovering objects and their locations
    4. Building a walkthrough/map
    """

    def __init__(self, game_data: bytes):
        self.vm = ZMachine(game_data)

        # Exploration state - room IDs are Z-machine object numbers
        self.rooms: Dict[int, Room] = {}
        self.current_room_id: int = 0

        # State snapshots for backtracking
        self.room_states: Dict[int, GameState] = {}

        # Known vocabulary
        self.vocabulary: List[str] = []

        # Exploration queue: (room_id, direction) pairs to try
        self.unexplored: List[Tuple[int, str]] = []

        # Object tracking
        self.discovered_objects: Dict[int, GameObject] = {}
        self.inventory: List[int] = []  # Object IDs we're carrying

        # Output tracking
        self.full_transcript: List[Tuple[str, str]] = []  # (command, output)

        # Room name detection
        self.known_room_names: Set[str] = set()

    def start(self) -> str:
        """Start the game and capture initial output"""
        self.vocabulary = self.vm.get_dictionary_words()

        # Run until first input prompt
        self.vm.run()
        output = self.vm.get_output()

        # Get the actual room object number from the Z-machine
        room_obj = self.vm.get_current_room()
        if room_obj:
            room_name = self.vm.get_current_room_name()
        else:
            # Fallback to parsing output
            room_name, _ = self._parse_room_output(output)
            room_obj = 1  # Use 1 as fallback ID

        room_desc = self._parse_room_description(output)

        initial_room = Room(
            id=room_obj,
            name=room_name or "Starting Room",
            description=room_desc or output,
            state_snapshot=self.vm.save_state()
        )
        self.rooms[room_obj] = initial_room
        self.current_room_id = room_obj
        self.known_room_names.add(room_name or "Starting Room")

        # Scan for objects in starting room
        self._scan_room_objects(room_obj)

        # Queue up initial directions to explore
        for direction in DIRECTIONS[:12]:  # Full direction names
            self.unexplored.append((room_obj, direction))

        self.full_transcript.append(("", output))
        return output

    def _parse_room_description(self, output: str) -> str:
        """Extract just the room description from output"""
        _, desc = self._parse_room_output(output)
        return desc or output

    def _parse_room_output(self, output: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Try to extract room name and description from output.
        Returns (room_name, description)
        """
        lines = output.strip().split('\n')

        # Look for a line that looks like a room name (short, title case)
        room_name = None
        desc_start = 0

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Room names are typically:
            # - Relatively short (< 50 chars)
            # - Often in title case or all caps
            # - Don't end with punctuation (except maybe period)
            if len(line) < 60 and not line.endswith(('?', '!', ':')):
                # Check if it looks like a title
                words = line.split()
                if words and (
                    line.isupper() or
                    all(w[0].isupper() or w.lower() in ('the', 'a', 'an', 'of', 'in', 'on', 'at', 'to')
                        for w in words if w)
                ):
                    room_name = line
                    desc_start = i + 1
                    break

        description = '\n'.join(lines[desc_start:]).strip() if desc_start < len(lines) else None

        return room_name, description

    def _is_blocked(self, output: str) -> bool:
        """Check if output indicates movement was blocked"""
        output_lower = output.lower()
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, output_lower):
                return True
        return False

    def _detect_new_room(self, old_room: int) -> bool:
        """
        Check if we've moved to a new room by comparing room object numbers.

        This is much more reliable than parsing output - it uses the Z-machine's
        actual room tracking.
        """
        new_room = self.vm.get_current_room()
        return new_room is not None and new_room != old_room

    def _get_or_create_room(self, output: str, from_room: int, direction: str) -> int:
        """
        Get the current room, creating a new Room record if needed.

        Uses the Z-machine's room object number directly - this is reliable
        even in mazes where multiple rooms have identical descriptions.
        """
        room_obj = self.vm.get_current_room()
        if room_obj is None:
            # Fallback if we can't detect room (shouldn't happen normally)
            return from_room

        # Check if we already know this room
        if room_obj in self.rooms:
            return room_obj

        # Get room name from object, not from output parsing
        room_name = self.vm.get_current_room_name()
        room_desc = self._parse_room_description(output)

        new_room = Room(
            id=room_obj,
            name=room_name or f"Room {room_obj}",
            description=room_desc or output,
            visited_from=(from_room, direction),
            state_snapshot=self.vm.save_state()
        )
        self.rooms[room_obj] = new_room

        if room_name:
            self.known_room_names.add(room_name)

        # Scan for objects in this room
        self._scan_room_objects(room_obj)

        # Queue directions to explore from new room
        for dir_name in DIRECTIONS[:12]:
            self.unexplored.append((room_obj, dir_name))

        return room_obj

    def _is_valid_object_name(self, name: str) -> bool:
        """Check if an object name looks valid (not garbage/parser buffers)"""
        if not name or len(name) < 2:
            return False
        # Must start with a lowercase letter (object names are typically lowercase)
        if not name[0].islower():
            return False
        # Should be mostly printable and not too long
        if len(name) > 40:
            return False
        # Should be mostly lowercase letters and spaces (object names are simple)
        valid_chars = sum(1 for c in name if c.isalpha() or c in ' -')
        if valid_chars < len(name) * 0.9:
            return False
        # Should not have too many spaces (garbage often has random spacing)
        if name.count(' ') > 5:
            return False
        # Should not have multiple consecutive spaces
        if '  ' in name:
            return False
        # Should not end with a space
        if name.endswith(' '):
            return False
        return True

    def _scan_room_objects(self, room_id: int) -> None:
        """Scan a room for objects and record them"""
        room = self.rooms.get(room_id)
        if not room:
            return

        player = self.vm.detect_player_object()

        for obj_num, name in self.vm.get_objects_in_room(room_id):
            if obj_num == player:
                continue
            if not self._is_valid_object_name(name):
                continue

            is_takeable = self.vm.is_takeable(obj_num)

            # Record in room
            room.objects.append((obj_num, name))
            if is_takeable:
                room.takeable_objects.append((obj_num, name))

            # Record in global object list
            if obj_num not in self.discovered_objects:
                self.discovered_objects[obj_num] = GameObject(
                    id=obj_num,
                    name=name,
                    found_in_room=room_id,
                    is_takeable=is_takeable
                )

    def _get_reverse_direction(self, direction: str) -> Optional[str]:
        """Get the opposite direction"""
        opposites = {
            "north": "south", "south": "north",
            "east": "west", "west": "east",
            "northeast": "southwest", "southwest": "northeast",
            "northwest": "southeast", "southeast": "northwest",
            "up": "down", "down": "up",
            "in": "out", "out": "in",
        }
        # Expand abbreviation if needed
        direction = DIR_ABBREV.get(direction, direction)
        return opposites.get(direction)

    def try_command(self, command: str) -> ExplorationResult:
        """
        Try a command and analyze the result.

        Uses Z-machine room object numbers for reliable room detection,
        even in mazes with identical room descriptions.
        """
        # Save state and room before command
        state_before = self.vm.save_state()
        room_before = self.vm.get_current_room()

        # Send command
        self.vm.send_input(command)
        self.vm.run()
        output = self.vm.get_output()

        self.full_transcript.append((command, output))

        result = ExplorationResult(command=command, output=output)

        # Check if we moved to a new room (using object numbers, not text parsing)
        room_after = self.vm.get_current_room()

        if self._is_blocked(output):
            result.blocked = True
            # Restore state since nothing happened
            self.vm.restore_state(state_before)
        elif room_after is not None and room_after != room_before:
            # We moved to a different room!
            result.new_room = True
            result.room_id = self._get_or_create_room(
                output, self.current_room_id, command
            )

            # Update current room's exits
            current_room = self.rooms[self.current_room_id]
            direction = DIR_ABBREV.get(command, command)
            current_room.exits[direction] = result.room_id

            # Update new room's exits (reverse direction)
            new_room = self.rooms[result.room_id]
            reverse = self._get_reverse_direction(command)
            if reverse and reverse not in new_room.exits:
                new_room.exits[reverse] = self.current_room_id

            self.current_room_id = result.room_id
        else:
            # Check if something interesting happened
            if len(output.strip()) > 50:
                result.interesting = True

        return result

    def explore_directions(self, room_id: Optional[int] = None) -> List[ExplorationResult]:
        """
        Explore all directions from a room.
        Returns list of results.
        """
        if room_id is None:
            room_id = self.current_room_id

        # Restore to room state if needed
        room = self.rooms.get(room_id)
        if room and room.state_snapshot and self.current_room_id != room_id:
            self.vm.restore_state(room.state_snapshot)
            self.current_room_id = room_id

        results = []
        for direction in DIRECTIONS[:12]:  # Full names
            if direction not in self.rooms[room_id].exits:
                result = self.try_command(direction)
                results.append(result)

                if result.new_room:
                    # Go back to explore more from original room
                    reverse = self._get_reverse_direction(direction)
                    if reverse:
                        self.try_command(reverse)

        return results

    def explore_breadth_first(self, max_rooms: int = 100) -> Dict[int, Room]:
        """
        Explore the game using breadth-first search.
        """
        explored_from: Set[int] = set()

        while self.unexplored and len(self.rooms) < max_rooms:
            room_id, direction = self.unexplored.pop(0)

            # Skip if already explored this room
            if room_id in explored_from:
                continue

            # Check if this direction already explored
            room = self.rooms.get(room_id)
            if not room or direction in room.exits:
                continue

            # Go to this room if needed
            if self.current_room_id != room_id:
                if room.state_snapshot:
                    self.vm.restore_state(room.state_snapshot)
                    self.current_room_id = room_id

            # Try the direction
            result = self.try_command(direction)

            if result.new_room:
                # Go back
                reverse = self._get_reverse_direction(direction)
                if reverse:
                    self.try_command(reverse)

            # Mark this direction as explored
            if not self.unexplored or self.unexplored[0][0] != room_id:
                explored_from.add(room_id)

        return self.rooms

    def try_vocabulary(self, room_id: Optional[int] = None,
                       filter_words: Optional[List[str]] = None) -> List[ExplorationResult]:
        """
        Try vocabulary words in current room.
        """
        if room_id is None:
            room_id = self.current_room_id

        room = self.rooms.get(room_id)
        if room and room.state_snapshot and self.current_room_id != room_id:
            self.vm.restore_state(room.state_snapshot)
            self.current_room_id = room_id

        words = filter_words or self.vocabulary
        results = []

        # Filter out directions and common uninteresting words
        skip_words = set(DIRECTIONS + ['the', 'a', 'an', 'is', 'are', 'it'])

        for word in words:
            word = word.strip()
            if word.lower() in skip_words:
                continue

            # Save state
            state = self.vm.save_state()

            result = self.try_command(word)
            results.append(result)

            # Restore state for next word
            self.vm.restore_state(state)
            self.current_room_id = room_id

        return results

    def get_map_text(self) -> str:
        """Generate a text representation of the map"""
        lines = ["=" * 60, "GAME MAP", "=" * 60, ""]

        for room_id in sorted(self.rooms.keys()):
            room = self.rooms[room_id]
            lines.append(f"[{room_id}] {room.name}")
            if room.description:
                # First 100 chars of description
                desc = room.description[:100].replace('\n', ' ')
                if len(room.description) > 100:
                    desc += "..."
                lines.append(f"    {desc}")

            if room.exits:
                exits_str = ", ".join(f"{d} -> [{dest}]" for d, dest in room.exits.items())
                lines.append(f"    Exits: {exits_str}")

            if room.takeable_objects:
                obj_str = ", ".join(f"{name} (#{oid})" for oid, name in room.takeable_objects)
                lines.append(f"    Objects: {obj_str}")

            lines.append("")

        return '\n'.join(lines)

    def get_transcript(self) -> str:
        """Get full transcript of exploration"""
        lines = []
        for cmd, output in self.full_transcript:
            if cmd:
                lines.append(f"> {cmd}")
            lines.append(output)
            lines.append("")
        return '\n'.join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """Get exploration statistics"""
        total_exits = sum(len(r.exits) for r in self.rooms.values())
        total_objects = len(self.discovered_objects)
        takeable_objects = sum(1 for o in self.discovered_objects.values() if o.is_takeable)
        return {
            "rooms_found": len(self.rooms),
            "total_exits": total_exits,
            "objects_found": total_objects,
            "takeable_objects": takeable_objects,
            "commands_tried": len(self.full_transcript),
            "vocabulary_size": len(self.vocabulary),
            "unexplored_remaining": len(self.unexplored),
        }

    def try_take_object(self, obj_name: str) -> ExplorationResult:
        """
        Try to take an object by name.

        Returns ExplorationResult with took_object=True if successful.
        """
        state_before = self.vm.save_state()
        inventory_before = set(obj for obj, _ in self.vm.get_inventory())

        cmd = f"take {obj_name}"
        self.vm.send_input(cmd)
        self.vm.run()
        output = self.vm.get_output()

        self.full_transcript.append((cmd, output))

        result = ExplorationResult(command=cmd, output=output)

        # Check if inventory changed
        inventory_after = set(obj for obj, _ in self.vm.get_inventory())
        new_items = inventory_after - inventory_before

        if new_items:
            result.took_object = True
            result.object_id = next(iter(new_items))
            self.inventory.extend(new_items)

            # Mark object as taken
            for obj_id in new_items:
                if obj_id in self.discovered_objects:
                    self.discovered_objects[obj_id].taken = True
        else:
            # Didn't take anything - restore state
            self.vm.restore_state(state_before)

        return result

    def try_take_all_in_room(self) -> List[ExplorationResult]:
        """Try to take all takeable objects in current room"""
        results = []
        room = self.rooms.get(self.current_room_id)
        if not room:
            return results

        for obj_id, obj_name in room.takeable_objects:
            if obj_id in self.inventory:
                continue  # Already have it
            result = self.try_take_object(obj_name)
            results.append(result)

        return results

    def get_word_categories(self) -> dict:
        """Get vocabulary words categorized by type (verbs, nouns, etc.)"""
        return self.vm.get_dictionary_words_by_type()

    def generate_verb_noun_commands(self, verbs: Optional[List[str]] = None,
                                     nouns: Optional[List[str]] = None,
                                     use_all_verbs: bool = False) -> List[str]:
        """
        Generate verb-noun command combinations.

        Args:
            verbs: List of verbs to use. If None, uses dictionary verbs.
            nouns: List of nouns to use. If None, uses object names from current room.
            use_all_verbs: If True, use ALL verbs from dictionary. If False, use
                          a prioritized subset for faster exploration.
        """
        if verbs is None:
            # Get verbs from dictionary
            word_cats = self.get_word_categories()
            all_verbs = word_cats.get('verbs', [])

            if use_all_verbs:
                verbs = all_verbs
            else:
                # Prioritize useful verbs that are in the dictionary
                priority_verbs = [
                    'take', 'get', 'open', 'close', 'read', 'examin',
                    'look', 'push', 'pull', 'turn', 'move', 'lift', 'light',
                    'unlock', 'lock', 'eat', 'drink', 'wear', 'remove',
                    'attack', 'kill', 'tie', 'untie', 'pour', 'fill', 'empty',
                    'climb', 'enter', 'break', 'cut', 'dig', 'drop', 'put',
                    'throw', 'give', 'show', 'search', 'touch', 'smell',
                    'listen', 'taste', 'rub', 'shake', 'wave', 'point'
                ]
                # Use priority verbs that exist, then fill with others
                verbs = [v for v in priority_verbs if v in all_verbs or v[:6] in [x[:6] for x in all_verbs]]
                # Add any remaining verbs not in priority list
                remaining = [v for v in all_verbs if v not in verbs and not v.startswith('#') and not v.startswith('$')]
                verbs.extend(remaining[:50])  # Cap at reasonable number

        if nouns is None:
            # Use object names from current room
            room = self.rooms.get(self.current_room_id)
            if room:
                nouns = [name for _, name in room.objects]
            else:
                nouns = []

            # Also include nouns from vocabulary if room has few objects
            if len(nouns) < 5:
                word_cats = self.get_word_categories()
                dict_nouns = word_cats.get('nouns', [])
                # Add some common nouns that might work
                for noun in dict_nouns[:20]:
                    if noun not in nouns and not noun.startswith('.') and len(noun) > 2:
                        nouns.append(noun)

        commands = []
        for verb in verbs:
            for noun in nouns:
                # Use first word of noun if multi-word
                noun_word = noun.split()[0] if ' ' in noun else noun
                # Skip very short words or special characters
                if len(noun_word) < 2 or noun_word.startswith('.'):
                    continue
                commands.append(f"{verb} {noun_word}")

        return commands

    def try_single_words(self, words: Optional[List[str]] = None,
                          max_words: int = 100) -> List[ExplorationResult]:
        """
        Try single word commands.

        Useful for finding hidden actions, testing verbs without objects, etc.
        """
        results = []

        if words is None:
            # Try all vocabulary words
            words = self.vocabulary[:max_words]

        # Filter out directions (already handled by explore_directions)
        direction_words = set(DIRECTIONS)

        for word in words:
            word = word.strip()
            if not word or word.lower() in direction_words:
                continue

            # Skip special/meta words
            if word.startswith('#') or word.startswith('$') or word.startswith('.'):
                continue

            state_before = self.vm.save_state()
            room_before = self.vm.get_current_room()

            self.vm.send_input(word)
            self.vm.run()
            output = self.vm.get_output()

            self.full_transcript.append((word, output))

            result = ExplorationResult(command=word, output=output)

            # Check if room changed
            room_after = self.vm.get_current_room()
            if room_after != room_before:
                result.new_room = True
                result.room_id = room_after
                result.interesting = True
            else:
                # Restore state for single words that don't change anything significant
                self.vm.restore_state(state_before)

            # Check if output is interesting
            output_lower = output.lower()
            boring = ["don't know", "don't understand", "can't see", "i beg your"]
            if not any(b in output_lower for b in boring):
                if len(output.strip()) > 30:
                    result.interesting = True

            results.append(result)

        return results

    def try_verb_noun_commands(self, max_commands: int = 50) -> List[ExplorationResult]:
        """
        Try verb-noun combinations in current room.

        Generates commands from verbs and object names, tries them,
        and records any interesting results.
        """
        results = []
        room = self.rooms.get(self.current_room_id)
        if not room:
            return results

        commands = self.generate_verb_noun_commands()[:max_commands]

        for cmd in commands:
            # Save state before trying
            state_before = self.vm.save_state()
            room_before = self.vm.get_current_room()

            self.vm.send_input(cmd)
            self.vm.run()
            output = self.vm.get_output()

            self.full_transcript.append((cmd, output))

            result = ExplorationResult(command=cmd, output=output)

            # Check if something interesting happened
            room_after = self.vm.get_current_room()
            if room_after != room_before:
                result.new_room = True
                result.room_id = room_after

            # Check if we took something
            inventory_after = set(obj for obj, _ in self.vm.get_inventory())
            inventory_before = set(self.inventory)
            new_items = inventory_after - inventory_before
            if new_items:
                result.took_object = True
                result.object_id = next(iter(new_items))
                self.inventory.extend(new_items)

            # Check for interesting output (not just error messages)
            output_lower = output.lower()
            boring_responses = [
                "don't understand", "can't see", "can't do that",
                "doesn't seem", "nothing happens", "that's not",
                "you can't", "i don't"
            ]
            if not any(br in output_lower for br in boring_responses):
                if len(output.strip()) > 20:
                    result.interesting = True

            results.append(result)

            # Restore state unless something permanent happened
            if not result.took_object and not result.new_room:
                self.vm.restore_state(state_before)

        return results

    def explore_with_commands(self, room_id: Optional[int] = None) -> List[ExplorationResult]:
        """
        Explore a room more thoroughly with verb-noun commands.

        Tries taking objects and common interactions.
        """
        if room_id is None:
            room_id = self.current_room_id

        room = self.rooms.get(room_id)
        if room and room.state_snapshot and self.current_room_id != room_id:
            self.vm.restore_state(room.state_snapshot)
            self.current_room_id = room_id

        results = []

        # First try to take all takeable objects
        take_results = self.try_take_all_in_room()
        results.extend(take_results)

        # Then try other verb-noun combinations
        cmd_results = self.try_verb_noun_commands(max_commands=30)
        results.extend(cmd_results)

        return results

    def explore_with_ai(self, ai_assistant=None, max_commands: int = 20) -> List[ExplorationResult]:
        """
        Explore current room with AI assistance.

        Uses an AI to analyze the room and suggest commands.

        Args:
            ai_assistant: AIAssistant instance (creates local one if None)
            max_commands: Maximum AI-suggested commands to try

        Returns:
            List of exploration results
        """
        from .ai_assist import AIAssistant, create_context_from_walker

        if ai_assistant is None:
            # Use local/heuristic mode by default (no API key needed)
            ai_assistant = AIAssistant(backend="local")

        # Create context for AI
        context = create_context_from_walker(self)

        # Get AI suggestions
        response = ai_assistant.analyze(context)

        results = []
        commands_tried = set()

        # Try suggested commands
        for cmd in response.suggested_commands[:max_commands]:
            if cmd in commands_tried:
                continue
            commands_tried.add(cmd)

            state_before = self.vm.save_state()
            room_before = self.vm.get_current_room()

            self.vm.send_input(cmd)
            self.vm.run()
            output = self.vm.get_output()

            self.full_transcript.append((cmd, output))

            result = ExplorationResult(command=cmd, output=output)

            # Check results
            room_after = self.vm.get_current_room()
            if room_after != room_before:
                result.new_room = True
                result.room_id = room_after
                result.interesting = True
            else:
                # Check for interesting output
                output_lower = output.lower()
                boring = ["don't understand", "can't see", "i don't know"]
                if not any(b in output_lower for b in boring):
                    if len(output.strip()) > 30:
                        result.interesting = True

                # Restore state for non-interesting commands
                if not result.interesting:
                    self.vm.restore_state(state_before)

            results.append(result)

        return results

    def get_ai_analysis(self, ai_assistant=None) -> dict:
        """
        Get AI analysis of current room without executing commands.

        Returns dict with:
        - suggested_commands: List of commands to try
        - reasoning: AI's explanation
        - objects_of_interest: Notable objects
        - possible_puzzles: Detected puzzles/obstacles
        - exploration_priority: high/medium/low
        """
        from .ai_assist import AIAssistant, create_context_from_walker

        if ai_assistant is None:
            ai_assistant = AIAssistant(backend="local")

        context = create_context_from_walker(self)
        response = ai_assistant.analyze(context)

        return {
            "suggested_commands": response.suggested_commands,
            "reasoning": response.reasoning,
            "objects_of_interest": response.objects_of_interest,
            "possible_puzzles": response.possible_puzzles,
            "exploration_priority": response.exploration_priority
        }

    def get_walkthrough(self) -> str:
        """
        Generate a walkthrough suitable for replay testing.

        Format:
        - Each line is: COMMAND | expected_room | inventory_hash | key_output_phrase

        This can be used to verify a new compile produces the same behavior.
        """
        lines = [
            "# ZWALKER WALKTHROUGH",
            "# Format: command | room_id | room_name | inventory_count",
            "# Generated for compiler regression testing",
            "#",
        ]

        for cmd, output in self.full_transcript:
            if not cmd:
                continue

            # Get current state after this command
            # (We'd need to track this during exploration - for now just record command)
            # First line of output as key phrase
            key_phrase = output.strip().split('\n')[0][:50] if output else ""

            lines.append(f"{cmd}")

        return '\n'.join(lines)

    def get_walkthrough_json(self) -> Dict[str, Any]:
        """
        Generate walkthrough data as JSON for replay testing.

        Returns a dictionary with:
        - commands: list of commands executed
        - rooms: dict of room_id -> room info
        - objects: dict of object_id -> object info
        - transcript: list of (command, output, room_after) tuples
        """
        return {
            "format_version": 1,
            "commands": [cmd for cmd, _ in self.full_transcript if cmd],
            "rooms": {
                room_id: {
                    "name": room.name,
                    "exits": room.exits,
                    "objects": room.objects,
                    "takeable": room.takeable_objects,
                }
                for room_id, room in self.rooms.items()
            },
            "objects": {
                obj_id: {
                    "name": obj.name,
                    "found_in_room": obj.found_in_room,
                    "is_takeable": obj.is_takeable,
                    "taken": obj.taken,
                }
                for obj_id, obj in self.discovered_objects.items()
            },
            "stats": self.get_stats(),
        }

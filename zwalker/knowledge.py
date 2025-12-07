"""
Knowledge Base for ZWalker

Persistent storage for game world knowledge, tracking:
- Room map with connections
- Object locations and properties
- All actions attempted with results
- Puzzles and solutions

This enables learning across runs and avoiding repeated failures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from pathlib import Path
import json
import hashlib
from datetime import datetime
import os


# =============================================================================
# Enums
# =============================================================================

class ResultType(Enum):
    """Outcome types for command attempts"""
    SUCCESS = "success"              # Command worked as expected
    PARTIAL = "partial"              # Partially worked
    FAILURE = "failure"              # Didn't work, no harm
    BLOCKED = "blocked"              # Prevented by something specific
    DEATH = "death"                  # Player died
    ALREADY_DONE = "already_done"    # "It's already open"
    NOT_HERE = "not_here"            # Object/direction not present
    NONSENSE = "nonsense"            # Parser didn't understand
    NO_EFFECT = "no_effect"          # Worked but nothing happened


class ExitStatus(Enum):
    """Status of an exit/connection"""
    OPEN = "open"
    LOCKED = "locked"
    BLOCKED = "blocked"
    ONE_WAY = "one_way"
    CONDITIONAL = "conditional"
    UNKNOWN = "unknown"


# =============================================================================
# World Map Structures
# =============================================================================

@dataclass
class Exit:
    """A connection from one room to another"""
    direction: str                              # "north", "up", "enter", etc.
    destination_id: Optional[int] = None        # Room ID if known

    # Exit properties
    status: str = "open"                        # ExitStatus value
    blocker: Optional[str] = None               # What blocks it
    unlock_action: Optional[str] = None         # How to open
    unlock_verified: bool = False               # Confirmed working

    # One-way detection
    is_one_way: bool = False
    return_direction: Optional[str] = None      # How to get back

    # Randomness
    varies_between_runs: bool = False
    variance_notes: str = ""

    def to_dict(self) -> dict:
        return {
            "direction": self.direction,
            "destination_id": self.destination_id,
            "status": self.status,
            "blocker": self.blocker,
            "unlock_action": self.unlock_action,
            "unlock_verified": self.unlock_verified,
            "is_one_way": self.is_one_way,
            "return_direction": self.return_direction,
            "varies_between_runs": self.varies_between_runs,
            "variance_notes": self.variance_notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Exit":
        return cls(**data)


@dataclass
class Room:
    """A discovered game location"""
    id: int                                     # Z-machine object number
    name: str                                   # Room name from game
    description: str = ""                       # Full description text
    first_seen_run: int = 1
    first_seen_turn: int = 0

    # Connections
    exits: Dict[str, Exit] = field(default_factory=dict)

    # Room properties
    is_dark: bool = False                       # Requires light source
    is_deadly: bool = False                     # Can die here
    death_reasons: List[str] = field(default_factory=list)
    is_maze: bool = False
    maze_group: Optional[str] = None

    # Objects found here (object IDs)
    objects_seen: List[int] = field(default_factory=list)

    # Randomness
    varies_between_runs: bool = False
    variance_notes: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "first_seen_run": self.first_seen_run,
            "first_seen_turn": self.first_seen_turn,
            "exits": {k: v.to_dict() for k, v in self.exits.items()},
            "is_dark": self.is_dark,
            "is_deadly": self.is_deadly,
            "death_reasons": self.death_reasons,
            "is_maze": self.is_maze,
            "maze_group": self.maze_group,
            "objects_seen": self.objects_seen,
            "varies_between_runs": self.varies_between_runs,
            "variance_notes": self.variance_notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Room":
        exits = {k: Exit.from_dict(v) for k, v in data.pop("exits", {}).items()}
        return cls(exits=exits, **data)


@dataclass
class WorldMap:
    """Complete discovered map of the game world"""
    game_name: str
    game_file: str
    game_checksum: str = ""

    rooms: Dict[int, Room] = field(default_factory=dict)
    starting_room_id: Optional[int] = None

    # Global properties discovered
    has_darkness_mechanic: bool = False
    has_maze: bool = False
    has_wandering_npc: bool = False             # Thief, etc.

    # Stats
    total_runs: int = 0
    last_updated: str = ""
    schema_version: str = "1.0"

    def to_dict(self) -> dict:
        return {
            "game_name": self.game_name,
            "game_file": self.game_file,
            "game_checksum": self.game_checksum,
            "rooms": {str(k): v.to_dict() for k, v in self.rooms.items()},
            "starting_room_id": self.starting_room_id,
            "has_darkness_mechanic": self.has_darkness_mechanic,
            "has_maze": self.has_maze,
            "has_wandering_npc": self.has_wandering_npc,
            "total_runs": self.total_runs,
            "last_updated": self.last_updated,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorldMap":
        rooms_data = data.pop("rooms", {})
        rooms = {int(k): Room.from_dict(v) for k, v in rooms_data.items()}
        return cls(rooms=rooms, **data)


# =============================================================================
# Object Tracking Structures
# =============================================================================

@dataclass
class LocationChange:
    """Record of an object moving"""
    from_location: Optional[int]                # Room ID or None (inventory)
    to_location: Optional[int]
    cause: str                                  # "taken", "dropped", "npc", "destroyed"
    turn: int
    run: int
    command: str

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "LocationChange":
        return cls(**data)


@dataclass
class GameObject:
    """A discovered game object"""
    id: int                                     # Z-machine object number
    name: str                                   # Primary name
    aliases: List[str] = field(default_factory=list)

    # Location tracking
    initial_location: Optional[int] = None      # Where first found
    current_location: Optional[int] = None      # Where it is now (None = inventory)
    in_inventory: bool = False
    location_history: List[LocationChange] = field(default_factory=list)

    # Properties discovered
    is_takeable: bool = False
    is_takeable_verified: bool = False
    take_failure_reason: str = ""

    is_container: bool = False
    is_openable: bool = False
    is_open: bool = False
    is_locked: bool = False
    unlock_key: Optional[int] = None            # Object ID of key

    is_wearable: bool = False
    is_edible: bool = False
    is_readable: bool = False
    read_text: str = ""

    is_light_source: bool = False
    is_lit: bool = False

    is_weapon: bool = False
    is_valuable: bool = False
    point_value: int = 0

    is_destroyed: bool = False

    # Randomness
    spawn_is_random: bool = False
    spawn_locations_seen: List[int] = field(default_factory=list)

    # Metadata
    first_seen_run: int = 1
    first_seen_turn: int = 0
    interaction_count: int = 0

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "aliases": self.aliases,
            "initial_location": self.initial_location,
            "current_location": self.current_location,
            "in_inventory": self.in_inventory,
            "location_history": [lc.to_dict() for lc in self.location_history],
            "is_takeable": self.is_takeable,
            "is_takeable_verified": self.is_takeable_verified,
            "take_failure_reason": self.take_failure_reason,
            "is_container": self.is_container,
            "is_openable": self.is_openable,
            "is_open": self.is_open,
            "is_locked": self.is_locked,
            "unlock_key": self.unlock_key,
            "is_wearable": self.is_wearable,
            "is_edible": self.is_edible,
            "is_readable": self.is_readable,
            "read_text": self.read_text,
            "is_light_source": self.is_light_source,
            "is_lit": self.is_lit,
            "is_weapon": self.is_weapon,
            "is_valuable": self.is_valuable,
            "point_value": self.point_value,
            "is_destroyed": self.is_destroyed,
            "spawn_is_random": self.spawn_is_random,
            "spawn_locations_seen": self.spawn_locations_seen,
            "first_seen_run": self.first_seen_run,
            "first_seen_turn": self.first_seen_turn,
            "interaction_count": self.interaction_count,
        }
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "GameObject":
        history = [LocationChange.from_dict(lc) for lc in data.pop("location_history", [])]
        return cls(location_history=history, **data)


@dataclass
class ObjectTracker:
    """Track all objects in the game"""
    objects: Dict[int, GameObject] = field(default_factory=dict)

    # Quick lookups (rebuilt on load)
    _objects_by_room: Dict[int, Set[int]] = field(default_factory=dict)
    _inventory: Set[int] = field(default_factory=set)

    def add_object(self, obj: GameObject):
        """Add or update an object"""
        self.objects[obj.id] = obj
        self._update_indexes()

    def get_objects_in_room(self, room_id: int) -> List[GameObject]:
        """Get all objects currently in a room"""
        return [
            self.objects[oid] for oid in self._objects_by_room.get(room_id, set())
        ]

    def get_inventory(self) -> List[GameObject]:
        """Get all objects in inventory"""
        return [self.objects[oid] for oid in self._inventory]

    def move_object(self, obj_id: int, to_room: Optional[int],
                    cause: str, turn: int, run: int, command: str):
        """Record object movement"""
        if obj_id not in self.objects:
            return

        obj = self.objects[obj_id]
        from_loc = None if obj.in_inventory else obj.current_location

        change = LocationChange(
            from_location=from_loc,
            to_location=to_room,
            cause=cause,
            turn=turn,
            run=run,
            command=command,
        )
        obj.location_history.append(change)

        if to_room is None:
            obj.in_inventory = True
            obj.current_location = None
        else:
            obj.in_inventory = False
            obj.current_location = to_room

        self._update_indexes()

    def _update_indexes(self):
        """Rebuild quick-lookup indexes"""
        self._objects_by_room = {}
        self._inventory = set()

        for oid, obj in self.objects.items():
            if obj.in_inventory:
                self._inventory.add(oid)
            elif obj.current_location is not None:
                if obj.current_location not in self._objects_by_room:
                    self._objects_by_room[obj.current_location] = set()
                self._objects_by_room[obj.current_location].add(oid)

    def to_dict(self) -> dict:
        return {
            "objects": {str(k): v.to_dict() for k, v in self.objects.items()}
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ObjectTracker":
        tracker = cls()
        for k, v in data.get("objects", {}).items():
            tracker.objects[int(k)] = GameObject.from_dict(v)
        tracker._update_indexes()
        return tracker


# =============================================================================
# Action Log Structures
# =============================================================================

@dataclass
class ActionAttempt:
    """Record of a single command attempt"""
    id: str                                     # UUID
    command: str                                # Exact command
    normalized_command: str                     # Canonical form

    # Context
    run: int
    turn: int
    room_id: int
    inventory: List[int] = field(default_factory=list)

    # Result
    output: str = ""
    result_type: str = "failure"                # ResultType value

    # Parsed effects
    room_changed: bool = False
    new_room_id: Optional[int] = None
    objects_taken: List[int] = field(default_factory=list)
    objects_dropped: List[int] = field(default_factory=list)
    score_change: int = 0

    # Learning
    prerequisites_discovered: List[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "command": self.command,
            "normalized_command": self.normalized_command,
            "run": self.run,
            "turn": self.turn,
            "room_id": self.room_id,
            "inventory": self.inventory,
            "output": self.output,
            "result_type": self.result_type,
            "room_changed": self.room_changed,
            "new_room_id": self.new_room_id,
            "objects_taken": self.objects_taken,
            "objects_dropped": self.objects_dropped,
            "score_change": self.score_change,
            "prerequisites_discovered": self.prerequisites_discovered,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ActionAttempt":
        return cls(**data)


@dataclass
class DoNotRetry:
    """Commands to skip unless conditions change"""
    command: str
    room_id: int
    reason: str
    unless: List[str] = field(default_factory=list)
    last_attempt_run: int = 0
    attempt_count: int = 1

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "DoNotRetry":
        return cls(**data)


@dataclass
class DeathRecord:
    """Record of a death-causing command"""
    command: str
    room_id: int
    death_message: str
    avoidable_by: List[str] = field(default_factory=list)
    occurrences: int = 1

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "DeathRecord":
        return cls(**data)


@dataclass
class ActionLog:
    """Complete log of all action attempts"""
    attempts: List[ActionAttempt] = field(default_factory=list)

    # Indexes
    by_command: Dict[str, List[str]] = field(default_factory=dict)
    by_room: Dict[int, List[str]] = field(default_factory=dict)

    # Negative knowledge
    do_not_retry: List[DoNotRetry] = field(default_factory=list)
    death_records: Dict[str, DeathRecord] = field(default_factory=dict)

    def add_attempt(self, attempt: ActionAttempt):
        """Add an attempt and update indexes"""
        self.attempts.append(attempt)

        # Update command index
        norm = attempt.normalized_command
        if norm not in self.by_command:
            self.by_command[norm] = []
        self.by_command[norm].append(attempt.id)

        # Update room index
        room = attempt.room_id
        if room not in self.by_room:
            self.by_room[room] = []
        self.by_room[room].append(attempt.id)

        # Track deaths
        if attempt.result_type == ResultType.DEATH.value:
            key = f"{attempt.room_id}:{attempt.normalized_command}"
            if key in self.death_records:
                self.death_records[key].occurrences += 1
            else:
                self.death_records[key] = DeathRecord(
                    command=attempt.command,
                    room_id=attempt.room_id,
                    death_message=attempt.output[:200],
                )

    def mark_do_not_retry(self, command: str, room_id: int, reason: str,
                          unless: List[str] = None, run: int = 0):
        """Mark a command as not worth retrying"""
        unless = unless or []

        # Check if already marked
        for dnr in self.do_not_retry:
            if dnr.command == command and dnr.room_id == room_id:
                dnr.attempt_count += 1
                dnr.last_attempt_run = run
                return

        self.do_not_retry.append(DoNotRetry(
            command=command,
            room_id=room_id,
            reason=reason,
            unless=unless,
            last_attempt_run=run,
        ))

    def should_skip(self, command: str, room_id: int,
                    current_state: Dict[str, Any] = None) -> Tuple[bool, str]:
        """Check if command should be skipped"""
        current_state = current_state or {}

        for dnr in self.do_not_retry:
            if dnr.command == command and dnr.room_id == room_id:
                # Check unless conditions
                for condition in dnr.unless:
                    # Simple condition checking
                    if condition.startswith("have "):
                        item = condition[5:]
                        if item in current_state.get("inventory_names", []):
                            return False, ""
                    elif condition in current_state.get("flags", []):
                        return False, ""

                return True, dnr.reason

        return False, ""

    def get_attempts_in_room(self, room_id: int) -> List[ActionAttempt]:
        """Get all attempts made in a room"""
        attempt_ids = self.by_room.get(room_id, [])
        id_to_attempt = {a.id: a for a in self.attempts}
        return [id_to_attempt[aid] for aid in attempt_ids if aid in id_to_attempt]

    def was_tried(self, command: str, room_id: int) -> Optional[ActionAttempt]:
        """Check if command was tried in room, return most recent"""
        for attempt in reversed(self.attempts):
            if attempt.normalized_command == command and attempt.room_id == room_id:
                return attempt
        return None

    def get_death_commands(self, room_id: int) -> List[str]:
        """Get commands that caused death in this room"""
        return [
            dr.command for key, dr in self.death_records.items()
            if dr.room_id == room_id
        ]

    def to_dict(self) -> dict:
        return {
            "attempts": [a.to_dict() for a in self.attempts],
            "by_command": self.by_command,
            "by_room": {str(k): v for k, v in self.by_room.items()},
            "do_not_retry": [d.to_dict() for d in self.do_not_retry],
            "death_records": {k: v.to_dict() for k, v in self.death_records.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ActionLog":
        log = cls()
        log.attempts = [ActionAttempt.from_dict(a) for a in data.get("attempts", [])]
        log.by_command = data.get("by_command", {})
        log.by_room = {int(k): v for k, v in data.get("by_room", {}).items()}
        log.do_not_retry = [DoNotRetry.from_dict(d) for d in data.get("do_not_retry", [])]
        log.death_records = {k: DeathRecord.from_dict(v) for k, v in data.get("death_records", {}).items()}
        return log


# =============================================================================
# Puzzle Tracking Structures
# =============================================================================

class PuzzleStatus(Enum):
    """Status of a puzzle"""
    DISCOVERED = "discovered"        # Found but not started
    WORKING = "working"              # Actively trying to solve
    SOLVED = "solved"                # Successfully solved
    STUCK = "stuck"                  # Can't make progress
    BLOCKED = "blocked"              # Needs something else first


@dataclass
class Clue:
    """A clue or hint related to a puzzle"""
    text: str                                   # The clue text/observation
    source: str                                 # "room_desc", "object_examine", "npc_dialogue", "failed_action"
    source_id: Optional[int] = None             # Room/object ID
    run: int = 0
    turn: int = 0
    relevance: str = "medium"                   # "high", "medium", "low"

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "Clue":
        return cls(**data)


@dataclass
class PuzzleAttempt:
    """Record of attempting to solve a puzzle"""
    commands: List[str]                         # Sequence tried
    result: str                                 # What happened
    success: bool = False
    partial_progress: bool = False              # Made some progress
    notes: str = ""                             # Analysis
    run: int = 0
    turn: int = 0

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "PuzzleAttempt":
        return cls(**data)


@dataclass
class Puzzle:
    """A discovered puzzle in the game"""
    id: str                                     # Generated identifier
    name: str                                   # Human-readable name
    description: str                            # What the puzzle seems to be
    puzzle_type: str = "unknown"                # "locked_door", "darkness", "combat", "inventory", "sequence", etc.

    # Location
    room_id: int = 0                            # Primary room
    related_rooms: List[int] = field(default_factory=list)

    # Objects involved
    required_objects: List[int] = field(default_factory=list)
    involved_objects: List[int] = field(default_factory=list)

    # State tracking
    status: str = "discovered"                  # PuzzleStatus value
    blocking: List[str] = field(default_factory=list)  # What this puzzle blocks
    blocked_by: List[str] = field(default_factory=list)  # Prerequisites

    # Clues found
    clues: List[Clue] = field(default_factory=list)

    # Solution attempts
    attempts: List[PuzzleAttempt] = field(default_factory=list)

    # Solution (if found)
    solution_commands: List[str] = field(default_factory=list)
    solution_verified: bool = False
    alternative_solutions: List[List[str]] = field(default_factory=list)

    # Metadata
    discovered_run: int = 0
    discovered_turn: int = 0
    solved_run: Optional[int] = None
    solved_turn: Optional[int] = None

    def add_clue(self, text: str, source: str, source_id: int = None,
                 run: int = 0, turn: int = 0, relevance: str = "medium"):
        """Add a clue to this puzzle"""
        # Avoid duplicates
        for clue in self.clues:
            if clue.text == text:
                return
        self.clues.append(Clue(
            text=text, source=source, source_id=source_id,
            run=run, turn=turn, relevance=relevance
        ))

    def add_attempt(self, commands: List[str], result: str, success: bool = False,
                    partial: bool = False, run: int = 0, turn: int = 0):
        """Record a solution attempt"""
        self.attempts.append(PuzzleAttempt(
            commands=commands, result=result, success=success,
            partial_progress=partial, run=run, turn=turn
        ))
        if success:
            self.status = PuzzleStatus.SOLVED.value
            self.solution_commands = commands
            self.solved_run = run
            self.solved_turn = turn

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "puzzle_type": self.puzzle_type,
            "room_id": self.room_id,
            "related_rooms": self.related_rooms,
            "required_objects": self.required_objects,
            "involved_objects": self.involved_objects,
            "status": self.status,
            "blocking": self.blocking,
            "blocked_by": self.blocked_by,
            "clues": [c.to_dict() for c in self.clues],
            "attempts": [a.to_dict() for a in self.attempts],
            "solution_commands": self.solution_commands,
            "solution_verified": self.solution_verified,
            "alternative_solutions": self.alternative_solutions,
            "discovered_run": self.discovered_run,
            "discovered_turn": self.discovered_turn,
            "solved_run": self.solved_run,
            "solved_turn": self.solved_turn,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Puzzle":
        clues = [Clue.from_dict(c) for c in data.pop("clues", [])]
        attempts = [PuzzleAttempt.from_dict(a) for a in data.pop("attempts", [])]
        puzzle = cls(**data)
        puzzle.clues = clues
        puzzle.attempts = attempts
        return puzzle


@dataclass
class PuzzleTracker:
    """Track all puzzles in the game"""
    puzzles: Dict[str, Puzzle] = field(default_factory=dict)

    # Dependency graph
    puzzle_order: List[str] = field(default_factory=list)  # Solved order
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)

    # Discovery
    potential_puzzles: List[str] = field(default_factory=list)

    def add_puzzle(self, puzzle: Puzzle):
        """Add or update a puzzle"""
        self.puzzles[puzzle.id] = puzzle

    def get_puzzle(self, puzzle_id: str) -> Optional[Puzzle]:
        """Get puzzle by ID"""
        return self.puzzles.get(puzzle_id)

    def get_puzzles_in_room(self, room_id: int) -> List[Puzzle]:
        """Get all puzzles in a room"""
        return [p for p in self.puzzles.values() if p.room_id == room_id]

    def get_unsolved_puzzles(self) -> List[Puzzle]:
        """Get all unsolved puzzles"""
        return [p for p in self.puzzles.values()
                if p.status != PuzzleStatus.SOLVED.value]

    def get_solvable_puzzles(self) -> List[Puzzle]:
        """Get puzzles that can be attempted (not blocked)"""
        solved_ids = {p.id for p in self.puzzles.values()
                      if p.status == PuzzleStatus.SOLVED.value}
        result = []
        for puzzle in self.puzzles.values():
            if puzzle.status == PuzzleStatus.SOLVED.value:
                continue
            # Check if all blockers are solved
            if all(bid in solved_ids for bid in puzzle.blocked_by):
                result.append(puzzle)
        return result

    def mark_solved(self, puzzle_id: str, commands: List[str], run: int, turn: int):
        """Mark a puzzle as solved"""
        if puzzle_id in self.puzzles:
            puzzle = self.puzzles[puzzle_id]
            puzzle.status = PuzzleStatus.SOLVED.value
            puzzle.solution_commands = commands
            puzzle.solved_run = run
            puzzle.solved_turn = turn
            if puzzle_id not in self.puzzle_order:
                self.puzzle_order.append(puzzle_id)

    def to_dict(self) -> dict:
        return {
            "puzzles": {k: v.to_dict() for k, v in self.puzzles.items()},
            "puzzle_order": self.puzzle_order,
            "dependency_graph": self.dependency_graph,
            "potential_puzzles": self.potential_puzzles,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PuzzleTracker":
        tracker = cls()
        for k, v in data.get("puzzles", {}).items():
            tracker.puzzles[k] = Puzzle.from_dict(v)
        tracker.puzzle_order = data.get("puzzle_order", [])
        tracker.dependency_graph = data.get("dependency_graph", {})
        tracker.potential_puzzles = data.get("potential_puzzles", [])
        return tracker


# =============================================================================
# Solution Structures
# =============================================================================

@dataclass
class Prerequisites:
    """Conditions that must be true to execute a step"""
    in_room: Optional[int] = None
    has_items: List[int] = field(default_factory=list)
    has_item_names: List[str] = field(default_factory=list)  # Alternate: by name
    state_flags: Dict[str, bool] = field(default_factory=dict)
    puzzles_solved: List[str] = field(default_factory=list)
    not_conditions: List[str] = field(default_factory=list)

    def check(self, current_room: int, inventory: List[int],
              inventory_names: List[str], solved_puzzles: List[str],
              flags: Dict[str, bool] = None) -> Tuple[bool, str]:
        """
        Check if prerequisites are met.

        Returns (True, "") if met, (False, reason) if not.
        """
        flags = flags or {}

        # Check room
        if self.in_room is not None and current_room != self.in_room:
            return False, f"must be in room {self.in_room}"

        # Check items by ID
        for item_id in self.has_items:
            if item_id not in inventory:
                return False, f"missing item #{item_id}"

        # Check items by name
        for item_name in self.has_item_names:
            if item_name.lower() not in [n.lower() for n in inventory_names]:
                return False, f"missing {item_name}"

        # Check puzzles
        for puzzle_id in self.puzzles_solved:
            if puzzle_id not in solved_puzzles:
                return False, f"puzzle {puzzle_id} not solved"

        # Check flags
        for flag, expected in self.state_flags.items():
            if flags.get(flag) != expected:
                return False, f"flag {flag} is not {expected}"

        # Check NOT conditions
        for condition in self.not_conditions:
            if condition in flags and flags[condition]:
                return False, f"condition {condition} must be false"

        return True, ""

    def to_dict(self) -> dict:
        return {
            "in_room": self.in_room,
            "has_items": self.has_items,
            "has_item_names": self.has_item_names,
            "state_flags": self.state_flags,
            "puzzles_solved": self.puzzles_solved,
            "not_conditions": self.not_conditions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Prerequisites":
        return cls(**data)


@dataclass
class SolutionStep:
    """A single step in a solution"""
    id: str                                     # Step identifier
    command: str                                # The command to execute

    # Context requirements
    prerequisites: Prerequisites = field(default_factory=Prerequisites)

    # Expected outcome
    expected_result: str = ""                   # What should happen
    expected_room: Optional[int] = None         # Where we should end up
    expected_inventory_add: List[int] = field(default_factory=list)
    expected_inventory_remove: List[int] = field(default_factory=list)

    # Validation
    success_indicators: List[str] = field(default_factory=list)
    failure_indicators: List[str] = field(default_factory=list)

    # Fallback
    on_failure: str = "abort"                   # "abort", "skip", "branch:id", "retry:n"

    # Metadata
    source: str = "discovered"                  # "discovered", "walkthrough", "ai_suggested"
    confidence: float = 1.0                     # 0.0 - 1.0
    verified_runs: int = 0
    notes: str = ""

    def check_success(self, output: str) -> bool:
        """Check if step succeeded based on output"""
        output_lower = output.lower()

        # Check failure indicators first
        for indicator in self.failure_indicators:
            if indicator.lower() in output_lower:
                return False

        # Check success indicators
        if self.success_indicators:
            return any(ind.lower() in output_lower for ind in self.success_indicators)

        # Default: success if no failure indicators matched
        return True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "command": self.command,
            "prerequisites": self.prerequisites.to_dict(),
            "expected_result": self.expected_result,
            "expected_room": self.expected_room,
            "expected_inventory_add": self.expected_inventory_add,
            "expected_inventory_remove": self.expected_inventory_remove,
            "success_indicators": self.success_indicators,
            "failure_indicators": self.failure_indicators,
            "on_failure": self.on_failure,
            "source": self.source,
            "confidence": self.confidence,
            "verified_runs": self.verified_runs,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SolutionStep":
        prereq_data = data.pop("prerequisites", {})
        step = cls(**data)
        step.prerequisites = Prerequisites.from_dict(prereq_data)
        return step


@dataclass
class SolutionBranch:
    """A conditional branch in the solution"""
    id: str
    name: str                                   # "handle_thief", "maze_variant_a"

    # When to use this branch
    trigger_type: str = "text_match"            # "text_match", "state_check", "random_detect"
    trigger_condition: str = ""                 # Pattern or condition

    # The steps in this branch
    steps: List[SolutionStep] = field(default_factory=list)

    # After branch completes
    rejoin_at: Optional[str] = None             # Step ID to continue from

    def matches(self, output: str, state: Dict[str, Any] = None) -> bool:
        """Check if this branch should be taken"""
        state = state or {}

        if self.trigger_type == "text_match":
            import re
            return bool(re.search(self.trigger_condition, output, re.IGNORECASE))

        elif self.trigger_type == "state_check":
            # Simple flag check
            return state.get(self.trigger_condition, False)

        elif self.trigger_type == "random_detect":
            # Check for randomness indicators
            return self.trigger_condition.lower() in output.lower()

        return False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "trigger_type": self.trigger_type,
            "trigger_condition": self.trigger_condition,
            "steps": [s.to_dict() for s in self.steps],
            "rejoin_at": self.rejoin_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SolutionBranch":
        steps = [SolutionStep.from_dict(s) for s in data.pop("steps", [])]
        branch = cls(**data)
        branch.steps = steps
        return branch


@dataclass
class Solution:
    """Complete solution for a game"""
    game_name: str
    game_file: str
    game_checksum: str = ""

    # Version tracking
    version: int = 1
    created: str = ""
    last_modified: str = ""
    last_verified: str = ""

    # Main solution path
    main_steps: List[SolutionStep] = field(default_factory=list)

    # Conditional branches
    branches: Dict[str, SolutionBranch] = field(default_factory=dict)

    # Solution quality
    completeness: str = "partial"               # "full", "partial", "to_point_X"
    end_state: str = ""                         # "won", "score_N", "reached_room_X"
    total_commands: int = 0
    estimated_turns: int = 0

    # Verification
    verified_count: int = 0
    last_failure: Optional[str] = None
    known_issues: List[str] = field(default_factory=list)

    def add_step(self, command: str, step_id: str = None,
                 prerequisites: Prerequisites = None,
                 success_indicators: List[str] = None,
                 source: str = "discovered") -> SolutionStep:
        """Add a step to the main solution"""
        if step_id is None:
            step_id = f"step_{len(self.main_steps) + 1:03d}"

        step = SolutionStep(
            id=step_id,
            command=command,
            prerequisites=prerequisites or Prerequisites(),
            success_indicators=success_indicators or [],
            source=source,
        )
        self.main_steps.append(step)
        self.total_commands = len(self.main_steps)
        return step

    def add_branch(self, branch: SolutionBranch):
        """Add a conditional branch"""
        self.branches[branch.id] = branch

    def get_step(self, step_id: str) -> Optional[SolutionStep]:
        """Get a step by ID"""
        for step in self.main_steps:
            if step.id == step_id:
                return step
        for branch in self.branches.values():
            for step in branch.steps:
                if step.id == step_id:
                    return step
        return None

    def get_next_step(self, current_step_id: str = None) -> Optional[SolutionStep]:
        """Get the next step after current"""
        if current_step_id is None:
            return self.main_steps[0] if self.main_steps else None

        for i, step in enumerate(self.main_steps):
            if step.id == current_step_id:
                if i + 1 < len(self.main_steps):
                    return self.main_steps[i + 1]
                return None

        return None

    def check_for_branch(self, output: str, state: Dict[str, Any] = None) -> Optional[SolutionBranch]:
        """Check if any branch should be taken based on output"""
        for branch in self.branches.values():
            if branch.matches(output, state):
                return branch
        return None

    def to_dict(self) -> dict:
        return {
            "game_name": self.game_name,
            "game_file": self.game_file,
            "game_checksum": self.game_checksum,
            "version": self.version,
            "created": self.created,
            "last_modified": self.last_modified,
            "last_verified": self.last_verified,
            "main_steps": [s.to_dict() for s in self.main_steps],
            "branches": {k: v.to_dict() for k, v in self.branches.items()},
            "completeness": self.completeness,
            "end_state": self.end_state,
            "total_commands": self.total_commands,
            "estimated_turns": self.estimated_turns,
            "verified_count": self.verified_count,
            "last_failure": self.last_failure,
            "known_issues": self.known_issues,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Solution":
        steps = [SolutionStep.from_dict(s) for s in data.pop("main_steps", [])]
        branches = {k: SolutionBranch.from_dict(v) for k, v in data.pop("branches", {}).items()}
        sol = cls(**data)
        sol.main_steps = steps
        sol.branches = branches
        return sol


# =============================================================================
# Main Knowledge Base Class
# =============================================================================

class KnowledgeBase:
    """
    Main interface to game knowledge.

    Provides persistent storage and querying for:
    - World map (rooms and connections)
    - Object tracking (locations and properties)
    - Action history (what was tried and results)
    - Puzzles discovered and their solutions
    - Complete game solutions with branching
    """

    def __init__(self, game_file: str, knowledge_dir: str = None):
        """
        Initialize knowledge base for a game.

        Args:
            game_file: Path to the .z game file
            knowledge_dir: Directory to store knowledge (default: ./knowledge/)
        """
        self.game_file = game_file
        self.game_name = Path(game_file).stem

        # Set up storage directory
        if knowledge_dir is None:
            knowledge_dir = Path(__file__).parent.parent / "knowledge"
        self.knowledge_dir = Path(knowledge_dir) / self.game_name
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

        # Compute game checksum for version tracking
        self.game_checksum = self._compute_checksum(game_file)

        # Core data structures
        self.world_map = WorldMap(
            game_name=self.game_name,
            game_file=str(game_file),
            game_checksum=self.game_checksum,
        )
        self.objects = ObjectTracker()
        self.actions = ActionLog()

        # Puzzle and solution tracking
        self.puzzles = PuzzleTracker()
        self.solution = Solution(
            game_name=self.game_name,
            game_file=str(game_file),
            game_checksum=self.game_checksum,
            created=datetime.now().isoformat(),
        )

        # Randomness tracking
        self.randomness = RandomnessTracker()

        # Current run state
        self.current_run = 0
        self.current_turn = 0

        # State flags for prerequisites
        self.state_flags: Dict[str, bool] = {}

        # Load existing knowledge
        self.load()

    def _compute_checksum(self, filepath: str) -> str:
        """Compute MD5 checksum of game file"""
        try:
            with open(filepath, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()[:8]
        except Exception:
            return ""

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------

    def load(self):
        """Load all knowledge from disk"""
        world_file = self.knowledge_dir / "world.json"
        objects_file = self.knowledge_dir / "objects.json"
        actions_file = self.knowledge_dir / "actions.json"
        puzzles_file = self.knowledge_dir / "puzzles.json"
        solution_file = self.knowledge_dir / "solution.json"
        randomness_file = self.knowledge_dir / "randomness.json"

        if world_file.exists():
            with open(world_file) as f:
                self.world_map = WorldMap.from_dict(json.load(f))

        if objects_file.exists():
            with open(objects_file) as f:
                self.objects = ObjectTracker.from_dict(json.load(f))

        if actions_file.exists():
            with open(actions_file) as f:
                self.actions = ActionLog.from_dict(json.load(f))

        if puzzles_file.exists():
            with open(puzzles_file) as f:
                self.puzzles = PuzzleTracker.from_dict(json.load(f))

        if solution_file.exists():
            with open(solution_file) as f:
                self.solution = Solution.from_dict(json.load(f))

        if randomness_file.exists():
            with open(randomness_file) as f:
                self.randomness = RandomnessTracker.from_dict(json.load(f))

        self.current_run = self.world_map.total_runs

    def save(self):
        """Save all knowledge to disk"""
        self.world_map.last_updated = datetime.now().isoformat()
        self.solution.last_modified = datetime.now().isoformat()

        with open(self.knowledge_dir / "world.json", "w") as f:
            json.dump(self.world_map.to_dict(), f, indent=2)

        with open(self.knowledge_dir / "objects.json", "w") as f:
            json.dump(self.objects.to_dict(), f, indent=2)

        with open(self.knowledge_dir / "actions.json", "w") as f:
            json.dump(self.actions.to_dict(), f, indent=2)

        with open(self.knowledge_dir / "puzzles.json", "w") as f:
            json.dump(self.puzzles.to_dict(), f, indent=2)

        with open(self.knowledge_dir / "solution.json", "w") as f:
            json.dump(self.solution.to_dict(), f, indent=2)

        with open(self.knowledge_dir / "randomness.json", "w") as f:
            json.dump(self.randomness.to_dict(), f, indent=2)

    def start_new_run(self) -> int:
        """Start a new game run, returns run number"""
        self.current_run = self.world_map.total_runs + 1
        self.world_map.total_runs = self.current_run
        self.current_turn = 0
        return self.current_run

    # -------------------------------------------------------------------------
    # World Map Operations
    # -------------------------------------------------------------------------

    def add_room(self, room_id: int, name: str, description: str = "") -> Room:
        """Add or update a room"""
        if room_id in self.world_map.rooms:
            room = self.world_map.rooms[room_id]
            if description and not room.description:
                room.description = description
            return room

        room = Room(
            id=room_id,
            name=name,
            description=description,
            first_seen_run=self.current_run,
            first_seen_turn=self.current_turn,
        )
        self.world_map.rooms[room_id] = room

        if self.world_map.starting_room_id is None:
            self.world_map.starting_room_id = room_id

        return room

    def add_exit(self, from_room: int, direction: str,
                 to_room: Optional[int] = None, status: str = "open") -> Exit:
        """Add or update an exit from a room"""
        if from_room not in self.world_map.rooms:
            return None

        room = self.world_map.rooms[from_room]

        if direction in room.exits:
            exit_obj = room.exits[direction]
            if to_room is not None and exit_obj.destination_id is None:
                exit_obj.destination_id = to_room
            return exit_obj

        exit_obj = Exit(
            direction=direction,
            destination_id=to_room,
            status=status,
        )
        room.exits[direction] = exit_obj
        return exit_obj

    def mark_exit_blocked(self, from_room: int, direction: str,
                          blocker: str, unlock_action: str = None):
        """Mark an exit as blocked"""
        if from_room not in self.world_map.rooms:
            return

        room = self.world_map.rooms[from_room]
        if direction not in room.exits:
            room.exits[direction] = Exit(direction=direction)

        exit_obj = room.exits[direction]
        exit_obj.status = ExitStatus.BLOCKED.value
        exit_obj.blocker = blocker
        exit_obj.unlock_action = unlock_action

    def mark_exit_one_way(self, from_room: int, direction: str):
        """Mark an exit as one-way (can't return)"""
        if from_room not in self.world_map.rooms:
            return

        room = self.world_map.rooms[from_room]
        if direction in room.exits:
            room.exits[direction].is_one_way = True

    def get_unexplored_exits(self) -> List[Tuple[int, str]]:
        """Get all exits we haven't tried yet"""
        unexplored = []
        for room_id, room in self.world_map.rooms.items():
            for direction, exit_obj in room.exits.items():
                if exit_obj.destination_id is None and exit_obj.status == "open":
                    unexplored.append((room_id, direction))
        return unexplored

    def find_path(self, from_room: int, to_room: int) -> Optional[List[str]]:
        """Find shortest path between rooms using BFS"""
        if from_room == to_room:
            return []

        if from_room not in self.world_map.rooms:
            return None
        if to_room not in self.world_map.rooms:
            return None

        # BFS
        from collections import deque
        queue = deque([(from_room, [])])
        visited = {from_room}

        while queue:
            current, path = queue.popleft()

            if current not in self.world_map.rooms:
                continue

            room = self.world_map.rooms[current]
            for direction, exit_obj in room.exits.items():
                if exit_obj.destination_id is None:
                    continue
                if exit_obj.status not in ["open", "one_way"]:
                    continue

                next_room = exit_obj.destination_id
                if next_room == to_room:
                    return path + [direction]

                if next_room not in visited:
                    visited.add(next_room)
                    queue.append((next_room, path + [direction]))

        return None

    # -------------------------------------------------------------------------
    # Object Operations
    # -------------------------------------------------------------------------

    def add_object(self, obj_id: int, name: str, room_id: Optional[int] = None,
                   is_takeable: bool = False) -> GameObject:
        """Add or update an object"""
        if obj_id in self.objects.objects:
            obj = self.objects.objects[obj_id]
            if is_takeable:
                obj.is_takeable = True
            return obj

        obj = GameObject(
            id=obj_id,
            name=name,
            initial_location=room_id,
            current_location=room_id,
            is_takeable=is_takeable,
            first_seen_run=self.current_run,
            first_seen_turn=self.current_turn,
        )
        self.objects.add_object(obj)

        # Track in room
        if room_id is not None and room_id in self.world_map.rooms:
            room = self.world_map.rooms[room_id]
            if obj_id not in room.objects_seen:
                room.objects_seen.append(obj_id)

        return obj

    def take_object(self, obj_id: int, command: str):
        """Record taking an object"""
        self.objects.move_object(
            obj_id, None, "taken",
            self.current_turn, self.current_run, command
        )
        if obj_id in self.objects.objects:
            self.objects.objects[obj_id].is_takeable = True
            self.objects.objects[obj_id].is_takeable_verified = True

    def drop_object(self, obj_id: int, room_id: int, command: str):
        """Record dropping an object"""
        self.objects.move_object(
            obj_id, room_id, "dropped",
            self.current_turn, self.current_run, command
        )

    def get_object_location(self, obj_id: int) -> Optional[int]:
        """Get current location of object (None = inventory)"""
        if obj_id not in self.objects.objects:
            return None
        obj = self.objects.objects[obj_id]
        return None if obj.in_inventory else obj.current_location

    def get_light_sources(self) -> List[GameObject]:
        """Get all known light sources"""
        return [obj for obj in self.objects.objects.values() if obj.is_light_source]

    # -------------------------------------------------------------------------
    # Action Operations
    # -------------------------------------------------------------------------

    def record_action(self, command: str, output: str, room_id: int,
                      result_type: str = "success", **kwargs) -> ActionAttempt:
        """Record an action attempt"""
        import uuid

        normalized = self._normalize_command(command)

        attempt = ActionAttempt(
            id=str(uuid.uuid4())[:8],
            command=command,
            normalized_command=normalized,
            run=self.current_run,
            turn=self.current_turn,
            room_id=room_id,
            inventory=[obj.id for obj in self.objects.get_inventory()],
            output=output,
            result_type=result_type,
            timestamp=datetime.now().isoformat(),
            **kwargs,
        )

        self.actions.add_attempt(attempt)
        self.current_turn += 1

        return attempt

    def _normalize_command(self, command: str) -> str:
        """Normalize command for comparison"""
        cmd = command.lower().strip()

        # Expand direction abbreviations
        abbrevs = {
            "n": "north", "s": "south", "e": "east", "w": "west",
            "ne": "northeast", "nw": "northwest",
            "se": "southeast", "sw": "southwest",
            "u": "up", "d": "down",
        }

        parts = cmd.split()
        if parts:
            if parts[0] in abbrevs:
                parts[0] = abbrevs[parts[0]]
            elif parts[0] == "go" and len(parts) > 1 and parts[1] in abbrevs:
                parts[1] = abbrevs[parts[1]]

        return " ".join(parts)

    def should_skip_command(self, command: str, room_id: int,
                            current_state: Dict = None) -> Tuple[bool, str]:
        """Check if we should skip this command"""
        normalized = self._normalize_command(command)
        return self.actions.should_skip(normalized, room_id, current_state)

    def mark_failed_command(self, command: str, room_id: int, reason: str,
                            retry_if: List[str] = None):
        """Mark command as not worth retrying"""
        normalized = self._normalize_command(command)
        self.actions.mark_do_not_retry(
            normalized, room_id, reason,
            unless=retry_if or [],
            run=self.current_run
        )

    def was_tried_here(self, command: str, room_id: int) -> Optional[ActionAttempt]:
        """Check if command was tried in this room"""
        normalized = self._normalize_command(command)
        return self.actions.was_tried(normalized, room_id)

    def get_successful_actions(self, room_id: int) -> List[ActionAttempt]:
        """Get successful actions in a room"""
        return [
            a for a in self.actions.get_attempts_in_room(room_id)
            if a.result_type in ["success", "partial"]
        ]

    def get_death_commands(self, room_id: int) -> List[str]:
        """Get commands that caused death in this room"""
        return self.actions.get_death_commands(room_id)

    # -------------------------------------------------------------------------
    # Query Interface for Solver
    # -------------------------------------------------------------------------

    def get_room(self, room_id: int) -> Optional[Room]:
        """Get room by ID"""
        return self.world_map.rooms.get(room_id)

    def get_all_rooms(self) -> List[Room]:
        """Get all discovered rooms"""
        return list(self.world_map.rooms.values())

    def get_room_count(self) -> int:
        """Get number of discovered rooms"""
        return len(self.world_map.rooms)

    def get_objects_in_room(self, room_id: int) -> List[GameObject]:
        """Get objects currently in a room"""
        return self.objects.get_objects_in_room(room_id)

    def get_inventory(self) -> List[GameObject]:
        """Get current inventory"""
        return self.objects.get_inventory()

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return {
            "game_name": self.game_name,
            "total_runs": self.world_map.total_runs,
            "rooms_discovered": len(self.world_map.rooms),
            "objects_discovered": len(self.objects.objects),
            "total_actions": len(self.actions.attempts),
            "do_not_retry_count": len(self.actions.do_not_retry),
            "death_records": len(self.actions.death_records),
            "puzzles_discovered": len(self.puzzles.puzzles),
            "puzzles_solved": len([p for p in self.puzzles.puzzles.values()
                                   if p.status == PuzzleStatus.SOLVED.value]),
            "solution_steps": len(self.solution.main_steps),
            "solution_branches": len(self.solution.branches),
            "random_events_known": len(self.randomness.events),
            "random_events_observed": sum(
                len(e.occurrences) for e in self.randomness.events.values()
            ),
            "variance_records": len(self.randomness.variances),
            "random_objects": len(self.randomness.get_random_objects()),
            "current_run": self.current_run,
            "current_turn": self.current_turn,
        }

    def get_context_for_ai(self, room_id: int) -> Dict[str, Any]:
        """Build context dict for AI/LLM queries"""
        room = self.get_room(room_id)
        if not room:
            return {}

        return {
            "room_id": room_id,
            "room_name": room.name,
            "room_description": room.description,
            "exits": {d: {"to": e.destination_id, "status": e.status}
                      for d, e in room.exits.items()},
            "objects_here": [obj.name for obj in self.get_objects_in_room(room_id)],
            "inventory": [obj.name for obj in self.get_inventory()],
            "death_commands": self.get_death_commands(room_id),
            "successful_actions": [a.command for a in self.get_successful_actions(room_id)],
            "total_rooms_known": len(self.world_map.rooms),
            "unexplored_exits": len(self.get_unexplored_exits()),
            "puzzles_here": [p.name for p in self.puzzles.get_puzzles_in_room(room_id)],
            "unsolved_puzzles": [p.name for p in self.puzzles.get_unsolved_puzzles()],
        }

    # -------------------------------------------------------------------------
    # Puzzle Operations
    # -------------------------------------------------------------------------

    def detect_puzzle(self, room_id: int, output: str, command: str = "") -> Optional[Puzzle]:
        """
        Analyze output for puzzle indicators and create puzzle if detected.

        Heuristics:
        - Locked doors/containers
        - Darkness requiring light
        - Blocked paths requiring items
        - Combat encounters
        - Sequence puzzles (buttons, levers)
        """
        import re
        import uuid

        output_lower = output.lower()
        puzzle = None

        # Locked door/container
        if re.search(r"(locked|won't open|need.+key|requires?.+key)", output_lower):
            puzzle_id = f"lock_{room_id}_{len(self.puzzles.puzzles)}"
            puzzle = Puzzle(
                id=puzzle_id,
                name=f"Locked obstacle in room {room_id}",
                description=output[:200],
                puzzle_type="locked_door",
                room_id=room_id,
                discovered_run=self.current_run,
                discovered_turn=self.current_turn,
            )
            puzzle.add_clue(output[:200], "failed_action", room_id,
                           self.current_run, self.current_turn, "high")

        # Darkness
        elif re.search(r"(too dark|pitch.?dark|can't see|darkness|need.+light)", output_lower):
            puzzle_id = f"dark_{room_id}"
            # Check if already exists
            if puzzle_id not in self.puzzles.puzzles:
                puzzle = Puzzle(
                    id=puzzle_id,
                    name=f"Darkness in room {room_id}",
                    description="Need a light source to proceed",
                    puzzle_type="darkness",
                    room_id=room_id,
                    discovered_run=self.current_run,
                    discovered_turn=self.current_turn,
                )
                self.world_map.has_darkness_mechanic = True

        # Blocked by creature/obstacle
        elif re.search(r"(troll|thief|guard|monster|blocks?|won't let)", output_lower):
            puzzle_id = f"obstacle_{room_id}_{len(self.puzzles.puzzles)}"
            puzzle = Puzzle(
                id=puzzle_id,
                name=f"Obstacle in room {room_id}",
                description=output[:200],
                puzzle_type="combat" if re.search(r"(troll|thief|monster)", output_lower) else "obstacle",
                room_id=room_id,
                discovered_run=self.current_run,
                discovered_turn=self.current_turn,
            )

        # Sequence/mechanism
        elif re.search(r"(button|lever|switch|mechanism|dial|combination)", output_lower):
            puzzle_id = f"mechanism_{room_id}_{len(self.puzzles.puzzles)}"
            puzzle = Puzzle(
                id=puzzle_id,
                name=f"Mechanism in room {room_id}",
                description=output[:200],
                puzzle_type="sequence",
                room_id=room_id,
                discovered_run=self.current_run,
                discovered_turn=self.current_turn,
            )

        if puzzle:
            self.puzzles.add_puzzle(puzzle)

        return puzzle

    def add_puzzle(self, name: str, description: str, room_id: int,
                   puzzle_type: str = "unknown") -> Puzzle:
        """Manually add a puzzle"""
        puzzle_id = f"{puzzle_type}_{room_id}_{len(self.puzzles.puzzles)}"
        puzzle = Puzzle(
            id=puzzle_id,
            name=name,
            description=description,
            puzzle_type=puzzle_type,
            room_id=room_id,
            discovered_run=self.current_run,
            discovered_turn=self.current_turn,
        )
        self.puzzles.add_puzzle(puzzle)
        return puzzle

    def add_clue_to_puzzle(self, puzzle_id: str, clue_text: str,
                           source: str = "observation", relevance: str = "medium"):
        """Add a clue to an existing puzzle"""
        puzzle = self.puzzles.get_puzzle(puzzle_id)
        if puzzle:
            puzzle.add_clue(clue_text, source, puzzle.room_id,
                           self.current_run, self.current_turn, relevance)

    def record_puzzle_attempt(self, puzzle_id: str, commands: List[str],
                              result: str, success: bool = False,
                              partial: bool = False):
        """Record an attempt to solve a puzzle"""
        puzzle = self.puzzles.get_puzzle(puzzle_id)
        if puzzle:
            puzzle.add_attempt(commands, result, success, partial,
                              self.current_run, self.current_turn)

    def mark_puzzle_solved(self, puzzle_id: str, commands: List[str]):
        """Mark a puzzle as solved with its solution"""
        self.puzzles.mark_solved(puzzle_id, commands,
                                 self.current_run, self.current_turn)

    def get_puzzles_in_room(self, room_id: int) -> List[Puzzle]:
        """Get all puzzles in a room"""
        return self.puzzles.get_puzzles_in_room(room_id)

    def get_solvable_puzzles(self) -> List[Puzzle]:
        """Get puzzles that can currently be attempted"""
        return self.puzzles.get_solvable_puzzles()

    # -------------------------------------------------------------------------
    # Solution Operations
    # -------------------------------------------------------------------------

    def add_solution_step(self, command: str, room_id: int = None,
                          success_indicators: List[str] = None,
                          source: str = "discovered") -> SolutionStep:
        """Add a step to the solution"""
        prereq = Prerequisites(in_room=room_id) if room_id else Prerequisites()
        return self.solution.add_step(
            command=command,
            prerequisites=prereq,
            success_indicators=success_indicators or [],
            source=source,
        )

    def add_solution_branch(self, branch_id: str, name: str,
                            trigger_pattern: str,
                            trigger_type: str = "text_match") -> SolutionBranch:
        """Add a conditional branch to the solution"""
        branch = SolutionBranch(
            id=branch_id,
            name=name,
            trigger_type=trigger_type,
            trigger_condition=trigger_pattern,
        )
        self.solution.add_branch(branch)
        return branch

    def get_next_solution_step(self, current_step_id: str = None) -> Optional[SolutionStep]:
        """Get next step in the solution"""
        return self.solution.get_next_step(current_step_id)

    def check_prerequisites(self, step: SolutionStep, room_id: int) -> Tuple[bool, str]:
        """Check if prerequisites for a step are met"""
        inventory_ids = [obj.id for obj in self.get_inventory()]
        inventory_names = [obj.name for obj in self.get_inventory()]
        solved_puzzles = [p.id for p in self.puzzles.puzzles.values()
                         if p.status == PuzzleStatus.SOLVED.value]

        return step.prerequisites.check(
            current_room=room_id,
            inventory=inventory_ids,
            inventory_names=inventory_names,
            solved_puzzles=solved_puzzles,
            flags=self.state_flags,
        )

    def set_flag(self, flag: str, value: bool = True):
        """Set a state flag"""
        self.state_flags[flag] = value

    def get_flag(self, flag: str) -> bool:
        """Get a state flag"""
        return self.state_flags.get(flag, False)

    def build_solution_from_transcript(self, successful_only: bool = True) -> Solution:
        """
        Build a solution from the action history.

        This extracts successful actions to create a replayable solution.
        """
        solution = Solution(
            game_name=self.game_name,
            game_file=str(self.game_file),
            game_checksum=self.game_checksum,
            created=datetime.now().isoformat(),
        )

        for attempt in self.actions.attempts:
            if successful_only and attempt.result_type not in ["success", "partial"]:
                continue

            # Skip if it's a redundant action (like failed movement)
            if attempt.result_type == "blocked":
                continue

            prereq = Prerequisites(in_room=attempt.room_id)
            step = SolutionStep(
                id=f"step_{len(solution.main_steps) + 1:03d}",
                command=attempt.command,
                prerequisites=prereq,
                expected_room=attempt.new_room_id,
                source="transcript",
            )
            solution.main_steps.append(step)

        solution.total_commands = len(solution.main_steps)
        return solution

    def export_solution(self) -> Dict[str, Any]:
        """Export solution as a dictionary for saving/sharing"""
        return self.solution.to_dict()

    def import_solution(self, solution_data: Dict[str, Any]):
        """Import a solution from a dictionary"""
        self.solution = Solution.from_dict(solution_data)

    # -------------------------------------------------------------------------
    # Randomness Operations
    # -------------------------------------------------------------------------

    def init_common_random_events(self):
        """Initialize common random event patterns from IF games"""
        events = create_common_random_events()
        for event in events:
            if event.id not in self.randomness.events:
                self.randomness.events[event.id] = event

    def check_for_random_event(self, output: str, room_id: int) -> Optional[RandomEvent]:
        """
        Check if game output indicates a random event occurred.

        Args:
            output: Game output text
            room_id: Current room ID

        Returns:
            RandomEvent if one was detected, None otherwise
        """
        return self.randomness.check_for_event(output, room_id)

    def record_random_event(self, event_id: str, room_id: int, turn: int,
                            output: str, response_used: List[str] = None):
        """
        Record an occurrence of a random event.

        Args:
            event_id: ID of the random event
            room_id: Room where event occurred
            turn: Turn number
            output: Game output when event occurred
            response_used: Commands used to respond to event
        """
        if event_id in self.randomness.events:
            self.randomness.events[event_id].add_occurrence(
                run=self.current_run,
                turn=turn,
                room_id=room_id,
                output=output,
            )

    def add_custom_random_event(self, event_id: str, name: str,
                                event_type: str, detection_pattern: str,
                                detection_rooms: List[int] = None) -> RandomEvent:
        """
        Add a custom random event pattern.

        Args:
            event_id: Unique identifier
            name: Human-readable name
            event_type: Type (wandering_npc, random_spawn, etc.)
            detection_pattern: Regex pattern to match
            detection_rooms: Rooms where event can occur (None = anywhere)

        Returns:
            The created RandomEvent
        """
        event = RandomEvent(
            id=event_id,
            name=name,
            event_type=event_type,
            detection_pattern=detection_pattern,
            detection_rooms=detection_rooms or [],
        )
        self.randomness.events[event_id] = event
        return event

    def take_snapshot(self, room_id: int, room_name: str,
                      object_locations: Dict[int, Optional[int]] = None) -> RunSnapshot:
        """
        Take a snapshot of game state for cross-run comparison.

        Args:
            room_id: Current room ID
            room_name: Current room name
            object_locations: Dict mapping object IDs to room IDs

        Returns:
            The created RunSnapshot
        """
        snapshot = RunSnapshot(
            run=self.current_run,
            turn=self.current_turn,
            room_id=room_id,
            room_name=room_name,
            object_locations=object_locations or {},
        )
        self.randomness.add_snapshot(snapshot)
        return snapshot

    def compare_runs(self, run1: int = None, run2: int = None) -> List[VarianceRecord]:
        """
        Compare two runs to detect random variance.

        Args:
            run1: First run number (default: second-to-last run)
            run2: Second run number (default: last run)

        Returns:
            List of variance records found
        """
        if run1 is None:
            run1 = max(1, self.current_run - 1)
        if run2 is None:
            run2 = self.current_run

        return self.randomness.detect_variance(run1, run2)

    def get_random_response(self, event: RandomEvent,
                            inventory_names: List[str] = None) -> List[str]:
        """
        Get the appropriate response commands for a random event.

        Args:
            event: The random event that occurred
            inventory_names: Items currently in inventory

        Returns:
            List of commands to execute as response
        """
        inventory_names = inventory_names or []

        # Check condition-based responses
        for condition, commands in event.responses.items():
            if condition == "default":
                continue

            # Check if condition is met
            # Format: "has <item>" or "in <room>"
            if condition.startswith("has "):
                item = condition[4:]
                if item.lower() in [n.lower() for n in inventory_names]:
                    return commands

        # Return default response if no conditions match
        return event.responses.get("default", [])

    def get_random_objects(self) -> List[int]:
        """Get list of object IDs with random locations"""
        return self.randomness.get_random_objects()

    def is_random_object(self, object_id: int) -> bool:
        """Check if an object has random location variance"""
        return object_id in self.randomness.get_random_objects()

    # -------------------------------------------------------------------------
    # Intelligence Layer - Strategic Queries
    # -------------------------------------------------------------------------

    def suggest_next_action(self, room_id: int) -> List[Dict[str, Any]]:
        """
        Suggest best next actions based on knowledge.

        Returns ranked list of suggestions with reasoning.
        """
        suggestions = []

        room = self.get_room(room_id)
        if not room:
            return [{"action": "look", "reason": "Unknown room - need to observe", "priority": 1}]

        # Priority 1: Explore unexplored exits
        for direction, exit_obj in room.exits.items():
            if exit_obj.destination_id is None and exit_obj.status != ExitStatus.BLOCKED.value:
                suggestions.append({
                    "action": direction,
                    "reason": f"Unexplored exit {direction}",
                    "priority": 1,
                    "type": "explore",
                })

        # Priority 2: Try to unblock blocked exits
        for direction, exit_obj in room.exits.items():
            if exit_obj.status == ExitStatus.BLOCKED.value and exit_obj.unlock_action:
                suggestions.append({
                    "action": exit_obj.unlock_action,
                    "reason": f"Unblock {direction} exit",
                    "priority": 2,
                    "type": "puzzle",
                })

        # Priority 3: Take untaken objects
        for obj in self.get_objects_in_room(room_id):
            if obj.is_takeable and not obj.in_inventory:
                suggestions.append({
                    "action": f"take {obj.name}",
                    "reason": f"Collect {obj.name}",
                    "priority": 3,
                    "type": "collect",
                })

        # Priority 4: Examine objects we haven't examined
        for obj in self.get_objects_in_room(room_id):
            examined = any(
                a.command.startswith(("examine", "look at", "x ")) and obj.name.lower() in a.command.lower()
                for a in self.actions.attempts if a.room_id == room_id
            )
            if not examined:
                suggestions.append({
                    "action": f"examine {obj.name}",
                    "reason": f"Investigate {obj.name}",
                    "priority": 4,
                    "type": "investigate",
                })

        # Priority 5: Work on solvable puzzles
        for puzzle in self.get_solvable_puzzles():
            if puzzle.room_id == room_id:
                # Suggest based on clues
                for clue in puzzle.clues[-3:]:  # Recent clues
                    suggestions.append({
                        "action": f"[solve puzzle: {puzzle.name}]",
                        "reason": f"Puzzle clue: {clue.text[:50]}",
                        "priority": 5,
                        "type": "puzzle",
                    })

        # Sort by priority
        suggestions.sort(key=lambda x: x["priority"])

        return suggestions[:10]  # Top 10 suggestions

    def get_exploration_status(self) -> Dict[str, Any]:
        """
        Get comprehensive exploration status.

        Returns progress metrics and what's left to explore.
        """
        total_rooms = len(self.world_map.rooms)
        unexplored_exits = self.get_unexplored_exits()
        blocked_exits = [
            (room_id, direction)
            for room_id, room in self.world_map.rooms.items()
            for direction, exit_obj in room.exits.items()
            if exit_obj.status == ExitStatus.BLOCKED.value
        ]

        return {
            "rooms_discovered": total_rooms,
            "unexplored_exits": len(unexplored_exits),
            "unexplored_details": unexplored_exits[:20],  # First 20
            "blocked_exits": len(blocked_exits),
            "blocked_details": [
                {"room": rid, "direction": d} for rid, d in blocked_exits
            ],
            "objects_found": len(self.objects.objects),
            "objects_in_inventory": len(self.get_inventory()),
            "puzzles_discovered": len(self.puzzles.puzzles),
            "puzzles_solved": len([p for p in self.puzzles.puzzles.values()
                                   if p.status == PuzzleStatus.SOLVED.value]),
            "commands_tried": len(self.actions.attempts),
            "unique_commands": len(self.actions.by_command),
            "do_not_retry_count": len(self.actions.do_not_retry),
            "death_commands_known": len(self.actions.death_records),
        }

    def find_path_to_unexplored(self, from_room: int) -> Optional[List[str]]:
        """
        Find shortest path from current room to nearest unexplored exit.

        Returns list of direction commands, or None if no path found.
        """
        unexplored = self.get_unexplored_exits()
        if not unexplored:
            return None

        # Find shortest path to any room with unexplored exit
        # unexplored is a list of tuples: (room_id, direction)
        target_rooms = set(room_id for room_id, _ in unexplored)

        shortest_path = None
        for target in target_rooms:
            path = self.find_path(from_room, target)
            if path and (shortest_path is None or len(path) < len(shortest_path)):
                shortest_path = path

        return shortest_path

    def get_required_items_for_room(self, room_id: int) -> List[str]:
        """
        Analyze what items might be needed to progress from a room.

        Based on blocked exits and puzzle clues.
        """
        required = []

        room = self.get_room(room_id)
        if not room:
            return required

        # Check blocked exits
        for direction, exit_obj in room.exits.items():
            if exit_obj.status == ExitStatus.BLOCKED.value:
                if "key" in (exit_obj.blocker or "").lower():
                    required.append("key")
                if "light" in (exit_obj.blocker or "").lower():
                    required.append("light source")

        # Check puzzle clues
        for puzzle in self.puzzles.get_puzzles_in_room(room_id):
            for clue in puzzle.clues:
                clue_lower = clue.text.lower()
                if "key" in clue_lower:
                    required.append("key")
                if "lamp" in clue_lower or "light" in clue_lower:
                    required.append("light source")
                if "sword" in clue_lower or "weapon" in clue_lower:
                    required.append("weapon")

        return list(set(required))

    # -------------------------------------------------------------------------
    # Intelligence Layer - Learning & Verification
    # -------------------------------------------------------------------------

    def verify_solution_step(self, step_index: int, output: str) -> Dict[str, Any]:
        """
        Verify a solution step worked as expected.

        Updates verification count and confidence.
        """
        if step_index >= len(self.solution.main_steps):
            return {"verified": False, "reason": "invalid step index"}

        step = self.solution.main_steps[step_index]

        # Check success indicators
        success = False
        for indicator in step.success_indicators:
            if indicator.lower() in output.lower():
                success = True
                break

        # Check failure indicators
        if step.failure_indicators:
            for indicator in step.failure_indicators:
                if indicator.lower() in output.lower():
                    success = False
                    break

        # Update verification
        if success:
            step.verified_runs += 1
            step.confidence = min(1.0, step.confidence + 0.1)
        else:
            step.confidence = max(0.0, step.confidence - 0.2)

        return {
            "verified": success,
            "step_id": step.id,
            "command": step.command,
            "new_confidence": step.confidence,
            "verified_runs": step.verified_runs,
        }

    def learn_from_transcript(self) -> Dict[str, Any]:
        """
        Analyze action transcript to learn patterns and improve knowledge.

        Returns summary of what was learned.
        """
        learned = {
            "new_prerequisites": [],
            "confirmed_patterns": [],
            "new_do_not_retry": [],
        }

        # Analyze sequences that led to success
        for i, attempt in enumerate(self.actions.attempts):
            if attempt.result_type == "success" and attempt.room_changed:
                # Room transition - check if there was a prerequisite action
                if i > 0:
                    prev = self.actions.attempts[i - 1]
                    if prev.room_id == attempt.room_id and prev.result_type == "success":
                        # Previous action might be prerequisite
                        learned["new_prerequisites"].append({
                            "for_command": attempt.command,
                            "prerequisite": prev.command,
                            "room": attempt.room_id,
                        })

        # Find patterns in blocked actions that later succeeded
        blocked_commands = {}
        for attempt in self.actions.attempts:
            key = (attempt.normalized_command, attempt.room_id)
            if attempt.result_type == "blocked":
                if key not in blocked_commands:
                    blocked_commands[key] = {"first_blocked": attempt, "later_success": None}
            elif attempt.result_type == "success":
                if key in blocked_commands and blocked_commands[key]["later_success"] is None:
                    blocked_commands[key]["later_success"] = attempt

        # Analyze what changed between blocked and success
        for key, data in blocked_commands.items():
            if data["later_success"]:
                blocked = data["first_blocked"]
                success = data["later_success"]

                # Check inventory difference
                inv_diff = set(success.inventory) - set(blocked.inventory)
                if inv_diff:
                    learned["confirmed_patterns"].append({
                        "command": blocked.command,
                        "room": blocked.room_id,
                        "required_items": list(inv_diff),
                        "pattern": "item_required",
                    })

        return learned

    def discover_prerequisites(self) -> List[Dict[str, Any]]:
        """
        Analyze action history to discover command prerequisites.

        Finds patterns like "open X" before "enter X" or
        "light lamp" before navigating dark areas.
        """
        prerequisites = []

        # Group successful room transitions
        transitions = []
        for attempt in self.actions.attempts:
            if attempt.room_changed and attempt.new_room_id:
                transitions.append(attempt)

        # Look for commands that consistently precede certain transitions
        command_sequences = {}
        for i, trans in enumerate(transitions):
            # Look at commands in same room before this transition
            preceding = []
            for j in range(i - 1, max(0, i - 5), -1):
                prev = self.actions.attempts[j]
                if prev.room_id == trans.room_id:
                    preceding.append(prev.normalized_command)
                else:
                    break

            if preceding:
                key = (trans.normalized_command, trans.room_id)
                if key not in command_sequences:
                    command_sequences[key] = []
                command_sequences[key].append(tuple(preceding))

        # Find consistent patterns
        for (cmd, room), sequences in command_sequences.items():
            if len(sequences) >= 2:
                # Find commands that appear in all sequences
                common = set(sequences[0])
                for seq in sequences[1:]:
                    common &= set(seq)

                if common:
                    prerequisites.append({
                        "command": cmd,
                        "room": room,
                        "required_commands": list(common),
                        "occurrences": len(sequences),
                    })

        return prerequisites

    def get_ai_prompt_context(self, room_id: int, task: str = "explore") -> str:
        """
        Build a comprehensive prompt context for AI integration.

        Args:
            room_id: Current room
            task: "explore", "solve_puzzle", "find_item", etc.

        Returns:
            Formatted string suitable for LLM prompting
        """
        room = self.get_room(room_id)
        if not room:
            return "Error: Unknown room"

        context_parts = [
            f"## Current State",
            f"Room: {room.name} (ID: {room_id})",
            f"Description: {room.description[:300]}",
            "",
            f"## Exits",
        ]

        for direction, exit_obj in room.exits.items():
            status = exit_obj.status
            dest = f" -> room {exit_obj.destination_id}" if exit_obj.destination_id else " -> unknown"
            context_parts.append(f"  {direction}: {status}{dest}")

        # Objects
        objects_here = self.get_objects_in_room(room_id)
        if objects_here:
            context_parts.append("")
            context_parts.append("## Objects Here")
            for obj in objects_here:
                takeable = "(takeable)" if obj.is_takeable else "(fixed)"
                context_parts.append(f"  - {obj.name} {takeable}")

        # Inventory
        inventory = self.get_inventory()
        if inventory:
            context_parts.append("")
            context_parts.append("## Inventory")
            for obj in inventory:
                context_parts.append(f"  - {obj.name}")

        # Puzzles
        puzzles = self.puzzles.get_puzzles_in_room(room_id)
        if puzzles:
            context_parts.append("")
            context_parts.append("## Known Puzzles Here")
            for p in puzzles:
                context_parts.append(f"  - {p.name} ({p.status}): {p.description[:100]}")

        # Commands to avoid
        death_cmds = self.get_death_commands(room_id)
        do_not_retry = [
            dnr for dnr in self.actions.do_not_retry
            if dnr.room_id == room_id
        ]

        if death_cmds or do_not_retry:
            context_parts.append("")
            context_parts.append("## Commands to AVOID")
            for cmd in death_cmds:
                context_parts.append(f"  - {cmd} (causes death)")
            for dnr in do_not_retry[:5]:
                context_parts.append(f"  - {dnr.command} ({dnr.reason})")

        # Suggestions
        suggestions = self.suggest_next_action(room_id)
        if suggestions:
            context_parts.append("")
            context_parts.append("## Suggested Actions")
            for s in suggestions[:5]:
                context_parts.append(f"  - {s['action']}: {s['reason']}")

        # Task-specific context
        context_parts.append("")
        context_parts.append(f"## Task: {task}")
        if task == "explore":
            unexplored = len(self.get_unexplored_exits())
            context_parts.append(f"  {unexplored} unexplored exits remaining")
        elif task == "solve_puzzle":
            unsolved = self.puzzles.get_unsolved_puzzles()
            context_parts.append(f"  {len(unsolved)} unsolved puzzles")

        return "\n".join(context_parts)

    def export_knowledge_summary(self) -> Dict[str, Any]:
        """
        Export a summary of all knowledge for external use.

        Suitable for saving state, debugging, or AI analysis.
        """
        return {
            "meta": {
                "game_name": self.game_name,
                "game_checksum": self.game_checksum,
                "total_runs": self.world_map.total_runs,
                "current_run": self.current_run,
                "current_turn": self.current_turn,
            },
            "world": {
                "rooms": len(self.world_map.rooms),
                "starting_room": self.world_map.starting_room_id,
                "has_darkness": self.world_map.has_darkness_mechanic,
                "has_maze": self.world_map.has_maze,
                "has_wandering_npc": self.world_map.has_wandering_npc,
            },
            "exploration": self.get_exploration_status(),
            "objects": {
                "total": len(self.objects.objects),
                "in_inventory": len(self.get_inventory()),
                "takeable": len([o for o in self.objects.objects.values() if o.is_takeable]),
            },
            "puzzles": {
                "total": len(self.puzzles.puzzles),
                "solved": len([p for p in self.puzzles.puzzles.values()
                              if p.status == PuzzleStatus.SOLVED.value]),
                "in_progress": len([p for p in self.puzzles.puzzles.values()
                                   if p.status == PuzzleStatus.WORKING.value]),
            },
            "solution": {
                "steps": len(self.solution.main_steps),
                "branches": len(self.solution.branches),
                "completeness": self.solution.completeness,
            },
            "randomness": {
                "events_known": len(self.randomness.events),
                "events_observed": sum(len(e.occurrences) for e in self.randomness.events.values()),
                "random_objects": len(self.randomness.get_random_objects()),
            },
        }


# =============================================================================
# Solution Execution Engine
# =============================================================================

class SolutionExecutor:
    """
    Executes a solution step by step, handling prerequisites and branches.

    Usage:
        executor = SolutionExecutor(kb, walker)
        while executor.has_next():
            step = executor.get_current_step()
            result = executor.execute_step()
            if result.success:
                executor.advance()
            else:
                # Handle failure
    """

    def __init__(self, kb: KnowledgeBase, walker=None):
        """
        Initialize executor.

        Args:
            kb: KnowledgeBase with solution to execute
            walker: Optional GameWalker for executing commands
        """
        self.kb = kb
        self.walker = walker
        self.solution = kb.solution

        # Execution state
        self.current_step_index = 0
        self.current_branch: Optional[SolutionBranch] = None
        self.branch_step_index = 0

        # History
        self.executed_steps: List[str] = []
        self.failed_steps: List[Tuple[str, str]] = []  # (step_id, reason)
        self.branch_history: List[str] = []  # Branch IDs taken

    def reset(self):
        """Reset execution to beginning"""
        self.current_step_index = 0
        self.current_branch = None
        self.branch_step_index = 0
        self.executed_steps = []
        self.failed_steps = []
        self.branch_history = []

    def has_next(self) -> bool:
        """Check if there are more steps to execute"""
        if self.current_branch:
            return self.branch_step_index < len(self.current_branch.steps)
        return self.current_step_index < len(self.solution.main_steps)

    def get_current_step(self) -> Optional[SolutionStep]:
        """Get current step without advancing"""
        if self.current_branch:
            if self.branch_step_index < len(self.current_branch.steps):
                return self.current_branch.steps[self.branch_step_index]
            return None

        if self.current_step_index < len(self.solution.main_steps):
            return self.solution.main_steps[self.current_step_index]
        return None

    def check_current_prerequisites(self, current_room: int) -> Tuple[bool, str]:
        """Check if current step's prerequisites are met"""
        step = self.get_current_step()
        if not step:
            return False, "no current step"
        return self.kb.check_prerequisites(step, current_room)

    def execute_step(self, current_room: int = None) -> Dict[str, Any]:
        """
        Execute current step if using walker.

        Returns dict with:
        - success: bool
        - output: str (game output)
        - step_id: str
        - advanced: bool (did we move to next step)
        - branch_taken: Optional[str]
        """
        step = self.get_current_step()
        if not step:
            return {"success": False, "output": "No step to execute", "step_id": None}

        result = {
            "success": False,
            "output": "",
            "step_id": step.id,
            "advanced": False,
            "branch_taken": None,
        }

        if not self.walker:
            return {"success": False, "output": "No walker attached", "step_id": step.id}

        # Check prerequisites
        room = current_room or self.walker.current_room_id
        prereq_ok, reason = self.check_current_prerequisites(room)
        if not prereq_ok:
            result["output"] = f"Prerequisites not met: {reason}"
            return result

        # Execute the command
        exec_result = self.walker.try_command(step.command, skip_if_tried=False)
        result["output"] = exec_result.output

        # Check if successful
        if step.check_success(exec_result.output):
            result["success"] = True
            self.executed_steps.append(step.id)
            step.verified_runs += 1

            # Check for branch trigger
            branch = self.solution.check_for_branch(exec_result.output, self.kb.state_flags)
            if branch:
                result["branch_taken"] = branch.id
                self.enter_branch(branch)
            else:
                self.advance()
                result["advanced"] = True
        else:
            self.failed_steps.append((step.id, exec_result.output[:100]))

            # Handle failure according to step's on_failure
            if step.on_failure == "skip":
                self.advance()
                result["advanced"] = True
            elif step.on_failure.startswith("branch:"):
                branch_id = step.on_failure[7:]
                if branch_id in self.solution.branches:
                    self.enter_branch(self.solution.branches[branch_id])
                    result["branch_taken"] = branch_id

        return result

    def advance(self):
        """Advance to next step"""
        if self.current_branch:
            self.branch_step_index += 1
            # Check if branch is complete
            if self.branch_step_index >= len(self.current_branch.steps):
                self.exit_branch()
        else:
            self.current_step_index += 1

    def enter_branch(self, branch: SolutionBranch):
        """Enter a conditional branch"""
        self.current_branch = branch
        self.branch_step_index = 0
        self.branch_history.append(branch.id)

    def exit_branch(self):
        """Exit current branch and rejoin main path"""
        if self.current_branch and self.current_branch.rejoin_at:
            # Find the rejoin step
            for i, step in enumerate(self.solution.main_steps):
                if step.id == self.current_branch.rejoin_at:
                    self.current_step_index = i
                    break
        self.current_branch = None
        self.branch_step_index = 0

    def skip_to_step(self, step_id: str) -> bool:
        """Skip to a specific step by ID"""
        for i, step in enumerate(self.solution.main_steps):
            if step.id == step_id:
                self.current_step_index = i
                self.current_branch = None
                return True
        return False

    def get_progress(self) -> Dict[str, Any]:
        """Get execution progress"""
        total = len(self.solution.main_steps)
        executed = len(self.executed_steps)
        return {
            "total_steps": total,
            "executed_steps": executed,
            "failed_steps": len(self.failed_steps),
            "progress_percent": (executed / total * 100) if total > 0 else 0,
            "current_step": self.get_current_step().id if self.get_current_step() else None,
            "in_branch": self.current_branch.id if self.current_branch else None,
            "branches_taken": self.branch_history,
        }

    def get_remaining_steps(self) -> List[SolutionStep]:
        """Get list of remaining steps"""
        if self.current_branch:
            return self.current_branch.steps[self.branch_step_index:]

        remaining = self.solution.main_steps[self.current_step_index:]

        # Add any rejoin steps if in branch
        return remaining

    def validate_solution(self) -> List[str]:
        """
        Validate the solution structure.

        Returns list of issues found.
        """
        issues = []

        # Check for empty solution
        if not self.solution.main_steps:
            issues.append("Solution has no steps")
            return issues

        # Check step IDs are unique
        step_ids = set()
        for step in self.solution.main_steps:
            if step.id in step_ids:
                issues.append(f"Duplicate step ID: {step.id}")
            step_ids.add(step.id)

        for branch in self.solution.branches.values():
            for step in branch.steps:
                if step.id in step_ids:
                    issues.append(f"Duplicate step ID in branch {branch.id}: {step.id}")
                step_ids.add(step.id)

        # Check branch rejoin points exist
        for branch in self.solution.branches.values():
            if branch.rejoin_at:
                if branch.rejoin_at not in step_ids:
                    issues.append(f"Branch {branch.id} rejoin point {branch.rejoin_at} not found")

        # Check on_failure branch references
        for step in self.solution.main_steps:
            if step.on_failure.startswith("branch:"):
                branch_id = step.on_failure[7:]
                if branch_id not in self.solution.branches:
                    issues.append(f"Step {step.id} references unknown branch: {branch_id}")

        return issues


# =============================================================================
# Randomness Detection and Handling
# =============================================================================

@dataclass
class RandomEvent:
    """A detected random event in the game"""
    id: str
    name: str
    event_type: str                             # "wandering_npc", "random_spawn", "maze_shuffle", "random_text"

    # Detection
    detection_pattern: str                      # Regex pattern that triggers this event
    detection_rooms: List[int] = field(default_factory=list)  # Rooms where this can occur (empty = anywhere)

    # Occurrences
    occurrences: List[Dict[str, Any]] = field(default_factory=list)  # [{run, turn, room, output}, ...]
    first_seen_run: int = 0
    last_seen_run: int = 0

    # Response strategies
    responses: Dict[str, List[str]] = field(default_factory=dict)  # {condition: [commands]}
    successful_response: Optional[str] = None   # Which condition's response worked

    def add_occurrence(self, run: int, turn: int, room_id: int, output: str):
        """Record an occurrence of this event"""
        self.occurrences.append({
            "run": run,
            "turn": turn,
            "room_id": room_id,
            "output": output[:200],
        })
        self.last_seen_run = run
        if self.first_seen_run == 0:
            self.first_seen_run = run

    def add_response(self, condition: str, commands: List[str]):
        """Add a response strategy for this event"""
        self.responses[condition] = commands

    def get_response(self, inventory_names: List[str], flags: Dict[str, bool]) -> Optional[List[str]]:
        """Get appropriate response based on current state"""
        for condition, commands in self.responses.items():
            if condition == "default":
                continue

            # Check condition
            if condition.startswith("has "):
                item = condition[4:]
                if item.lower() in [n.lower() for n in inventory_names]:
                    return commands
            elif condition in flags and flags[condition]:
                return commands

        # Return default if no specific condition matched
        return self.responses.get("default")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "event_type": self.event_type,
            "detection_pattern": self.detection_pattern,
            "detection_rooms": self.detection_rooms,
            "occurrences": self.occurrences,
            "first_seen_run": self.first_seen_run,
            "last_seen_run": self.last_seen_run,
            "responses": self.responses,
            "successful_response": self.successful_response,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RandomEvent":
        return cls(**data)


@dataclass
class RunSnapshot:
    """Snapshot of game state at a point in a run"""
    run: int
    turn: int
    room_id: int
    room_name: str

    # Object locations at this point
    object_locations: Dict[int, Optional[int]] = field(default_factory=dict)  # obj_id -> room_id (None = inventory)

    # Observations
    room_description: str = ""
    output: str = ""

    def to_dict(self) -> dict:
        return {
            "run": self.run,
            "turn": self.turn,
            "room_id": self.room_id,
            "room_name": self.room_name,
            "object_locations": {str(k): v for k, v in self.object_locations.items()},
            "room_description": self.room_description,
            "output": self.output,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RunSnapshot":
        obj_locs = {int(k): v for k, v in data.pop("object_locations", {}).items()}
        return cls(object_locations=obj_locs, **data)


@dataclass
class VarianceRecord:
    """Record of detected variance between runs"""
    id: str
    variance_type: str                          # "object_location", "room_content", "npc_position", "maze_connection"

    # What varies
    subject_id: Optional[int] = None            # Object or room ID
    subject_name: str = ""

    # Observed values
    observed_values: List[Dict[str, Any]] = field(default_factory=list)  # [{run, value, context}, ...]

    # Analysis
    is_random: bool = True                      # Confirmed random vs just unexplored
    affects_solution: bool = False              # Does this affect the solution?
    notes: str = ""

    def add_observation(self, run: int, value: Any, context: str = ""):
        """Record an observed value"""
        self.observed_values.append({
            "run": run,
            "value": value,
            "context": context,
        })

    def get_unique_values(self) -> List[Any]:
        """Get list of unique values observed"""
        seen = set()
        unique = []
        for obs in self.observed_values:
            v = str(obs["value"])
            if v not in seen:
                seen.add(v)
                unique.append(obs["value"])
        return unique

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "VarianceRecord":
        return cls(**data)


@dataclass
class RandomnessTracker:
    """Track random elements across runs"""

    # Random events (thief, etc.)
    events: Dict[str, RandomEvent] = field(default_factory=dict)

    # Variance records
    variances: Dict[str, VarianceRecord] = field(default_factory=dict)

    # Per-run snapshots for comparison
    run_snapshots: Dict[int, List[RunSnapshot]] = field(default_factory=dict)

    # Known random patterns
    known_random_patterns: List[str] = field(default_factory=list)

    def add_event(self, event: RandomEvent):
        """Add a random event"""
        self.events[event.id] = event

    def add_variance(self, variance: VarianceRecord):
        """Add a variance record"""
        self.variances[variance.id] = variance

    def add_snapshot(self, snapshot: RunSnapshot):
        """Add a run snapshot"""
        if snapshot.run not in self.run_snapshots:
            self.run_snapshots[snapshot.run] = []
        self.run_snapshots[snapshot.run].append(snapshot)

    def check_for_event(self, output: str, room_id: int) -> Optional[RandomEvent]:
        """Check if output matches any known random event"""
        import re
        for event in self.events.values():
            # Check room restriction
            if event.detection_rooms and room_id not in event.detection_rooms:
                continue

            # Check pattern
            if re.search(event.detection_pattern, output, re.IGNORECASE):
                return event

        return None

    def detect_variance(self, run1: int, run2: int) -> List[VarianceRecord]:
        """Compare two runs to detect variance"""
        if run1 not in self.run_snapshots or run2 not in self.run_snapshots:
            return []

        variances = []
        snapshots1 = {s.room_id: s for s in self.run_snapshots[run1]}
        snapshots2 = {s.room_id: s for s in self.run_snapshots[run2]}

        # Compare rooms that appear in both runs
        common_rooms = set(snapshots1.keys()) & set(snapshots2.keys())

        for room_id in common_rooms:
            s1 = snapshots1[room_id]
            s2 = snapshots2[room_id]

            # Compare object locations
            all_objects = set(s1.object_locations.keys()) | set(s2.object_locations.keys())
            for obj_id in all_objects:
                loc1 = s1.object_locations.get(obj_id)
                loc2 = s2.object_locations.get(obj_id)

                if loc1 != loc2:
                    var_id = f"obj_{obj_id}_location"
                    if var_id not in self.variances:
                        variance = VarianceRecord(
                            id=var_id,
                            variance_type="object_location",
                            subject_id=obj_id,
                        )
                        variance.add_observation(run1, loc1, f"room {room_id}")
                        variance.add_observation(run2, loc2, f"room {room_id}")
                        self.variances[var_id] = variance
                        variances.append(variance)
                    else:
                        self.variances[var_id].add_observation(run2, loc2, f"room {room_id}")

        return variances

    def get_random_objects(self) -> List[int]:
        """Get list of object IDs that have random locations"""
        return [
            v.subject_id for v in self.variances.values()
            if v.variance_type == "object_location" and v.subject_id is not None
        ]

    def to_dict(self) -> dict:
        return {
            "events": {k: v.to_dict() for k, v in self.events.items()},
            "variances": {k: v.to_dict() for k, v in self.variances.items()},
            "run_snapshots": {
                str(k): [s.to_dict() for s in v]
                for k, v in self.run_snapshots.items()
            },
            "known_random_patterns": self.known_random_patterns,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RandomnessTracker":
        tracker = cls()
        tracker.events = {k: RandomEvent.from_dict(v) for k, v in data.get("events", {}).items()}
        tracker.variances = {k: VarianceRecord.from_dict(v) for k, v in data.get("variances", {}).items()}
        tracker.run_snapshots = {
            int(k): [RunSnapshot.from_dict(s) for s in v]
            for k, v in data.get("run_snapshots", {}).items()
        }
        tracker.known_random_patterns = data.get("known_random_patterns", [])
        return tracker


# Common random event patterns for IF games
COMMON_RANDOM_EVENTS = [
    {
        "id": "thief_encounter",
        "name": "Thief Encounter",
        "event_type": "wandering_npc",
        "detection_pattern": r"thief|someone carrying a large bag|figure holding a bag",
        "responses": {
            "has sword": ["kill thief with sword"],
            "default": ["drop valuables", "wait", "wait", "take valuables"],
        },
    },
    {
        "id": "grue_warning",
        "name": "Grue Warning",
        "event_type": "random_text",
        "detection_pattern": r"grue|eaten by|lurking in the dark",
        "responses": {
            "has lamp": ["light lamp"],
            "default": ["go back"],  # Try to escape
        },
    },
    {
        "id": "combat_start",
        "name": "Combat Initiated",
        "event_type": "wandering_npc",
        "detection_pattern": r"attacks?|strikes|swings at|lunges",
        "responses": {
            "has sword": ["kill enemy with sword", "attack enemy"],
            "default": ["flee", "run"],
        },
    },
]


def create_common_random_events() -> List[RandomEvent]:
    """Create RandomEvent objects for common IF random events"""
    events = []
    for data in COMMON_RANDOM_EVENTS:
        event = RandomEvent(
            id=data["id"],
            name=data["name"],
            event_type=data["event_type"],
            detection_pattern=data["detection_pattern"],
        )
        for condition, commands in data.get("responses", {}).items():
            event.add_response(condition, commands)
        events.append(event)
    return events

# ZWalker Knowledge Base Schema

## Overview

This document defines the data structures for a persistent knowledge base that tracks game world state like a human player would. The schema supports:

- Multi-run persistence (learn across attempts)
- Random element detection and handling
- Failed attempt tracking (don't repeat mistakes)
- Prerequisite discovery (X requires Y)
- Branching solutions for variable game states

## Storage Format

Primary: JSON files per game (human-readable, git-friendly)
Optional: SQLite for complex queries during solving

```
knowledge/
├── zork1/
│   ├── world.json          # Rooms, connections, objects
│   ├── actions.json        # Everything tried
│   ├── puzzles.json        # Puzzle state and clues
│   ├── solutions.json      # Working solution branches
│   └── runs/
│       ├── run_001.json    # Per-run snapshots
│       └── run_002.json
└── trinity/
    └── ...
```

---

## Core Data Structures

### 1. WorldMap

The complete discovered map of the game world.

```python
@dataclass
class Room:
    id: int                          # Z-machine object number (stable identifier)
    name: str                        # Room name from game
    description: str                 # Full description text
    first_seen_run: int              # Which run we discovered this
    first_seen_turn: int             # What turn number

    # Connections
    exits: Dict[str, Exit]           # direction -> Exit object

    # Room properties discovered
    is_dark: bool = False            # Requires light source
    is_deadly: bool = False          # Can die here
    death_reasons: List[str] = []    # How you can die
    is_maze: bool = False            # Part of a maze
    maze_group: Optional[str] = None # Which maze it belongs to

    # Random flags
    varies_between_runs: bool = False
    variance_notes: str = ""


@dataclass
class Exit:
    direction: str                   # "north", "up", "enter", etc.
    destination_id: Optional[int]    # Room ID if known, None if blocked/unknown

    # Exit properties
    status: str                      # "open", "locked", "blocked", "one_way", "conditional"
    blocker: Optional[str] = None    # What blocks it ("door", "troll", "darkness")
    unlock_action: Optional[str] = None  # How to open ("unlock door with key")
    unlock_verified: bool = False    # Have we confirmed this works?

    # One-way detection
    is_one_way: bool = False         # Can't return this way
    return_path: Optional[List[str]] = None  # Alternative route back

    # Randomness
    varies_between_runs: bool = False
    variance_type: str = ""          # "shuffled", "random_destination", etc.


@dataclass
class WorldMap:
    game_name: str
    game_file: str
    game_checksum: str               # Verify same game version

    rooms: Dict[int, Room]           # room_id -> Room
    starting_room_id: int

    # Global properties
    has_darkness_mechanic: bool = False
    has_maze: bool = False
    has_thief_or_wanderer: bool = False

    # Discovery stats
    total_runs: int = 0
    rooms_discovered_by_run: Dict[int, List[int]] = {}  # run -> [room_ids]

    # Metadata
    last_updated: str                # ISO timestamp
    schema_version: str = "1.0"
```

### 2. ObjectTracker

Track every object in the game: location, properties, and behavior.

```python
@dataclass
class GameObject:
    id: int                          # Z-machine object number
    name: str                        # Primary name
    aliases: List[str] = []          # Other names that work

    # Location tracking
    initial_location: Optional[int]  # Room ID where first found (None = carried/nowhere)
    current_location: Optional[int]  # Where it is now (None = in inventory or destroyed)
    location_history: List[LocationChange] = []

    # Properties discovered through interaction
    is_takeable: bool = False
    is_takeable_verified: bool = False   # Have we tried?
    take_failure_reason: str = ""        # "too heavy", "fixed in place", etc.

    is_container: bool = False
    contains: List[int] = []             # Object IDs inside
    is_openable: bool = False
    is_open: bool = False
    is_locked: bool = False
    unlock_key: Optional[int] = None     # Object ID of key

    is_wearable: bool = False
    is_edible: bool = False
    is_readable: bool = False
    read_text: str = ""

    is_light_source: bool = False
    is_lit: bool = False
    light_duration: Optional[int] = None  # Turns until depleted

    is_weapon: bool = False
    weapon_effectiveness: Dict[str, str] = {}  # enemy -> result

    # Special properties
    is_valuable: bool = False            # Treasure/scoring item
    point_value: int = 0

    is_consumable: bool = False          # Gets used up
    is_destroyed: bool = False           # No longer exists

    # Randomness
    spawn_is_random: bool = False        # Location varies per run
    spawn_locations_seen: List[int] = [] # All locations observed
    behavior_is_random: bool = False     # Does random things

    # Discovery metadata
    first_seen_run: int
    first_seen_turn: int
    interaction_count: int = 0


@dataclass
class LocationChange:
    from_location: Optional[int]
    to_location: Optional[int]
    cause: str                       # "taken", "dropped", "moved_by_npc", "destroyed"
    turn: int
    run: int
    command: str                     # What caused it


@dataclass
class ObjectTracker:
    objects: Dict[int, GameObject]   # object_id -> GameObject

    # Quick lookups
    objects_by_room: Dict[int, List[int]]      # room_id -> [object_ids]
    takeable_objects: List[int]
    light_sources: List[int]
    containers: List[int]

    # Inventory tracking
    max_inventory_seen: int = 0      # Max items carried at once
    inventory_limit_hit: bool = False

    # Random object tracking
    random_spawn_objects: List[int]  # Objects that move between runs
```

### 3. ActionLog

Every action ever attempted, with full context and results.

```python
@dataclass
class ActionAttempt:
    id: str                          # UUID for reference
    command: str                     # Exact command entered
    normalized_command: str          # Canonical form ("go north" -> "north")

    # Context when attempted
    run: int
    turn: int
    room_id: int
    inventory: List[int]             # Object IDs held
    relevant_state: Dict[str, Any]   # Other relevant state (lamp lit, door open, etc.)

    # Result
    output: str                      # Game's response
    result_type: str                 # See ResultType enum below

    # Parsed effects
    room_changed: bool = False
    new_room_id: Optional[int] = None
    objects_taken: List[int] = []
    objects_dropped: List[int] = []
    objects_destroyed: List[int] = []
    state_changes: List[str] = []    # ["lamp is now lit", "door is now open"]
    score_change: int = 0

    # Learning
    prerequisites_discovered: List[str] = []  # "requires lamp", "needs key"
    unlocks_discovered: List[str] = []        # "this opens the grate"

    # Metadata
    timestamp: str


class ResultType(Enum):
    SUCCESS = "success"              # Command worked as expected
    PARTIAL = "partial"              # Partially worked
    FAILURE = "failure"              # Didn't work, no harm
    BLOCKED = "blocked"              # Prevented by something specific
    DEATH = "death"                  # Player died
    ALREADY_DONE = "already_done"    # "It's already open"
    NOT_HERE = "not_here"            # Object/direction not present
    NONSENSE = "nonsense"            # Parser didn't understand
    NO_EFFECT = "no_effect"          # Worked but nothing happened


@dataclass
class ActionPattern:
    """Generalized pattern from multiple attempts"""
    pattern: str                     # "take {object}" or "unlock {container} with {key}"

    # When it works
    success_conditions: List[str]    # ["object is takeable", "object is in room"]
    success_examples: List[str]      # [attempt_id, ...]

    # When it fails
    failure_conditions: Dict[str, List[str]]  # {failure_reason: [conditions]}
    failure_examples: Dict[str, List[str]]    # {failure_reason: [attempt_ids]}

    # Prerequisites discovered
    requires: List[str]              # ["light source", "specific object"]


@dataclass
class ActionLog:
    attempts: List[ActionAttempt]    # All attempts in order

    # Indexes for fast lookup
    by_command: Dict[str, List[str]]         # normalized_command -> [attempt_ids]
    by_room: Dict[int, List[str]]            # room_id -> [attempt_ids]
    by_result: Dict[str, List[str]]          # result_type -> [attempt_ids]

    # Learned patterns
    patterns: Dict[str, ActionPattern]       # pattern -> ActionPattern

    # Negative knowledge (don't retry)
    do_not_retry: List[DoNotRetry]

    # Death tracking
    death_commands: Dict[str, DeathInfo]     # command -> DeathInfo


@dataclass
class DoNotRetry:
    """Commands to skip unless conditions change"""
    command: str
    room_id: int
    reason: str                      # "always fails", "causes death", etc.
    unless: List[str]                # Conditions that would make retry worthwhile
    # e.g., ["have sword", "troll is dead"]


@dataclass
class DeathInfo:
    command: str
    room_id: int
    death_message: str
    avoidable_by: List[str]          # Known ways to survive
    occurrences: int
```

### 4. PuzzleTracker

Track puzzle discovery, clues, and solution attempts.

```python
@dataclass
class Puzzle:
    id: str                          # Generated identifier
    name: str                        # Human-readable name
    description: str                 # What the puzzle seems to be

    # Location
    room_id: int                     # Primary room
    related_rooms: List[int]         # Other involved rooms

    # Objects involved
    required_objects: List[int]      # Objects needed to solve
    involved_objects: List[int]      # Objects that interact with puzzle

    # State tracking
    status: str                      # "discovered", "working", "solved", "stuck"
    blocking: List[str]              # What this puzzle blocks access to
    blocked_by: List[str]            # What must be solved first

    # Clues found
    clues: List[Clue]

    # Solution attempts
    attempts: List[PuzzleAttempt]

    # Solution (if found)
    solution: Optional[PuzzleSolution] = None
    solution_verified: bool = False
    alternative_solutions: List[PuzzleSolution] = []


@dataclass
class Clue:
    text: str                        # The clue text/observation
    source: str                      # Where found: "room_desc", "object_examine", "npc_dialogue"
    source_id: Optional[int]         # Room/object ID
    run: int
    turn: int
    relevance: str                   # "high", "medium", "low", "unknown"


@dataclass
class PuzzleAttempt:
    commands: List[str]              # Sequence tried
    result: str                      # What happened
    success: bool
    partial_progress: bool           # Made some progress
    notes: str                       # AI/human analysis
    run: int
    turn: int


@dataclass
class PuzzleSolution:
    commands: List[str]              # Exact command sequence
    prerequisites: List[str]         # What must be true first
    # e.g., ["in room 5", "have lamp", "lamp is lit"]

    setup_commands: List[str]        # Commands to get prerequisites
    verification: str                # How to verify it worked

    # Reliability
    works_every_time: bool = True
    random_factor: str = ""          # What varies
    alternative_if_fails: Optional[str] = None  # Fallback solution ID


@dataclass
class PuzzleTracker:
    puzzles: Dict[str, Puzzle]       # puzzle_id -> Puzzle

    # Dependency graph
    puzzle_order: List[str]          # Solved order (for learning prerequisites)
    dependency_graph: Dict[str, List[str]]  # puzzle_id -> [prerequisite_puzzle_ids]

    # Discovery
    potential_puzzles: List[str]     # Suspected but unconfirmed puzzles
```

### 5. SolutionBuilder

Build and store working solutions with branching for randomness.

```python
@dataclass
class SolutionStep:
    id: str                          # Step identifier
    command: str                     # The command to execute

    # Context requirements
    prerequisites: Prerequisites

    # Expected outcome
    expected_result: str             # What should happen
    expected_room: Optional[int]     # Where we should end up
    expected_inventory_add: List[int] = []
    expected_inventory_remove: List[int] = []

    # Validation
    success_indicators: List[str]    # Text patterns indicating success
    failure_indicators: List[str]    # Text patterns indicating failure

    # Fallback
    on_failure: str                  # "abort", "skip", "branch:branch_id", "retry:n"

    # Metadata
    source: str                      # "discovered", "walkthrough", "ai_suggested"
    confidence: float                # 0.0 - 1.0
    verified_runs: int = 0           # Times this worked


@dataclass
class Prerequisites:
    """Conditions that must be true to execute a step"""
    in_room: Optional[int] = None
    has_items: List[int] = []
    state_flags: Dict[str, bool] = {}   # {"lamp_lit": True, "door_open": True}
    puzzles_solved: List[str] = []
    not_conditions: List[str] = []      # Things that must NOT be true


@dataclass
class SolutionBranch:
    """A conditional branch in the solution"""
    id: str
    name: str                        # "handle_thief", "maze_variant_a"

    # When to use this branch
    trigger_type: str                # "text_match", "state_check", "random_detect"
    trigger_condition: str           # Pattern or condition

    # The steps in this branch
    steps: List[SolutionStep]

    # After branch completes
    rejoin_at: Optional[str] = None  # Step ID to continue from
    # None = branch is terminal (ends solution or dead end)


@dataclass
class Solution:
    """Complete solution for a game"""
    game_name: str
    game_file: str
    game_checksum: str

    # Version tracking
    version: int
    created: str
    last_modified: str
    last_verified: str

    # Main solution path
    main_steps: List[SolutionStep]

    # Conditional branches
    branches: Dict[str, SolutionBranch]  # branch_id -> SolutionBranch

    # Random element handlers
    random_handlers: List[RandomHandler]

    # Solution quality
    completeness: str                # "full", "partial", "to_point_X"
    end_state: str                   # "won", "score_N", "reached_room_X"
    total_commands: int
    estimated_turns: int

    # Verification
    verified_count: int = 0          # Successful run-throughs
    last_failure: Optional[str] = None
    known_issues: List[str] = []


@dataclass
class RandomHandler:
    """Handle random game elements"""
    id: str
    name: str                        # "thief_encounter", "maze_layout"
    description: str

    # Detection
    detection_method: str            # "text_match", "room_change", "object_missing"
    detection_pattern: str

    # When detected, what room/context
    applies_in_rooms: List[int]      # Empty = anywhere

    # Response branches
    responses: Dict[str, List[str]]  # {condition: [step_ids]}
    # e.g., {"has sword": ["kill thief"], "default": ["flee east"]}

    # Learning
    occurrences: int = 0
    successful_responses: Dict[str, int] = {}  # response -> success_count
```

### 6. RunState

Per-run state for the current playthrough.

```python
@dataclass
class RunState:
    """State for a single playthrough"""
    run_id: int
    started: str                     # ISO timestamp
    game_file: str

    # Current state
    turn: int = 0
    current_room_id: int = 0
    inventory: List[int] = []
    score: int = 0

    # This run's observations
    object_locations: Dict[int, int] = {}    # What we've seen this run
    random_elements_detected: List[str] = [] # Random things noticed

    # Execution state
    current_step_id: Optional[str] = None    # In solution execution
    current_branch: Optional[str] = None
    steps_completed: List[str] = []
    steps_failed: List[str] = []

    # Snapshots for backtracking
    checkpoints: Dict[str, Checkpoint] = {}  # name -> Checkpoint

    # Outcome
    status: str = "running"          # "running", "won", "died", "stuck", "error"
    end_turn: Optional[int] = None
    end_reason: str = ""


@dataclass
class Checkpoint:
    name: str
    turn: int
    room_id: int
    inventory: List[int]
    step_id: Optional[str]
    vm_state: bytes                  # Serialized Z-machine state
    created: str
```

---

## Query Patterns

### Common Queries the Solver Needs

```python
class KnowledgeBase:
    """Main interface to the knowledge base"""

    # World queries
    def get_unexplored_exits(self) -> List[Tuple[int, str]]:
        """Rooms with exits we haven't tried"""

    def get_rooms_with_unsolved_puzzles(self) -> List[int]:
        """Rooms where we got stuck"""

    def find_path(self, from_room: int, to_room: int) -> Optional[List[str]]:
        """Shortest path between rooms"""

    # Action queries
    def was_tried(self, command: str, room_id: int,
                  with_inventory: List[int]) -> Optional[ActionAttempt]:
        """Check if we tried this before in similar context"""

    def get_successful_actions(self, room_id: int) -> List[ActionAttempt]:
        """What worked in this room"""

    def get_death_commands(self, room_id: int) -> List[str]:
        """Commands that caused death here"""

    def should_retry(self, command: str, room_id: int,
                     current_state: Dict) -> Tuple[bool, str]:
        """Should we try this again? Returns (yes/no, reason)"""

    # Object queries
    def where_is(self, object_id: int) -> Optional[int]:
        """Current known location of object"""

    def what_opens(self, container_id: int) -> Optional[int]:
        """What key/tool opens this"""

    def get_light_sources(self) -> List[int]:
        """All known light sources"""

    # Puzzle queries
    def get_blocking_puzzles(self, room_id: int) -> List[Puzzle]:
        """What puzzles block progress from this room"""

    def get_clues_for(self, puzzle_id: str) -> List[Clue]:
        """All clues found for a puzzle"""

    # Solution queries
    def get_next_step(self, current_room: int,
                      inventory: List[int]) -> Optional[SolutionStep]:
        """What's the next solution step"""

    def handle_random_event(self, output: str,
                           room_id: int) -> Optional[List[str]]:
        """Get commands to handle detected random event"""
```

---

## State Machine for Solver

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────┐    stuck     ┌─────────────┐
│  EXPLORING  │─────────────►│  ANALYZING  │
│  (map world)│◄─────────────│  (use AI)   │
└──────┬──────┘   got hint   └──────┬──────┘
       │                            │
       │ found puzzle               │ found solution
       ▼                            ▼
┌─────────────┐              ┌─────────────┐
│   SOLVING   │◄─────────────│  EXECUTING  │
│  (puzzle)   │  need more   │  (solution) │
└──────┬──────┘    info      └──────┬──────┘
       │                            │
       │ solved                     │ random event
       ▼                            ▼
┌─────────────┐              ┌─────────────┐
│  ADVANCING  │              │  BRANCHING  │
│ (next area) │              │(handle rng) │
└──────┬──────┘              └──────┬──────┘
       │                            │
       │ game complete              │
       ▼                            │
┌─────────────┐                     │
│    WON      │◄────────────────────┘
└─────────────┘
```

---

## File Formats

### world.json Example

```json
{
  "game_name": "Zork I",
  "game_file": "zork1.z3",
  "game_checksum": "a5b3c2d1",
  "schema_version": "1.0",
  "last_updated": "2024-01-15T10:30:00Z",

  "starting_room_id": 45,
  "has_darkness_mechanic": true,
  "has_maze": true,
  "has_thief_or_wanderer": true,

  "rooms": {
    "45": {
      "id": 45,
      "name": "West of House",
      "description": "You are standing in an open field west of a white house...",
      "first_seen_run": 1,
      "first_seen_turn": 1,
      "exits": {
        "north": {
          "direction": "north",
          "destination_id": 46,
          "status": "open"
        },
        "east": {
          "direction": "east",
          "destination_id": null,
          "status": "blocked",
          "blocker": "house",
          "unlock_action": "open window from inside"
        }
      },
      "is_dark": false,
      "is_deadly": false
    }
  },

  "total_runs": 5,
  "rooms_discovered_by_run": {
    "1": [45, 46, 47],
    "2": [45, 46, 47, 48, 49]
  }
}
```

### actions.json Example

```json
{
  "attempts": [
    {
      "id": "a1b2c3",
      "command": "take mailbox",
      "normalized_command": "take mailbox",
      "run": 1,
      "turn": 3,
      "room_id": 45,
      "inventory": [],
      "output": "The small mailbox is securely anchored.",
      "result_type": "failure",
      "prerequisites_discovered": ["mailbox is fixed in place"]
    }
  ],

  "do_not_retry": [
    {
      "command": "take mailbox",
      "room_id": 45,
      "reason": "always fails - fixed in place",
      "unless": []
    }
  ],

  "death_commands": {
    "jump": {
      "command": "jump",
      "room_id": 67,
      "death_message": "You fall to your death.",
      "avoidable_by": [],
      "occurrences": 2
    }
  }
}
```

### solutions.json Example

```json
{
  "game_name": "Zork I",
  "version": 3,
  "completeness": "partial",
  "end_state": "score_50",

  "main_steps": [
    {
      "id": "step_001",
      "command": "open mailbox",
      "prerequisites": {
        "in_room": 45
      },
      "expected_result": "Opening the small mailbox reveals a leaflet.",
      "success_indicators": ["leaflet"],
      "on_failure": "skip",
      "confidence": 1.0,
      "verified_runs": 5
    },
    {
      "id": "step_002",
      "command": "take leaflet",
      "prerequisites": {
        "in_room": 45,
        "state_flags": {"mailbox_open": true}
      },
      "expected_inventory_add": [23],
      "on_failure": "abort",
      "confidence": 1.0
    }
  ],

  "random_handlers": [
    {
      "id": "thief_handler",
      "name": "Thief Encounter",
      "detection_method": "text_match",
      "detection_pattern": "thief|Someone carrying a large bag",
      "responses": {
        "has_sword && sword_is_ready": ["kill thief with sword"],
        "default": ["drop valuables", "wait", "wait", "take valuables"]
      }
    }
  ]
}
```

---

## Implementation Priority

### Phase 1: Core Knowledge Base
1. `WorldMap` - Room graph with connections
2. `ObjectTracker` - Object locations and properties
3. `ActionLog` - Track all attempts with results
4. `DoNotRetry` logic - Skip failed commands

### Phase 2: Puzzle & Solution
5. `PuzzleTracker` - Clues and solution attempts
6. `Solution` with `SolutionStep` - Working solutions
7. `Prerequisites` checking - Know when steps can run

### Phase 3: Randomness Handling
8. `RandomHandler` - Detect and respond to variance
9. `SolutionBranch` - Conditional paths
10. Cross-run variance detection

### Phase 4: Intelligence Layer
11. Knowledge-based query interface
12. AI integration using full context
13. Learning from verified solutions
14. Automatic prerequisite discovery

---

## Integration with Existing Code

### Updates to `walker.py`
- After each command, update `ActionLog`
- After room discovery, update `WorldMap`
- After object interaction, update `ObjectTracker`

### Updates to `advanced_solver.py`
- Load knowledge base at start
- Query before trying commands (was this tried?)
- Save all discoveries persistently
- Use `Solution` format for output

### New `knowledge.py` Module
- `KnowledgeBase` class implementing all queries
- Load/save JSON files
- Provide interface for solver

---

## Usage Examples

### Basic Usage with GameWalker

```python
from zwalker.walker import GameWalker

# Create walker with persistent knowledge
walker = GameWalker.create_with_knowledge("games/zcode/zork1.z3")
walker.start()

# Knowledge base persists across runs
print(f"Previous runs: {walker.kb.world_map.total_runs}")

# Try commands - failed ones are tracked
result = walker.try_command("north")
if result.blocked:
    # Command added to do-not-retry list automatically
    pass

# Get AI-powered suggestions
suggestions = walker.get_suggested_actions()
for s in suggestions[:5]:
    print(f"{s['action']}: {s['reason']}")

# Auto-explore using knowledge
result = walker.auto_explore(max_turns=50)
print(f"Found {result['new_rooms_found']} new rooms")

# Save knowledge
walker.save_knowledge()
```

### Using the Knowledge Base Directly

```python
from zwalker.knowledge import KnowledgeBase

# Load or create knowledge base
kb = KnowledgeBase("games/zcode/zork1.z3")

# Check exploration status
status = kb.get_exploration_status()
print(f"Unexplored exits: {status['unexplored_exits']}")

# Get AI prompt context
prompt = kb.get_ai_prompt_context(room_id=64, task="explore")
print(prompt)

# Learn from action history
learned = kb.learn_from_transcript()
for prereq in learned['new_prerequisites']:
    print(f"{prereq['for_command']} requires {prereq['prerequisite']}")

# Export knowledge
summary = kb.export_knowledge_summary()
```

### Handling Random Events

```python
# Initialize common random event patterns
kb.init_common_random_events()

# Check for events in game output
event = kb.check_for_random_event(output, room_id)
if event:
    # Get appropriate response
    response_cmds = kb.get_random_response(event, inventory_names=["sword"])
    for cmd in response_cmds:
        walker.try_command(cmd)

# Track variance across runs
kb.take_snapshot(room_id, room_name, object_locations)
# ... later ...
variances = kb.compare_runs()
random_objects = kb.get_random_objects()
```

### Command Line Tools

```bash
# Solve a game with knowledge base
python scripts/solve_with_knowledge.py games/zcode/zork1.z3

# Auto-explore
python scripts/solve_with_knowledge.py games/zcode/zork1.z3 --auto-explore --max-turns 100

# Show knowledge status
python scripts/solve_with_knowledge.py games/zcode/zork1.z3 --status

# Knowledge base management
python scripts/kb_manage.py list
python scripts/kb_manage.py status zork1
python scripts/kb_manage.py rooms zork1
python scripts/kb_manage.py solution zork1
python scripts/kb_manage.py export zork1 zork1_kb.json
```

---

## Implementation Status

- [x] Phase 1: Core Knowledge Base (WorldMap, ObjectTracker, ActionLog)
- [x] Phase 2: Puzzles & Solutions (PuzzleTracker, Solution, Prerequisites)
- [x] Phase 3: Randomness Handling (RandomEvent, Variance Detection)
- [x] Phase 4: Intelligence Layer (Suggestions, Learning, AI Integration)

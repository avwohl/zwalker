"""
Advanced AI Solver using Claude with sophisticated reasoning.

This solver uses:
- Multi-turn planning and strategy
- Chain-of-thought reasoning
- Backtracking when stuck
- Long-term memory and goal tracking
- Deep understanding of IF game mechanics
"""

import os
import json
import time
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict


@dataclass
class GameState:
    """Snapshot of game state for backtracking"""
    room_id: int
    inventory: List[str]
    command_history: List[str]
    output_history: List[str]
    vm_state: Any  # Saved Z-machine state
    turn_number: int


@dataclass
class Strategy:
    """A multi-step strategy/plan"""
    goal: str
    steps: List[str]
    reasoning: str
    confidence: float  # 0.0 - 1.0
    status: str = "pending"  # pending, executing, completed, failed


@dataclass
class PuzzleMemory:
    """Memory of attempted puzzle solutions"""
    puzzle_description: str
    location: str
    attempted_solutions: List[str]
    failed_approaches: List[str]
    clues_found: List[str]
    likely_solution: Optional[str] = None


class AdvancedAISolver:
    """
    Sophisticated AI solver that actually understands and solves complex IF games.

    Uses Claude with:
    - Long-term memory and goal tracking
    - Multi-step planning and replanning
    - Backtracking from dead ends
    - Deep reasoning about game state
    - Understanding of IF conventions and puzzle patterns
    """

    def __init__(self, game_data: bytes, verbose: bool = True, hints_file: str = None):
        """Initialize the advanced solver

        Args:
            game_data: The Z-machine game file bytes
            verbose: Whether to print detailed progress
            hints_file: Optional path to a walkthrough/hints file to guide the AI
        """
        from zwalker.walker import GameWalker
        import anthropic

        self.walker = GameWalker(game_data)
        self.verbose = verbose

        # Load hints/walkthrough if provided
        self.hints = None
        self.walkthrough_commands = []  # Extracted commands for direct execution
        self.walkthrough_index = 0  # Current position in walkthrough
        self.walkthrough_failures = []  # Track where walkthrough fails: [(index, cmd, error)]
        if hints_file:
            self.hints = self._load_hints(hints_file)
            if self.hints:
                self.log(f"Loaded {len(self.hints)} lines of hints/walkthrough", "INFO")
                # Try to extract direct commands from walkthrough
                self.walkthrough_commands = self._extract_walkthrough_commands(self.hints)
                if self.walkthrough_commands:
                    self.log(f"Extracted {len(self.walkthrough_commands)} executable commands from walkthrough", "INFO")

        # Initialize API client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-opus-4-20250514"  # Opus 4

        # Long-term memory
        self.visited_rooms: Dict[int, Dict[str, Any]] = {}
        self.global_map: Dict[int, Dict[str, int]] = {}  # room_id -> {direction: room_id}
        self.inventory_history: List[List[str]] = []
        self.puzzles: Dict[str, PuzzleMemory] = {}
        self.current_strategy: Optional[Strategy] = None
        self.strategy_history: List[Strategy] = []

        # Checkpoints for backtracking
        self.checkpoints: List[GameState] = []
        self.max_checkpoints = 20

        # Game progress tracking
        self.turn_number = 0
        self.stuck_counter = 0
        self.last_progress_turn = 0

        # Win conditions
        self.game_won = False
        self.win_detected_turn = None

        # Death tracking - to help AI avoid repeated deaths
        self.death_count = 0
        self.death_causes = []  # List of (turn, room, last_command, cause)

        # Maze/room connection tracking - persists between runs
        self.room_connections = {}  # {from_room_id: {direction: to_room_id}}
        self.room_names = {}  # {room_id: name}

        # State file for persistence
        self.state_file = None

    def save_learned_state(self, state_file: str = None):
        """Save learned knowledge to a file for resuming later"""
        if state_file:
            self.state_file = state_file
        if not self.state_file:
            return

        state = {
            "death_count": self.death_count,
            "death_causes": self.death_causes,
            "room_connections": self.room_connections,
            "room_names": self.room_names,
            "turn_number": self.turn_number,
        }

        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            self.log(f"Saved learned state to {self.state_file}", "INFO")
        except Exception as e:
            self.log(f"Could not save state: {e}", "ERROR")

    def load_learned_state(self, state_file: str):
        """Load previously learned knowledge from a file"""
        self.state_file = state_file
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)

            self.death_count = state.get("death_count", 0)
            self.death_causes = state.get("death_causes", [])
            self.room_connections = state.get("room_connections", {})
            self.room_names = state.get("room_names", {})
            # Don't restore turn_number - we're starting fresh game state

            self.log(f"Loaded learned state: {self.death_count} deaths, {len(self.room_connections)} room connections", "IMPORTANT")
            return True
        except FileNotFoundError:
            self.log(f"No previous state file found - starting fresh", "INFO")
            return False
        except Exception as e:
            self.log(f"Could not load state: {e}", "ERROR")
            return False

    def record_room_transition(self, from_room: int, direction: str, to_room: int, room_name: str = None):
        """Record a room connection for maze mapping"""
        from_key = str(from_room)
        if from_key not in self.room_connections:
            self.room_connections[from_key] = {}
        self.room_connections[from_key][direction] = to_room

        if room_name and to_room:
            self.room_names[str(to_room)] = room_name

    def _load_hints(self, hints_file: str) -> Optional[str]:
        """Load hints/walkthrough from a file"""
        try:
            with open(hints_file, 'r') as f:
                content = f.read()
            return content
        except Exception as e:
            self.log(f"Could not load hints file: {e}", "ERROR")
            return None

    def _extract_walkthrough_commands(self, hints_content: str) -> List[str]:
        """Extract executable commands from a walkthrough file.

        Looks for lines that appear to be game commands (not comments or headers).
        Common IF commands: go/n/s/e/w, get/take, open, look, inventory, etc.
        """
        commands = []

        # Common IF command patterns
        command_starts = [
            'go ', 'north', 'south', 'east', 'west', 'up', 'down',
            'n', 's', 'e', 'w', 'u', 'd',
            'get ', 'take ', 'drop ', 'put ', 'give ',
            'open ', 'close ', 'lock ', 'unlock ',
            'look', 'examine ', 'read ', 'x ',
            'inventory', 'i',
            'climb ', 'enter ', 'exit ', 'leave ',
            'turn ', 'push ', 'pull ', 'move ', 'press ',
            'attack ', 'kill ', 'hit ', 'fight ',
            'say ', 'tell ', 'ask ', 'show ',
            'wave ', 'light ', 'extinguish ',
            'eat ', 'drink ',
            'tie ', 'untie ', 'cut ',
            'dig', 'fill ', 'empty ',
            'wear ', 'remove ',
            'wait', 'z',
            'save', 'restore', 'restart', 'quit',
            'odysseus', 'ulysses',  # Zork-specific
            'pray', 'ring ', 'wind ',
            'inflate ', 'deflate ', 'launch',
            'score', 'verbose', 'brief',
        ]

        for line in hints_content.split('\n'):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip comments (lines starting with #)
            if line.startswith('#'):
                continue

            # Skip section headers (lines starting with ##)
            if line.startswith('##'):
                continue

            # Skip lines that look like descriptions (too long, have certain patterns)
            if len(line) > 60:
                continue
            if ':' in line and not line.lower().startswith(('say ', 'tell ')):
                continue

            # Check if line starts with a known command
            line_lower = line.lower()
            is_command = False

            for cmd_start in command_starts:
                if line_lower.startswith(cmd_start) or line_lower == cmd_start.strip():
                    is_command = True
                    break

            if is_command:
                commands.append(line)

        return commands

    def get_next_walkthrough_command(self) -> Optional[str]:
        """Get the next command from the walkthrough, if available."""
        if self.walkthrough_index < len(self.walkthrough_commands):
            cmd = self.walkthrough_commands[self.walkthrough_index]
            self.walkthrough_index += 1
            return cmd
        return None

    def execute_command(self, command: str):
        """Execute a single command and return the result.

        Similar to execute_strategy but for a single command.
        """
        room_id_before = self.walker.current_room_id

        # Execute the command
        result = self.walker.try_command(command)

        room_id_after = self.walker.current_room_id

        # Track room transitions
        if room_id_before != room_id_after:
            self.record_room_transition(room_id_before, command, room_id_after)

        # Update turn counter
        self.turn_number += 1

        # Print output with room ID info
        if result:
            room_info = f"[Room {room_id_before}"
            if room_id_after != room_id_before:
                room_info += f" → {room_id_after}"
            room_info += "]"
            print(f"  {room_info} → {result.output[:200]}...")
            print()

            # Check for win condition
            if self.detect_win_condition(result.output):
                self.game_won = True
                self.win_detected_turn = self.turn_number
                self.log(f"WIN DETECTED at turn {self.turn_number}!", "WIN")

        return result

    def log(self, message: str, level: str = "INFO"):
        """Logging with levels"""
        if self.verbose or level in ["IMPORTANT", "WIN", "ERROR"]:
            prefix = {
                "INFO": "ℹ️ ",
                "IMPORTANT": "⚠️ ",
                "WIN": "🎉",
                "ERROR": "❌",
                "THINK": "🤔",
                "PLAN": "📋",
                "TRY": "🎯"
            }.get(level, "")
            print(f"{prefix} {message}")

    def save_checkpoint(self):
        """Save current game state for potential backtracking"""
        # Get recent commands from transcript
        recent_commands = [cmd for cmd, _ in self.walker.full_transcript[-50:]]

        checkpoint = GameState(
            room_id=self.walker.current_room_id,
            inventory=self.get_current_inventory(),
            command_history=recent_commands,
            output_history=[],  # Truncate to save memory
            vm_state=self.walker.vm.save_state(),
            turn_number=self.turn_number
        )

        self.checkpoints.append(checkpoint)

        # Keep only recent checkpoints
        if len(self.checkpoints) > self.max_checkpoints:
            self.checkpoints.pop(0)

        # Also save learned state periodically (every 5 checkpoints)
        if self.state_file and len(self.checkpoints) % 5 == 0:
            self.save_learned_state()

        self.log(f"Checkpoint saved (turn {self.turn_number})", "INFO")

    def restore_checkpoint(self, checkpoint_index: int = -1):
        """Restore to a previous checkpoint"""
        if not self.checkpoints:
            self.log("No checkpoints to restore", "ERROR")
            return False

        checkpoint = self.checkpoints[checkpoint_index]
        self.walker.vm.restore_state(checkpoint.vm_state)
        self.turn_number = checkpoint.turn_number

        self.log(f"Restored to checkpoint at turn {checkpoint.turn_number}", "IMPORTANT")
        return True

    def get_current_inventory(self) -> List[str]:
        """Get current inventory items"""
        return [name for _, name in self.walker.vm.get_inventory()]

    def detect_win_condition(self, output: str) -> bool:
        """Check if game has been won"""
        # More specific win phrases to avoid false positives
        # (e.g., "congratulations" appearing in game manuals/papers)
        win_phrases = [
            "you have won",
            "*** you have won ***",
            "you've won",
            "you are victorious",
            "game over - you won",
            "you have completed the game",
            "your score is 350",  # Zork specific - max score
            "350 points in",  # Zork win
            "all 19 treasures",  # Zork win
            "master adventurer",  # Zork title for winning
            "you have achieved the rank of master",
        ]

        output_lower = output.lower()
        for phrase in win_phrases:
            if phrase in output_lower:
                return True

        return False

    def detect_death_condition(self, output: str) -> bool:
        """Check if player has died"""
        death_phrases = [
            "you have died",
            "*** you have died ***",
            "you are dead",
            "you're dead",
            "you died",
            "your adventure ends here",
            "game over",
            "you have been killed",
            "you were killed",
            "that last blow was too much",
            "restart, restore, or quit",
            "type restart, restore, or quit"
        ]

        output_lower = output.lower()
        for phrase in death_phrases:
            if phrase in output_lower:
                return True

        return False

    def build_context_for_ai(self, depth: int = 30) -> Dict[str, Any]:
        """Build comprehensive context for AI analysis"""
        room = self.walker.rooms.get(self.walker.current_room_id)

        # Recent history from transcript
        recent_transcript = self.walker.full_transcript[-depth:]
        recent_commands = [cmd for cmd, _ in recent_transcript]
        recent_outputs = [out for _, out in recent_transcript]

        # Current state
        current_inventory = self.get_current_inventory()

        # Map knowledge
        explored_rooms = len(self.visited_rooms)
        total_exits_found = sum(len(r.exits) for r in self.walker.rooms.values())

        # Puzzle tracking
        active_puzzles = [p for p in self.puzzles.values() if p.likely_solution is None]

        context = {
            "turn_number": self.turn_number,
            "current_room": {
                "id": self.walker.current_room_id,
                "name": room.name if room else "Unknown",
                "description": room.description if room else "",
                "exits": room.exits if room else {},
                "objects": [name for _, name in room.objects] if room else []
            },
            "inventory": current_inventory,
            "recent_history": [
                {"command": cmd, "output": out[:500]}  # Truncate long outputs
                for cmd, out in zip(recent_commands, recent_outputs)
            ],
            "current_room_id": self.walker.current_room_id,  # Emphasize current room ID
            "map_knowledge": {
                "rooms_explored": explored_rooms,
                "exits_mapped": total_exits_found,
                "current_map": {
                    room_id: {"name": r.name, "exits": list(r.exits.keys())}
                    for room_id, r in self.walker.rooms.items()
                }
            },
            "puzzles": {
                "active": [
                    {
                        "description": p.puzzle_description,
                        "location": p.location,
                        "attempts": len(p.attempted_solutions),
                        "clues": p.clues_found
                    }
                    for p in active_puzzles
                ],
                "solved": len([p for p in self.puzzles.values() if p.likely_solution])
            },
            "current_strategy": {
                "goal": self.current_strategy.goal if self.current_strategy else None,
                "status": self.current_strategy.status if self.current_strategy else None,
                "steps_remaining": len(self.current_strategy.steps) if self.current_strategy else 0
            } if self.current_strategy else None,
            "progress": {
                "turns_since_progress": self.turn_number - self.last_progress_turn,
                "stuck": self.stuck_counter > 5
            },
            "deaths": {
                "total_deaths": self.death_count,
                "recent_deaths": self.death_causes[-5:] if self.death_causes else []
            }
        }

        return context

    def get_strategic_plan(self, context: Dict[str, Any]) -> Strategy:
        """
        Ask the AI to analyze the game state and create a multi-step strategic plan.
        This is the core of sophisticated game solving.
        """
        self.log(f"Asking {self.model} for strategic plan...", "THINK")

        prompt = f"""You are an expert interactive fiction game solver with deep understanding of IF puzzles, mechanics, and conventions.

CURRENT GAME STATE:
===================
Turn: {context['turn_number']}
Room: {context['current_room']['name']} (ID: {context['current_room']['id']})
Description: {context['current_room']['description']}
Visible Objects: {', '.join(context['current_room']['objects']) or 'none'}
Exits: {', '.join(context['current_room']['exits'].keys()) or 'none'}
Inventory: {', '.join(context['inventory']) or 'empty'}

RECENT ACTIONS:
===============
{self._format_recent_history(context['recent_history'][-10:])}

MAP KNOWLEDGE:
==============
Explored {context['map_knowledge']['rooms_explored']} rooms
Found {context['map_knowledge']['exits_mapped']} exits
Known rooms: {self._format_map(context['map_knowledge']['current_map'])}

ACTIVE PUZZLES:
===============
{self._format_puzzles(context['puzzles']['active'])}

PROGRESS STATUS:
================
Turns since last progress: {context['progress']['turns_since_progress']}
Currently stuck: {context['progress']['stuck']}

DEATH HISTORY:
==============
Total deaths: {context['deaths']['total_deaths']}
{self._format_deaths(context['deaths']['recent_deaths'])}

LEARNED ROOM CONNECTIONS (from previous runs):
==============================================
{self._format_room_connections()}

{self._format_hints_section()}

YOUR TASK:
==========
Analyze this game state deeply and create a strategic plan to WIN this game.
If a walkthrough/hints section is provided above, USE IT to guide your strategy!

Consider:
1. What is the main objective/goal of this game?
2. What puzzles or obstacles are currently blocking progress?
3. What items or information might be needed?
4. Are there unexplored areas that might contain keys/solutions?
5. Are we stuck in a dead end that requires backtracking?
6. What IF puzzle patterns apply here? (locked doors, inventory puzzles, NPCs, timing puzzles, etc.)

Think step-by-step about the best strategy to make progress toward winning.

Respond in JSON format:
{{
    "analysis": "Deep analysis of current situation and what's blocking progress",
    "goal": "Primary goal for next phase (e.g., 'find key to unlock door', 'solve light puzzle')",
    "puzzle_pattern": "IF puzzle pattern detected (e.g., 'locked_door', 'inventory_combination', 'npc_dialogue', 'maze', etc.)",
    "strategy": "Multi-step strategy to achieve goal",
    "steps": [
        "specific command or action 1",
        "specific command or action 2",
        ...
    ],
    "confidence": 0.8,
    "requires_backtracking": false,
    "reasoning": "Detailed explanation of why this strategy should work"
}}

IMPORTANT:
- Be specific with commands (not just "examine things" but "examine lamp", "take key", etc.)
- Consider IF game logic (objects often need to be examined before use, doors unlocked before opening, etc.)
- If truly stuck, suggest backtracking or systematic exploration
- Aim for 5-15 concrete steps
- Think about inventory management and puzzle dependencies
- ONLY USE OBJECTS IN THE ROOM OR INVENTORY: Don't try to take, use, or interact with objects that aren't mentioned in the current room description or your inventory. Trying to use objects not present wastes turns and returns "You can't see any such thing."
- AVOID DEATH: Check death history above. Don't repeat commands/situations that led to death.
- In Zork, combat with trolls requires a weapon (sword). Don't go north without protection!
- If a troll blocks a passage, you need to defeat it with the elvish sword before passing.
- MAZE NAVIGATION: Pay attention to the Room ID! In mazes where all rooms look alike, the Room ID is UNIQUE and tells you which room you're actually in. Use room IDs to map the maze and avoid going in circles. Track which room ID connects to which direction.
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.7,  # Some creativity but not too random
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Parse JSON response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            data = json.loads(response_text)

            strategy = Strategy(
                goal=data.get("goal", "explore"),
                steps=data.get("steps", []),
                reasoning=data.get("reasoning", ""),
                confidence=data.get("confidence", 0.5)
            )

            self.log(f"Strategy: {strategy.goal}", "PLAN")
            self.log(f"Confidence: {strategy.confidence:.0%}", "PLAN")
            self.log(f"Steps: {len(strategy.steps)}", "PLAN")
            if self.verbose:
                self.log(f"Reasoning: {strategy.reasoning}", "THINK")

            return strategy

        except Exception as e:
            self.log(f"Error getting strategy: {e}", "ERROR")
            # Fallback: basic exploration
            return Strategy(
                goal="explore systematically",
                steps=["north", "south", "east", "west", "look", "inventory"],
                reasoning="Fallback strategy due to API error",
                confidence=0.3
            )

    def execute_strategy(self, strategy: Strategy) -> bool:
        """
        Execute a strategic plan step by step.
        Returns True if strategy made progress, False if stuck.
        """
        self.log(f"Executing strategy: {strategy.goal}", "PLAN")

        progress_made = False

        for i, step in enumerate(strategy.steps):
            self.log(f"Step {i+1}/{len(strategy.steps)}: {step}", "TRY")

            # Track room ID before command
            room_id_before = self.walker.current_room_id

            # Execute command
            result = self.walker.try_command(step)
            output = result.output

            # Track room ID after command
            room_id_after = self.walker.current_room_id

            self.turn_number += 1

            # Show output with room ID (especially useful for mazes!)
            if self.verbose:
                room_info = f"[Room {room_id_before}"
                if room_id_after != room_id_before:
                    room_info += f" → {room_id_after}]"
                else:
                    room_info += "]"
                print(f"  {room_info} → {output[:280]}{'...' if len(output) > 280 else ''}\n")

            # Record room transition for maze mapping (persists between runs)
            if room_id_after != room_id_before:
                # Extract direction from command
                direction = step.lower().replace("go ", "").strip()
                room = self.walker.rooms.get(room_id_after)
                room_name = room.name if room else None
                self.record_room_transition(room_id_before, direction, room_id_after, room_name)

            # Check for win
            if self.detect_win_condition(output):
                self.game_won = True
                self.win_detected_turn = self.turn_number
                self.log(f"GAME WON at turn {self.turn_number}!", "WIN")
                return True

            # Check for death - restore from checkpoint if died
            if self.detect_death_condition(output):
                self.death_count += 1
                room = self.walker.rooms.get(self.walker.current_room_id)
                room_name = room.name if room else "Unknown"
                # Record the death cause for learning
                self.death_causes.append({
                    "turn": self.turn_number,
                    "room": room_name,
                    "command": step,
                    "output_snippet": output[:200]
                })
                self.log(f"PLAYER DIED (death #{self.death_count}) at turn {self.turn_number}! Command: '{step}' in {room_name}", "IMPORTANT")
                self.log(f"Restoring checkpoint...", "IMPORTANT")
                # Restore to a recent checkpoint (go back a few to avoid same death)
                if len(self.checkpoints) >= 3:
                    self.restore_checkpoint(-3)  # Go back 3 checkpoints
                elif len(self.checkpoints) >= 1:
                    self.restore_checkpoint(-1)  # Go back to last checkpoint
                else:
                    self.log("No checkpoints to restore! Game may be unrecoverable.", "ERROR")
                # Mark strategy as failed so we get a new plan
                strategy.status = "failed"
                return False

            # Track progress
            if result.new_room:
                self.log(f"  ✓ Entered new room", "INFO")
                progress_made = True
                self.last_progress_turn = self.turn_number
                self.stuck_counter = 0
            elif result.took_object:
                self.log(f"  ✓ Acquired object", "INFO")
                progress_made = True
                self.last_progress_turn = self.turn_number
            elif result.interesting:
                self.log(f"  ✓ Interesting event", "INFO")
                progress_made = True
                self.last_progress_turn = self.turn_number

            # Save checkpoint periodically
            if self.turn_number % 10 == 0:
                self.save_checkpoint()

        strategy.status = "completed"
        return progress_made

    def solve(self, max_turns: int = 500, planning_interval: int = 15) -> Dict[str, Any]:
        """
        Main solving loop.

        If a walkthrough with executable commands is available, runs those first.
        Falls back to AI planning when walkthrough runs out or commands fail.

        Args:
            max_turns: Maximum number of turns to try
            planning_interval: How often to replan (in turns)

        Returns:
            Solution data including commands and success status
        """
        self.log(f"Starting advanced solver (max {max_turns} turns)", "IMPORTANT")
        self.log(f"Using model: {self.model}", "INFO")

        # Check if we have walkthrough commands to execute directly
        if self.walkthrough_commands:
            self.log(f"WALKTHROUGH MODE: Will execute {len(self.walkthrough_commands)} commands directly", "IMPORTANT")

        # Start game
        output = self.walker.start()
        self.log("Game started", "INFO")
        print(f"\n{output}\n")

        # Add initial output to transcript
        self.walker.full_transcript.append(("", output))

        self.save_checkpoint()  # Save initial state

        consecutive_failures = 0  # Track failures to know when to fall back to AI

        while self.turn_number < max_turns and not self.game_won:
            # WALKTHROUGH MODE: Try to execute walkthrough commands directly
            if self.walkthrough_commands and self.walkthrough_index < len(self.walkthrough_commands):
                cmd = self.get_next_walkthrough_command()
                if cmd:
                    self.log(f"Walkthrough [{self.walkthrough_index}/{len(self.walkthrough_commands)}]: {cmd}", "TRY")

                    # Execute the command
                    result = self.execute_command(cmd)

                    # Check result
                    if result:
                        output_text = result.output if hasattr(result, 'output') else str(result)

                        # Check for death
                        if self.detect_death_condition(output_text):
                            self.log(f"DEATH detected! Restoring checkpoint...", "ERROR")
                            consecutive_failures += 1
                            if len(self.checkpoints) > 0:
                                self.restore_checkpoint(-1)
                            continue

                        # Check for "can't" messages that indicate command didn't work
                        cant_patterns = ["can't see", "can't go", "don't understand", "isn't here", "you can't"]
                        is_failure = any(p in output_text.lower() for p in cant_patterns)

                        if is_failure:
                            consecutive_failures += 1
                            # Record the failure
                            self.walkthrough_failures.append({
                                "index": self.walkthrough_index - 1,
                                "command": cmd,
                                "error": output_text[:200],
                                "turn": self.turn_number,
                                "room": self.walker.current_room_id
                            })
                            self.log(f"Command may have failed: {output_text[:100]}", "INFO")
                        else:
                            consecutive_failures = 0  # Reset on success

                        # If too many consecutive failures, skip to AI mode
                        if consecutive_failures > 5:
                            self.log("Multiple walkthrough commands failing - switching to AI mode", "IMPORTANT")
                            self.log(f"Failed at command #{self.walkthrough_index}: {cmd}", "ERROR")
                            self.walkthrough_index = len(self.walkthrough_commands)  # Skip rest of walkthrough

                    # Periodic checkpoint
                    if self.turn_number % 10 == 0:
                        self.save_checkpoint()

                    continue  # Continue with next walkthrough command

            # AI MODE: Fall back to AI planning when walkthrough is exhausted or unavailable
            # Check if we need a new plan
            need_new_plan = (
                self.current_strategy is None or
                self.current_strategy.status == "completed" or
                self.current_strategy.status == "failed" or
                self.turn_number % planning_interval == 0 or
                self.stuck_counter > 10
            )

            if need_new_plan:
                # Build context and get new strategy
                context = self.build_context_for_ai()
                strategy = self.get_strategic_plan(context)

                self.current_strategy = strategy
                self.strategy_history.append(strategy)

                # Execute the strategy
                progress = self.execute_strategy(strategy)

                if not progress:
                    self.stuck_counter += 1
                    self.log(f"No progress (stuck counter: {self.stuck_counter})", "IMPORTANT")

                    # If very stuck, consider backtracking
                    if self.stuck_counter > 20 and len(self.checkpoints) > 5:
                        self.log("Too stuck - restoring earlier checkpoint", "IMPORTANT")
                        self.restore_checkpoint(-5)  # Go back 5 checkpoints
                        self.stuck_counter = 0
                else:
                    self.stuck_counter = max(0, self.stuck_counter - 2)

            # Safety check
            if self.stuck_counter > 30:
                self.log("Solver appears completely stuck", "ERROR")
                break

        # Save learned state at end of run
        if self.state_file:
            self.save_learned_state()

        # Compile results
        result = {
            "game_won": self.game_won,
            "turns_taken": self.turn_number,
            "win_turn": self.win_detected_turn,
            "rooms_explored": len(self.walker.rooms),
            "strategies_tried": len(self.strategy_history),
            "commands": [cmd for cmd, _ in self.walker.full_transcript if cmd],  # Extract commands
            "final_inventory": self.get_current_inventory(),
            "success": self.game_won,
            "room_connections_learned": len(self.room_connections),
            "deaths_recorded": self.death_count,
            "walkthrough_commands_total": len(self.walkthrough_commands),
            "walkthrough_commands_executed": self.walkthrough_index,
            "walkthrough_failures": self.walkthrough_failures
        }

        # Log walkthrough status
        if self.walkthrough_commands:
            self.log(f"Walkthrough: executed {self.walkthrough_index}/{len(self.walkthrough_commands)} commands", "INFO")
            if self.walkthrough_failures:
                self.log(f"Walkthrough failures: {len(self.walkthrough_failures)}", "IMPORTANT")
                for f in self.walkthrough_failures[:5]:  # Show first 5 failures
                    self.log(f"  - #{f['index']}: '{f['command']}' -> {f['error'][:60]}...", "INFO")

        return result

    def _format_recent_history(self, history: List[Dict]) -> str:
        """Format recent command history for prompt"""
        lines = []
        for entry in history[-10:]:
            cmd = entry.get('command', '')
            out = entry.get('output', '')[:200]
            lines.append(f"> {cmd}\n{out}")
        return "\n".join(lines)

    def _format_map(self, map_data: Dict) -> str:
        """Format map knowledge for prompt"""
        lines = []
        for room_id, info in list(map_data.items())[:15]:  # Show first 15 rooms
            exits = ', '.join(info['exits']) if info['exits'] else 'none'
            lines.append(f"  Room ID {room_id}: {info['name']} - exits: {exits}")
        if len(map_data) > 15:
            lines.append(f"  ... and {len(map_data) - 15} more rooms")
        return "\n".join(lines)

    def _format_puzzles(self, puzzles: List[Dict]) -> str:
        """Format active puzzles for prompt"""
        if not puzzles:
            return "No active puzzles detected"

        lines = []
        for p in puzzles[:5]:
            lines.append(f"  - {p['description']} at {p['location']}")
            lines.append(f"    Attempts: {p['attempts']}, Clues: {', '.join(p['clues']) or 'none'}")
        return "\n".join(lines)

    def _format_deaths(self, deaths: List[Dict]) -> str:
        """Format death history for prompt to help AI avoid repeated deaths"""
        if not deaths:
            return "No deaths yet - be careful!"

        lines = ["AVOID THESE DEADLY SITUATIONS:"]
        for d in deaths:
            lines.append(f"  - Turn {d['turn']}: Command '{d['command']}' in {d['room']}")
            lines.append(f"    Result: {d['output_snippet'][:100]}...")
        return "\n".join(lines)

    def _format_room_connections(self) -> str:
        """Format learned room connections for the prompt (especially useful for mazes)"""
        if not self.room_connections:
            return "No room connections learned yet."

        lines = []
        for from_room, connections in list(self.room_connections.items())[:20]:
            from_name = self.room_names.get(from_room, f"Room {from_room}")
            conn_strs = []
            for direction, to_room in connections.items():
                to_name = self.room_names.get(str(to_room), f"Room {to_room}")
                conn_strs.append(f"{direction}→{to_room}({to_name})")
            lines.append(f"  From {from_room} ({from_name}): {', '.join(conn_strs)}")

        if len(self.room_connections) > 20:
            lines.append(f"  ... and {len(self.room_connections) - 20} more connections")

        return "\n".join(lines) if lines else "No room connections learned yet."

    def _format_hints_section(self) -> str:
        """Format hints/walkthrough section for the prompt"""
        if not self.hints:
            return ""

        return f"""WALKTHROUGH/HINTS (USE THIS!):
==============================
The following is a human-written walkthrough for this game. Follow these commands
in order, adapting as needed based on the current game state:

{self.hints}

IMPORTANT: The walkthrough commands above are your PRIMARY guide. Follow them closely!
"""

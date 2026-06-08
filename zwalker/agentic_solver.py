"""
Agentic IF solver — "Plan B".

A proper perceive -> decide -> act -> verify agent for Z-machine games, built
ON TOP of the already-working pieces:

  * GameWalker  (zwalker/walker.py)   — try_command(), room detection by object
                                         number, the learned map/room graph.
  * ZMachine    (zwalker/zmachine.py) — get_score/get_turns/get_max_score,
                                         get_inventory, save_state/restore_state,
                                         get_objects_in_room/object tree.
  * extract_json + the score/goal prompt framing (zwalker/advanced_solver.py).

The existing AdvancedAISolver.solve() is left untouched; this is a NEW class.

Four components (see the four numbered sections below):

  1. AgenticSolver.solve()  — the PERCEIVE -> DECIDE -> EXECUTE ONE -> VERIFY loop.
  2. Deterministic navigation — WorldModel.path_to() (BFS) + AgenticSolver.go_to(),
     exposed to the planner as the meta-action  go to <room name>.
  3. WorldModel              — structured, compact, serializable world state.
  4. Checkpoint/backtracking — a stack of save_state() snapshots; restore to the
     best-scoring promising checkpoint when score stalls or on death, and mark
     the failed branch so it is not retried.

A pluggable `decider` lets the whole thing run for FREE with a local/stubbed
decider (no Anthropic API). `make_opus_decider()` returns a decider that calls
Claude Opus 4.8 for real LLM runs.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .walker import GameWalker, _normalize_direction, CANONICAL_DIRECTIONS
from .advanced_solver import extract_json


# Directions the parser understands as movement (used to tell a navigation
# meta-action apart from a normal verb-noun command).
_MOVE_WORDS = set(CANONICAL_DIRECTIONS) | {
    "n", "s", "e", "w", "ne", "nw", "se", "sw", "u", "d", "in", "out",
}

# Substrings that mean "the parser/world rejected this command" — a no-op we
# must record so we never replay it from the same room.
_REJECT_MARKERS = (
    "i don't know the word",
    "i don't understand",
    "that's not a verb",
    "you can't see any such thing",
    "there's nothing here",
    "you can't go that way",
    "you can't go",
    "nothing happens",
    "i beg your pardon",
    "that sentence isn't one i recognize",
)

_DEATH_MARKERS = (
    "you have died",
    "you are dead",
    "you have been killed",
    "that last blow was too much",
    "*** you have died ***",
    "you clearly are a suicidal maniac",
)


# =============================================================================
# 3. STRUCTURED WORLD MODEL
# =============================================================================

@dataclass
class WMRoom:
    """A room in the world model (mirrors the walker's room, kept separate so
    the agent owns its own view and can annotate it freely)."""
    id: int
    name: str
    # All exits the walker believes exist (includes inferred reverse edges).
    exits: Dict[str, int] = field(default_factory=dict)        # dir -> room_id
    # Edges the AGENT itself traversed and verified (dir -> dest). Only these
    # are trusted for go_to(), because IF exits are frequently asymmetric
    # (Zork: North-of-House south does NOT return to West-of-House) and the
    # walker's auto-added reverse edges would otherwise mislead navigation.
    verified_exits: Dict[str, int] = field(default_factory=dict)
    objects_seen: Set[str] = field(default_factory=set)        # object names
    blocked_dirs: Set[str] = field(default_factory=set)


@dataclass
class WorldModel:
    """
    Structured, agent-owned model of the game world.

    Updated every turn from the parsed response + vm.get_inventory() + the
    object tree.  Serialized COMPACTLY (not raw transcript) for the planner.
    """
    rooms: Dict[int, WMRoom] = field(default_factory=dict)
    # object name -> room_id (int) or the literal string 'inventory'
    object_locations: Dict[str, Any] = field(default_factory=dict)
    # observable open/closed state for containers & doors, when seen in text
    container_state: Dict[str, str] = field(default_factory=dict)   # name -> 'open'|'closed'
    # (room_id, normalized_action) -> outcome string
    tried_actions: Dict[Tuple[int, str], str] = field(default_factory=dict)
    # explicit sub-goal / task stack (top of stack == current focus)
    task_stack: List[str] = field(default_factory=list)
    # score history as (turn, score)
    score_history: List[Tuple[int, int]] = field(default_factory=list)
    # branches we restored away from: (room_id, action) we must not retry
    dead_branches: Set[Tuple[int, str]] = field(default_factory=set)
    # the deposit point once discovered (room_id), e.g. Zork trophy-case room
    deposit_room: Optional[int] = None

    # ---- updates -----------------------------------------------------------

    def observe_room(self, room_id: int, name: str,
                     exits: Dict[str, int], objects: List[str],
                     blocked: Set[str]) -> None:
        wr = self.rooms.get(room_id)
        if wr is None:
            wr = WMRoom(id=room_id, name=name)
            self.rooms[room_id] = wr
        wr.name = name or wr.name
        for d, dest in exits.items():
            wr.exits[d] = dest
        wr.blocked_dirs |= set(blocked)
        # Drop any inferred (unverified) edge now known to be blocked.
        for d in blocked:
            if d not in wr.verified_exits:
                wr.exits.pop(d, None)
        for obj in objects:
            wr.objects_seen.add(obj)
            # An object physically present in a room lives there (unless we are
            # holding it — inventory is set explicitly by sync_inventory()).
            if self.object_locations.get(obj) != "inventory":
                self.object_locations[obj] = room_id

    def sync_inventory(self, inv_names: List[str]) -> None:
        """Authoritative inventory from vm.get_inventory(): these are held now,
        and anything previously 'inventory' that is no longer held was dropped
        (its location becomes unknown until re-observed)."""
        held = set(inv_names)
        for name in held:
            self.object_locations[name] = "inventory"
        for name, loc in list(self.object_locations.items()):
            if loc == "inventory" and name not in held:
                # Dropped/placed somewhere; mark unknown, room observation fixes it.
                del self.object_locations[name]

    def record_move(self, from_room: int, direction: str, to_room: int) -> None:
        """Record an edge the agent ACTUALLY traversed (verified). These are the
        only edges go_to()/path_to() trust."""
        wr = self.rooms.get(from_room)
        if wr is None:
            wr = WMRoom(id=from_room, name="")
            self.rooms[from_room] = wr
        nd = _normalize_direction(direction) or direction.strip().lower()
        wr.verified_exits[nd] = to_room
        wr.exits[nd] = to_room

    def record_action(self, room_id: int, action: str, outcome: str) -> None:
        norm = _norm_action(action)
        self.tried_actions[(room_id, norm)] = outcome

    def action_outcome(self, room_id: int, action: str) -> Optional[str]:
        return self.tried_actions.get((room_id, _norm_action(action)))

    def note_score(self, turn: int, score: int) -> None:
        if not self.score_history or self.score_history[-1][1] != score:
            self.score_history.append((turn, score))

    def push_goal(self, goal: str) -> None:
        if goal and (not self.task_stack or self.task_stack[-1] != goal):
            self.task_stack.append(goal)

    def current_goal(self) -> Optional[str]:
        return self.task_stack[-1] if self.task_stack else None

    # ---- deterministic navigation (component 2: the graph half) ------------

    def path_to(self, start_room: int, target_room: int,
                trust: str = "verified") -> Optional[List[str]]:
        """BFS over known edges -> ordered list of directions, or None.

        Empty list means already there.  This is the navigation core used by
        AgenticSolver.go_to().  By default it uses ONLY verified edges (ones the
        agent itself traversed), so a returned path is guaranteed walkable on
        the known map even though IF exits are often asymmetric.  Pass
        trust="all" to also use the walker's inferred reverse edges.
        """
        if start_room == target_room:
            return []
        if start_room not in self.rooms:
            return None
        visited = {start_room}
        queue: deque = deque([(start_room, [])])
        while queue:
            rid, path = queue.popleft()
            room = self.rooms.get(rid)
            if room is None:
                continue
            edges = room.verified_exits if trust == "verified" else room.exits
            for direction, dest in edges.items():
                if dest == target_room:
                    return path + [direction]
                if dest not in visited:
                    visited.add(dest)
                    queue.append((dest, path + [direction]))
        return None

    def find_room_by_name(self, name: str) -> Optional[int]:
        """Resolve a (case-insensitive, substring) room NAME to a room id, so
        the planner can say "go to Living Room" without remembering directions."""
        if not name:
            return None
        q = name.strip().lower()
        # exact first
        for rid, room in self.rooms.items():
            if room.name.lower() == q:
                return rid
        for rid, room in self.rooms.items():
            if q in room.name.lower():
                return rid
        return None

    # ---- compact serialization for the planner prompt ----------------------

    def summary(self, current_room: int, max_rooms: int = 25) -> str:
        """A COMPACT textual summary for the planner (never the raw transcript)."""
        lines: List[str] = []
        cur = self.rooms.get(current_room)
        lines.append(f"current_room: {current_room} "
                     f"({cur.name if cur else '?'})")
        if self.task_stack:
            lines.append("goal_stack: " + " > ".join(self.task_stack[-4:]))
        if self.deposit_room is not None:
            dn = self.rooms.get(self.deposit_room)
            lines.append(f"deposit_point: room {self.deposit_room} "
                         f"({dn.name if dn else '?'})")
        # inventory + where known treasures are
        inv = [n for n, loc in self.object_locations.items() if loc == "inventory"]
        lines.append("carrying: " + (", ".join(sorted(inv)) or "(nothing)"))
        # rooms (id, name, exits, untried-ness)
        lines.append("known_rooms:")
        for rid in list(self.rooms)[:max_rooms]:
            room = self.rooms[rid]
            ex = ", ".join(f"{d}->{dst}" for d, dst in room.exits.items()) or "none"
            objs = ", ".join(sorted(room.objects_seen)[:6]) or "-"
            marker = " *HERE*" if rid == current_room else ""
            lines.append(f"  [{rid}] {room.name}{marker} | exits: {ex} | objs: {objs}")
        if len(self.rooms) > max_rooms:
            lines.append(f"  ... +{len(self.rooms) - max_rooms} more rooms")
        if self.dead_branches:
            db = list(self.dead_branches)[:8]
            lines.append("avoid (dead branches): "
                         + ", ".join(f"{r}:{a}" for r, a in db))
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rooms": {rid: {"name": r.name, "exits": r.exits,
                            "objects_seen": sorted(r.objects_seen)}
                      for rid, r in self.rooms.items()},
            "object_locations": dict(self.object_locations),
            "task_stack": list(self.task_stack),
            "score_history": list(self.score_history),
            "deposit_room": self.deposit_room,
        }


def _norm_action(action: str) -> str:
    """Normalize an action for the tried-actions table: movement collapses to
    its canonical direction; everything else is lowercased/stripped."""
    nd = _normalize_direction(action)
    if nd is not None:
        return nd
    return " ".join(action.lower().split())


# =============================================================================
# PERCEPTION + DECISION DATA
# =============================================================================

@dataclass
class Perception:
    """Everything the agent perceives at the start of a turn (component 1)."""
    turn: int
    room_id: int
    room_name: str
    room_description: str
    inventory: List[str]
    score: int
    max_score: Optional[int]
    visible_objects: List[str]
    known_exits: Dict[str, int]
    untried_directions: List[str]
    blocked_directions: List[str]
    last_command: str
    last_response: str
    world_summary: str
    dictionary_verbs: List[str]
    available_nouns: List[str]


@dataclass
class Decision:
    """What DECIDE returns: the next action plus an explicit sub-goal.

    `action` is one Z-machine command OR a navigation meta-action of the form
    "go to <room name or id>" which the solver resolves deterministically.
    `plan` is an optional short ordered list of follow-up actions (the solver
    still executes ONE at a time and re-perceives, but a plan lets a cheap
    local decider avoid re-deciding every step).
    """
    action: str
    subgoal: str = ""
    plan: List[str] = field(default_factory=list)
    reasoning: str = ""


# Type of a decider: (Perception) -> Decision
Decider = Callable[[Perception], Decision]


# =============================================================================
# THE AGENT
# =============================================================================

@dataclass
class _Checkpoint:
    """A tree-search checkpoint (component 4)."""
    vm_state: Any
    room_id: int
    score: int
    turn: int
    world: WorldModel       # shallow snapshot reference (we re-derive on restore)
    label: str = ""


class AgenticSolver:
    """
    Perceive -> Decide -> Execute ONE -> Verify agent.

    Invoke headlessly:

        from zwalker.agentic_solver import AgenticSolver
        result = AgenticSolver(game_data).solve(max_turns=200)

    Pass an Opus decider for a real LLM run (see make_opus_decider):

        result = AgenticSolver(game_data,
                               decider=make_opus_decider()).solve(max_turns=400)

    Returns the SAME result-dict shape as AdvancedAISolver.solve():
        final_score, best_score, max_score, rooms_explored, game_won,
        final_inventory, turns_taken, commands.
    """

    def __init__(self, game_data: bytes,
                 decider: Optional[Decider] = None,
                 verbose: bool = False,
                 stall_limit: int = 12,
                 max_seconds: Optional[float] = None):
        self.walker = GameWalker(game_data)
        self.vm = self.walker.vm
        self.world = WorldModel()
        self.decider: Decider = decider or local_decider
        self.verbose = verbose
        # K: turns of no score improvement before we backtrack a branch.
        self.stall_limit = stall_limit
        # OPTIONAL wall-clock cap (seconds). Default None == unbounded, so
        # max_turns is the real limiter; solve(max_seconds=...) can override.
        self.max_seconds = max_seconds

        self.turn = 0
        self.best_score = 0
        self.game_won = False
        self.commands: List[str] = []

        # component 4: checkpoint stack + best-seen checkpoint
        self.checkpoints: List[_Checkpoint] = []
        self.best_checkpoint: Optional[_Checkpoint] = None
        self._turns_since_score = 0

    # ---- logging -----------------------------------------------------------

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg)

    # ---- 1. PERCEIVE -------------------------------------------------------

    def perceive(self, last_command: str = "", last_response: str = "") -> Perception:
        room = self.walker.rooms.get(self.walker.current_room_id)
        inv = [name for _, name in self.vm.get_inventory()]
        score = self.vm.get_score()

        # dictionary verbs (reuse the walker's categorization)
        try:
            by_type = self.vm.get_dictionary_words_by_type()
            verbs = by_type.get("verbs", []) + by_type.get("directions", [])
            verbs = list(dict.fromkeys(v for v in verbs if v and v[0].isalpha()))
        except Exception:
            verbs = []

        visible = [name for _, name in room.objects] if room else []
        nouns = list(dict.fromkeys(
            (n.split()[0].lower() if n else n) for n in (visible + inv)))

        return Perception(
            turn=self.turn,
            room_id=self.walker.current_room_id,
            room_name=room.name if room else "Unknown",
            room_description=room.description if room else "",
            inventory=inv,
            score=score,
            max_score=self.walker.max_score,
            visible_objects=visible,
            known_exits=dict(room.exits) if room else {},
            untried_directions=room.untried_directions() if room else [],
            blocked_directions=sorted(room.blocked_directions) if room else [],
            last_command=last_command,
            last_response=last_response,
            world_summary=self.world.summary(self.walker.current_room_id),
            dictionary_verbs=verbs,
            available_nouns=nouns,
        )

    def _sync_world_from_perception(self) -> None:
        """Fold the current room/inventory/objects into the world model."""
        room = self.walker.rooms.get(self.walker.current_room_id)
        if room is None:
            return
        self.world.observe_room(
            room_id=room.id,
            name=room.name,
            exits=dict(room.exits),
            objects=[name for _, name in room.objects],
            blocked=set(room.blocked_directions),
        )
        self.world.sync_inventory([n for _, n in self.vm.get_inventory()])
        # Heuristic: remember a trophy-case / deposit room when we see one.
        if self.world.deposit_room is None:
            low = (room.name + " " + (room.description or "")).lower()
            if "trophy case" in low or "case" in {o.lower() for o in
                                                  (name for _, name in room.objects)}:
                self.world.deposit_room = room.id

    # ---- 2. DETERMINISTIC NAVIGATION --------------------------------------

    def go_to(self, target: Any) -> Tuple[bool, str]:
        """
        Navigate to a known room by id or name, executing the BFS move sequence
        and VERIFYING each step lands in the expected room.  Returns
        (arrived, info).  If a move is blocked / lands somewhere unexpected we
        stop and re-probe (the caller re-perceives and re-plans).
        """
        target_id = target if isinstance(target, int) else \
            self.world.find_room_by_name(str(target))
        if target_id is None:
            return False, f"unknown target {target!r}"

        start = self.walker.current_room_id
        path = self.world.path_to(start, target_id)
        if path is None:
            return False, f"no known path {start}->{target_id}"
        if path == []:
            return True, "already there"

        # Each step's expected destination comes from a VERIFIED edge, so we can
        # check that the move actually lands where the map promised.
        for direction in path:
            wr = self.world.rooms.get(self.walker.current_room_id)
            expected = wr.verified_exits.get(direction) if wr else None
            res = self._do(direction)
            if res is None:
                return False, f"vm error on '{direction}'"
            now = self.walker.current_room_id
            if expected is not None and now != expected:
                # Move blocked or non-deterministic (maze/locked door): bail so
                # the agent re-perceives the real situation and replans.
                return False, (f"step '{direction}' expected room {expected} "
                               f"but landed in {now}")
        arrived = self.walker.current_room_id == target_id
        return arrived, ("arrived" if arrived else
                         f"ended in {self.walker.current_room_id}, wanted {target_id}")

    # ---- raw command execution (isolates VM errors) ------------------------

    def _do(self, command: str):
        """Execute ONE walker command, isolating interpreter errors so one bad
        opcode can't abort the run (mirrors solve_local/execute_strategy)."""
        pre = self.vm.save_state()
        pre_room = self.walker.current_room_id
        try:
            result = self.walker.try_command(command)
        except Exception as e:  # noqa: BLE001 - includes ZMachineError
            try:
                self.vm.restore_state(pre)
            except Exception:
                pass
            self.walker.current_room_id = pre_room
            self.turn += 1
            self.commands.append(command)
            self._log(f"  {self.turn:4d} > {command:<20} [vm-error: {e}]")
            return None
        self.turn += 1
        self.commands.append(command)
        # If this was a movement command that actually changed rooms, record the
        # VERIFIED edge so go_to()/path_to() can trust it.
        now = self.walker.current_room_id
        if now != pre_room:
            nd = _normalize_direction(command)
            if nd is not None:
                self.world.record_move(pre_room, nd, now)
        return result

    # ---- 4. CHECKPOINTS / BACKTRACKING ------------------------------------

    def checkpoint(self, label: str = "") -> None:
        cp = _Checkpoint(
            vm_state=self.vm.save_state(),
            room_id=self.walker.current_room_id,
            score=self.vm.get_score(),
            turn=self.turn,
            world=self.world,
            label=label,
        )
        self.checkpoints.append(cp)
        if len(self.checkpoints) > 40:
            self.checkpoints.pop(0)
        if self.best_checkpoint is None or cp.score >= self.best_checkpoint.score:
            self.best_checkpoint = cp

    def _restore(self, cp: _Checkpoint, reason: str) -> None:
        self.vm.restore_state(cp.vm_state)
        self.walker.current_room_id = cp.room_id
        self.walker.score = self.vm.get_score()
        self._turns_since_score = 0
        self._log(f"  ⤺ BACKTRACK ({reason}) -> room {cp.room_id} "
                  f"score {cp.score} (saved at turn {cp.turn})")

    def backtrack(self, failed_action: Optional[str], reason: str,
                  failed_room: Optional[int] = None) -> bool:
        """Restore to the best promising checkpoint and mark the failed branch
        so it is not repeated.  `failed_room` is the room the action was ISSUED
        from (defaults to the current room); marking it there means the agent
        won't re-issue the fatal/stalling action after it restores back to that
        same room.  Returns True if it restored."""
        if failed_action is not None:
            room = failed_room if failed_room is not None \
                else self.walker.current_room_id
            self.world.dead_branches.add((room, _norm_action(failed_action)))
        target = self.best_checkpoint
        # Prefer a checkpoint strictly BEFORE the current point if best == now.
        if target is None or target.turn >= self.turn:
            # fall back to an earlier checkpoint on the stack
            for cp in reversed(self.checkpoints):
                if cp.turn < self.turn:
                    target = cp
                    break
        if target is None:
            return False
        self._restore(target, reason)
        self._sync_world_from_perception()
        return True

    # ---- meta-action resolution -------------------------------------------

    def _is_nav_meta(self, action: str) -> Optional[str]:
        """If `action` is a 'go to <room>' meta-action, return the target token,
        else None."""
        a = action.strip().lower()
        for prefix in ("go to ", "goto ", "navigate to ", "return to ",
                       "travel to "):
            if a.startswith(prefix):
                return action.strip()[len(prefix):].strip()
        return None

    def _execute_action(self, action: str) -> Tuple[Optional[Any], bool]:
        """Execute one decided action (command or nav meta-action).

        Returns (result_or_None, is_navigation).  For navigation, result is a
        synthetic object carrying the final room's last output is not needed —
        the caller re-perceives — so we return (None, True) and let VERIFY read
        live state.
        """
        nav_target = self._is_nav_meta(action)
        if nav_target is not None:
            # resolve "<id>" or "<name>"
            target: Any = int(nav_target) if nav_target.isdigit() else nav_target
            turn_before = self.turn
            arrived, info = self.go_to(target)
            self._log(f"  {self.turn:4d} > go_to({nav_target}) [{info}]")
            if self.turn == turn_before:
                # Zero-move navigation (already there / no known path) advanced
                # no game turn. Consume a turn anyway so the loop can't spin
                # re-deciding the same dead nav forever (the spin bug), and mark
                # it dead so it isn't re-proposed from this room.
                self.turn += 1
                self.commands.append(action)
                self.world.dead_branches.add(
                    (self.walker.current_room_id, _norm_action(action)))
            return None, True
        return self._do(action), False

    # ---- 1. THE LOOP -------------------------------------------------------

    def solve(self, max_turns: int = 200, max_seconds: Optional[float] = None,
              checkpoint_every: int = 8) -> Dict[str, Any]:
        """
        Main perceive->decide->execute-ONE->verify loop with PLAN CACHING.

        max_turns is the primary limiter. max_seconds is an OPTIONAL wall-clock
        cap (seconds); when None (the default, also overridable via the
        constructor's max_seconds=) the run is bounded ONLY by max_turns — so a
        120-turn run actually runs ~120 turns instead of being silently cut off
        by an internal ~300s budget. Pass max_seconds=... (here or to the
        constructor) to bound wall-clock for, e.g., expensive LLM deciders.

        PLAN CACHING: the decider returns Decision(action, subgoal, plan). We
        seed a `current_plan` queue from action+plan and POP from it on
        subsequent turns WITHOUT re-consulting the decider, as long as we are
        "on track" (last command was not a reject/no-op/death and the queue is
        non-empty). The decider is re-consulted (and the queue refilled) ONLY
        when genuinely needed: empty queue, a reject/no-op/dead-branch, or a
        notable event (death, score change, new room) that warrants replanning.
        This cuts LLM calls/turn well below 1 when plans are long, with no
        change to VERIFY / world-model / checkpoint / backtrack behavior, which
        still run every turn regardless of whether the decider was consulted.

        Returns the AdvancedAISolver-compatible result dict.
        """
        # Resolve the optional wall-clock cap (call arg overrides constructor).
        budget = max_seconds if max_seconds is not None else self.max_seconds
        start_time = time.time()

        # Start the game and seed the world model.
        first_output = self.walker.start()
        self.best_score = self.vm.get_score()
        self.world.note_score(0, self.best_score)
        self._sync_world_from_perception()
        self.checkpoint("start")

        last_command, last_response = "", first_output
        stall_reason = "turn budget reached"

        # PLAN-CACHE state.
        current_plan: deque = deque()    # queued backup/follow-on commands
        current_subgoal = ""             # subgoal of the in-flight plan
        decider_calls = 0                # instrumentation (calls-per-turn)
        # Whether the last executed command kept us "on track" (benign result).
        on_track = False

        def _useless(a: str, here: int) -> bool:
            # No nav-meta exemption: a "go to X" that already went nowhere from
            # here is as useless as any other no-op. Exempting nav-metas was the
            # source of the spin (the decider could re-propose a dead nav forever).
            if (here, _norm_action(a)) in self.world.dead_branches:
                return True
            return self.world.action_outcome(here, a) in ("reject", "noop", "nav-noop")

        while self.turn < max_turns:
            if budget is not None and time.time() - start_time > budget:
                stall_reason = "wall-clock budget reached"
                break
            if self.walker.max_score is not None and \
                    self.vm.get_score() >= self.walker.max_score:
                self.game_won = True
                stall_reason = "won (max score reached)"
                break

            here = self.walker.current_room_id

            # --- CHOOSE NEXT ACTION (plan-cache vs. decider) ---
            # Reuse the cached plan WITHOUT calling the decider when we are on
            # track and the queue still has a usable command. Otherwise consult
            # the decider once and refill the queue from action+plan.
            action: Optional[str] = None
            if on_track and current_plan:
                # Pop usable queued commands; drop known-dead ones WITHOUT
                # burning a turn or immediately re-calling the decider.
                while current_plan:
                    cand = current_plan.popleft()
                    if cand and not _useless(cand, here):
                        action = cand
                        break

            if action is None:
                # --- PERCEIVE + DECIDE (refill the queue) ---
                perception = self.perceive(last_command, last_response)
                decision = self.decider(perception)
                decider_calls += 1
                current_subgoal = decision.subgoal
                if decision.subgoal:
                    self.world.push_goal(decision.subgoal)

                # Seed the queue from action followed by the ordered plan, and
                # take the first usable command. Falls through to the raw action
                # if everything is useless (stall/backtrack machinery then runs).
                current_plan = deque(
                    [decision.action] + list(decision.plan or []))
                while current_plan:
                    cand = current_plan.popleft()
                    if cand and not _useless(cand, here):
                        action = cand
                        break
                if action is None:
                    action = decision.action
            elif current_subgoal:
                # Keep the in-flight subgoal current while consuming the plan.
                self.world.push_goal(current_subgoal)

            score_before = self.vm.get_score()
            room_before = self.walker.current_room_id
            inv_before = set(n for _, n in self.vm.get_inventory())

            # --- EXECUTE ONE ---
            result, was_nav = self._execute_action(action)

            # --- VERIFY ---
            last_command = action
            if was_nav:
                last_response = "(navigation)"
            else:
                last_response = result.output if result is not None else "(vm-error)"

            self._sync_world_from_perception()

            score_after = self.vm.get_score()
            room_after = self.walker.current_room_id
            inv_after = set(n for _, n in self.vm.get_inventory())
            score_delta = score_after - score_before
            room_changed = room_after != room_before
            inv_gained = inv_after - inv_before
            inv_lost = inv_before - inv_after

            self.world.note_score(self.turn, score_after)

            # Record the action's real outcome (so we never repeat a no-op).
            outcome = self._classify(result, was_nav, score_delta,
                                     room_changed, inv_gained, inv_lost,
                                     last_response)
            self.world.record_action(room_before, action, outcome)

            # progress accounting
            if score_after > self.best_score:
                self.best_score = score_after
                self._turns_since_score = 0
                self.checkpoint(f"score={score_after}")
            elif score_delta > 0:
                self._turns_since_score = 0
            else:
                self._turns_since_score += 1

            self._log_turn(action, was_nav, score_delta, score_after,
                           room_changed, room_after, inv_gained, last_response)

            # On-track? A turn is "on track" (the cached plan may continue
            # WITHOUT re-deciding) when the command was NOT a reject/no-op/
            # dead-branch, did not die, and produced no notable event (a score
            # change or reaching a genuinely new room) that warrants fresh
            # planning. Notable events / rejects drop the cached plan so the
            # next turn re-consults the decider.
            is_reject_outcome = outcome in ("reject", "noop", "nav-noop",
                                            "vm-error")
            # A room change is a fresh decision point: the queued plan is keyed
            # to the room it was made in (its take/open/examine target the old
            # room's objects), so replan on ANY room change. A score change is
            # also notable. Same-room benign actions (examine/open/push/...) and
            # nav meta-actions keep the cached plan flowing without a decider
            # call — that is where the calls/turn savings come from.
            notable = (score_delta != 0) or room_changed
            on_track = (not is_reject_outcome) and (not notable)
            if not on_track:
                current_plan.clear()

            # death -> backtrack immediately. Mark the branch at the room the
            # fatal action was ISSUED FROM (room_before), so after the restore
            # lands us back there we don't re-issue the same fatal command.
            if self._is_death(last_response):
                self._log(f"  ✗ DEATH after '{action}'")
                current_plan.clear()
                on_track = False
                if not self.backtrack(action, "death", failed_room=room_before):
                    stall_reason = "died with no checkpoint"
                    break
                last_command, last_response = "", "(restored after death)"
                continue

            # periodic checkpoint at decision points
            if self.turn % checkpoint_every == 0:
                self.checkpoint(f"turn={self.turn}")

            # stall -> backtrack to the best promising branch, mark dead branch.
            # Only do this once we actually have a promising (positive-score)
            # checkpoint to return to. Before the first point, restoring to the
            # zero-score start just re-loops; instead keep exploring forward
            # (the dead-branch / no-op gate still prevents pure spinning).
            have_promising = (self.best_checkpoint is not None
                              and self.best_checkpoint.score > 0)
            if self._turns_since_score >= self.stall_limit and have_promising:
                self._log(f"  ⚠ stalled {self._turns_since_score} turns")
                current_plan.clear()
                on_track = False
                if self.backtrack(action, "score stall", failed_room=room_before):
                    last_command, last_response = "", "(restored after stall)"
                    continue
                else:
                    stall_reason = "stalled with no earlier checkpoint"
                    break
            elif self._turns_since_score >= self.stall_limit:
                # No promising checkpoint yet: reset the stall counter so we keep
                # exploring forward rather than thrashing the backtrack.
                self._turns_since_score = 0

        elapsed = round(time.time() - start_time, 1)
        if self.walker.max_score is not None and \
                self.vm.get_score() >= self.walker.max_score:
            self.game_won = True

        return {
            "game_won": self.game_won,
            "final_score": self.vm.get_score(),
            "best_score": self.best_score,
            "max_score": self.walker.max_score,
            "rooms_explored": len(self.walker.rooms),
            "final_inventory": [name for _, name in self.vm.get_inventory()],
            "turns_taken": self.turn,
            "commands": list(self.commands),
            "stall_reason": stall_reason,
            "elapsed_sec": elapsed,
            "decider_calls": decider_calls,
            "calls_per_turn": round(decider_calls / max(self.turn, 1), 3),
            "world_model": self.world.to_dict(),
        }

    # ---- VERIFY helpers ----------------------------------------------------

    @staticmethod
    def _is_death(text: str) -> bool:
        low = (text or "").lower()
        return any(m in low for m in _DEATH_MARKERS)

    @staticmethod
    def _is_reject(text: str) -> bool:
        low = (text or "").lower()
        return any(m in low for m in _REJECT_MARKERS)

    def _classify(self, result, was_nav: bool, score_delta: int,
                  room_changed: bool, inv_gained: Set[str],
                  inv_lost: Set[str], text: str) -> str:
        if was_nav:
            return "navigated" if room_changed else "nav-noop"
        if result is None:
            return "vm-error"
        if score_delta > 0:
            return f"score+{score_delta}"
        if inv_gained:
            return "took:" + ",".join(sorted(inv_gained))
        if inv_lost:
            return "dropped:" + ",".join(sorted(inv_lost))
        if room_changed:
            return "moved"
        if self._is_reject(text):
            return "reject"
        return "noop"

    def _log_turn(self, action, was_nav, score_delta, score_after,
                  room_changed, room_after, inv_gained, text) -> None:
        if not self.verbose or was_nav:
            return
        tag = ""
        if score_delta > 0:
            tag = f" [+{score_delta} -> {score_after}]"
        elif inv_gained:
            tag = f" [took {','.join(sorted(inv_gained))}]"
        elif room_changed:
            tag = f" [-> room {room_after}]"
        elif self._is_reject(text):
            tag = " [reject]"
        self._log(f"  {self.turn:4d} > {action:<20}{tag}")


# =============================================================================
# 2 (cont.) + DECIDERS
# =============================================================================

def local_decider(p: Perception) -> Decision:
    """
    FREE, stubbed decider (no API).  Score-greedy + deterministic-nav aware.

    Priority each turn:
      1. If carrying treasures and a deposit point is known and we are NOT there,
         request the navigation meta-action  "go to <deposit room>".
      2. take all  (cheap score in treasure games), once per room.
      3. turn on a carried lamp/lantern (Zork needs light).
      4. an untried, non-blocked movement direction (discover rooms).
      5. examine/open visible objects we haven't acted on here.
      6. a known exit toward the frontier (rooms with untried exits).

    It consults Perception.world_summary only indirectly (it works off the
    structured fields the solver passes in), but crucially it emits the SAME
    Decision shape an LLM decider does, so the loop is identical either way.
    """
    room_id = p.room_id

    # 4/6 candidate directions
    untried = [d for d in p.untried_directions if d not in p.blocked_directions]

    # 2) take all — only suggest once per room (the solver records tried actions,
    #    but the decider is stateless, so we gate on whether anything is takeable).
    plan: List[str] = []

    # 3) lamp
    inv_low = " ".join(p.inventory).lower()
    lamp_word = ("lamp" if "lamp" in inv_low else
                 "lantern" if "lantern" in inv_low else
                 "light" if "light" in inv_low else None)

    # 5) object interactions on visible objects (examine/open/move).
    obj_cmds: List[str] = []
    for obj in p.visible_objects:
        head = obj.split()[0].lower() if obj else ""
        if not head:
            continue
        obj_cmds += [f"open {head}", f"move {head}", f"examine {head}"]

    # 5b) Description-driven interaction hints — the SAME table the proven local
    #     analyzer (ai_assist._analyze_local) uses, so the stub decider can do
    #     score-bearing things like enter the house (open window/enter), reveal
    #     the trap door (move rug) and descend (open trap door / down).
    desc_words = set(w.strip(".,!?;:'\"()").lower()
                     for w in (p.room_description or "").split())
    interactive_hints = {
        "window": ["open window", "enter"],
        "door": ["open door", "unlock door"],
        "rug": ["move rug", "look under rug"],
        "trap": ["open trap door", "down"],
        "trapdoor": ["open trapdoor", "down"],
        "grating": ["open grating", "down"],
        "case": ["open case"],
        "mailbox": ["open mailbox", "read leaflet"],
        "egg": ["take egg", "open egg"],
        "chest": ["open chest"],
        "button": ["push button"],
        "lever": ["pull lever"],
    }
    hint_cmds: List[str] = []
    for noun, cmds in interactive_hints.items():
        if noun in desc_words:
            hint_cmds += cmds

    # Assemble an ordered candidate list; the solver executes the first that is
    # not a known dead branch / prior no-op (it passes alternatives via plan).
    candidates: List[str] = []
    candidates.append("take all")
    if lamp_word:
        candidates.append(f"turn on {lamp_word}")
    candidates += obj_cmds[:6]
    candidates += hint_cmds
    candidates += untried[:2]
    candidates += untried[2:]
    candidates += list(p.known_exits.keys())
    candidates += ["look"]

    # de-dup preserving order
    seen: Set[str] = set()
    ordered = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            ordered.append(c)

    action = ordered[0] if ordered else "look"
    subgoal = "explore and grab score" if not p.inventory else "explore / deposit"
    return Decision(action=action, subgoal=subgoal, plan=ordered[1:14],
                    reasoning="local score-greedy heuristic")


def make_opus_decider(model: str = "claude-opus-4-8",
                      max_tokens: int = 1200,
                      client: Any = None) -> Decider:
    """
    Build an LLM decider backed by Claude Opus 4.8.

    This is the ONLY place that would call the Anthropic API.  It is NOT used by
    the free verification; pass the returned callable as
    AgenticSolver(game_data, decider=make_opus_decider()).

    The decider asks for the NEXT single action (or a short ordered plan) WITH
    an explicit sub-goal, framed by the score/deposit guidance from
    advanced_solver, and parses the reply with the hardened extract_json.
    """
    import os
    if client is None:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        client = anthropic.Anthropic(api_key=api_key)

    def decide(p: Perception) -> Decision:
        score_str = (f"{p.score}/{p.max_score}" if p.max_score is not None
                     else str(p.score))
        verbs = ", ".join(p.dictionary_verbs[:60]) or "(unknown)"
        nouns = ", ".join(p.available_nouns) or "none"
        untried = ", ".join(p.untried_directions) or "none"
        blocked = ", ".join(p.blocked_directions) or "none"

        prompt = f"""You are an expert interactive-fiction agent. Decide the agent's
NEXT SINGLE ACTION (you may also give a short ordered backup plan). Your single
overriding objective is to RAISE THE SCORE.

SCORING MECHANIC: in treasure-hunt IF (Zork family) big points come from
DEPOSITING treasures at the drop-off (Zork's trophy case: "put <item> in case"),
NOT from merely carrying them. If you are holding valuables and the score is
flat, NAVIGATE BACK to the deposit point and deposit each item.

NAVIGATION: instead of remembering directions you may emit the meta-action
"go to <room name>" (or "go to <room id>") and the agent will walk there
deterministically over the known map. Use it to return to the deposit point.

CURRENT PERCEPTION
==================
turn: {p.turn}
score: {score_str}   (best-so-far handled by the agent)
room: {p.room_name} (id {p.room_id})
description: {p.room_description}
visible objects: {', '.join(p.visible_objects) or 'none'}
inventory: {', '.join(p.inventory) or 'empty'}
known exits: {', '.join(f'{d}->{r}' for d, r in p.known_exits.items()) or 'none'}
untried directions (prefer these for new rooms): {untried}
blocked directions (never retry): {blocked}
last command: {p.last_command or '(none)'}
last response: {p.last_response[:300]}

WORD CONSTRAINT — the parser ONLY knows these:
  VERBS: {verbs}
  NOUNS (visible + inventory): {nouns}
Using any other verb/noun wastes a turn. Directions are always allowed, as is
the "go to <room>" meta-action.

WORLD MODEL (compact):
{p.world_summary}

Respond ONLY with JSON:
{{
  "subgoal": "the immediate sub-goal you are pursuing",
  "action": "ONE command or 'go to <room>' meta-action to execute now",
  "plan": ["optional", "ordered", "backup actions"],
  "reasoning": "one sentence why this raises the score / makes progress"
}}"""

        try:
            resp = client.messages.create(
                model=model, max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text
            data = extract_json(text)
            if not isinstance(data, dict) or not data.get("action"):
                # fall back to the local heuristic on a bad/empty reply
                return local_decider(p)
            return Decision(
                action=str(data.get("action", "look")).strip(),
                subgoal=str(data.get("subgoal", "")).strip(),
                plan=[str(s).strip() for s in data.get("plan", []) if s],
                reasoning=str(data.get("reasoning", "")).strip(),
            )
        except Exception:
            # Any API/parse failure degrades gracefully to the free decider.
            return local_decider(p)

    return decide

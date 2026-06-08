"""
AI assistance for interpreting game output and suggesting actions.

This module provides LLM-based analysis of interactive fiction game states
to help with automated exploration.
"""

import os
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class GameContext:
    """Current game state for AI analysis"""
    room_name: str
    room_description: str
    room_id: int
    visible_objects: List[str]
    inventory: List[str]
    exits: Dict[str, int]
    recent_commands: List[str]
    recent_outputs: List[str]
    vocabulary_sample: List[str]  # Sample of available words
    # Exits/score awareness for dictionary-constrained, score-driven solving.
    untried_directions: List[str] = None  # Compass directions not yet tried here
    blocked_directions: List[str] = None  # Directions known to be blocked here
    dictionary_verbs: List[str] = None    # Real verbs from the game's dictionary
    dictionary_words: List[str] = None    # Full dictionary word set
    score: int = 0
    max_score: Optional[int] = None

    def __post_init__(self):
        # Mutable defaults must be normalized to empty lists.
        if self.untried_directions is None:
            self.untried_directions = []
        if self.blocked_directions is None:
            self.blocked_directions = []
        if self.dictionary_verbs is None:
            self.dictionary_verbs = []
        if self.dictionary_words is None:
            self.dictionary_words = []


@dataclass
class AIResponse:
    """Response from AI analysis"""
    suggested_commands: List[str]
    reasoning: str
    objects_of_interest: List[str]
    possible_puzzles: List[str]
    exploration_priority: str  # "high", "medium", "low"


class AIAssistant:
    """
    AI assistant for game exploration.

    Uses an LLM to analyze game state and suggest actions.
    Supports multiple backends (Anthropic Claude, OpenAI, local).
    """

    def __init__(self, backend: str = "anthropic", model: Optional[str] = None):
        """
        Initialize AI assistant.

        Args:
            backend: "anthropic", "openai", or "local"
            model: Model name (defaults based on backend)
        """
        self.backend = backend
        self.model = model
        self._client = None

        if backend == "anthropic":
            self.model = model or "claude-haiku-4-5-20251001"
            self._init_anthropic()
        elif backend == "openai":
            self.model = model or "gpt-3.5-turbo"
            self._init_openai()
        elif backend == "local":
            # For local models, we'll use a simple prompt-based approach
            pass
        else:
            raise ValueError(f"Unknown backend: {backend}")

    def _init_anthropic(self):
        """Initialize Anthropic client"""
        try:
            import anthropic
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self._client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            import openai
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self._client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def _build_prompt(self, context: GameContext) -> str:
        """Build the analysis prompt"""
        if context.exits:
            exits_str = ", ".join(f"{d}: room {rid}" for d, rid in context.exits.items())
        else:
            exits_str = "none discovered yet"
        untried_str = ", ".join(context.untried_directions) if context.untried_directions else "none"
        blocked_str = ", ".join(context.blocked_directions) if context.blocked_directions else "none"
        objects_str = ", ".join(context.visible_objects) if context.visible_objects else "none visible"
        inventory_str = ", ".join(context.inventory) if context.inventory else "empty"
        recent_str = "\n".join(f"> {cmd}\n{out}" for cmd, out in
                               zip(context.recent_commands[-5:], context.recent_outputs[-5:]))

        # Dictionary constraint: the game only understands these verbs/words.
        verbs_str = ", ".join(context.dictionary_verbs[:60]) if context.dictionary_verbs else \
            ", ".join(context.vocabulary_sample[:50])
        # Nouns the parser will accept right now = visible objects + inventory.
        noun_pool = []
        for name in (context.visible_objects or []) + (context.inventory or []):
            noun_pool.append(name.split()[0].lower() if name else name)
        nouns_str = ", ".join(dict.fromkeys(noun_pool)) if noun_pool else "none"
        score_str = f"{context.score}/{context.max_score}" if context.max_score is not None \
            else str(context.score)

        prompt = f"""You are an expert at COMPLETING interactive fiction games. Your goal is to WIN this game (maximize SCORE), not just explore it.

CURRENT ROOM: {context.room_name} (ID: {context.room_id})
DESCRIPTION: {context.room_description}

SCORE: {score_str}
VISIBLE OBJECTS: {objects_str}
INVENTORY: {inventory_str}
KNOWN EXITS: {exits_str}
UNTRIED DIRECTIONS (try these to find new rooms): {untried_str}
BLOCKED DIRECTIONS (do not retry): {blocked_str}

RECENT COMMANDS AND RESPONSES:
{recent_str}

WORD CONSTRAINT — the game's parser ONLY understands these words:
  VERBS you may use: {verbs_str}
  NOUNS available now (visible objects + inventory): {nouns_str}

CRITICAL INSTRUCTIONS:
- ONLY use verbs from the VERBS list above and nouns from the NOUNS list above (or the directions). Using any other word wastes a turn with "I don't know the word".
- Your goal is to RAISE THE SCORE and reach the winning condition.
- Prefer UNTRIED DIRECTIONS to discover new rooms; never retry BLOCKED DIRECTIONS.
- Pick up items ("take all"), examine and open things, turn on a lamp if you have one.
- Read descriptions for clues; unlock doors, solve puzzles, find keys.

Suggest 5-10 commands that will raise the score / win. Prioritize:
1. Actions that directly advance the plot or solve puzzles (score gains)
2. Picking up useful items ("take all")
3. Trying UNTRIED exits to find important areas
4. Examining/opening objects for clues
5. Only fall back to systematic exploration if truly stuck

Respond in JSON format:
{{
    "suggested_commands": ["command1", "command2", ...],
    "reasoning": "brief explanation of how these help WIN the game",
    "objects_of_interest": ["object1", "object2", ...],
    "possible_puzzles": ["puzzle description", ...],
    "exploration_priority": "high/medium/low"
}}
"""
        return prompt

    def analyze(self, context: GameContext) -> AIResponse:
        """
        Analyze game state and get suggestions.

        Args:
            context: Current game context

        Returns:
            AIResponse with suggested commands and analysis
        """
        prompt = self._build_prompt(context)

        if self.backend == "anthropic":
            return self._analyze_anthropic(prompt)
        elif self.backend == "openai":
            return self._analyze_openai(prompt)
        else:
            return self._analyze_local(prompt, context)

    def _analyze_anthropic(self, prompt: str) -> AIResponse:
        """Get analysis from Anthropic Claude"""
        message = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text
        return self._parse_response(response_text)

    def _analyze_openai(self, prompt: str) -> AIResponse:
        """Get analysis from OpenAI"""
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024
        )

        response_text = response.choices[0].message.content
        return self._parse_response(response_text)

    def _analyze_local(self, prompt: str, context: GameContext) -> AIResponse:
        """
        Competent, dictionary-aware, score-greedy local command generator.

        From the current room + inventory it generates:
          - go untried exits (preferring directions not yet attempted),
          - "take all",
          - examine / open / unlock / move / read / push / pull visible nouns,
          - turn on the lamp/lantern if carried,
          - basic state commands (look, inventory),
        and then filters every generated command so that its verb and nouns all
        exist in the game's dictionary. This kills the constant
        'I don't know the word "..."' / 'That's not a verb I recognise' waste.
        """
        dict_words = set(w.lower() for w in (context.dictionary_words or []))
        dict_verbs = set(v.lower() for v in (context.dictionary_verbs or []))

        def dict_has(word: str) -> bool:
            """A word is usable if it (or a 6-char prefix) is in the dictionary.
            Empty dictionary => permissive (don't over-filter)."""
            if not dict_words:
                return True
            w = word.lower()
            if w in dict_words:
                return True
            # Z-machine dictionaries store truncated words (4 chars V1-3, 6 V4+).
            return any(dw.startswith(w[:6]) or w.startswith(dw) for dw in dict_words)

        def verb_ok(verb: str) -> bool:
            if dict_verbs:
                v = verb.lower()
                return v in dict_verbs or any(dv.startswith(v[:6]) for dv in dict_verbs)
            return dict_has(verb)

        def cmd_ok(cmd: str) -> bool:
            """Every token of the command must be dictionary-valid."""
            tokens = cmd.lower().split()
            if not tokens:
                return False
            if not verb_ok(tokens[0]):
                return False
            # Skip trivial fillers; require the remaining content words to exist.
            fillers = {"all", "at", "to", "with", "on", "off", "the", "a", "an",
                       "in", "out", "up", "down", "through", "into"}
            for tok in tokens[1:]:
                if tok in fillers:
                    continue
                if not dict_has(tok):
                    return False
            return True

        suggested: List[str] = []
        objects_of_interest: List[str] = []

        # 1) GRAB EVERYTHING first (cheap, high score yield in treasure games).
        suggested.append("take all")

        # 2) A FEW untried directions up front so object work and exploration
        #    interleave (the rest of the directions are appended at the end).
        untried = list(context.untried_directions or [])
        for d in untried[:4]:
            suggested.append(d)

        # 3) Light source: turn on a carried lamp/lantern (Zork needs this).
        inv_lower = " ".join(context.inventory).lower()
        if "lamp" in inv_lower or "lantern" in inv_lower or "light" in inv_lower:
            noun = "lamp" if "lamp" in inv_lower else ("lantern" if "lantern" in inv_lower else "light")
            suggested.extend([f"turn on {noun}", f"light {noun}"])

        # 4) Interact with visible objects: examine/take/open/unlock/move/read.
        seen_nouns = set()
        for obj in (context.visible_objects or []):
            head = obj.split()[0].lower() if obj else ""
            if not head or head in seen_nouns:
                continue
            seen_nouns.add(head)
            objects_of_interest.append(obj)
            suggested.extend([
                f"examine {head}",
                f"take {head}",
                f"open {head}",
                f"read {head}",
                f"move {head}",
                f"push {head}",
            ])

        # 5) Nouns mentioned in the room description but not yet object-listed.
        desc_words = set(w.strip(".,!?;:'\"()").lower()
                         for w in context.room_description.split())
        interactive_hints = {
            "door": ["open door", "unlock door"],
            "window": ["open window", "enter"],
            "button": ["push button", "press button"],
            "lever": ["pull lever", "push lever"],
            "chest": ["open chest", "examine chest"],
            "box": ["open box", "examine box"],
            "trapdoor": ["open trapdoor", "down"],
            "grating": ["open grating", "down"],
            "case": ["open case", "examine case"],
            "mailbox": ["open mailbox", "read leaflet"],
            "egg": ["take egg", "open egg"],
            "rug": ["move rug", "look under rug"],
        }
        for noun, cmds in interactive_hints.items():
            if noun in desc_words and noun not in seen_nouns:
                suggested.extend(cmds)
                objects_of_interest.append(noun)

        # 6) Remaining untried directions + known exits (exploration tail).
        for d in untried[4:]:
            suggested.append(d)
        for d in context.exits.keys():
            if d not in untried:
                suggested.append(d)

        # 7) Cheap state commands.
        suggested.extend(["look", "inventory"])

        # Dictionary-filter + dedupe while preserving order.
        filtered: List[str] = []
        seen = set()
        for cmd in suggested:
            c = cmd.strip().lower()
            if not c or c in seen:
                continue
            seen.add(c)
            if cmd_ok(c):
                filtered.append(c)

        # Priority: high if we have untried exits or many objects.
        priority = "medium"
        if (context.untried_directions and len(context.untried_directions) > 2) \
                or len(context.visible_objects) > 3:
            priority = "high"
        elif not context.untried_directions and not context.visible_objects:
            priority = "low"

        reasoning = (
            f"Dictionary-aware heuristic: {len(context.untried_directions or [])} untried "
            f"exits, {len(context.visible_objects or [])} visible objects, score "
            f"{context.score}/{context.max_score if context.max_score is not None else '?'}."
        )

        return AIResponse(
            suggested_commands=filtered[:12],
            reasoning=reasoning,
            objects_of_interest=objects_of_interest,
            possible_puzzles=[],
            exploration_priority=priority,
        )

    def _parse_response(self, response_text: str) -> AIResponse:
        """Parse JSON response from LLM"""
        try:
            # Try to extract JSON from response
            # Handle cases where LLM wraps JSON in markdown
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end]
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end]

            data = json.loads(response_text.strip())

            return AIResponse(
                suggested_commands=data.get("suggested_commands", []),
                reasoning=data.get("reasoning", ""),
                objects_of_interest=data.get("objects_of_interest", []),
                possible_puzzles=data.get("possible_puzzles", []),
                exploration_priority=data.get("exploration_priority", "medium")
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Return a basic response if parsing fails
            return AIResponse(
                suggested_commands=["look", "inventory", "examine room"],
                reasoning=f"Failed to parse AI response: {e}",
                objects_of_interest=[],
                possible_puzzles=[],
                exploration_priority="medium"
            )

    def suggest_for_puzzle(self, puzzle_description: str,
                           inventory: List[str],
                           vocabulary: List[str]) -> List[str]:
        """
        Get suggestions for solving a specific puzzle.

        Args:
            puzzle_description: Description of the puzzle/obstacle
            inventory: Current inventory items
            vocabulary: Available game vocabulary

        Returns:
            List of suggested commands to try
        """
        prompt = f"""You are solving a puzzle in an interactive fiction game.

PUZZLE/OBSTACLE: {puzzle_description}

INVENTORY: {', '.join(inventory) if inventory else 'empty'}

AVAILABLE VOCABULARY: {', '.join(vocabulary[:100])}

Suggest 5-10 specific commands that might solve this puzzle.
Consider using inventory items, examining things, or trying actions.

Respond with just a JSON list of commands:
["command1", "command2", ...]
"""

        if self.backend == "anthropic":
            message = self._client.messages.create(
                model=self.model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text
        elif self.backend == "openai":
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512
            )
            response_text = response.choices[0].message.content
        else:
            # Local fallback
            return [f"use {item}" for item in inventory[:3]] + ["examine", "look"]

        try:
            # Extract JSON list
            if "[" in response_text:
                start = response_text.find("[")
                end = response_text.rfind("]") + 1
                commands = json.loads(response_text[start:end])
                return commands
        except:
            pass

        return ["examine", "look", "inventory"]


def create_context_from_walker(walker, num_recent: int = 5) -> GameContext:
    """
    Create a GameContext from a GameWalker instance.

    Args:
        walker: GameWalker instance
        num_recent: Number of recent commands to include

    Returns:
        GameContext for AI analysis
    """
    room = walker.rooms.get(walker.current_room_id)

    # Get recent transcript
    recent = walker.full_transcript[-num_recent:] if walker.full_transcript else []
    recent_commands = [cmd for cmd, _ in recent if cmd]
    recent_outputs = [out for _, out in recent]

    # Get inventory
    inventory = [name for _, name in walker.vm.get_inventory()]

    # Get visible objects
    visible = [name for _, name in room.objects] if room else []

    # Sample vocabulary
    vocab_sample = walker.vocabulary[:100] if walker.vocabulary else []

    # Real, untried, and blocked exits for this room (Fix C: exits bug).
    untried = room.untried_directions() if room else []
    blocked = sorted(room.blocked_directions) if room else []

    # Dictionary-derived verbs (Fix C: dictionary constraint).
    dict_words = walker.vocabulary or []
    try:
        by_type = walker.vm.get_dictionary_words_by_type()
        dict_verbs = by_type.get("verbs", []) + by_type.get("directions", [])
        # Drop Infocom internal/debug pseudo-verbs ($ve, #random, ...).
        dict_verbs = list(dict.fromkeys(
            v for v in dict_verbs if v and v[0].isalpha()))
    except Exception:
        dict_verbs = []

    return GameContext(
        room_name=room.name if room else "Unknown",
        room_description=room.description if room else "",
        room_id=walker.current_room_id,
        visible_objects=visible,
        inventory=inventory,
        exits=room.exits if room else {},
        recent_commands=recent_commands,
        recent_outputs=recent_outputs,
        vocabulary_sample=vocab_sample,
        untried_directions=untried,
        blocked_directions=blocked,
        dictionary_verbs=dict_verbs,
        dictionary_words=dict_words,
        score=getattr(walker, "score", 0),
        max_score=getattr(walker, "max_score", None),
    )

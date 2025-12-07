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
            self.model = model or "claude-3-haiku-20240307"
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
        exits_str = ", ".join(f"{dir}: room {id}" for dir, id in context.exits.items())
        objects_str = ", ".join(context.visible_objects) if context.visible_objects else "none visible"
        inventory_str = ", ".join(context.inventory) if context.inventory else "empty"
        recent_str = "\n".join(f"> {cmd}\n{out}" for cmd, out in
                               zip(context.recent_commands[-5:], context.recent_outputs[-5:]))
        vocab_str = ", ".join(context.vocabulary_sample[:50])

        prompt = f"""You are an expert at COMPLETING interactive fiction games. Your goal is to WIN this game, not just explore it.

CURRENT ROOM: {context.room_name} (ID: {context.room_id})
DESCRIPTION: {context.room_description}

VISIBLE OBJECTS: {objects_str}
INVENTORY: {inventory_str}
EXITS: {exits_str}

RECENT COMMANDS AND RESPONSES:
{recent_str}

AVAILABLE VOCABULARY (sample): {vocab_str}

CRITICAL INSTRUCTIONS:
- Your ONLY goal is to COMPLETE this game and reach the winning condition
- Don't just explore - actively try to solve puzzles and advance the plot
- Pick up items that might be useful later
- Try commands that make progress toward objectives
- If stuck, try examining everything, combining items, or using items in creative ways
- Read descriptions carefully for clues about what to do next
- Look for goal-oriented actions: unlock doors, solve puzzles, find keys, talk to characters

Suggest 5-10 commands that will help WIN this game. Prioritize:
1. Actions that directly advance the plot or solve puzzles
2. Picking up useful items
3. Trying new exits to find important areas
4. Examining objects for clues
5. Only explore systematically if truly stuck

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
        Simple local analysis without LLM.

        Uses heuristics to suggest commands based on visible objects
        and room description.
        """
        suggested = []
        objects_of_interest = []

        # Look for interactive objects in description
        desc_lower = context.room_description.lower()

        # Common interactive elements
        if "door" in desc_lower:
            suggested.extend(["open door", "examine door"])
            objects_of_interest.append("door")
        if "button" in desc_lower:
            suggested.extend(["push button", "press button"])
            objects_of_interest.append("button")
        if "lever" in desc_lower:
            suggested.extend(["pull lever", "push lever"])
            objects_of_interest.append("lever")
        if "window" in desc_lower:
            suggested.extend(["open window", "look through window"])
            objects_of_interest.append("window")
        if "box" in desc_lower or "chest" in desc_lower:
            suggested.extend(["open box", "examine box"])
            objects_of_interest.append("box/chest")

        # Suggest examining visible objects
        for obj in context.visible_objects[:5]:
            obj_word = obj.split()[0]
            suggested.append(f"examine {obj_word}")
            suggested.append(f"take {obj_word}")

        # Basic exploration commands
        suggested.extend(["look", "inventory", "examine room"])

        # Determine priority based on unexplored aspects
        priority = "medium"
        if len(context.visible_objects) > 3:
            priority = "high"
        if not context.visible_objects and len(context.exits) <= 2:
            priority = "low"

        return AIResponse(
            suggested_commands=suggested[:10],
            reasoning="Heuristic analysis based on room description and objects",
            objects_of_interest=objects_of_interest,
            possible_puzzles=[],
            exploration_priority=priority
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

    return GameContext(
        room_name=room.name if room else "Unknown",
        room_description=room.description if room else "",
        room_id=walker.current_room_id,
        visible_objects=visible,
        inventory=inventory,
        exits=room.exits if room else {},
        recent_commands=recent_commands,
        recent_outputs=recent_outputs,
        vocabulary_sample=vocab_sample
    )

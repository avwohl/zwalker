#!/usr/bin/env python3
"""
Generate smart JavaScript test scripts that handle random events.

Unlike the basic generator, this creates tests that:
1. Check output after each command for random event patterns
2. Execute appropriate responses (fight thief, flee grue, etc.)
3. Continue with the main solution after handling events
"""

import json
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any


# Random events that can interrupt normal gameplay
RANDOM_EVENTS = [
    {
        "id": "thief_encounter",
        "name": "Thief",
        "pattern": r"thief|someone carrying a large bag|nasty knife|stiletto",
        "responses": {
            "has_sword": ["kill thief with sword", "attack thief with sword"],
            "default": ["drop all", "wait", "wait", "wait", "take all"]
        },
        "check_inventory": "sword"
    },
    {
        "id": "troll_encounter",
        "name": "Troll",
        "pattern": r"troll|nasty troll|dangerous troll",
        "responses": {
            "has_sword": ["kill troll with sword", "attack troll"],
            "default": ["flee", "run", "retreat"]
        },
        "check_inventory": "sword"
    },
    {
        "id": "grue_warning",
        "name": "Grue",
        "pattern": r"eaten by a grue|lurking grue|grue is|pitch black|dark\\..*eaten",
        "responses": {
            "has_lamp": ["turn on lamp", "light lamp"],
            "default": ["go back", "retreat", "flee"]
        },
        "check_inventory": "lamp"
    },
    {
        "id": "combat_attack",
        "name": "Combat",
        "pattern": r"attacks you|strikes at you|swings at you|lunges at you|hits you",
        "responses": {
            "has_sword": ["kill attacker with sword", "attack", "fight"],
            "default": ["flee", "run"]
        },
        "check_inventory": "sword"
    },
    {
        "id": "cyclops_encounter",
        "name": "Cyclops",
        "pattern": r"cyclops|one-eyed giant",
        "responses": {
            "default": ["give lunch to cyclops", "say odysseus", "odysseus", "ulysses"]
        },
        "check_inventory": None
    }
]


def escape_js_string(s: str) -> str:
    """Escape a string for JavaScript"""
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')


def generate_smart_test_script(
    game_name: str,
    commands: List[str],
    output_path: Path,
    z2js_file: Optional[str] = None,
    branches: Optional[Dict[str, Any]] = None,
    random_events: List[Dict] = None
) -> None:
    """
    Generate a smart JavaScript test script that handles random events.
    """
    if z2js_file is None:
        z2js_file = f"./{game_name}_z2js.js"

    if random_events is None:
        random_events = RANDOM_EVENTS

    # Filter out empty commands from the beginning
    filtered_commands = []
    started = False
    for cmd in commands:
        if cmd or started:
            started = True
            filtered_commands.append(cmd)

    # Generate command array
    cmd_lines = [f'    "{escape_js_string(cmd)}",' for cmd in filtered_commands]
    commands_array = '\n'.join(cmd_lines).rstrip(',')

    # Generate random event handlers
    event_patterns = []
    event_responses = []
    for event in random_events:
        event_patterns.append(f'    {{ id: "{event["id"]}", name: "{event["name"]}", pattern: /{event["pattern"]}/i, checkItem: {json.dumps(event.get("check_inventory"))} }}')

        responses_obj = {}
        for key, cmds in event["responses"].items():
            responses_obj[key] = cmds
        event_responses.append(f'    "{event["id"]}": {json.dumps(responses_obj)}')

    events_js = ',\n'.join(event_patterns)
    responses_js = ',\n'.join(event_responses)

    script = f'''#!/usr/bin/env node
/**
 * Smart test for {game_name} with z2js
 *
 * Handles random events (combat, thief, grue, etc.)
 * Commands: {len(filtered_commands)}
 */

const {{ createZMachine }} = require('{z2js_file}');

// Suppress z2js noise ("[Z-Machine execution stopped]")
const originalError = console.error;
console.error = (...args) => {{
    const msg = args.join(' ');
    if (!msg.includes('Z-Machine execution stopped')) {{
        originalError.apply(console, args);
    }}
}};

const commands = [
{commands_array}
];

// Random event patterns to detect
const randomEvents = [
{events_js}
];

// Responses for each event type
const eventResponses = {{
{responses_js}
}};

async function test() {{
    console.log('='.repeat(60));
    console.log(' {game_name.upper()}: SMART Z2JS TEST');
    console.log('='.repeat(60));
    console.log(`Running ${{commands.length}} commands (with random event handling)\\n`);

    const m = createZMachine();
    let outputBuffer = '';
    let allOutput = '';
    let inventory = new Set();  // Track inventory for conditional responses

    m.outputCallback = (text) => {{
        outputBuffer += text;
        allOutput += text;

        // Track inventory changes
        if (/you.*(?:take|get|pick up)/i.test(text)) {{
            const itemMatch = text.match(/(?:take|get|pick up)\\s+(?:the\\s+)?([\\w\\s]+)/i);
            if (itemMatch) inventory.add(itemMatch[1].toLowerCase().trim());
        }}
        if (/taken/i.test(text) && outputBuffer.length < 50) {{
            // Short "Taken." response - item from last command
        }}
    }};

    let cmdIndex = 0;
    let eventCommandsQueue = [];  // Commands to handle current event
    let handlingEvent = false;
    let eventsHandled = 0;
    let lastProgressReport = 0;

    function checkForRandomEvent(output) {{
        for (const event of randomEvents) {{
            if (event.pattern.test(output)) {{
                return event;
            }}
        }}
        return null;
    }}

    function getEventResponse(event) {{
        const responses = eventResponses[event.id];
        if (!responses) return [];

        // Check if we have the required item for special response
        if (event.checkItem && inventory.has(event.checkItem)) {{
            const key = `has_${{event.checkItem}}`;
            if (responses[key]) return [...responses[key]];
        }}

        return responses.default ? [...responses.default] : [];
    }}

    function showProgress() {{
        if (cmdIndex - lastProgressReport >= 30) {{
            console.log(`--- Progress: ${{cmdIndex}}/${{commands.length}} commands (events handled: ${{eventsHandled}}) ---`);
            lastProgressReport = cmdIndex;
        }}
    }}

    return new Promise((resolve, reject) => {{
        function feedNextCommand() {{
            // First, check if we detected a random event in last output
            if (!handlingEvent) {{
                const event = checkForRandomEvent(outputBuffer);
                if (event) {{
                    console.log(`\\n>>> RANDOM EVENT: ${{event.name}} detected!`);
                    eventCommandsQueue = getEventResponse(event);
                    if (eventCommandsQueue.length > 0) {{
                        handlingEvent = true;
                        eventsHandled++;
                        console.log(`    Responding with: ${{eventCommandsQueue[0]}}`);
                    }}
                }}
            }}

            // Handle event commands first
            if (handlingEvent && eventCommandsQueue.length > 0) {{
                const eventCmd = eventCommandsQueue.shift();
                if (eventCommandsQueue.length === 0) {{
                    handlingEvent = false;  // Done with this event
                }}

                if (m.inputCallback) {{
                    outputBuffer = '';
                    m.inputCallback(eventCmd);
                    setTimeout(feedNextCommand, 5);
                    return;
                }}
            }}

            // Normal command processing
            if (cmdIndex >= commands.length) {{
                console.log('\\n--- All commands executed ---');
                console.log(`Events handled: ${{eventsHandled}}\\n`);
                console.log('FINAL OUTPUT (last 1500 chars):');
                console.log(allOutput.slice(-1500));

                // Extract score
                const scoreMatch = allOutput.match(/(\\d+)\\s*(?:out of|\\/)\\s*(\\d+)/i);
                if (scoreMatch) {{
                    console.log(`\\nFinal Score: ${{scoreMatch[1]}}/${{scoreMatch[2]}} points`);
                }}

                // Check victory
                if (/\\*\\*\\* You have won \\*\\*\\*|You have won|Victory|Congratulations/i.test(allOutput)) {{
                    console.log('\\n✓ VICTORY: Game completed!');
                }}

                resolve({{ success: true, output: allOutput, eventsHandled }});
                return;
            }}

            showProgress();

            const cmd = commands[cmdIndex];
            cmdIndex++;

            // Track take commands for inventory
            if (/^(?:take|get|pick up)\\s+/i.test(cmd)) {{
                const itemMatch = cmd.match(/^(?:take|get|pick up)\\s+(?:the\\s+)?(.+)/i);
                if (itemMatch) inventory.add(itemMatch[1].toLowerCase().trim());
            }}

            if (m.inputCallback) {{
                outputBuffer = '';
                m.inputCallback(cmd);
                setTimeout(feedNextCommand, 5);
            }} else if (m.finished) {{
                console.log('\\n!!! Game finished early');
                console.log('Final output:', outputBuffer.slice(-500));
                resolve({{ success: true, output: allOutput, eventsHandled }});
            }} else {{
                setTimeout(feedNextCommand, 10);
            }}
        }}

        process.on('uncaughtException', (err) => {{
            console.error('\\nError:', err.message);
            console.error('Command index:', cmdIndex);
            if (cmdIndex > 0) console.error('Last command:', commands[cmdIndex - 1]);
            reject(err);
        }});

        try {{
            m.run();
            setTimeout(feedNextCommand, 50);
        }} catch (e) {{
            console.error('Failed to start:', e.message);
            reject(e);
        }}
    }});
}}

test()
    .then((result) => {{
        console.log('\\n' + '='.repeat(60));
        console.log(` TEST COMPLETE - Events: ${{result.eventsHandled}}`);
        console.log('='.repeat(60));
        process.exit(0);
    }})
    .catch((err) => {{
        console.error('\\nTest failed:', err);
        process.exit(1);
    }});
'''

    output_path.write_text(script)
    output_path.chmod(0o755)
    print(f"✓ Generated smart test: {output_path}")
    print(f"  Commands: {len(filtered_commands)}")
    print(f"  Random events: {len(random_events)} patterns")


def load_solution(solution_path: Path) -> tuple:
    """Load solution JSON and extract game name, commands, and branches"""
    data = json.loads(solution_path.read_text())

    game_name = data.get('game', solution_path.stem.replace('_solution', ''))
    commands = data.get('commands') or data.get('solution_commands') or []
    branches = data.get('branches', {})

    if not commands:
        raise ValueError(f"No commands found in {solution_path}")

    if '/' in game_name:
        game_name = Path(game_name).stem

    return game_name, commands, branches


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate smart JavaScript test scripts with random event handling'
    )
    parser.add_argument(
        'solution_file',
        type=Path,
        help='Solution JSON file'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output test script path'
    )
    parser.add_argument(
        '-z', '--z2js-file',
        help='Path to z2js compiled file'
    )

    args = parser.parse_args()

    if not args.solution_file.exists():
        print(f"Error: Solution file not found: {args.solution_file}", file=sys.stderr)
        return 1

    try:
        game_name, commands, branches = load_solution(args.solution_file)

        if args.output:
            output_path = args.output
        else:
            output_path = Path('scripts') / f'test_{game_name}_smart.js'

        generate_smart_test_script(
            game_name=game_name,
            commands=commands,
            output_path=output_path,
            z2js_file=args.z2js_file,
            branches=branches
        )

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

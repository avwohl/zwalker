#!/usr/bin/env python3
"""
Generate JavaScript test scripts from solution JSON files.

Takes a solution JSON file and creates a Node.js test script that can run
the commands against a z2js-compiled version of the game.
"""

import json
import sys
from pathlib import Path
from typing import List, Optional


def escape_js_string(s: str) -> str:
    """Escape a string for JavaScript"""
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')


def generate_test_script(
    game_name: str,
    commands: List[str],
    output_path: Path,
    z2js_file: Optional[str] = None,
    show_progress: bool = True,
    final_output_lines: int = 2000
) -> None:
    """
    Generate a JavaScript test script.

    Args:
        game_name: Name of the game (e.g., "zork1")
        commands: List of commands to execute
        output_path: Path to write the test script
        z2js_file: Path to z2js compiled file (defaults to {game_name}_z2js.js)
        show_progress: Whether to show progress during execution
        final_output_lines: Number of characters to show in final output
    """
    if z2js_file is None:
        z2js_file = f"./{game_name}_z2js.js"

    # Filter out empty commands from the beginning (they're the initial game output)
    filtered_commands = []
    started = False
    for cmd in commands:
        if cmd or started:
            started = True
            filtered_commands.append(cmd)

    # Generate command array for JavaScript
    cmd_lines = []
    for cmd in filtered_commands:
        escaped_cmd = escape_js_string(cmd)
        cmd_lines.append(f'    "{escaped_cmd}",')

    commands_array = '\n'.join(cmd_lines).rstrip(',')

    # Progress tracking code
    progress_code = """
    // Progress tracking
    let lastProgressReport = 0;

    function showProgress() {
        if (cmdIndex - lastProgressReport >= 30) {
            console.log(`--- Progress: ${cmdIndex}/${commands.length} commands ---`);
            lastProgressReport = cmdIndex;
        }
    }
""" if show_progress else ""

    progress_call = "showProgress();" if show_progress else ""

    script = f'''#!/usr/bin/env node
/**
 * Test {game_name} with z2js
 *
 * Generated from solution JSON file
 * Commands: {len(filtered_commands)}
 */

const {{ createZMachine }} = require('{z2js_file}');

const commands = [
{commands_array}
];

async function test() {{
    console.log('=' .repeat(60));
    console.log(' {game_name.upper()}: Z2JS ENGINE TEST');
    console.log('=' .repeat(60));
    console.log(`Running ${{commands.length}} commands\\n`);

    const m = createZMachine();
    let outputBuffer = '';
    let allOutput = '';

    m.outputCallback = (text) => {{
        outputBuffer += text;
        allOutput += text;
    }};

    let cmdIndex = 0;
{progress_code}
    return new Promise((resolve, reject) => {{
        function feedNextCommand() {{
            if (cmdIndex >= commands.length) {{
                console.log('\\n--- All commands executed ---\\n');
                console.log('FINAL OUTPUT:');
                console.log(allOutput.slice(-{final_output_lines}));

                // Try to extract score
                const scoreMatch = allOutput.match(/(\\d+)\\s+(?:out of|\\/)\\s*(\\d+)/i);
                if (scoreMatch) {{
                    console.log(`\\nFinal Score: ${{scoreMatch[1]}}/${{scoreMatch[2]}} points`);
                }}

                // Check for victory
                if (allOutput.match(/\\*\\*\\* You have won \\*\\*\\*|You have won|Victory|Congratulations/i)) {{
                    console.log('\\n✓ VICTORY: Game completed!');
                }}

                resolve({{ success: true, output: allOutput }});
                return;
            }}

            {progress_call}

            const cmd = commands[cmdIndex];
            cmdIndex++;

            if (m.inputCallback) {{
                outputBuffer = '';
                m.inputCallback(cmd);
                setTimeout(feedNextCommand, 5);
            }} else if (m.finished) {{
                console.log('\\n!!! Game finished early');
                console.log('Final output:');
                console.log(outputBuffer.slice(-500));
                resolve({{ success: true, output: allOutput }});
            }} else {{
                setTimeout(feedNextCommand, 10);
            }}
        }}

        process.on('uncaughtException', (err) => {{
            console.error('\\nError:', err.message);
            console.error('Command index:', cmdIndex);
            if (cmdIndex > 0) {{
                console.error('Last command:', commands[cmdIndex - 1]);
            }}
            reject(err);
        }});

        try {{
            m.run();
            setTimeout(feedNextCommand, 50);
        }} catch (e) {{
            console.error('Failed to start game:', e.message);
            reject(e);
        }}
    }});
}}

test()
    .then((result) => {{
        console.log('\\n' + '=' .repeat(60));
        console.log(' TEST COMPLETE');
        console.log('=' .repeat(60));
        process.exit(0);
    }})
    .catch((err) => {{
        console.error('\\nTest failed:', err);
        process.exit(1);
    }});
'''

    output_path.write_text(script)
    output_path.chmod(0o755)  # Make executable
    print(f"✓ Generated test script: {output_path}")
    print(f"  Commands: {len(filtered_commands)}")
    print(f"  Z2JS file: {z2js_file}")


def load_solution(solution_path: Path) -> tuple[str, List[str]]:
    """Load a solution JSON file and extract game name and commands"""
    data = json.loads(solution_path.read_text())

    game_name = data.get('game', solution_path.stem.replace('_solution', ''))

    # Try different field names for commands
    commands = data.get('commands') or data.get('solution_commands') or []

    if not commands:
        raise ValueError(f"No commands found in {solution_path}")

    # Extract game name from path if it's a full path
    if '/' in game_name:
        game_name = Path(game_name).stem

    return game_name, commands


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate JavaScript test scripts from solution JSON files'
    )
    parser.add_argument(
        'solution_file',
        type=Path,
        help='Solution JSON file (e.g., solutions/zork1_solution.json)'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output test script path (default: scripts/test_{game}_solution.js)'
    )
    parser.add_argument(
        '-z', '--z2js-file',
        help='Path to z2js compiled file (default: ./{game}_z2js.js)'
    )
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress reporting during test'
    )
    parser.add_argument(
        '--final-output',
        type=int,
        default=2000,
        help='Number of characters to show in final output (default: 2000)'
    )

    args = parser.parse_args()

    if not args.solution_file.exists():
        print(f"Error: Solution file not found: {args.solution_file}", file=sys.stderr)
        return 1

    try:
        # Load solution
        game_name, commands = load_solution(args.solution_file)

        # Determine output path
        if args.output:
            output_path = args.output
        else:
            output_path = Path('scripts') / f'test_{game_name}_solution.js'

        # Generate script
        generate_test_script(
            game_name=game_name,
            commands=commands,
            output_path=output_path,
            z2js_file=args.z2js_file,
            show_progress=not args.no_progress,
            final_output_lines=args.final_output
        )

        print(f"\nTo run the test:")
        print(f"  cd scripts")
        print(f"  node {output_path.name}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

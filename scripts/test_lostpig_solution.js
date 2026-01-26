#!/usr/bin/env node
/**
 * Test lostpig with z2js
 *
 * Generated from solution JSON file
 * Commands: 123
 */

const { createZMachine } = require('./lostpig_z2js.js');

const commands = [
    "EXAMINE FIELD",
    "EXAMINE FOREST",
    "GO EAST",
    "GO NORTH",
    "EXAMINE MOON",
    "GO SOUTH",
    "EXAMINE FOREST",
    "GO EAST",
    "GO NORTH",
    "LISTEN",
    "GO NORTHEAST",
    "EXAMINE TORCH",
    "EXAMINE CRACK",
    "EXAMINE STAIRS",
    "CLIMB STAIRS",
    "EXAMINE CRACK",
    "EXAMINE METAL THING",
    "CLIMB STAIRS",
    "EXAMINE TUNNEL",
    "EXAMINE TUNNEL",
    "EXAMINE CRACK",
    "EXAMINE TORCH",
    "SEARCH HOLE",
    "EXAMINE CRACK",
    "EXAMINE STAIRS",
    "EXAMINE TORCH",
    "GO WEST",
    "EXAMINE CRACK",
    "EXAMINE CRACK",
    "EXAMINE BROKEN STAIR",
    "EXAMINE TUNNEL",
    "SEARCH CRACK",
    "GO NORTH",
    "EXAMINE TORCH",
    "SEARCH CRACK",
    "EXAMINE CRACK",
    "EXAMINE STAIRS",
    "EXAMINE CRACK",
    "EXAMINE TUNNEL",
    "EXAMINE STAIRS",
    "EXAMINE CRACK",
    "GO NORTH",
    "GO SOUTHEAST",
    "GO SOUTHWEST",
    "EXAMINE TORCH",
    "EXAMINE CRACK",
    "EXAMINE CRACK",
    "GO WEST",
    "EXAMINE TORCH",
    "EXAMINE CRACK",
    "EXAMINE CRACK",
    "GO WEST",
    "EXAMINE STAIRS",
    "EXAMINE TORCH",
    "EXAMINE TUNNEL",
    "EXAMINE STAIRS",
    "EXAMINE CRACK",
    "GO NORTH",
    "GO SOUTHEAST",
    "EXAMINE TORCH",
    "EXAMINE CRACK",
    "EXAMINE CRACK",
    "GO WEST",
    "GO NORTH",
    "EXAMINE TORCH",
    "EXAMINE CRACK",
    "EXAMINE CRACK",
    "EXAMINE TORCH",
    "EXAMINE CRACK",
    "GO WEST",
    "GO NORTH",
    "GO SOUTHEAST",
    "EXAMINE TORCH",
    "EXAMINE BROKEN STAIRS",
    "EXAMINE CRACK",
    "GO NORTH",
    "GO SOUTHEAST",
    "GO SOUTHWEST",
    "EXAMINE TORCH",
    "EXAMINE CRACK",
    "EXAMINE CRACK",
    "GO WEST",
    "EXAMINE TUNNEL",
    "EXAMINE CRACK",
    "CLIMB STAIRS",
    "EXAMINE TORCH",
    "EXAMINE CRACK",
    "EXAMINE CRACK",
    "EXAMINE BROKEN STAIR",
    "EXAMINE TORCH",
    "EXAMINE CRACK",
    "EXAMINE STAIRS",
    "GO WEST",
    "EXAMINE TORCH",
    "CLIMB STAIRS",
    "EXAMINE STAIRS",
    "EXAMINE CRACK",
    "GO WEST",
    "EXAMINE TORCH",
    "EXAMINE HOLE",
    "EXAMINE STAIRS",
    "EXAMINE CRACK",
    "examine torch",
    "examine crack",
    "examine stairs",
    "examine crack",
    "examine stairs",
    "examine torch",
    "examine crack",
    "examine crack",
    "examine tunnel",
    "climb stairs",
    "examine torch",
    "examine crack",
    "go north",
    "examine crack",
    "examine tunnel",
    "climb stairs",
    "examine torch",
    "examine crack",
    "examine crack",
    "climb stairs",
    "examine tunnel"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' LOSTPIG: Z2JS ENGINE TEST');
    console.log('=' .repeat(60));
    console.log(`Running ${commands.length} commands\n`);

    const m = createZMachine();
    let outputBuffer = '';
    let allOutput = '';

    m.outputCallback = (text) => {
        outputBuffer += text;
        allOutput += text;
    };

    let cmdIndex = 0;

    // Progress tracking
    let lastProgressReport = 0;

    function showProgress() {
        if (cmdIndex - lastProgressReport >= 30) {
            console.log(`--- Progress: ${cmdIndex}/${commands.length} commands ---`);
            lastProgressReport = cmdIndex;
        }
    }

    return new Promise((resolve, reject) => {
        function feedNextCommand() {
            if (cmdIndex >= commands.length) {
                console.log('\n--- All commands executed ---\n');
                console.log('FINAL OUTPUT:');
                console.log(allOutput.slice(-2000));

                // Try to extract score
                const scoreMatch = allOutput.match(/(\d+)\s+(?:out of|\/)\s*(\d+)/i);
                if (scoreMatch) {
                    console.log(`\nFinal Score: ${scoreMatch[1]}/${scoreMatch[2]} points`);
                }

                // Check for victory
                if (allOutput.match(/\*\*\* You have won \*\*\*|You have won|Victory|Congratulations/i)) {
                    console.log('\n✓ VICTORY: Game completed!');
                }

                resolve({ success: true, output: allOutput });
                return;
            }

            showProgress();

            const cmd = commands[cmdIndex];
            cmdIndex++;

            if (m.inputCallback) {
                outputBuffer = '';
                m.inputCallback(cmd);
                setTimeout(feedNextCommand, 5);
            } else if (m.finished) {
                console.log('\n!!! Game finished early');
                console.log('Final output:');
                console.log(outputBuffer.slice(-500));
                resolve({ success: true, output: allOutput });
            } else {
                setTimeout(feedNextCommand, 10);
            }
        }

        process.on('uncaughtException', (err) => {
            console.error('\nError:', err.message);
            console.error('Command index:', cmdIndex);
            if (cmdIndex > 0) {
                console.error('Last command:', commands[cmdIndex - 1]);
            }
            reject(err);
        });

        try {
            m.run();
            setTimeout(feedNextCommand, 50);
        } catch (e) {
            console.error('Failed to start game:', e.message);
            reject(e);
        }
    });
}

test()
    .then((result) => {
        console.log('\n' + '=' .repeat(60));
        console.log(' TEST COMPLETE');
        console.log('=' .repeat(60));
        process.exit(0);
    })
    .catch((err) => {
        console.error('\nTest failed:', err);
        process.exit(1);
    });

#!/usr/bin/env node
/**
 * Test dracula with z2js
 *
 * Generated from solution JSON file
 * Commands: 200
 */

const { createZMachine } = require('./dracula_z2js.js');

const commands = [
    "n",
    "s",
    "e",
    "w",
    "u",
    "d",
    "ne",
    "nw",
    "se",
    "sw",
    "in",
    "out",
    "open window",
    "enter window",
    "go window",
    "enter",
    "in",
    "d",
    "down",
    "open door",
    "enter door",
    "go door",
    "enter",
    "in",
    "d",
    "down",
    "open gate",
    "enter gate",
    "go gate",
    "enter",
    "in",
    "d",
    "down",
    "open trapdoor",
    "enter trapdoor",
    "go trapdoor",
    "enter",
    "in",
    "d",
    "down",
    "move rug",
    "move carpet",
    "pull lever",
    "push button",
    "open chest",
    "enter chest",
    "go chest",
    "enter",
    "in",
    "d",
    "down",
    "open box",
    "enter box",
    "go box",
    "enter",
    "in",
    "d",
    "down",
    "enter",
    "climb down",
    "climb up",
    "open trap door",
    "enter trap door",
    "go trap door",
    "enter",
    "in",
    "d",
    "down",
    "unlock door",
    "unlock gate",
    "take all",
    "get all",
    "take lamp",
    "take lantern",
    "take sword",
    "take knife",
    "take key",
    "take keys",
    "take bottle",
    "take food",
    "take leaflet",
    "take egg",
    "take jewels",
    "take coins",
    "turn on lamp",
    "light lamp",
    "turn on lantern",
    "light lantern",
    "n",
    "s",
    "e",
    "w",
    "u",
    "d",
    "ne",
    "nw",
    "se",
    "sw",
    "in",
    "out",
    "open window",
    "enter window",
    "go window",
    "enter",
    "in",
    "d",
    "down",
    "open door",
    "enter door",
    "go door",
    "enter",
    "in",
    "d",
    "down",
    "open gate",
    "enter gate",
    "go gate",
    "enter",
    "in",
    "d",
    "down",
    "open trapdoor",
    "enter trapdoor",
    "go trapdoor",
    "enter",
    "in",
    "d",
    "down",
    "move rug",
    "move carpet",
    "pull lever",
    "push button",
    "open chest",
    "enter chest",
    "go chest",
    "enter",
    "in",
    "d",
    "down",
    "open box",
    "enter box",
    "go box",
    "enter",
    "in",
    "d",
    "down",
    "enter",
    "climb down",
    "climb up",
    "open trap door",
    "enter trap door",
    "go trap door",
    "enter",
    "in",
    "d",
    "down",
    "unlock door",
    "unlock gate",
    "look",
    "examine grass",
    "examine ruin",
    "examine silhouette",
    "examine shines",
    "examine blood",
    "examine wood",
    "examine moon",
    "examine surrounded",
    "examine covered",
    "examine gothic",
    "take grass",
    "take ruin",
    "take silhouette",
    "take shines",
    "take blood",
    "take wood",
    "take moon",
    "take surrounded",
    "take covered",
    "take gothic",
    "open grass",
    "open ruin",
    "open silhouette",
    "open shines",
    "open blood",
    "open wood",
    "open moon",
    "open surrounded",
    "open covered",
    "open gothic",
    "read grass",
    "read ruin",
    "read silhouette",
    "read shines",
    "read blood",
    "read wood",
    "read moon",
    "read surrounded",
    "read covered",
    "read gothic",
    "move grass"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' DRACULA: Z2JS ENGINE TEST');
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

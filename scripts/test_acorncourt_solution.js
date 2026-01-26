#!/usr/bin/env node
/**
 * Test acorncourt with z2js
 *
 * Generated from solution JSON file
 * Commands: 177
 */

const { createZMachine } = require('./acorncourt_z2js.js');

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
    "open gate",
    "open trapdoor",
    "move rug",
    "move carpet",
    "pull lever",
    "push button",
    "open chest",
    "open box",
    "enter",
    "climb down",
    "climb up",
    "open trap door",
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
    "open gate",
    "open trapdoor",
    "move rug",
    "move carpet",
    "pull lever",
    "push button",
    "open chest",
    "open box",
    "enter",
    "climb down",
    "climb up",
    "open trap door",
    "unlock door",
    "unlock gate",
    "look",
    "examine rock",
    "examine from",
    "examine casts",
    "examine large",
    "examine twigs",
    "examine court",
    "examine wall",
    "examine sized",
    "examine looking",
    "examine yard",
    "take rock",
    "take from",
    "take casts",
    "take large",
    "take twigs",
    "take court",
    "take wall",
    "take sized",
    "take looking",
    "take yard",
    "open rock",
    "open from",
    "open casts",
    "open large",
    "open twigs",
    "open court",
    "open wall",
    "open sized",
    "open looking",
    "open yard",
    "read rock",
    "read from",
    "read casts",
    "read large",
    "read twigs",
    "read court",
    "read wall",
    "read sized",
    "read looking",
    "read yard",
    "move rock",
    "move from",
    "move casts",
    "move large",
    "move twigs",
    "move court",
    "move wall",
    "move sized",
    "move looking",
    "move yard",
    "push rock",
    "push from",
    "push casts",
    "push large",
    "push twigs",
    "push court",
    "push wall",
    "push sized",
    "push looking",
    "push yard",
    "pull rock",
    "pull from",
    "pull casts",
    "pull large",
    "pull twigs",
    "pull court",
    "pull wall",
    "pull sized",
    "pull looking",
    "pull yard",
    "turn rock",
    "turn from",
    "turn casts",
    "turn large",
    "turn twigs",
    "turn court",
    "turn wall",
    "turn sized",
    "turn looking",
    "turn yard",
    "light rock",
    "light from",
    "light casts",
    "light large",
    "light twigs",
    "light court",
    "light wall",
    "light sized",
    "light looking",
    "light yard"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' ACORNCOURT: Z2JS ENGINE TEST');
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

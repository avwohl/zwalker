#!/usr/bin/env node
/**
 * Test Ralph with z2js
 *
 * Generated from solution JSON file
 * Commands: 165
 */

const { createZMachine } = require('./Ralph_z2js.js');

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
    "examine wall",
    "examine frozen",
    "examine wildly",
    "examine leads",
    "examine outward",
    "examine roof",
    "examine together",
    "examine serve",
    "examine what",
    "examine enough",
    "take wall",
    "take frozen",
    "take wildly",
    "take leads",
    "take outward",
    "take roof",
    "take together",
    "take serve",
    "take what",
    "take enough",
    "open wall",
    "open frozen",
    "open wildly",
    "open leads",
    "open outward",
    "open roof",
    "open together",
    "open serve",
    "open what",
    "open enough",
    "read wall",
    "read frozen",
    "read wildly",
    "read leads",
    "read outward",
    "read roof",
    "read together",
    "read serve",
    "read what",
    "read enough",
    "move wall",
    "move frozen",
    "move wildly",
    "move leads",
    "move outward",
    "move roof",
    "move together",
    "move serve",
    "move what",
    "move enough",
    "push wall",
    "push frozen",
    "push wildly",
    "push leads",
    "push outward",
    "push roof",
    "push together",
    "push serve",
    "push what",
    "push enough",
    "pull wall",
    "pull frozen",
    "pull wildly",
    "pull leads",
    "pull outward",
    "pull roof",
    "pull together",
    "pull serve",
    "pull what",
    "pull enough",
    "turn wall",
    "turn frozen",
    "turn wildly",
    "turn leads",
    "turn outward",
    "turn roof",
    "turn together",
    "turn serve",
    "turn what",
    "turn enough",
    "light wall",
    "light frozen",
    "light wildly",
    "light leads",
    "light outward",
    "light roof",
    "light together",
    "light serve",
    "light what",
    "light enough"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' RALPH: Z2JS ENGINE TEST');
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

#!/usr/bin/env node
/**
 * Test etude with z2js
 *
 * Generated from solution JSON file
 * Commands: 165
 */

const { createZMachine } = require('./etude_z2js.js');

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
    "examine output",
    "examine itself",
    "examine display",
    "examine single-key",
    "examine quitting",
    "examine division",
    "examine changes",
    "examine capability",
    "examine menu)",
    "examine analysis",
    "take output",
    "take itself",
    "take display",
    "take single-key",
    "take quitting",
    "take division",
    "take changes",
    "take capability",
    "take menu)",
    "take analysis",
    "open output",
    "open itself",
    "open display",
    "open single-key",
    "open quitting",
    "open division",
    "open changes",
    "open capability",
    "open menu)",
    "open analysis",
    "read output",
    "read itself",
    "read display",
    "read single-key",
    "read quitting",
    "read division",
    "read changes",
    "read capability",
    "read menu)",
    "read analysis",
    "move output",
    "move itself",
    "move display",
    "move single-key",
    "move quitting",
    "move division",
    "move changes",
    "move capability",
    "move menu)",
    "move analysis",
    "push output",
    "push itself",
    "push display",
    "push single-key",
    "push quitting",
    "push division",
    "push changes",
    "push capability",
    "push menu)",
    "push analysis",
    "pull output",
    "pull itself",
    "pull display",
    "pull single-key",
    "pull quitting",
    "pull division",
    "pull changes",
    "pull capability",
    "pull menu)",
    "pull analysis",
    "turn output",
    "turn itself",
    "turn display",
    "turn single-key",
    "turn quitting",
    "turn division",
    "turn changes",
    "turn capability",
    "turn menu)",
    "turn analysis",
    "light output",
    "light itself",
    "light display",
    "light single-key",
    "light quitting",
    "light division",
    "light changes",
    "light capability",
    "light menu)",
    "light analysis"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' ETUDE: Z2JS ENGINE TEST');
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

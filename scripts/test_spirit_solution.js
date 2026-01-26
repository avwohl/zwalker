#!/usr/bin/env node
/**
 * Test spirit with z2js
 *
 * Generated from solution JSON file
 * Commands: 165
 */

const { createZMachine } = require('./spirit_z2js.js');

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
    "examine repair",
    "examine voices",
    "examine balance",
    "examine dying",
    "examine concentration",
    "examine order",
    "examine longer",
    "examine air",
    "examine attempts",
    "examine outsiders",
    "take repair",
    "take voices",
    "take balance",
    "take dying",
    "take concentration",
    "take order",
    "take longer",
    "take air",
    "take attempts",
    "take outsiders",
    "open repair",
    "open voices",
    "open balance",
    "open dying",
    "open concentration",
    "open order",
    "open longer",
    "open air",
    "open attempts",
    "open outsiders",
    "read repair",
    "read voices",
    "read balance",
    "read dying",
    "read concentration",
    "read order",
    "read longer",
    "read air",
    "read attempts",
    "read outsiders",
    "move repair",
    "move voices",
    "move balance",
    "move dying",
    "move concentration",
    "move order",
    "move longer",
    "move air",
    "move attempts",
    "move outsiders",
    "push repair",
    "push voices",
    "push balance",
    "push dying",
    "push concentration",
    "push order",
    "push longer",
    "push air",
    "push attempts",
    "push outsiders",
    "pull repair",
    "pull voices",
    "pull balance",
    "pull dying",
    "pull concentration",
    "pull order",
    "pull longer",
    "pull air",
    "pull attempts",
    "pull outsiders",
    "turn repair",
    "turn voices",
    "turn balance",
    "turn dying",
    "turn concentration",
    "turn order",
    "turn longer",
    "turn air",
    "turn attempts",
    "turn outsiders",
    "light repair",
    "light voices",
    "light balance",
    "light dying",
    "light concentration",
    "light order",
    "light longer",
    "light air",
    "light attempts",
    "light outsiders"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' SPIRIT: Z2JS ENGINE TEST');
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

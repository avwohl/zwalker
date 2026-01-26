#!/usr/bin/env node
/**
 * Test amfv with z2js
 *
 * Generated from solution JSON file
 * Commands: 100
 */

const { createZMachine } = require('./amfv_z2js.js');

const commands = [
    "$ver",
    "$ver",
    "$verif",
    "$verif",
    "$ver",
    "$refre",
    "examine room",
    "activate ppcc",
    "activate ppcc",
    "activate ppcc",
    "activate ppcc",
    "activate ppcc",
    "examine description",
    "examine room",
    "activate ppcc",
    "activate ppcc",
    "activate ppcc",
    "activate ppcc",
    "activate ppcc",
    "examine description",
    "examine",
    "examine verse",
    "examine verse",
    "examine description",
    "examine",
    "examine verse",
    "examine",
    "examine",
    "examine",
    "examine verse",
    "examine verse",
    "examine description",
    "examine verse",
    "examine description",
    "examine description",
    "examine",
    "examine room",
    "activate PPCC",
    "activate PPCC",
    "activate PPCC",
    "activate PPCC",
    "activate PPCC",
    "examine description",
    "examine $ver",
    "examine",
    "examine $ver",
    "examine room",
    "activate ppcc",
    "activate ppcc",
    "activate ppcc",
    "activate ppcc",
    "activate ppcc",
    "examine description",
    "examine room",
    "activate ppcc",
    "activate ppcc",
    "activate ppcc",
    "activate ppcc",
    "activate ppcc",
    "examine room",
    "activate ppcc",
    "activate ppcc",
    "activate ppcc",
    "activate ppcc",
    "activate wnnf",
    "examine poem",
    "examine poem",
    "examine description",
    "examine description",
    "activate $refre",
    "activate $refre",
    "examine",
    "examine",
    "examine",
    "examine description",
    "examine $ver",
    "examine",
    "examine $ver",
    "examine",
    "examine $refre",
    "examine poem",
    "examine room",
    "activate prism project control center",
    "examine description",
    "activate prism project control center",
    "activate prism project control center",
    "activate prism project control center",
    "examine prism",
    "examine prism",
    "examine door",
    "examine door",
    "examine room",
    "examine door",
    "examine room",
    "examine door",
    "examine door",
    "examine door",
    "examine prism",
    "activate wnnf",
    "examine door"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' AMFV: Z2JS ENGINE TEST');
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

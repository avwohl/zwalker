#!/usr/bin/env node
/**
 * Test adv550 with z2js
 *
 * Generated from solution JSON file
 * Commands: 100
 */

const { createZMachine } = require('./adv550_z2js.js');

const commands = [
    "NEWS",
    "NEWS",
    "EXAMINE STREAM",
    "EXAMINE STREAM",
    "ENTER BUILDING",
    "TAKE KEYS",
    "TAKE LAMP",
    "NEWS",
    "TAKE KEYS",
    "TAKE LAMP",
    "TAKE KEYS",
    "EXAMINE ROOM",
    "EXAMINE ROOM",
    "NEWS",
    "NEWS",
    "TAKE KEYS",
    "LOOK",
    "TAKE FOOD",
    "EXAMINE FOOD",
    "TAKE BOTTLE",
    "NEWS",
    "NEWS",
    "TAKE BOTTLE",
    "TAKE BOTTLE",
    "TAKE LAMP",
    "TAKE SWORD",
    "INVENTORY",
    "NEWS",
    "TAKE KEYS",
    "NEWS",
    "EXAMINE ROOM",
    "TAKE LANTERN",
    "TAKE KEYS",
    "NEWS",
    "TAKE KEYS",
    "EXAMINE ROOM",
    "NEWS",
    "TAKE KEYS",
    "EXAMINE ROOM",
    "NEWS",
    "LOOK",
    "TAKE KEYS",
    "TAKE KEYS",
    "SEARCH WELL",
    "LOOK",
    "NEWS",
    "TAKE KEYS",
    "NEWS",
    "TAKE KEYS",
    "EXAMINE KEYS",
    "GO WEST",
    "EXAMINE STREAM",
    "EXAMINE STREAM",
    "NEWS",
    "NEWS",
    "GO WEST",
    "EXAMINE BUILDING",
    "GO WEST",
    "GO WEST",
    "NEWS",
    "NEWS",
    "NEWS",
    "EXAMINE ROOM",
    "EXAMINE STARTING ROOM",
    "LOOK",
    "GO WEST",
    "NEWS",
    "NEWS",
    "GO WEST",
    "GO EAST",
    "EXAMINE BUILDING",
    "ENTER BUILDING",
    "EXAMINE STREAM",
    "NEWS",
    "NEWS",
    "EXAMINE BUILDING",
    "TAKE LAMP",
    "TAKE KEYS",
    "GO WEST",
    "TAKE LAMP",
    "NEWS",
    "TAKE LAMP",
    "GO WEST",
    "TAKE LAMP",
    "TAKE LAMP",
    "TAKE LAMP",
    "NEWS",
    "NEWS",
    "TAKE LAMP",
    "TAKE LAMP",
    "GET LAMP",
    "LOOK",
    "TAKE LAMP",
    "NEWS",
    "NEWS",
    "GET LAMP",
    "GO NORTH",
    "EXAMINE BUILDING",
    "ENTER BUILDING",
    "EXAMINE STREAM"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' ADV550: Z2JS ENGINE TEST');
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

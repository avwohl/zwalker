#!/usr/bin/env node
/**
 * Test lists with z2js
 *
 * Generated from solution JSON file
 * Commands: 237
 */

const { createZMachine } = require('./lists_z2js.js');

const commands = [
    "about",
    "look",
    "examine stuff",
    "open door",
    "go through door",
    "examine genie",
    "examine box",
    "wake genie",
    "examine genie",
    "examine box",
    "wake genie",
    "ask genie",
    "examine box",
    "break glass",
    "ask genie",
    "examine genie",
    "examine desk",
    "examine genie",
    "ask genie",
    "search bookshelves",
    "examine genie",
    "turn on computer",
    "examine box",
    "examine computer",
    "take genie",
    "talk to genie",
    "search desk",
    "examine box",
    "examine computer",
    "search desk",
    "talk to genie",
    "take genie",
    "examine box",
    "examine computer",
    "search desk",
    "talk to genie",
    "take genie",
    "examine box",
    "examine computer",
    "examine desk",
    "talk to genie",
    "take genie",
    "examine box",
    "examine computer",
    "examine desk",
    "talk to genie",
    "wake up genie",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "wake up genie",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "wake up genie",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "wake up genie",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "wake up genie",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "wake up genie",
    "look",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "look",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take genie",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take genie",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "wake up genie",
    "look",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "look",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "look",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "look",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "look",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take box",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take box",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take box",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take box",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take box",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take box",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take box",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take box",
    "look",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "look",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "look",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "look",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "look",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "look",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "look",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "look",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take box",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take box",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take box",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take box",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take box",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take box",
    "examine box",
    "examine computer",
    "examine desk",
    "examine genie",
    "take box"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' LISTS: Z2JS ENGINE TEST');
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

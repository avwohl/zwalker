#!/usr/bin/env node
/**
 * Test aisle with z2js
 *
 * Generated from solution JSON file
 * Commands: 40
 */

const { createZMachine } = require('./aisle_z2js.js');

const commands = [
    "will give endings in putpbaa. some that give the same endings",
    "commands are marked in a 'compacted' manner: that is, notify (on,",
    "about",
    "amusing",
    "inventory",
    "superbrief",
    "look",
    "look in (me, booth, pants)",
    "look under (me, booth)",
    "in, out",
    "blow up (booth, me)",
    "close (-, booth, me)",
    "drink (booth, me)",
    "frotz (booth, me, pants)",
    "get (booth, me)",
    "open (booth, me, pants)",
    "squeeze (booth, me)",
    "swing (booth, me)",
    "take off (booth, pants)",
    "*bunk in (booth, me)",
    "*ozmoo (booth, me)",
    "*waltz (-, something, with (booth, me))",
    "lie down",
    "sing",
    "think",
    "wait",
    "win",
    "xyzzy",
    "*tango",
    "*zork",
    "*put nales in nose",
    "ask me about nonword",
    "ask booth about nonword",
    "weird things",
    "blow up dir",
    "frotz dir",
    "sit on floor (bizarre errors)",
    "empty anything",
    "look behind anything",
    "drop anything"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' AISLE: Z2JS ENGINE TEST');
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

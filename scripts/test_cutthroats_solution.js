#!/usr/bin/env node
/**
 * Test cutthroats with z2js
 *
 * Generated from solution JSON file
 * Commands: 165
 */

const { createZMachine } = require('./cutthroats_z2js.js');

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
    "examine while",
    "examine your",
    "examine corner",
    "examine comfortable",
    "examine slept",
    "examine lopsided",
    "examine door",
    "examine slipped",
    "examine closet",
    "examine floor",
    "take while",
    "take your",
    "take corner",
    "take comfortable",
    "take slept",
    "take lopsided",
    "take door",
    "take slipped",
    "take closet",
    "take floor",
    "open while",
    "open your",
    "open corner",
    "open comfortable",
    "open slept",
    "open lopsided",
    "open door",
    "open slipped",
    "open closet",
    "open floor",
    "read while",
    "read your",
    "read corner",
    "read comfortable",
    "read slept",
    "read lopsided",
    "read door",
    "read slipped",
    "read closet",
    "read floor",
    "move while",
    "move your",
    "move corner",
    "move comfortable",
    "move slept",
    "move lopsided",
    "move door",
    "move slipped",
    "move closet",
    "move floor",
    "push while",
    "push your",
    "push corner",
    "push comfortable",
    "push slept",
    "push lopsided",
    "push door",
    "push slipped",
    "push closet",
    "push floor",
    "pull while",
    "pull your",
    "pull corner",
    "pull comfortable",
    "pull slept",
    "pull lopsided",
    "pull door",
    "pull slipped",
    "pull closet",
    "pull floor",
    "turn while",
    "turn your",
    "turn corner",
    "turn comfortable",
    "turn slept",
    "turn lopsided",
    "turn door",
    "turn slipped",
    "turn closet",
    "turn floor",
    "light while",
    "light your",
    "light corner",
    "light comfortable",
    "light slept",
    "light lopsided",
    "light door",
    "light slipped",
    "light closet",
    "light floor"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' CUTTHROATS: Z2JS ENGINE TEST');
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

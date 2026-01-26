#!/usr/bin/env node
/**
 * Test jewel with z2js
 *
 * Generated from solution JSON file
 * Commands: 165
 */

const { createZMachine } = require('./jewel_z2js.js');

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
    "examine ceiling",
    "examine tumble",
    "examine first",
    "examine deep",
    "examine much",
    "examine your",
    "examine when",
    "examine month",
    "examine samples",
    "examine perfect",
    "take ceiling",
    "take tumble",
    "take first",
    "take deep",
    "take much",
    "take your",
    "take when",
    "take month",
    "take samples",
    "take perfect",
    "open ceiling",
    "open tumble",
    "open first",
    "open deep",
    "open much",
    "open your",
    "open when",
    "open month",
    "open samples",
    "open perfect",
    "read ceiling",
    "read tumble",
    "read first",
    "read deep",
    "read much",
    "read your",
    "read when",
    "read month",
    "read samples",
    "read perfect",
    "move ceiling",
    "move tumble",
    "move first",
    "move deep",
    "move much",
    "move your",
    "move when",
    "move month",
    "move samples",
    "move perfect",
    "push ceiling",
    "push tumble",
    "push first",
    "push deep",
    "push much",
    "push your",
    "push when",
    "push month",
    "push samples",
    "push perfect",
    "pull ceiling",
    "pull tumble",
    "pull first",
    "pull deep",
    "pull much",
    "pull your",
    "pull when",
    "pull month",
    "pull samples",
    "pull perfect",
    "turn ceiling",
    "turn tumble",
    "turn first",
    "turn deep",
    "turn much",
    "turn your",
    "turn when",
    "turn month",
    "turn samples",
    "turn perfect",
    "light ceiling",
    "light tumble",
    "light first",
    "light deep",
    "light much",
    "light your",
    "light when",
    "light month",
    "light samples",
    "light perfect"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' JEWEL: Z2JS ENGINE TEST');
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

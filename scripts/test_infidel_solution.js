#!/usr/bin/env node
/**
 * Test infidel with z2js
 *
 * Generated from solution JSON file
 * Commands: 165
 */

const { createZMachine } = require('./infidel_z2js.js');

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
    "examine makes",
    "examine bearable",
    "examine heat",
    "examine large",
    "examine cot.)",
    "examine southern",
    "examine army",
    "examine little",
    "examine your",
    "examine foot",
    "take makes",
    "take bearable",
    "take heat",
    "take large",
    "take cot.)",
    "take southern",
    "take army",
    "take little",
    "take your",
    "take foot",
    "open makes",
    "open bearable",
    "open heat",
    "open large",
    "open cot.)",
    "open southern",
    "open army",
    "open little",
    "open your",
    "open foot",
    "read makes",
    "read bearable",
    "read heat",
    "read large",
    "read cot.)",
    "read southern",
    "read army",
    "read little",
    "read your",
    "read foot",
    "move makes",
    "move bearable",
    "move heat",
    "move large",
    "move cot.)",
    "move southern",
    "move army",
    "move little",
    "move your",
    "move foot",
    "push makes",
    "push bearable",
    "push heat",
    "push large",
    "push cot.)",
    "push southern",
    "push army",
    "push little",
    "push your",
    "push foot",
    "pull makes",
    "pull bearable",
    "pull heat",
    "pull large",
    "pull cot.)",
    "pull southern",
    "pull army",
    "pull little",
    "pull your",
    "pull foot",
    "turn makes",
    "turn bearable",
    "turn heat",
    "turn large",
    "turn cot.)",
    "turn southern",
    "turn army",
    "turn little",
    "turn your",
    "turn foot",
    "light makes",
    "light bearable",
    "light heat",
    "light large",
    "light cot.)",
    "light southern",
    "light army",
    "light little",
    "light your",
    "light foot"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' INFIDEL: Z2JS ENGINE TEST');
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

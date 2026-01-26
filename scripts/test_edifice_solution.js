#!/usr/bin/env node
/**
 * Test edifice with z2js
 *
 * Generated from solution JSON file
 * Commands: 165
 */

const { createZMachine } = require('./edifice_z2js.js');

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
    "examine your",
    "examine them",
    "examine nearby",
    "examine where",
    "examine entire",
    "examine reaching",
    "examine clouds",
    "examine high",
    "examine have",
    "examine forest",
    "take your",
    "take them",
    "take nearby",
    "take where",
    "take entire",
    "take reaching",
    "take clouds",
    "take high",
    "take have",
    "take forest",
    "open your",
    "open them",
    "open nearby",
    "open where",
    "open entire",
    "open reaching",
    "open clouds",
    "open high",
    "open have",
    "open forest",
    "read your",
    "read them",
    "read nearby",
    "read where",
    "read entire",
    "read reaching",
    "read clouds",
    "read high",
    "read have",
    "read forest",
    "move your",
    "move them",
    "move nearby",
    "move where",
    "move entire",
    "move reaching",
    "move clouds",
    "move high",
    "move have",
    "move forest",
    "push your",
    "push them",
    "push nearby",
    "push where",
    "push entire",
    "push reaching",
    "push clouds",
    "push high",
    "push have",
    "push forest",
    "pull your",
    "pull them",
    "pull nearby",
    "pull where",
    "pull entire",
    "pull reaching",
    "pull clouds",
    "pull high",
    "pull have",
    "pull forest",
    "turn your",
    "turn them",
    "turn nearby",
    "turn where",
    "turn entire",
    "turn reaching",
    "turn clouds",
    "turn high",
    "turn have",
    "turn forest",
    "light your",
    "light them",
    "light nearby",
    "light where",
    "light entire",
    "light reaching",
    "light clouds",
    "light high",
    "light have",
    "light forest"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' EDIFICE: Z2JS ENGINE TEST');
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

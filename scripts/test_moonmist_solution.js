#!/usr/bin/env node
/**
 * Test moonmist with z2js
 *
 * Generated from solution JSON file
 * Commands: 177
 */

const { createZMachine } = require('./moonmist_z2js.js');

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
    "enter window",
    "go window",
    "enter",
    "in",
    "d",
    "down",
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
    "enter window",
    "go window",
    "enter",
    "in",
    "d",
    "down",
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
    "examine dragon",
    "examine against",
    "examine moonlit",
    "examine hear",
    "examine moonlight",
    "examine lone",
    "examine urgently",
    "examine two-legged",
    "examine rocks",
    "examine gate",
    "take dragon",
    "take against",
    "take moonlit",
    "take hear",
    "take moonlight",
    "take lone",
    "take urgently",
    "take two-legged",
    "take rocks",
    "take gate",
    "open dragon",
    "open against",
    "open moonlit",
    "open hear",
    "open moonlight",
    "open lone",
    "open urgently",
    "open two-legged",
    "open rocks",
    "open gate",
    "read dragon",
    "read against",
    "read moonlit",
    "read hear",
    "read moonlight",
    "read lone",
    "read urgently",
    "read two-legged",
    "read rocks",
    "read gate",
    "move dragon",
    "move against",
    "move moonlit",
    "move hear",
    "move moonlight",
    "move lone",
    "move urgently",
    "move two-legged",
    "move rocks",
    "move gate",
    "push dragon",
    "push against",
    "push moonlit",
    "push hear",
    "push moonlight",
    "push lone",
    "push urgently",
    "push two-legged",
    "push rocks",
    "push gate",
    "pull dragon",
    "pull against",
    "pull moonlit",
    "pull hear",
    "pull moonlight",
    "pull lone",
    "pull urgently",
    "pull two-legged",
    "pull rocks",
    "pull gate",
    "turn dragon",
    "turn against",
    "turn moonlit",
    "turn hear",
    "turn moonlight",
    "turn lone",
    "turn urgently",
    "turn two-legged",
    "turn rocks",
    "turn gate",
    "light dragon",
    "light against",
    "light moonlit",
    "light hear",
    "light moonlight",
    "light lone",
    "light urgently",
    "light two-legged",
    "light rocks",
    "light gate"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' MOONMIST: Z2JS ENGINE TEST');
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

#!/usr/bin/env node
/**
 * Test enemies with z2js
 *
 * Generated from solution JSON file
 * Commands: 165
 */

const { createZMachine } = require('./enemies_z2js.js');

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
    "examine sound",
    "examine street",
    "examine comes",
    "examine almost",
    "examine eight-screen",
    "examine more",
    "examine marquee",
    "examine black",
    "examine leather-clad",
    "examine brings",
    "take sound",
    "take street",
    "take comes",
    "take almost",
    "take eight-screen",
    "take more",
    "take marquee",
    "take black",
    "take leather-clad",
    "take brings",
    "open sound",
    "open street",
    "open comes",
    "open almost",
    "open eight-screen",
    "open more",
    "open marquee",
    "open black",
    "open leather-clad",
    "open brings",
    "read sound",
    "read street",
    "read comes",
    "read almost",
    "read eight-screen",
    "read more",
    "read marquee",
    "read black",
    "read leather-clad",
    "read brings",
    "move sound",
    "move street",
    "move comes",
    "move almost",
    "move eight-screen",
    "move more",
    "move marquee",
    "move black",
    "move leather-clad",
    "move brings",
    "push sound",
    "push street",
    "push comes",
    "push almost",
    "push eight-screen",
    "push more",
    "push marquee",
    "push black",
    "push leather-clad",
    "push brings",
    "pull sound",
    "pull street",
    "pull comes",
    "pull almost",
    "pull eight-screen",
    "pull more",
    "pull marquee",
    "pull black",
    "pull leather-clad",
    "pull brings",
    "turn sound",
    "turn street",
    "turn comes",
    "turn almost",
    "turn eight-screen",
    "turn more",
    "turn marquee",
    "turn black",
    "turn leather-clad",
    "turn brings",
    "light sound",
    "light street",
    "light comes",
    "light almost",
    "light eight-screen",
    "light more",
    "light marquee",
    "light black",
    "light leather-clad",
    "light brings"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' ENEMIES: Z2JS ENGINE TEST');
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

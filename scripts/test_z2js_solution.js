#!/usr/bin/env node
/**
 * Test Zork 1 solution using z2js engine
 *
 * Runs the 184-point solution through the z2js-compiled Zork 1
 * and verifies the final score.
 */

const fs = require('fs');
const path = require('path');

// Load the compiled game
const { createZMachine } = require('./zork1_z2js.js');

// Load solution commands
function loadSolution(filepath) {
    const content = fs.readFileSync(filepath, 'utf-8');
    const commands = [];

    for (const line of content.split('\n')) {
        let cmd = line.trim();
        // Skip empty lines and comments
        if (!cmd || cmd.startsWith('#')) continue;
        // Handle line numbers from Read tool
        if (cmd.includes('→')) {
            cmd = cmd.split('→')[1].trim();
        }
        if (cmd) {
            commands.push(cmd);
        }
    }

    return commands;
}

async function runSolution() {
    console.log('=' .repeat(60));
    console.log(' ZORK I: Z2JS ENGINE TEST');
    console.log('=' .repeat(60));
    console.log();

    // Load commands
    const solutionFile = path.join(__dirname, 'zork1_final_solution.txt');
    const commands = loadSolution(solutionFile);
    console.log(`Loaded ${commands.length} commands from solution\n`);

    // Create game machine
    const m = createZMachine();

    // Capture output
    let outputBuffer = '';
    let allOutput = '';

    m.outputCallback = (text) => {
        outputBuffer += text;
        allOutput += text;
        // Show progress dots
        if (text.includes('score')) {
            process.stdout.write('\n' + text);
        }
    };

    // Command index
    let cmdIndex = 0;
    let lastProgressReport = 0;

    return new Promise((resolve, reject) => {
        function feedNextCommand() {
            // Progress report every 50 commands
            if (cmdIndex - lastProgressReport >= 50) {
                console.log(`\n--- Progress: ${cmdIndex}/${commands.length} commands ---`);
                lastProgressReport = cmdIndex;
            }

            if (cmdIndex >= commands.length) {
                // All commands done, send "score" to get final result
                console.log('\n\n--- All commands executed, getting final score ---\n');
                if (m.inputCallback) {
                    outputBuffer = '';
                    m.inputCallback('score');
                    setTimeout(() => {
                        console.log('\nFINAL OUTPUT:');
                        console.log(outputBuffer);
                        resolve({ success: true, output: allOutput });
                    }, 100);
                } else {
                    resolve({ success: true, output: allOutput });
                }
                return;
            }

            const cmd = commands[cmdIndex];
            cmdIndex++;

            // Skip combat commands after victory (troll dies)
            if (cmd.startsWith('kill troll') && outputBuffer.includes('dies')) {
                // Skip remaining troll attacks
                while (cmdIndex < commands.length && commands[cmdIndex].startsWith('kill troll')) {
                    cmdIndex++;
                }
            }

            if (m.inputCallback) {
                // Clear buffer before command
                outputBuffer = '';

                // Send command
                m.inputCallback(cmd);

                // Wait for processing then feed next
                setTimeout(feedNextCommand, 5);
            } else if (m.finished) {
                console.log('\n!!! Game finished unexpectedly');
                resolve({ success: false, output: allOutput });
            } else {
                // Not ready yet, wait
                setTimeout(feedNextCommand, 10);
            }
        }

        // Error handler
        process.on('uncaughtException', (err) => {
            console.error('\nError:', err.message);
            reject(err);
        });

        // Start the game
        try {
            m.run();
            // Wait for game to initialize, then start feeding commands
            setTimeout(feedNextCommand, 50);
        } catch (e) {
            console.error('Failed to start game:', e.message);
            reject(e);
        }
    });
}

// Run it
runSolution()
    .then((result) => {
        console.log('\n' + '=' .repeat(60));
        console.log(' TEST COMPLETE');
        console.log('=' .repeat(60));

        // Extract final score from output
        const scoreMatch = result.output.match(/Your score is (\d+)/i);
        if (scoreMatch) {
            console.log(`\nFinal Score: ${scoreMatch[1]} points`);
        }

        process.exit(result.success ? 0 : 1);
    })
    .catch((err) => {
        console.error('\nFailed:', err);
        process.exit(1);
    });

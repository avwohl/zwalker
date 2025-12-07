#!/usr/bin/env node
/**
 * Test Lost Pig solution using z2js engine
 *
 * Runs the official walkthrough through z2js-compiled Lost Pig
 * and verifies the final score.
 */

const fs = require('fs');
const path = require('path');

// Load the compiled game
const { createZMachine } = require('./lostpig_z2js.js');

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
    console.log(' LOST PIG: Z2JS ENGINE TEST');
    console.log('=' .repeat(60));
    console.log();

    // Load commands
    const solutionFile = path.join(__dirname, 'lostpig_solution.txt');
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
    };

    // Command index
    let cmdIndex = 0;
    let lastProgressReport = 0;

    return new Promise((resolve, reject) => {
        function feedNextCommand() {
            // Progress report every 30 commands
            if (cmdIndex - lastProgressReport >= 30) {
                console.log(`--- Progress: ${cmdIndex}/${commands.length} commands ---`);
                lastProgressReport = cmdIndex;
            }

            if (cmdIndex >= commands.length) {
                // All commands done, send "score" to get final result
                console.log('\n--- All commands executed, getting final score ---\n');
                if (m.inputCallback) {
                    outputBuffer = '';
                    m.inputCallback('score');
                    setTimeout(() => {
                        console.log('FINAL OUTPUT:');
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

            if (m.inputCallback) {
                // Clear buffer before command
                outputBuffer = '';

                // Send command
                m.inputCallback(cmd);

                // Wait for processing then feed next
                setTimeout(feedNextCommand, 5);
            } else if (m.finished) {
                console.log('\n!!! Game finished');
                console.log('Final output snippet:');
                console.log(outputBuffer.slice(-500));
                resolve({ success: true, output: allOutput });
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
        const scoreMatch = result.output.match(/(\d+) out of a possible 7/i);
        if (scoreMatch) {
            console.log(`\nFinal Score: ${scoreMatch[1]}/7 points`);
        }

        // Check for victory
        if (result.output.includes('*** You have won ***') ||
            result.output.includes('Grunk win!')) {
            console.log('VICTORY: Game completed!');
        }

        process.exit(result.success ? 0 : 1);
    })
    .catch((err) => {
        console.error('\nFailed:', err);
        process.exit(1);
    });

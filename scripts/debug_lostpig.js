#!/usr/bin/env node
/**
 * Debug Lost Pig walkthrough - show output for each command
 */

const fs = require('fs');
const path = require('path');

const { createZMachine } = require('./lostpig_z2js.js');

function loadSolution(filepath) {
    const content = fs.readFileSync(filepath, 'utf-8');
    const commands = [];
    for (const line of content.split('\n')) {
        let cmd = line.trim();
        if (!cmd || cmd.startsWith('#')) continue;
        if (cmd.includes('→')) cmd = cmd.split('→')[1].trim();
        if (cmd) commands.push(cmd);
    }
    return commands;
}

async function debug() {
    const solutionFile = path.join(__dirname, 'lostpig_solution.txt');
    const commands = loadSolution(solutionFile);
    console.log(`Loaded ${commands.length} commands\n`);

    const m = createZMachine();
    let outputBuffer = '';

    m.outputCallback = (text) => {
        outputBuffer += text;
    };

    let cmdIndex = 0;

    return new Promise((resolve) => {
        function feedNext() {
            if (cmdIndex >= commands.length) {
                console.log('\n=== STOPPED AT COMMAND', cmdIndex, '===');
                m.inputCallback && m.inputCallback('score');
                setTimeout(() => {
                    console.log('\nSCORE OUTPUT:', outputBuffer);
                    resolve();
                }, 100);
                return;
            }

            const cmd = commands[cmdIndex];
            cmdIndex++;

            if (m.inputCallback) {
                outputBuffer = '';
                m.inputCallback(cmd);
                setTimeout(() => {
                    // Show command and response
                    const response = outputBuffer.trim().split('\n').slice(0, 3).join(' | ');
                    const hasError = outputBuffer.includes("don't understand") ||
                                    outputBuffer.includes("can't see") ||
                                    outputBuffer.includes("doesn't make sense") ||
                                    outputBuffer.includes("not here");
                    const marker = hasError ? '❌' : '✓';
                    console.log(`${marker} [${cmdIndex}] ${cmd}`);
                    // Show all responses
                    console.log(`   → ${response.substring(0, 150)}`);
                    feedNext();
                }, 5);
            } else if (m.finished) {
                console.log('Game finished');
                resolve();
            } else {
                setTimeout(feedNext, 10);
            }
        }

        m.run();
        setTimeout(feedNext, 50);
    });
}

debug().then(() => process.exit(0));

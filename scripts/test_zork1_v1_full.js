#!/usr/bin/env node
/**
 * Test Zork I v1 (Z-machine version 1) full walkthrough
 */

const { createZMachine } = require('./zork1_v1_z2js.js');

// Adapted walkthrough for v1 (same as v3 but syntax may differ slightly)
const commands = [
    // Opening - get supplies
    "open mailbox", "take leaflet", "south", "east", "open window", "in",
    "west", "take lamp", "take sword", "move rug", "open trapdoor", "turn on lamp",
    "down",
    // Troll fight
    "north", "kill troll with sword", "kill troll", "kill troll", "kill troll", "kill troll",
    "kill troll", "kill troll", "kill troll", "kill troll", "kill troll",
    // Get egg from tree
    "west", "west", "up", "take egg", "down", "east",
    // Loud Room - get bar
    "north", "east", "north", "east", "east",
    "echo", "take bar", "west", "west",
    // Check score
    "score"
];

async function test() {
    const m = createZMachine();
    let output = '';
    let allOutput = '';
    m.outputCallback = (text) => { 
        output += text; 
        allOutput += text;
    };
    
    let idx = 0;
    return new Promise((resolve) => {
        function next() {
            if (idx >= commands.length) {
                console.log("\n=== FINAL STATUS ===");
                // Find score in output
                const scoreMatch = allOutput.match(/score[^\n]*(\d+)/i);
                console.log(allOutput.slice(-800));
                resolve();
                return;
            }
            const cmd = commands[idx++];
            if (m.inputCallback) {
                output = '';
                m.inputCallback(cmd);
                setTimeout(() => {
                    const hasError = output.includes("can't") || output.includes("don't understand");
                    const marker = hasError ? '!' : ' ';
                    const resp = output.slice(0, 120).replace(/\n/g, ' | ');
                    console.log(`${marker}[${idx}] ${cmd.padEnd(25)} -> ${resp}`);
                    next();
                }, 10);
            } else if (m.finished) {
                console.log("Game finished");
                resolve();
            } else {
                setTimeout(next, 20);
            }
        }
        m.run();
        setTimeout(next, 100);
    });
}

test().then(() => process.exit(0));

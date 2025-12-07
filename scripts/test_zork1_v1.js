#!/usr/bin/env node
/**
 * Test Zork I v1 (Z-machine version 1) with z2js
 */

const { createZMachine } = require('./zork1_v1_z2js.js');

// Quick test commands
const commands = [
    "look",
    "open mailbox",
    "read leaflet",
    "go south",
    "go east",
    "open window",
    "go in",
    "go west",
    "take lamp",
    "take sword",
    "go east",
    "go east",
    "open trapdoor",
    "go down",
    "turn on lamp",
    "look"
];

async function test() {
    const m = createZMachine();
    let output = '';
    m.outputCallback = (text) => { output += text; };
    
    let idx = 0;
    return new Promise((resolve) => {
        function next() {
            if (idx >= commands.length) {
                console.log("=== FINAL OUTPUT ===");
                console.log(output.slice(-1500));
                resolve();
                return;
            }
            const cmd = commands[idx++];
            console.log("CMD:", cmd);
            if (m.inputCallback) {
                output = '';
                m.inputCallback(cmd);
                setTimeout(() => {
                    const resp = output.slice(0, 200).replace(/\n/g, ' | ');
                    console.log("RESP:", resp);
                    next();
                }, 10);
            } else {
                setTimeout(next, 20);
            }
        }
        m.run();
        setTimeout(next, 100);
    });
}

test().then(() => process.exit(0));

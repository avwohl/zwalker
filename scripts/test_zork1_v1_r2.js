#!/usr/bin/env node
const { createZMachine } = require('./zork1_v1_r2_z2js.js');

const commands = [
    "look", "open mailbox", "take leaflet", "read leaflet",
    "south", "east", "open window", "in",
    "west", "take lamp", "take sword", "move rug", "open trapdoor",
    "turn on lamp", "down", "north",
    "kill troll with sword", "kill troll", "kill troll", "kill troll", "kill troll",
    "west", "south", "east", "south", "southeast", "take coins",
    "northwest", "north", "west", "north",
    "score"
];

async function test() {
    const m = createZMachine();
    let output = '';
    m.outputCallback = (text) => { output += text; };
    
    let idx = 0;
    return new Promise((resolve) => {
        function next() {
            if (idx >= commands.length) {
                console.log("\n=== FINAL ===\n" + output.slice(-600));
                resolve();
                return;
            }
            const cmd = commands[idx++];
            if (m.inputCallback) {
                output = '';
                m.inputCallback(cmd);
                setTimeout(() => {
                    const err = output.includes("can't") || output.includes("don't");
                    const m = err ? '!' : ' ';
                    console.log(`${m}[${idx}] ${cmd.padEnd(22)} -> ${output.slice(0,100).replace(/\n/g,' | ')}`);
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

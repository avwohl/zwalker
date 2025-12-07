#!/usr/bin/env node
const { createZMachine } = require('./905_z2js.js');

const commands = [
    "answer phone", "stand", "south",
    "remove watch", "remove clothes", "drop all", "enter shower",
    "take watch", "wear watch", "north",
    "get all from table", "open dresser", "get clothes", "wear clothes",
    "east", "open front door", "south",
    "unlock car", "open car",
    "no",   // freeway onramp
    "wait",
    "no",   // stop for food
    "wait",
    "yes"   // arrive at work
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
            if (idx >= commands.length || m.finished) {
                console.log("\n=== FINAL OUTPUT ===");
                console.log(allOutput.slice(-2500));
                resolve();
                return;
            }
            const cmd = commands[idx++];
            if (m.inputCallback) {
                output = '';
                m.inputCallback(cmd);
                setTimeout(() => {
                    console.log(`[${idx}] ${cmd.padEnd(18)} -> ${output.slice(0,90).replace(/\n/g,' | ')}`);
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

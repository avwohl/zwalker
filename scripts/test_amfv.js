#!/usr/bin/env node
const { createZMachine } = require('./amfv_z2js.js');

const commands = [
    " ",        
    "peof",     
    "z", "z", "z", "z", "z", "z", "z",
    "look",
    "examine desk",
    "examine decoder on desk",
    "look at decoder on desk",
    "read article"
];

async function test() {
    const m = createZMachine();
    let output = '';
    m.outputCallback = (text) => { output += text; };
    
    let idx = 0;
    return new Promise((resolve) => {
        function next() {
            if (idx >= commands.length || m.finished) {
                console.log("\n=== FINAL ===");
                console.log(output.slice(-2000));
                resolve();
                return;
            }
            const cmd = commands[idx++];
            if (m.inputCallback) {
                output = '';
                m.inputCallback(cmd);
                setTimeout(() => {
                    if (cmd !== "z") {
                        console.log(`[${idx}] ${cmd.padEnd(25)} -> ${output.slice(0,150).replace(/\n/g,' | ')}`);
                    }
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

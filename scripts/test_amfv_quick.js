#!/usr/bin/env node
const { createZMachine } = require('./amfv_z2js.js');

const commands = ["look", "inventory", "south"];

async function test() {
    const m = createZMachine();
    let output = '';
    m.outputCallback = (text) => { output += text; };
    
    let idx = 0;
    return new Promise((resolve) => {
        function next() {
            if (idx >= commands.length) {
                console.log("=== OUTPUT ===");
                console.log(output.slice(-2000));
                resolve();
                return;
            }
            const cmd = commands[idx++];
            if (m.inputCallback) {
                m.inputCallback(cmd);
                setTimeout(next, 20);
            } else {
                setTimeout(next, 30);
            }
        }
        m.run();
        setTimeout(next, 100);
    });
}

test().then(() => process.exit(0));

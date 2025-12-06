#!/usr/bin/env node
/**
 * Replay a walkthrough in a z2js-generated game
 *
 * Usage: node replay_walkthrough.js <game.js> <walkthrough.json>
 */

const fs = require('fs');

if (process.argv.length < 4) {
    console.error('Usage: node replay_walkthrough.js <game.js> <walkthrough.json>');
    process.exit(1);
}

const gameFile = process.argv[2];
const walkthroughFile = process.argv[3];

// Load the z2js-generated game
const gameModule = require(gameFile);

// Load the walkthrough
const walkthrough = JSON.parse(fs.readFileSync(walkthroughFile, 'utf8'));
const commands = walkthrough.commands || [];

console.log('='.repeat(60));
console.log('REPLAYING WALKTHROUGH IN Z2JS');
console.log('='.repeat(60));
console.log(`Game: ${gameFile}`);
console.log(`Commands: ${commands.length}`);
console.log('');

// Mock I/O for automated playback
let commandIndex = 0;
let outputs = [];

// Replace the input function to feed commands
global.readInput = function() {
    if (commandIndex < commands.length) {
        const cmd = commands[commandIndex++];
        console.log(`\n> ${cmd}`);
        return cmd;
    }
    return 'quit';
};

// Replace output function to capture output
let currentOutput = '';
global.writeOutput = function(text) {
    currentOutput += text;
    process.stdout.write(text);
};

// Start the game
console.log('Starting game...\n');
try {
    gameModule.run();
} catch (e) {
    console.error(`\nGame error: ${e.message}`);
}

console.log('\n' + '='.repeat(60));
console.log('REPLAY COMPLETE');
console.log('='.repeat(60));
console.log(`Commands executed: ${commandIndex}`);

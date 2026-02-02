#!/usr/bin/env node
/**
 * Smart test for loose with z2js
 *
 * Handles random events (combat, thief, grue, etc.)
 * Commands: 500
 */

const { createZMachine } = require('./loose_z2js.js');

// Suppress z2js noise ("[Z-Machine execution stopped]")
const originalError = console.error;
console.error = (...args) => {
    const msg = args.join(' ');
    if (!msg.includes('Z-Machine execution stopped')) {
        originalError.apply(console, args);
    }
};

const commands = [
    "n",
    "s",
    "e",
    "w",
    "u",
    "d",
    "ne",
    "nw",
    "se",
    "sw",
    "in",
    "out",
    "open window",
    "open door",
    "open gate",
    "open trapdoor",
    "move rug",
    "move carpet",
    "pull lever",
    "push button",
    "open chest",
    "open box",
    "enter",
    "climb down",
    "climb up",
    "open trap door",
    "unlock door",
    "unlock gate",
    "take all",
    "get all",
    "take lamp",
    "take lantern",
    "take sword",
    "take knife",
    "take key",
    "take keys",
    "take bottle",
    "take food",
    "take leaflet",
    "take egg",
    "take jewels",
    "take coins",
    "turn on lamp",
    "light lamp",
    "turn on lantern",
    "light lantern",
    "n",
    "s",
    "e",
    "w",
    "u",
    "d",
    "ne",
    "nw",
    "se",
    "sw",
    "in",
    "out",
    "open window",
    "open door",
    "open gate",
    "open trapdoor",
    "move rug",
    "move carpet",
    "pull lever",
    "push button",
    "open chest",
    "open box",
    "enter",
    "climb down",
    "climb up",
    "open trap door",
    "unlock door",
    "unlock gate",
    "n",
    "s",
    "e",
    "w",
    "u",
    "d",
    "ne",
    "nw",
    "se",
    "sw",
    "in",
    "out",
    "open window",
    "open door",
    "open gate",
    "open trapdoor",
    "move rug",
    "move carpet",
    "pull lever",
    "push button",
    "open chest",
    "open box",
    "enter",
    "climb down",
    "climb up",
    "open trap door",
    "unlock door",
    "unlock gate",
    "n",
    "s",
    "e",
    "w",
    "u",
    "d",
    "ne",
    "nw",
    "se",
    "sw",
    "in",
    "out",
    "open window",
    "open door",
    "open gate",
    "open trapdoor",
    "move rug",
    "move carpet",
    "pull lever",
    "push button",
    "open chest",
    "open box",
    "enter",
    "climb down",
    "climb up",
    "open trap door",
    "unlock door",
    "unlock gate",
    "n",
    "s",
    "e",
    "w",
    "u",
    "d",
    "ne",
    "nw",
    "se",
    "sw",
    "in",
    "out",
    "open window",
    "open door",
    "open gate",
    "open trapdoor",
    "move rug",
    "move carpet",
    "pull lever",
    "push button",
    "open chest",
    "open box",
    "enter",
    "climb down",
    "climb up",
    "open trap door",
    "unlock door",
    "unlock gate",
    "n",
    "s",
    "e",
    "w",
    "u",
    "d",
    "ne",
    "nw",
    "se",
    "sw",
    "in",
    "out",
    "open window",
    "enter window",
    "go window",
    "enter",
    "in",
    "d",
    "down",
    "open door",
    "open gate",
    "open trapdoor",
    "move rug",
    "move carpet",
    "pull lever",
    "push button",
    "open chest",
    "open box",
    "enter",
    "climb down",
    "climb up",
    "open trap door",
    "unlock door",
    "unlock gate",
    "n",
    "s",
    "e",
    "w",
    "u",
    "d",
    "ne",
    "nw",
    "se",
    "sw",
    "in",
    "out",
    "open window",
    "enter window",
    "go window",
    "enter",
    "in",
    "d",
    "down",
    "open door",
    "open gate",
    "open trapdoor",
    "move rug",
    "move carpet",
    "pull lever",
    "push button",
    "open chest",
    "open box",
    "enter",
    "climb down",
    "climb up",
    "open trap door",
    "unlock door",
    "unlock gate",
    "n",
    "s",
    "e",
    "w",
    "u",
    "d",
    "ne",
    "nw",
    "se",
    "sw",
    "in",
    "out",
    "open window",
    "open door",
    "open gate",
    "open trapdoor",
    "move rug",
    "move carpet",
    "pull lever",
    "push button",
    "open chest",
    "open box",
    "enter",
    "climb down",
    "climb up",
    "open trap door",
    "unlock door",
    "unlock gate",
    "n",
    "s",
    "e",
    "w",
    "u",
    "d",
    "ne",
    "nw",
    "se",
    "sw",
    "in",
    "out",
    "open window",
    "enter window",
    "open door",
    "enter door",
    "open gate",
    "open trapdoor",
    "move rug",
    "move carpet",
    "pull lever",
    "push button",
    "open chest",
    "open box",
    "enter",
    "climb down",
    "climb up",
    "open trap door",
    "unlock door",
    "unlock gate",
    "n",
    "s",
    "e",
    "w",
    "u",
    "d",
    "ne",
    "nw",
    "se",
    "sw",
    "in",
    "out",
    "open window",
    "open door",
    "open gate",
    "open trapdoor",
    "move rug",
    "move carpet",
    "pull lever",
    "push button",
    "open chest",
    "open box",
    "enter",
    "climb down",
    "climb up",
    "open trap door",
    "unlock door",
    "unlock gate",
    "n",
    "s",
    "e",
    "w",
    "u",
    "d",
    "ne",
    "nw",
    "se",
    "sw",
    "in",
    "out",
    "open window",
    "enter window",
    "go window",
    "enter",
    "in",
    "d",
    "down",
    "open door",
    "enter door",
    "go door",
    "enter",
    "in",
    "d",
    "down",
    "open gate",
    "open trapdoor",
    "move rug",
    "move carpet",
    "pull lever",
    "push button",
    "open chest",
    "open box",
    "enter",
    "climb down",
    "climb up",
    "open trap door",
    "unlock door",
    "unlock gate",
    "look",
    "examine front",
    "examine hasn't",
    "examine little",
    "examine bedtime",
    "examine isn't",
    "examine that",
    "examine running",
    "examine your",
    "examine fence",
    "examine veers",
    "take front",
    "take hasn't",
    "take little",
    "take bedtime",
    "take isn't",
    "take that",
    "take running",
    "take your",
    "take fence",
    "take veers",
    "open front",
    "open hasn't",
    "open little",
    "open bedtime",
    "open isn't",
    "open that",
    "open running",
    "open your",
    "open fence",
    "open veers",
    "read front",
    "read hasn't",
    "read little",
    "read bedtime",
    "read isn't",
    "read that",
    "read running",
    "read your",
    "read fence",
    "read veers",
    "move front",
    "move hasn't",
    "move little",
    "move bedtime",
    "move isn't",
    "move that",
    "move running",
    "move your",
    "move fence",
    "move veers",
    "push front",
    "push hasn't",
    "push little",
    "push bedtime",
    "push isn't",
    "push that",
    "push running",
    "push your",
    "push fence",
    "push veers",
    "pull front",
    "pull hasn't",
    "pull little",
    "pull bedtime",
    "pull isn't",
    "pull that",
    "pull running",
    "pull your",
    "pull fence",
    "pull veers",
    "turn front",
    "turn hasn't",
    "turn little",
    "turn bedtime",
    "turn isn't",
    "turn that",
    "turn running",
    "turn your",
    "turn fence",
    "turn veers",
    "light front",
    "light hasn't",
    "light little",
    "light bedtime",
    "light isn't",
    "light that",
    "light running",
    "light your",
    "light fence",
    "light veers",
    "look",
    "examine coils",
    "examine fingers",
    "examine barricade",
    "examine here",
    "examine around",
    "examine exits",
    "examine gnarled",
    "examine forest",
    "examine clammy",
    "take coils",
    "take fingers",
    "take barricade",
    "take here",
    "take around",
    "take exits",
    "take gnarled",
    "take forest",
    "take clammy",
    "open coils",
    "open fingers",
    "open barricade",
    "open here",
    "open around",
    "open exits",
    "open gnarled",
    "open forest",
    "open clammy",
    "read coils",
    "read fingers",
    "read barricade",
    "read here",
    "read around",
    "read exits",
    "read gnarled",
    "read forest",
    "read clammy",
    "move coils",
    "move fingers",
    "move barricade",
    "move here",
    "move around",
    "move exits",
    "move gnarled",
    "move forest",
    "move clammy",
    "push coils",
    "push fingers",
    "push barricade",
    "push here",
    "push around",
    "push exits",
    "push gnarled",
    "push forest",
    "push clammy",
    "pull coils",
    "pull fingers"
];

// Random event patterns to detect
const randomEvents = [
    { id: "thief_encounter", name: "Thief", pattern: /thief|someone carrying a large bag|nasty knife|stiletto/i, checkItem: "sword" },
    { id: "troll_encounter", name: "Troll", pattern: /troll|nasty troll|dangerous troll/i, checkItem: "sword" },
    { id: "grue_warning", name: "Grue", pattern: /eaten by a grue|lurking grue|grue is|pitch black|dark\\..*eaten/i, checkItem: "lamp" },
    { id: "combat_attack", name: "Combat", pattern: /attacks you|strikes at you|swings at you|lunges at you|hits you/i, checkItem: "sword" },
    { id: "cyclops_encounter", name: "Cyclops", pattern: /cyclops|one-eyed giant/i, checkItem: null }
];

// Responses for each event type
const eventResponses = {
    "thief_encounter": {"has_sword": ["kill thief with sword", "attack thief with sword"], "default": ["drop all", "wait", "wait", "wait", "take all"]},
    "troll_encounter": {"has_sword": ["kill troll with sword", "attack troll"], "default": ["flee", "run", "retreat"]},
    "grue_warning": {"has_lamp": ["turn on lamp", "light lamp"], "default": ["go back", "retreat", "flee"]},
    "combat_attack": {"has_sword": ["kill attacker with sword", "attack", "fight"], "default": ["flee", "run"]},
    "cyclops_encounter": {"default": ["give lunch to cyclops", "say odysseus", "odysseus", "ulysses"]}
};

async function test() {
    console.log('='.repeat(60));
    console.log(' LOOSE: SMART Z2JS TEST');
    console.log('='.repeat(60));
    console.log(`Running ${commands.length} commands (with random event handling)\n`);

    const m = createZMachine();
    let outputBuffer = '';
    let allOutput = '';
    let inventory = new Set();  // Track inventory for conditional responses

    m.outputCallback = (text) => {
        outputBuffer += text;
        allOutput += text;

        // Track inventory changes
        if (/you.*(?:take|get|pick up)/i.test(text)) {
            const itemMatch = text.match(/(?:take|get|pick up)\s+(?:the\s+)?([\w\s]+)/i);
            if (itemMatch) inventory.add(itemMatch[1].toLowerCase().trim());
        }
        if (/taken/i.test(text) && outputBuffer.length < 50) {
            // Short "Taken." response - item from last command
        }
    };

    let cmdIndex = 0;
    let eventCommandsQueue = [];  // Commands to handle current event
    let handlingEvent = false;
    let eventsHandled = 0;
    let lastProgressReport = 0;

    function checkForRandomEvent(output) {
        for (const event of randomEvents) {
            if (event.pattern.test(output)) {
                return event;
            }
        }
        return null;
    }

    function getEventResponse(event) {
        const responses = eventResponses[event.id];
        if (!responses) return [];

        // Check if we have the required item for special response
        if (event.checkItem && inventory.has(event.checkItem)) {
            const key = `has_${event.checkItem}`;
            if (responses[key]) return [...responses[key]];
        }

        return responses.default ? [...responses.default] : [];
    }

    function showProgress() {
        if (cmdIndex - lastProgressReport >= 30) {
            console.log(`--- Progress: ${cmdIndex}/${commands.length} commands (events handled: ${eventsHandled}) ---`);
            lastProgressReport = cmdIndex;
        }
    }

    return new Promise((resolve, reject) => {
        function feedNextCommand() {
            // First, check if we detected a random event in last output
            if (!handlingEvent) {
                const event = checkForRandomEvent(outputBuffer);
                if (event) {
                    console.log(`\n>>> RANDOM EVENT: ${event.name} detected!`);
                    eventCommandsQueue = getEventResponse(event);
                    if (eventCommandsQueue.length > 0) {
                        handlingEvent = true;
                        eventsHandled++;
                        console.log(`    Responding with: ${eventCommandsQueue[0]}`);
                    }
                }
            }

            // Handle event commands first
            if (handlingEvent && eventCommandsQueue.length > 0) {
                const eventCmd = eventCommandsQueue.shift();
                if (eventCommandsQueue.length === 0) {
                    handlingEvent = false;  // Done with this event
                }

                if (m.inputCallback) {
                    outputBuffer = '';
                    m.inputCallback(eventCmd);
                    setTimeout(feedNextCommand, 5);
                    return;
                }
            }

            // Normal command processing
            if (cmdIndex >= commands.length) {
                console.log('\n--- All commands executed ---');
                console.log(`Events handled: ${eventsHandled}\n`);
                console.log('FINAL OUTPUT (last 1500 chars):');
                console.log(allOutput.slice(-1500));

                // Extract score
                const scoreMatch = allOutput.match(/(\d+)\s*(?:out of|\/)\s*(\d+)/i);
                if (scoreMatch) {
                    console.log(`\nFinal Score: ${scoreMatch[1]}/${scoreMatch[2]} points`);
                }

                // Check victory
                if (/\*\*\* You have won \*\*\*|You have won|Victory|Congratulations/i.test(allOutput)) {
                    console.log('\n✓ VICTORY: Game completed!');
                }

                resolve({ success: true, output: allOutput, eventsHandled });
                return;
            }

            showProgress();

            const cmd = commands[cmdIndex];
            cmdIndex++;

            // Track take commands for inventory
            if (/^(?:take|get|pick up)\s+/i.test(cmd)) {
                const itemMatch = cmd.match(/^(?:take|get|pick up)\s+(?:the\s+)?(.+)/i);
                if (itemMatch) inventory.add(itemMatch[1].toLowerCase().trim());
            }

            if (m.inputCallback) {
                outputBuffer = '';
                m.inputCallback(cmd);
                setTimeout(feedNextCommand, 5);
            } else if (m.finished) {
                console.log('\n!!! Game finished early');
                console.log('Final output:', outputBuffer.slice(-500));
                resolve({ success: true, output: allOutput, eventsHandled });
            } else {
                setTimeout(feedNextCommand, 10);
            }
        }

        process.on('uncaughtException', (err) => {
            console.error('\nError:', err.message);
            console.error('Command index:', cmdIndex);
            if (cmdIndex > 0) console.error('Last command:', commands[cmdIndex - 1]);
            reject(err);
        });

        try {
            m.run();
            setTimeout(feedNextCommand, 50);
        } catch (e) {
            console.error('Failed to start:', e.message);
            reject(e);
        }
    });
}

test()
    .then((result) => {
        console.log('\n' + '='.repeat(60));
        console.log(` TEST COMPLETE - Events: ${result.eventsHandled}`);
        console.log('='.repeat(60));
        process.exit(0);
    })
    .catch((err) => {
        console.error('\nTest failed:', err);
        process.exit(1);
    });

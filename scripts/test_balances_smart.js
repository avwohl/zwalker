#!/usr/bin/env node
/**
 * Smart test for balances with z2js
 *
 * Handles random events (combat, thief, grue, etc.)
 * Commands: 486
 */

const { createZMachine } = require('./balances_z2js.js');

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
    "turn on lamp",
    "light lamp",
    "turn on lantern",
    "light lantern",
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
    "look",
    "examine matchwood",
    "examine lived",
    "examine extend",
    "examine day",
    "examine horizon",
    "examine feel",
    "examine glassless",
    "examine sunny",
    "examine warm",
    "examine someone",
    "take matchwood",
    "take lived",
    "take extend",
    "take day",
    "take horizon",
    "take feel",
    "take glassless",
    "take sunny",
    "take warm",
    "take someone",
    "open matchwood",
    "open lived",
    "open extend",
    "open day",
    "open horizon",
    "open feel",
    "open glassless",
    "open sunny",
    "open warm",
    "open someone",
    "read matchwood",
    "read lived",
    "read extend",
    "read day",
    "read horizon",
    "read feel",
    "read glassless",
    "read sunny",
    "read warm",
    "read someone",
    "move matchwood",
    "move lived",
    "move extend",
    "move day",
    "move horizon",
    "move feel",
    "move glassless",
    "move sunny",
    "move warm",
    "move someone",
    "push matchwood",
    "push lived",
    "push extend",
    "push day",
    "push horizon",
    "push feel",
    "push glassless",
    "push sunny",
    "push warm",
    "push someone",
    "pull matchwood",
    "pull lived",
    "pull extend",
    "pull day",
    "pull horizon",
    "pull feel",
    "pull glassless",
    "pull sunny",
    "pull warm",
    "pull someone",
    "turn matchwood",
    "turn lived",
    "turn extend",
    "turn day",
    "turn horizon",
    "turn feel",
    "turn glassless",
    "turn sunny",
    "turn warm",
    "turn someone",
    "light matchwood",
    "light lived",
    "light extend",
    "light day",
    "light horizon",
    "light feel",
    "light glassless",
    "light sunny",
    "light warm",
    "light someone",
    "look",
    "examine broken",
    "examine directions",
    "examine this",
    "examine sway",
    "examine peaceful",
    "examine faint",
    "examine grasslands",
    "examine north",
    "examine over",
    "examine hills",
    "take broken",
    "take directions",
    "take this",
    "take sway",
    "take peaceful",
    "take faint",
    "take grasslands",
    "take north",
    "take over",
    "take hills",
    "open broken",
    "open directions",
    "open this",
    "open sway",
    "open peaceful",
    "open faint",
    "open grasslands",
    "open north",
    "open over",
    "open hills",
    "read broken",
    "read directions",
    "read this",
    "read sway",
    "read peaceful",
    "read faint",
    "read grasslands",
    "read north",
    "read over",
    "read hills",
    "move broken",
    "move directions",
    "move this",
    "move sway",
    "move peaceful",
    "move faint",
    "move grasslands",
    "move north",
    "move over",
    "move hills",
    "push broken",
    "push directions",
    "push this",
    "push sway",
    "push peaceful",
    "push faint",
    "push grasslands",
    "push north",
    "push over",
    "push hills",
    "pull broken",
    "pull directions",
    "pull this",
    "pull sway",
    "pull peaceful",
    "pull faint",
    "pull grasslands",
    "pull north",
    "pull over",
    "pull hills",
    "turn broken",
    "turn directions",
    "turn this",
    "turn sway",
    "turn peaceful",
    "turn faint",
    "turn grasslands",
    "turn north",
    "turn over",
    "turn hills",
    "light broken",
    "light directions",
    "light this",
    "light sway",
    "light peaceful",
    "light faint",
    "light grasslands",
    "light north",
    "light over",
    "light hills",
    "look",
    "examine trail",
    "examine pile",
    "examine runs",
    "examine oats",
    "examine horse",
    "examine valley",
    "examine here",
    "examine munching",
    "examine pleasant",
    "take trail",
    "take pile",
    "take runs",
    "take oats",
    "take horse",
    "take valley",
    "take here",
    "take munching",
    "take pleasant",
    "open trail",
    "open pile",
    "open runs",
    "open oats",
    "open horse",
    "open valley",
    "open here",
    "open munching",
    "open pleasant",
    "read trail",
    "read pile",
    "read runs",
    "read oats",
    "read horse",
    "read valley",
    "read here",
    "read munching",
    "read pleasant",
    "move trail",
    "move pile",
    "move runs",
    "move oats",
    "move horse",
    "move valley",
    "move here",
    "move munching",
    "move pleasant",
    "push trail",
    "push pile",
    "push runs",
    "push oats",
    "push horse",
    "push valley",
    "push here",
    "push munching",
    "push pleasant",
    "pull trail",
    "pull pile",
    "pull runs",
    "pull oats",
    "pull horse",
    "pull valley",
    "pull here",
    "pull munching",
    "pull pleasant",
    "turn trail",
    "turn pile",
    "turn runs",
    "turn oats",
    "turn horse",
    "turn valley",
    "turn here",
    "turn munching",
    "turn pleasant",
    "light trail",
    "light pile",
    "light runs",
    "light oats",
    "light horse",
    "light valley",
    "light here",
    "light munching",
    "light pleasant"
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
    console.log(' BALANCES: SMART Z2JS TEST');
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

#!/usr/bin/env node
/**
 * Smart test for trinity with z2js
 *
 * Handles random events (combat, thief, grue, etc.)
 * Commands: 244
 */

const { createZMachine } = require('./trinity_z2js.js');

// Suppress z2js noise ("[Z-Machine execution stopped]")
const originalError = console.error;
console.error = (...args) => {
    const msg = args.join(' ');
    if (!msg.includes('Z-Machine execution stopped')) {
        originalError.apply(console, args);
    }
};

const commands = [
    "trinity",
    "as you'll see, trinity is not all that difficult a game, although there are a",
    "to time, in case you make an error along the way. apple owners should note that",
    "they can get only 3 positions on the save disk, even tho the docs say 4. a",
    "second save disk may therefore come in handy. also, from time to time in some",
    "places, little quotes will pop up in your screen. these are meant to give a",
    "little flavor to the game; they are not really clues or hints. so if you don't",
    "know french (or latin, for that matter), don't worry about it. finally, this",
    "walkthru shows only one way of completing the game, so don't be afraid to",
    "ok, here you are in london, on the last day of your $599 package tour,",
    "strolling around the kensington gardens. all seems well, but in a short time,",
    "world war iii is going to start, and you certainly don't want to be around when",
    "that happens. from the palace gate, go ne to the wabe and the sundial. it looks",
    "just like the one that comes in the game package, so you needn't spend precious",
    "instead, unscrew the gnomon from the dial and get it (and be prepared for some",
    "really awful gnomon jokes later on). with that in hand, saunter on se to the",
    "flower walk, where you find a soccer ball someone left behind. pick that up,",
    "here you see an old woman struggling with an umbrella. as you step forward to",
    "help her, you are momentarily frozen in your tracks by the sight of her face,",
    "the umbrella flies loose and lodges in the branches of a tree. the old woman",
    "all of that happens automatically; there is nothing you can do to stop it from",
    "happening. just as well, since you will be needing that umbrella later on. so,",
    "as they sometimes say in london), head along west past the round pond, admiring",
    "buy a bag, but don't do anything with it just yet. make sure you take the bag",
    "before you leave (you can take the coin, too, although i never did find a use",
    "for it). go north to the black lion gate, where you find an unattended",
    "perambulator (which, fortunately, you can abbreviate to pram in the game). open",
    "it (there is nothing inside, but you want the pram for itself), then push it se",
    "to the round pond again (the boy blowing soap bubbles at inverness terrace is",
    "this time, you see a graceful paper crane swimming in the pond. get that and",
    "open it up. aha, a message! long water, 4 o'clock. put the paper in your pocket",
    "while you think on that a moment. long water is off to the east, but there",
    "seems no way of reaching it. the only route is across the grass at the",
    "you could stuff yourself in the pram, and open the umbrella, the wind might",
    "blow you over to long water. unfortunately, the wind is coming from the east,",
    "so that idea seems out. or does it? push the pram over to lancaster walk, get",
    "a ruby slips out! wow, how about that? but before you can do anything about it,",
    "a bird that looks suspiciously like a road runner picks it up and darts away to",
    "the east. and at that moment, the winds die down briefly, then start up again",
    "from the west (finding the ruby triggers the wind change). now, open your",
    "hurt at all. pick up anything you may have dropped, then just hang around for a",
    "little while. it won't be long before you notice a missile overhead, falling",
    "with excruciating slowness. however, don't stand there gawking; as the missile",
    "approaches, you notice a door has appeared, hovering in the air just above the",
    "water's surface. that's what you've been waiting for, so move quickly east and",
    "through the door (no, you can't take the pram with you, and you don't need it",
    "trinity",
    "you find youself stepping out of a door set in the stem of an enormous",
    "toadstool that is growing in a pleasant meadow. even as you turn to look, the",
    "door fades away into the mushroom. hmmmm. but there is no time to worry about",
    "from the meadow, walk north to the summit. after admiring the view, tramp ne",
    "the south bog. not a very pretty place, especially with that decaying log",
    "at your feet. try getting the log, and it falls to pieces, leaving behind only",
    "pick up the splinter, then go se past the trellis, se again to the arbor",
    "here you find a bizarre glass sculpture, with felix klein 1849-1925 on the",
    "now, go south up the south arbor, then up again to the top. a pretty dizzy",
    "climb, eh? but look what's here: a silver axe. take that, then go north and",
    "ummm...something is not right here. the inscription on the base of the",
    "sculpture is now backwards!!! in fact, if you start wandering around the area,",
    "you'll find that everything is now reversed! but, don't panic! you have just",
    "the trick here is to make a complete circuit, in either direction. you can go",
    "north and come back south, or go south and come back north. either route will",
    "set things to rights again. just make sure you drop the gnomon before you make",
    "ok, pick up the gnomon and make your way back to the trellis. from there, go",
    "due north to the stair bottom (this, by the way, is a good place to leave",
    "the top (brr, it's a bit chilly up here) where you find another sundial,",
    "into the face of the dial....and a lever pops up from the platform (a terrible",
    "this lever is quite important, and controls the dial. examine the dial, and",
    "shadow begins moving again. any time the shadow is directly on a symbol, the",
    "door in a particular toadstoll will open. therefore, you must wait for the",
    "symbol #2 is the toadstool at the waterfall; symbol #3 is the one in the",
    "it is not possible to go through the doors in order to complete the game; you",
    "will need objects from different places in order to finish. so, as usual, you",
    "are going to have to do a bit of waiting here (this is an infocom game, so you",
    "anyway, now that you have the sundial set up, take out some time to map the",
    "area thoroughly. there is no funny business here; the mapping is all very",
    "straighforward, and it's important that you know where everything is and how",
    "to get somewhere quickly. along the way, you'll find an oak tree at the chasm's",
    "you will also find a cottage; by all means, go inside. listen to the magpie",
    "(take the cage) while you read the book of hours (can you guess what it",
    "represents?), and examine the map on the wall (it's your own map, hehehe). poke",
    "around in the garden back of the cottage, too, where you'll find some garlic in",
    "and i'd recommend you not try to disturb the boy blowing bubbles at the",
    "promontory; he's quite a bit larger than when you last saw him. but keep him in",
    "while you're becoming familiar with the area, you might want to do a few other",
    "things, too, such as getting the metal from the crater. visit the ice cavern",
    "west of the waterfall, bringing the axe with you. throw the axe at the icicles",
    "on the ceiling, and one of them will break off. get that and go straight east",
    "the icicle is beginning to melt, and if you go much further, it won't last",
    "until you reach the metal. however, it's pretty cool up at the top, so climb",
    "up to the dial, where the icicle freezes up again. now you can go down again",
    "and you'll have just enough time to get into the crater and put the icicle",
    "honey is usually found in some places, so put your hand in the hole. ouch!",
    "the north bog and the giant venus fly trap. the bee comes buzzing after you,",
    "but is sidetracked and eaten by the plant. whew! now you can go back to the",
    "ok, now that you've done your mapping, it's time to get busy. back at the",
    "sundial, wait until the shadow is on the third symbol. push the lever, then",
    "head along to the ossuary (at the stair bottom, you can drop off the cage and",
    "however, since you have light with you, he is relatively harmless. proceed",
    "through the door in the toadstool, which transports you to an underground",
    "pick up the walkie talkie and turn it on. sooner or later, a small lizard will",
    "the skink runs past you to the next room, and you'll find he's a slippery",
    "little devil. but you can fool him! turn on the lamp and drop it. then go to",
    "the next room, where the skink is hiding in a crevice. push your splinter into",
    "the crevice, and wait. the lizard will run out to the previous room...but your",
    "lamp is there, and now the poor thing is confused. it comes rushing back in,",
    "to run wildly around your feet. pick it up and put it in your pocket (the skink",
    "now return the way you came (the door is still there) to the ossuary. since",
    "you'll find a key. this key fits in the hole in the other room. turning the",
    "key opens a secret passage in the floor to a room below. go down that into",
    "the ice cavern while the wight stomps about in rage at your escape. turn off",
    "drop off the walkie-talkie and the lamp here. then up you go, pull the lever,",
    "and wait for the shadow to touch the fourth symbol, after which you traipse",
    "on over to the mesa, walk carefully across the tree, and through the open",
    "you're in some kind of building. climb down the ladder, open the box, push the",
    "red button and the switch, and step outside. ah, the south pacific! however,",
    "going to explode soon. make a quick circuit of the area; it's pretty small,",
    "eh? and what about that ominous fin that seems to follow you around?",
    "on the west beach, you spy a small islet offshore, with nothing more than a",
    "small palm tree on it. palm trees are noted for having coconuts, amd coconuts,",
    "as we all know, contain milk (aha!). i'll bet you could swim there...ouch!",
    "nasty crabs! in fact, a whole lot of nasty crabs! you'll never get to that",
    "and now, to make your day, a huge mouthful of sharp teeth erupts from the",
    "water. but wait...it's not a shark, it's a dolphin!! whew! good thing dolphins",
    "are friendly...and playful...and smart, too. just point to the coconut that's",
    "trinity",
    "all right, we're making some progress here. drop off the coconut at the stair",
    "bottom, get the cage, and release the magpie (you don't need him anymore). up",
    "at the top, wait for the shadow to reach the fifth symbol, then hop on down and",
    "brrrrr! it's cold around here, and no wonder: you're in siberia now (america",
    "isn't the only country that conducts nuclear tests). climb down the ladder, and",
    "you'll see that the area is over-run with rodents, all dashing madly off across",
    "the tundra. whatever could they be doing? the only way to find out is to follow",
    "right on going, over the edge to their doom. now you know what they are:",
    "lemmings! and you can see that one of them is stuck in a fissure. grab him",
    "quick and stick him in the cage, then return to the door (freezing to death",
    "ahhh, that's better, nice and warm again. drop off the cage at the stairs, and",
    "go to the top, where you wait for the shadow to touch the sixth symbol. on your",
    "way to the moor, remember to pick up the umbrella, and also make sure you have",
    "oh my, you seem to be falling....and falling pretty quickly, too! one move is",
    "all you have, so don't waste it: open that umbrella, fast!! ooof! a hard",
    "landing, but you seem to be in one piece. pick up anything you may have",
    "children to the north, teachers to the south, a shelter to the east, and a",
    "building to the west. very small place. examining the decorations around the",
    "windows, you note they are origami. uh oh. you're in nagasaki, only a few",
    "shows up. she's about five and very cute. she's also entranced by your umbrella",
    "(guess who she is?). give her the umbrella, and follow the girl into the",
    "now your only question is: how do i get back to the door, fourteen hundred feet",
    "the note to the little girl. she recognizes it immediately as origami, and",
    "as you watch, you see the crane glowing with magical energies. step out of the",
    "shelter, and the crane begins to grow...and grow...and grow...until it's large",
    "that little episode may have left you with an unpleasant feeling, but things",
    "are going to get worse very shortly. drop off the spade, climb up to the dial,",
    "and wait until it reaches symbol #2. go down again, pick up the metal and the",
    "climb into the dish of soapy water, and wait until you're inside a bubble. it",
    "won't hold up very long, so without wasting time, go south, then southwest, and",
    "look, you're in outer space! fortunately, the bubble immediately freezes around",
    "you, providing protection for your frail body. now you see two things: a",
    "crescent moon and a satellite. this is the place; take the skink from your",
    "pocket, and kill the poor thing, strangling it with your fingers. there is no",
    "once that very unpleasant task is done, the satellite is much closer, and the",
    "now the satellite is moving back the way you came. again, there isn't much time",
    "here before you get vaporized, so when you see the door getting closer, break",
    "ok, you have everything now that the magpie told you about. get the coconut,",
    "and make your way to the cottage. drop the coconut, hit it with the axe, get",
    "the coconut, and pour the last of the milk into the cauldron. drop the axe and",
    "ouch! but at least the honey is off your hand and in the pot. now drop in the",
    "skink, and the garlic, then leave and wait outside. when all the excitement",
    "dies down, go back in. hmmm...not much left of the book of hours, but that's",
    "not important. peek in the cauldron, and at the bottom, you see...an emerald!",
    "from the cottage, go to the cemetary over the waterfall. pry the crypt open",
    "with the spade (remember, it's sturdy enough...and how many of you out there",
    "grave-robbing time. take the shroud and the two crazy boots. untie the bandage",
    "and the corpse's mouth falls open, revealing a silver coin. get that too (you",
    "can drop the bandage). examine the boots, and you see that each has a",
    "compartment in it. put the emerald in the green boot. aha, it's sprouted wings!",
    "too bad you don't have something for the red boot, but maybe you'll come across",
    "go down, and make sure you have the following with you before you go to the",
    "river: shroud (worn), boots (worn), silver coin, cage (with lemming), the lamp,",
    "ok, you stand on the shore of the river styx, waiting for the dark oarsman to",
    "by a shroud, he lets you in the boat (you wonder why he doesn't notice the cage",
    "with the live lemming, or the hissing walkie-talkie...). hand him the silver",
    "coin. in due time, the boat pushes off for the other side, and you are on your",
    "trinity",
    "part iv",
    "and so you step through the final door. new mexico, 1945. in a short while, the",
    "again. you are here to sabotage that explosion, but not for the reasons you may",
    "think. however, there's a long way to go before you can get around to doing",
    "wait until the voices leave. while you wait, examine the paperbook book; inside",
    "is a very important piece of cardboard (you don't have to take it with you;",
    "just note down what's written on it). you might also want to take a look at",
    "ok, climb down to the bottom of the tower, and there you see...the roadrunner!",
    "he's sitting on a mysterious locked box that you can't open (yet!), and in his",
    "beak, he holds the ruby, which he drops for you to take. get that, and put it",
    "in the red boot. now, you can move pretty quickly across the desert. just as",
    "from the tower, zip across the sands to point able (your faithful roadrunner",
    "don't go too close; what you're interested in here is the abandoned jeep. get",
    "inside. you can ignore the wallet (it has a picture of a boy inside...guess",
    "who?). look at the radio dial, and see what number it's set to. this number is",
    "so far, so good. now it's time to visit old mcdonald's ranch (sorry, no",
    "hamburgers). check the floor plan on the map. go to the assembly room. oops!",
    "helluva thing if you came this far, only to die of a snakebite, so hop right",
    "of course, this is only a temporary measure. you have to come out, sooner or",
    "later, and the rattler will still be there. so, you're going to have to give",
    "him something. that something, alas, is the lemming. open the cage, and the",
    "lemming will jump out and begin scurrying around on the floor. open the door,",
    "after the snake leaves, examine the workbench (you can drop the cage, by the",
    "way). here you find a screwdriver. take that, then go to the kitchen, where",
    "you pick up a steak knife. then it's outside, for a visit to the reservoir",
    "at the reservoir, climb up and drop everything you're holding (no need to",
    "a creaky ladder leads up, and it doesn't look very safe. however, nothing",
    "ventured, nothing gained, so you go up the ladder. just as you reach out to",
    "grab the binoculars....crash!!!!",
    "you fell through into the reservoir. and what about the binoculars? well,",
    "they're at the bottom. how to get them? simple! climb out, get the lamp, and",
    "jump back in again. turn on the lamp, and swim down. aha, there they are! grab",
    "the binocs (you can abbreviate them like that in the game, too), and return to",
    "the surface. pick up all your other stuff (you can drop the lamp), and make",
    "there certainly is a lot of activity around this place. better stay hidden",
    "behind the shed. while you're there, why not take a peek at the shelters with",
    "your binocs? hmmm...isn't that interesting: looks like you just found the key",
    "to that mysterious locked box by the tower. on the other hand, there certainly",
    "when your speedy friend shows up, tell him to get the key and voila! he nips",
    "in, grabs it, and nips out again. pretty speedy, all right!",
    "return to the tower, and open the box (you can drop the key and padlock after",
    "that). inside is a lot of electrical equipment, and a breaker. open the",
    "breaker, then immediately close it again. listen to the reactions over the",
    "now, you need to get back up the tower, but with the spotlight on, you're",
    "certain to be seen. something will have to be done about this, so head",
    "good doggie, nice doggie...be very quiet, and don't wake the german shepherd",
    "that's sleeping outside the bunker. instead, drop the bag of crumbs, and wait",
    "for the roadrunner to arrive. as soon as he does, run like the wind for the",
    "tower. waste no time here at all. get to the tower, and climb right up to the",
    "top and get inside while your friendly roadrunner is raising hell back at the",
    "whew! just made it. ok, turn on the light (there's a chain switch you can pull)",
    "and unscrew the panel with the screwdriver. look inside, and you'll see four",
    "wires. only one is the right one to cut. but, don't be in a rush, you have a",
    "little time now, so wait. wait until you hear over the walkie-talkie that the",
    "auto-sequencer is running. at that point, cut the red wire!",
    "the countdown goes on...5..4..3..2..1...zilch. no explosion. and even as you",
    "wonder what it is you've just done, everything begins to melt away, and that",
    "so you've saved the entire state of new mexico from being smeared off the map",
    "(the bomb was just a bit stronger than expected). cold comfort, when you begin",
    "to realize how nature is going to fix up this paradox. all prams lead to the"
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
    console.log(' TRINITY: SMART Z2JS TEST');
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

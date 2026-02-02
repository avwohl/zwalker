#!/usr/bin/env node
/**
 * Smart test for anchor with z2js
 *
 * Handles random events (combat, thief, grue, etc.)
 * Commands: 298
 */

const { createZMachine } = require('./anchor_z2js.js');

// Suppress z2js noise ("[Z-Machine execution stopped]")
const originalError = console.error;
console.error = (...args) => {
    const msg = args.join(' ');
    if (!msg.includes('Z-Machine execution stopped')) {
        originalError.apply(console, args);
    }
};

const commands = [
    "anchorhead: an interactive tale of lovecrafian horror by michael gentry",
    "story about how to finish the game off. the game is split into four \"days\",",
    "with a set of puzzles to complete each day. once certain puzzles have been",
    "completed, the day moves to \"evening\", where you are expected to go home &",
    "circumstances. there are some puzzles that can be done at any time after a",
    "certain point, and by no means are all the puzzles expected to be completed",
    "in order. certain puzzles are optional; the game can be completed without a",
    "full score if you forget to do certain things, or couldn`t be bothered, or",
    "so, without further ado;",
    "you have arrived in anchorhead, carrying nothing but an umbrella, a trenchcoat,",
    "the clothes you stand up in & your wedding ring. if you read the blurb at the",
    "start, you find out that michael, your husband, has run off to the university",
    "to check out some paperwork, leaving you to pick up the keys to his family",
    "house. if you wander around a bit, find the university, and michael, he'll",
    "get a little exasperated at you if you don`t have the keys, so you'd better",
    "find them. you start out outside the agent's office, which is inexplicably",
    "locked, so you try & find another way in; the alley to the se looks promising,",
    "so have a look down there. you`ll see a fence, which you should examine, and",
    "some garbage cans (or \"bins\", as i insist in calling them). there is also a",
    "window. if you have read the \"about\", you'll notice a dead giveaway in that one",
    "of the hardest things mr. gentry found to code was shoving the can under the",
    "window - so give that a go. if you stand on it, open the window, and close your",
    "you can look things up in the files, but what? well, head to the main office,",
    "cousin, or whatever), so go & look up verlac in the files, where you'll find",
    "the keys to the house. ignore the styrofoam cup; it tastes pretty foul; it",
    "head to the university library, where michael is working, but on the way, head",
    "up the side road just past the pub, where you'll find a blank wall, with no",
    "obvious way around. head back sw (not se), and go find michael. before you",
    "disturb him, go & have a look at what you need to get a book out of the",
    "you are there, have a look at what michael is reading. quite a weighty tome,",
    "so maybe you should try & have a look at it yourself later. for now, go & say",
    "hello to your husband, show him the keys, and try & find the house. if you go",
    "too far wrong, michael will tell you it isn`t in that direction, but if",
    "as to exactly where it is. so, head to the obelisk, and find your way out of",
    "town to the south - michael will stop you going too far wrong (from the",
    "obelisk, go e, s, sw, nw). read the notice, and unlock the front door. head",
    "into the house, but don`t explore too far - you don`t have a torch. it's safer",
    "when you get into bed, \"sleep\", and remember what you dream (pretty harrowing",
    "you wake up to the sound of michael showering. if you want to, listen to him",
    "for a while - he comes out with some highly amusing comments, in the light of",
    "subsequent events, but the important thing here is to get the means of reading",
    "what he was reading yesterday, so examine his pants. search them (it is a good",
    "search his wallet as well, and get the faculty card. he'll come out, tell you",
    "anyway, put on your clothes, and your trenchcoat - which can hold an amazing",
    "amount of stuff - and go into the bathroom, picking up the towel, and putting",
    "it in your coat. head back through the bedroom, picking up your umbrella and",
    "keyring on the way - put the umbrella in your coat as well - and have a wander",
    "around the house. there are a lot of things you can do, now, and there isn`t",
    "from the foyer, head n to the back hall, and w into the kitchen. grab the",
    "flashlight from the kitchen, and head for the pantry, turning the torch on",
    "first. in there is a broom, which comes in very useful for various bit of the",
    "game, so get it. unlock the cellar door (you did pick up your keyring, didn`t",
    "you?), and head down. look in the wine cellar - nothing important there for",
    "the moment, so go into the storage room. have a good poke about, and while",
    "you are at it, have a closer look at the spiders web. before you get the key,",
    "from the landing, go e and then s. the contents of the jewellery box are",
    "worth a look, so get the locket, and have a look at the contents. you can",
    "wear that, so go ahead. have a look at the bed, as well. and under it. the",
    "have a look in the hole, & read the pages, providing you with a fair bit",
    "of useful names, and dates. while you are at it, head into the library north",
    "of the room, & pick up & read the book you find there. if you go e & disturb",
    "michael, don`t stress about it, he'll just tell you to go away. on your way",
    "head back to the university, picking up the newspaper in the town square on",
    "your way (read it, giving you a bit more information about what is going on),",
    "and go to the circulation desk. remember the title of the book from the",
    "register? ring the bell, and show michael's id card to the librarian, and",
    "as anything). read the book - a bit more information, there - and a slip of",
    "paper drops out. keep hold of the paper for now, & read the book again. the",
    "history will give you some names & dates you should look up later, so make a",
    "note of them. chilling stuff. you can`t leave the library with the book, so",
    "4. the magical shoppe",
    "from the narrow street, head nw up the twisting lane. the blank wall that",
    "you saw yesterday has suddenly picked up a bit of graffiti - remember your",
    "head into the cauldron, where the proprietor will be glad to help you,",
    "especially if you ask him about things he has in his cabinet. specifically,",
    "you want the amulet, but he'll give it to you if you ask him about it. wear it,",
    "now you have picked up some names & dates, go look them up in the courthouse",
    "births & deaths records. it is possible to work out the names of the male",
    "verlacs pretty much back to croseus, but don`t stress about doing that just",
    "hmm. a bit quiet? head up to the study, and see if michael is home. well, he",
    "it is a 4 digit code, a date he is likely to remember, so how about his",
    "wedding annivarsay? remove your ring, and have a look on the inside - the",
    "date is june 28th, so how about that? type 0628 on the laptop, and have a read",
    "of what he was typing. those numbers look familiar? read the slip of paper that",
    "you found in the library, and you'll see the two match. head back to the",
    "library, and examine the bookshelves. a somewhat out of place copy of poe will",
    "stand out, so get it, and reveal a safe hidden away behind the cases. the safe",
    "is a dial-type, so try turning the dial to the numbers on the slip of paper",
    "and the laptop, and lo! the safe opens. search the safe to find a puzzle box",
    "and a flute. both of these come in useful, but how to get the darn box open?",
    "well, someone knows how to do it. for now, though, put the box in your pocket,",
    "and head back into the study. have a good look around the fireplace, which",
    "should jar some memories of dreams - \"i don`t know what it opens yet, but i",
    "have a good idea\" - so try turning the spheres. if you go sw you walk into a",
    "maze which is worth wandering around so you get a good idea how to move about",
    "before you do that, however, pick up the letter opener - it will be useful -",
    "(sw from first room leads you to the portrait in the front room, nw from there",
    "leads you to the observatory, the way out). have a look at the telescope, and",
    "then head se, leading you into the crawlspace in the attic. head for the attic,",
    "and examine that locked door. annoying, isn`t it? you can't see through the",
    "keyhole, so what could be blocking it? how about the key? put the newspaper",
    "under the door, and put the opener in the keyhole. something drops onto the",
    "paper, so get the paper, and the key falls off it. get the key, and put it on",
    "your keyring - and then unlock the door. search the room, but pay particular",
    "attention to the straw, where another locket is found, this time gold. wear",
    "this, and head to the kitchen again, this time going out the back door. head",
    "for the crypt, and unlock & open it. there are quite a lot of coffins here, so",
    "routing through them could take some time, but you know the names of two people",
    "at least who have been buried here - edward & william. have a look for their",
    "coffins - notice a difference? open william's coffin, & get what you find",
    "there. head back towards town, go to the cauldron again, and show the puzzle",
    "box to the proprietor, who will open it, revealing a disk. head to the pub,",
    "resist the temptation to drink it yourself. while you are there, you might as",
    "well pick up the lantern, but blow it out first. have a quick wander around the",
    "town if you havn`t already, orientating yourself with the important places,",
    "have a chat with the orderly at the asylum if you want - talk to him about his",
    "magazine, if you like - and then go find the bum who isn`t a bum at all. listen",
    "than the coffee, which will open him up a bit. you have to ask him some pretty",
    "direct questions, and you need to be persistant, but you'll be able to find out",
    "and apparently buried william. you know that that is bogus, as in william's",
    "persist in your questioning about william (\"show skull to bum\", \"bum, tell me",
    "about william\", \"ask bum about william\", and repeat in various ways) until he",
    "breaks down, and tells you. he gets a bit funny about wanting protection,",
    "at this point, so give him the amulet from the cauldron. he'll give you the",
    "copper key, and evening will fall. head se, get the tin of oil, and head back",
    "home. michael isn`t back yet, so stress a little bit, but forget about it for",
    "now & have a bath, after remembering to lock the back door. turn the torch off",
    "the day is split up into a few distinct segments that must be completed. it is",
    "well, apart from part 2 & 3 - no choice about that - and you don`t really",
    "have to do a lot of part 1 - just get the name and work out how to open the",
    "after michael has woken up & wandered off so that you don`t know where",
    "he is, head for the secret passageways in the study, and sw, look through",
    "hole, & nw, look through hole. head for the observatory, put the disk in the",
    "slot, & look through the telescope - write down the name you hear, as it",
    "comes in useful. go down to the wine cellar, and have a look at the wine",
    "bottles that mike was playing with - examine all of them, and make a note of",
    "records office, if you feel like, and check out the dates on the labels;",
    "you'll find corresponding names to the letters on the bottles. head back to",
    "the cellar, and turn the bottles in date order, earliest first, based on",
    "what you know about the family - croseus' birthdate is unknown, but he was",
    "the bottle is a bit faster than typing \"turn pinot\", esp if you forget which",
    "order the bottles go in). this will open the secret door in the cellar,",
    "leading into the windy passages. you`ll get to a pit, eventually, with w &",
    "e ledges - examine both edges, and you`ll see footprints on one of them; head",
    "the crawlspace in the attic - don`t worry about it for now. head down the",
    "stairs, until you come to a door; examine it, and the symbol, and this should",
    "make you think of a passage in \"wardes & seales\", about speaking the name of",
    "a deity to open a door; this is that door. the only deity that resembles the",
    "symbol is the name of the thing you saw through the telescope, so say that",
    "name (you can`t open the door, even if you know the name, unless you have",
    "picked up the points for learning the name), and the door will open. have",
    "a good look at the obelisk - checking out the pictograms is always good - and",
    "have a good look at those columns as well. try blowing the flute, and then",
    "try blowing it with holes covered by your fingers (when trying this out,",
    "remember to remove your finger from one hole before covering the next, until",
    "you know which holes to cover). when you have worked out which holes to cover,",
    "before leaving the house, check the pile of luggage in the foyer. see a bag?",
    "ok, you've checked out practically everywhere in the house, so go for another",
    "wander around the town itself. the cauldron has disappeared again, but never",
    "mind. head south to the deserted lane, and remember your dream - you headed",
    "head along until you get to the slaughterhouse, get everything you see, and",
    "have a look at the picture. odd, isn`t it? oh well, head south, and move the",
    "plywood. have a look down the well, and search the bones, getting the teddy",
    "while you are there. head back out of the slaughterhouse, but wait! whats that",
    "doesn`t take kindly to strangers, and even if you could show the locket of his",
    "mother to him, he won`t give you time to do anything. anyway, after hiding for",
    "go back towards town, but you`ll find your route cut off, somewhat, by a group",
    "of people who are a little disappointed in you. head for the church, but go",
    "around the back - you`ll never get through the door in a month of sundays. have",
    "a look at the trapdoor, and then a look at the padlock - something heavy? have",
    "a look at the meat hook, which shows itself as being something heavy, so try",
    "what's down here? the suggestive shape is, sadly, your estate agent. some",
    "people may make jokes about estate agents and this being the best thing for",
    "them, here, but not i. search the body a couple of times, until you find the",
    "key, and open the furnace, just for morbidity's sake. head to the stairwell,",
    "but don`t jump just yet. stow as much as you can in your pockets - the torch,",
    "more than anything - and jump. you`ll reach the riser, but everything in your",
    "hands will drop down the shaft. don`t worry about it for now, just go &",
    "explore the church. get the robe, and have a read of the black tome on the",
    "altar - but don`t carry on reading it. examine the cross - that may give you",
    "an idea about what went on in this church, and then head for the belfry. get",
    "the rope, and then go back to the stairwell. drop the robe down the shaft, and",
    "it can`t be far to the bottom, so let go of the rope, and lo! you have escaped",
    "you are now in the sewer system. turn the torch on, and get everything that you",
    "may have dropped down the shaft. if you head nw, and u, you can open the door",
    "with the copper key, bringing you out at the riverside. if you exit there, you",
    "can visit everywhere south of the bridge; if you stay in the sewer system, you",
    "can go under the river, and eventually come out behind the fence in the alley",
    "next to the estate agents. go in there in the usual manner, and unlock the",
    "drawer with the steel key you found on her body. read the letter, and put the",
    "key you find on your keyring. head out - the files don`t have anything about",
    "the mill or the lighthouse - and go & find mrs. greer. she lives - read the",
    "you go there and knock on the door, and show her the teddy, she will invite you",
    "in and answer any questions you may have. search max's overalls, get the key,",
    "wander around there as well - make sure you remember the directions you go in,",
    "as well. you may not have time to go \"oh, is it sw or se?\" and pick the wrong",
    "one. when you have finished with that, head for the mill. have a look around,",
    "search _everything_, but especially the thickets. you should be able to unlock",
    "it might be an idea to leave the robe you picked up here, so that you can get",
    "the passageway you are in is fraught with danger; time it wrong and you could",
    "end up steamed. the safest way through is to turn the steam off, rather than",
    "trying to judge the mechanics, so take your towel, and put it on the wheel. the",
    "wheel is now cool enough to touch, and so turn it so the needle drops back",
    "down - the corridor is now safe enough to saunter through. at the end is a bit",
    "of a stuck hatch, so just persist in going through it - eventually it will",
    "open. in the mill itself is a maze and an optional way of avoiding it. if you",
    "have kept hold of your broom, you can avoid the maze; if you havn`t, you must",
    "get through the maze pretty quickly, otherwise you could end up as flambe. the",
    "maze is only 6 rooms, so you should be able to map it pretty easily - just",
    "save & undo a lot. however, if you have kept your broom, you can just go over",
    "the top. have a look at that control panel, and try pulling the lever. a big",
    "block of something you can stand on appears from the roof. now push the",
    "button - and it goes back up. so, if you stood on the block, and had something",
    "broom. when you get to the catwalk, just \"out\" will get you off the block, and",
    "you can check out the device blueprints that the agent alluded to in her",
    "letter. if you read the blues, you'll notice that the main focusing mirror has",
    "two numbers, one crossed out, and another; in the rack is a collection of",
    "spares, so no-one will notice you taking one... get the calipers, and measure",
    "the mirrors, & take the one with the corresponding size to the not-crossed-out",
    "put the mirror in your pocket, and head back the way you came to go back to",
    "who is that? michael? well, lets follow him, then. have a look in the",
    "lighthouse - which is presumably where he went to - and then head back out",
    "of the lighthouse. michael turns up, and he isn`t too happy, but at least he",
    "you wake up inside a padded cell. presumably, you are inside the asylum, the",
    "one you spent hours trying to get in earlier in the game. how to get out?",
    "well, if you examine the door, you`ll notice it is a bit loose on its hinges -",
    "so violence is the answer to this one. hit the door a couple of times, and you",
    "are out of the cell. however, you are still stuck in your straightjacket, and",
    "you are without your belongings, so the first thing is to get out of the",
    "jacket. have a close look at the window. see those cracks? one of them is big",
    "enough to hold the shard of glass on the floor. if you \"rub glass\", you can get",
    "a hint about how to get out of the jacket, so put the glass in the crack, and",
    "then rub it - freedom! have a look in the closet as well - all your belongings",
    "were placed there, the nice chaps they were. get everything, and try to find",
    "your way out. but wait! what's that on the window, further down the corridor?",
    "bloodtains? how did edward die? well, if you asked the orderly, he would have",
    "have a look in there (\"unlock west\" \"open west cell\") and search the tear in",
    "the padding for edwards last testament. read it - giving you another clue - and",
    "to escape the madman, you need to get to the exit, where you find the orderly,",
    "sadly demised, but at least he won`t tweak any more pimples. his magazine is",
    "if you try & go for the key, the madman will catch up with you & start eating",
    "your brains, however, if you get the magazine, and show it to the madman he'll",
    "suddenly be distracted by it & stop chasing you quite so much. this gives you",
    "a few useful seconds to try & get the key. it is out of reach, but you have",
    "something that could snag it - your umbrella (about tells you to keep hold of",
    "keys on your keyring, so do that, and unlock the gate. when you go through it,",
    "the madman starts to chase after you again, but he gets distracted by the",
    "head towards the town square, but before you can get too far, you notice the",
    "mob returning. to stop yourself being caught, go & hide down the side alley,",
    "and just wait until the poor old doc has quacked his last. head back to the",
    "while you are here, you could do something to disrupt the ceremony that you",
    "think is going to happen with the mirror devices, so get the tin of fish oil,",
    "hold it, and open it. put a blob of it on the mirror, and then head north to",
    "get to where the ceremony is likely to be. unfortunately, wills is on the",
    "so try showing him the gold locket, the one containing the picture of his",
    "mother. he will start ignoring you, so the best thing for you to do would",
    "be to kill him before he thinks about killing you, so go & hit him with the",
    "with wills out of the way, head towards the lighthouse again, picking up the",
    "robe you left outside the mill & wearing it - this stops you being spotted by",
    "random groups of people heading towards the ceremony. once you get in the",
    "lighthouse, remove the robe & wear your coat again. get up to the top, and",
    "this would be a good way of disrupting the ceremony, so take it out - but",
    "just then, michael comes in. he hasn`t noticed that you have taken the mirror",
    "the mirror you smeared fish oil on - it is the same size as the real mirror, so",
    "then you will be taken to an island, where you can do nothing apart from",
    "examine things - a good idea, really - until the lighthouse does something",
    "highly amusing, and explodes. everyone runs off, including your guards, so you",
    "can try to pick your handcuffs with the hairpin. of course, due to a small bug,",
    "you can just drop the handcuffs without anyone noticing - at any point at",
    "island before it sinks, and michael will start being _really_ nasty to his new",
    "wife. follow michael back to town, where he sinks into the ground at the",
    "go home, and into the kitchen, where you should be able to find some",
    "matches in the cupboards. head towards the cellar, and open the secret door in",
    "the same way you did earlier in the day. enter the windy passage, and *bang*",
    "your torch finally gives up the ghost. good job you picked up those matches,",
    "then. you can light the lantern from the pub with them, and this won`t blow out",
    "when a hot wind starts coming up the pit. when you get to the pit, cross on the",
    "same side as the footprints (the same side you crossed previously) and then",
    "head _down_ the stairs to the burial mound (you can do this in darkness). when",
    "you get to the mound, michael will start to kill you, so distract him. your",
    "wedding ring always makes you feel sentimental, so maybe the same would happen",
    "to mike - so show it to him. ah! he lets go; but, go for the kill, here. the",
    "amulet is a ward against evil, so maybe you could give it to mike and get rid",
    "of the evil in him, so whikle he is distracted, put the amulet on him, and",
    "croseus verlac is exorcised from mike. earlier today, you should have tried out",
    "the flute in here, so you know which holes to cover, so don`t bother listening",
    "it too long, mike dies, and you finish the game with 65/80. if you do it in",
    "some other things you can do (courtesy michael {not me ;) } )",
    "* the puzzle box an be opened by putting it on the train tracks, if you forget",
    "* if you don`t have the broom, you can tie the chain around your waist and pull",
    "* as well as the two holes mentioned in the maze from the study, there is",
    "another hole that shows the children's bedroom; when michael is wandering",
    "* if you didn`t pick up the lantern from the pub, you can just hold lit matches",
    "for a couple of turns before they blow out - but the hot wind will blow it out",
    "if it appears. hot winds appear at random intervals, so really the lantern is a",
    "* examine william (ugh!)",
    "and is available from ftp://ftp.gmd.de/if-archve/games/inform/anchorhead.z8",
    "and is available from http://www.personal.leeds.ac.uk/~phsmw/anchor.sol"
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
    console.log(' ANCHOR: SMART Z2JS TEST');
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

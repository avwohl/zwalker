#!/usr/bin/env node
/**
 * Test zork3 with z2js
 *
 * Generated from solution JSON file
 * Commands: 209
 */

const { createZMachine } = require('./zork3_z2js.js');

const commands = [
    "* * *  zork i hints  * * *",
    "3. the platinum bar",
    "4. the pot of gold",
    "5. opening the egg",
    "2.  first, get the spirits' attention. having done that,  there's only two",
    "other things  left to do, so play around a little until you have",
    "everything in the right order. read any  good books lately?",
    "3.  this one is easy, if subtle. consider the outstanding quality of the",
    "4.  well, you know where to look, right? you just have to do something",
    "first. have you seen anything around that might remind you of a rainbow?",
    "get the point?",
    "6.  first, you need to have the egg open. then, you have to go to  the",
    "logical place and do the logical thing. when the egg is open, this",
    "7.  everything you need is at hand. play around in the maintenance room, and",
    "remember to check other rooms as well for a  change. tools can come in",
    "* * *  zork ii hints  * * *",
    "1. the riddle room",
    "2. the red sphere",
    "3. the dragon",
    "4. the balloon",
    "5. the bank",
    "6. the menhir",
    "7. the oddly-angled room",
    "8. the demon",
    "1.  aren't riddles a pain? this one should make you thirsty. (think about",
    "that for awhile)",
    "2.  you can't do this one by  yourself, so bring along some help. and keep",
    "in mind that just because you can't see something, that doesn't mean",
    "3.  you can't do anything with him where you find him; now, if you could",
    "4.  balloons are filled with hot air; seen anything flammable  around",
    "lately?",
    "5.  yes, this is certainly a tricky one! the key is the curtain of light;",
    "pay close attention to its description, as well as the piece of paper on",
    "the floor.  also keep in mind that things are not always what they seem",
    "6.  ah, if only you had magical powers, you might be able to do something",
    "about this!",
    "club look like to you? third, read the name on the club carefully; that",
    "should give you some ideas. fourth, what's on the floors? think about",
    "want! (hint: remember the menhir!)",
    "* * *  zork iii hints  * * *",
    "1. the hooded figure",
    "2. the chest",
    "3. scenic vista",
    "4. the ship",
    "5. the jewel room",
    "6. the royal puzzle",
    "7. the guardians of zork",
    "3.  what would you do here if you couldn't see? and don't forget what's on",
    "4.  remember the book from zork i? no? well, just be friendly!",
    "5.  first, read the date on the cage carefully. second, don't be greedy!",
    "third, the way to bring back what you have should be obvious; you just",
    "6.  don't take the easy way out...be pushy! (it helps to have paper  and",
    "pencil handy here!) westward ho!",
    "* * *  starcross hints  * * *",
    "1. the red rod",
    "2. the blue rod",
    "3. the green rod",
    "4. the silver rod",
    "5. the violet rod",
    "6. the crystal rod",
    "7. the control bubble",
    "8. breathable air",
    "2.  this one is tricky. the disks will help you here, once you figure out",
    "what they are. you will also need something else here (\"a tisket, a",
    "3.  again, the disks will be  helpful. also, be a litterbug!",
    "4.  this one you have to look for, but it isn't far away. shake a few",
    "things, and see what happens",
    "6.  you have to project yourself  into this one. it would also  help if you",
    "7.  \"for every action, there is an equal and opposite reaction...\". think",
    "* * *  suspended hints  * * *",
    "1. trouble with weather control?",
    "2. can't fix iris?",
    "3. main supply machine broken?",
    "4. want the camera?",
    "5. looking for spare parts?",
    "6. worried about poet and waldo?",
    "7. trying to reset?",
    "8. still trying to reset?",
    "* * *  deadline hints  * * *",
    "1. looking for a motive?",
    "2. can't figure out the method?",
    "3. still wondering about method?",
    "4. need more proof?",
    "5. trying to lay a trap?",
    "6. does your trap fail?",
    "3.  you look like you need to freshen up.  when you get where you're going,",
    "* * *  witness hints  * * *",
    "1. nothing exciting happening?",
    "2. can't find any clues?",
    "3. wondering about the method?",
    "4. is the butler inscrutable?",
    "5. trying to nail down proof?",
    "6. can't unlock the clock?",
    "* *  mask of the sun hints  * *",
    "1. the silver bowl",
    "2. exiting the first pyramid",
    "3. the gas chamber",
    "4. leaving the altar room",
    "5. exiting the third pyramid",
    "1.  something you've had with you from the very beginning of the  game can",
    "2.  you have to urn your way out of this one. heavy stuff!",
    "* *  serpent's star hints  * *",
    "1. getting past the wolf",
    "2. the wandering monk",
    "3. the first monastery",
    "4. the second monastery",
    "5. the monk's first question",
    "6. the monk's second question",
    "7. the monk's third question",
    "8. the dragon's first question",
    "9. the dragon's second question",
    "2.  he might be in the mood for a little conversation....and  doesn't he",
    "look a bit thin?",
    "6.  the answer to this one is hard to give a hint for; you really have to",
    "know something about eastern religion. if you happen to know the names",
    "of the male and female principles, that's the answer. check out the wall",
    "7.  well, the answer is *not* sophia loren...think about that for awhile!",
    "isn't the yellow brick road!)",
    "* *  dark crystal hints  * *",
    "1. crossing the swamp",
    "2. aughra's riddle",
    "3. evading the garthim",
    "4. entering the castle",
    "5. getting to the crystal",
    "1.  well, you can't just walk through the swamp, so, do you remember seeing",
    "anything anywhere that floats?",
    "4.  there could be something behind those bars; wonder if there's anyone",
    "around who could slip through them?",
    "* * *  planetfall hints  * * *",
    "1. the key in the crack",
    "2. across the rift",
    "3. fromitz replacement 4. miniaturization card",
    "5. the microbe",
    "6. the mutants",
    "2.  extend yourself, and you may get the idea!",
    "5.  hot stuff! in fact, too hot to handle!",
    "6.  don't stop for anything!!",
    "* * * the enchanter hints * * *",
    "1. the jeweled box",
    "2. the engine room 3. the gallery",
    "4. the adventurer",
    "5. the guarded door",
    "6. the map",
    "7. the guncho scroll",
    "8. the winding stairs",
    "1.  think sharp....you might have to risk your life for this one, but the",
    "sacrifice is worth it. get the point?",
    "4.  first, get his attention (why not give him a call?). then, get on his",
    "on the pencil!",
    "* death in the caribbean hints *",
    "1. the message on the monument",
    "2. crossing the river",
    "3. the zombie",
    "4. the fog",
    "5. the bull",
    "6. the quicksand",
    "2.  first, take safety precautions. then, consider what might be able to",
    "* * *  infidel hints  * * *",
    "1. some hieroglyphs",
    "2. the circular room",
    "3. the niches",
    "4. the slab room",
    "5. the scarab",
    "6. the four statues",
    "/!\\    beam                  <--*   put               -!-    balance",
    "*>    scarab                !!!    door              *-->   take/pick",
    "3.  beam me up, scotty!",
    "4.  the position of the holes should remind you of something; or are you",
    "going around in circles?",
    "5.  stay level-headed, and your cup will not runneth over!",
    "6.  one good turn deserves another. keep an orderly mind @ all times",
    "* * * sorcerer hints * * *",
    "1. getting out",
    "2. the glass maze",
    "3. the cannon",
    "4. no place left to go?",
    "5. seeing double?",
    "6. those grues!",
    "1.  you need to get the trunk open. have you read your infotater lately?",
    "2.  you'll need to go batty to solve this one! and have you been down by the",
    "riverside yet?",
    "3.  careful reading of the infotater should help...and that's no manure!!",
    "4.  stop draggin' your feet. this is a one in a malyon chance!",
    "5.  remember the golden rule, and at whom you're looking!",
    "6.  repellant, aren't they? don't forget that weeds are still weeds!",
    "* * * seastalker hints * * *",
    "1. can't fix the videophone?",
    "2. can't start the sub?",
    "3. circuits overheating?",
    "4. can't identify the traitor?",
    "5. can't navigate accurately?",
    "6. can't stop the sea cat?",
    "4.  check the emergency survival unit and confront the persons who installed",
    "6.  better zap the power pod!",
    "1. the babel fish",
    "2. the dark",
    "3. the spare drive",
    "4. the bugblatter",
    "5. zaphod & the hog",
    "6. the screening door",
    "7. opening the hatch",
    "1.  bring some junk along with you, and put it somewhere!",
    "2.  you have five senses; count while you wait!",
    "4.  consult the guide about the bugblatter. do some sharp thinking about the",
    "memorial, and don't throw in the towel!",
    "5.  have you forgotten trillian? isn't she holding something?",
    "6.  consult the guide about intelligence. what happens when you pick up the",
    "real tea?",
    "one, and that's no fluff!"
];

async function test() {
    console.log('=' .repeat(60));
    console.log(' ZORK3: Z2JS ENGINE TEST');
    console.log('=' .repeat(60));
    console.log(`Running ${commands.length} commands\n`);

    const m = createZMachine();
    let outputBuffer = '';
    let allOutput = '';

    m.outputCallback = (text) => {
        outputBuffer += text;
        allOutput += text;
    };

    let cmdIndex = 0;

    // Progress tracking
    let lastProgressReport = 0;

    function showProgress() {
        if (cmdIndex - lastProgressReport >= 30) {
            console.log(`--- Progress: ${cmdIndex}/${commands.length} commands ---`);
            lastProgressReport = cmdIndex;
        }
    }

    return new Promise((resolve, reject) => {
        function feedNextCommand() {
            if (cmdIndex >= commands.length) {
                console.log('\n--- All commands executed ---\n');
                console.log('FINAL OUTPUT:');
                console.log(allOutput.slice(-2000));

                // Try to extract score
                const scoreMatch = allOutput.match(/(\d+)\s+(?:out of|\/)\s*(\d+)/i);
                if (scoreMatch) {
                    console.log(`\nFinal Score: ${scoreMatch[1]}/${scoreMatch[2]} points`);
                }

                // Check for victory
                if (allOutput.match(/\*\*\* You have won \*\*\*|You have won|Victory|Congratulations/i)) {
                    console.log('\n✓ VICTORY: Game completed!');
                }

                resolve({ success: true, output: allOutput });
                return;
            }

            showProgress();

            const cmd = commands[cmdIndex];
            cmdIndex++;

            if (m.inputCallback) {
                outputBuffer = '';
                m.inputCallback(cmd);
                setTimeout(feedNextCommand, 5);
            } else if (m.finished) {
                console.log('\n!!! Game finished early');
                console.log('Final output:');
                console.log(outputBuffer.slice(-500));
                resolve({ success: true, output: allOutput });
            } else {
                setTimeout(feedNextCommand, 10);
            }
        }

        process.on('uncaughtException', (err) => {
            console.error('\nError:', err.message);
            console.error('Command index:', cmdIndex);
            if (cmdIndex > 0) {
                console.error('Last command:', commands[cmdIndex - 1]);
            }
            reject(err);
        });

        try {
            m.run();
            setTimeout(feedNextCommand, 50);
        } catch (e) {
            console.error('Failed to start game:', e.message);
            reject(e);
        }
    });
}

test()
    .then((result) => {
        console.log('\n' + '=' .repeat(60));
        console.log(' TEST COMPLETE');
        console.log('=' .repeat(60));
        process.exit(0);
    })
    .catch((err) => {
        console.error('\nTest failed:', err);
        process.exit(1);
    });

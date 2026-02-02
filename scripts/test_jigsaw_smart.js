#!/usr/bin/env node
/**
 * Smart test for jigsaw with z2js
 *
 * Handles random events (combat, thief, grue, etc.)
 * Commands: 470
 */

const { createZMachine } = require('./jigsaw_z2js.js');

// Suppress z2js noise ("[Z-Machine execution stopped]")
const originalError = console.error;
console.error = (...args) => {
    const msg = args.join(' ');
    if (!msg.includes('Z-Machine execution stopped')) {
        originalError.apply(console, args);
    }
};

const commands = [
    "3nd and *final* revision",
    "by bonni mierzejewska",
    "this is as complete as one person (that person being me) can make it.  many",
    "century park",
    "you begin in century park on new year's eve, 1999.  there's a party raging",
    "that is giving you a headache, and you're trying to avoid it as long as",
    "go east.  this is the beer tent, and you'll catch sight of that intriguing",
    "stranger in black (everyone was supposed to wear white to this party, as you",
    "know if you read the party ticket in your possession).  get the sparkler from",
    "the potato.  going back west, you find that black has left you a jigsaw",
    "go southeast to behind the beer tent.  take the rucksack and search the crate",
    "(examine it, too - it's stamped a4).  take the curious device and the tagged",
    "going back nw, go ne to the churchyard.  go e into the church, and e again",
    "into the vestry.  look under the stool and get the pencil; look in the stool",
    "and get emily's book.  go w twice (back to the churchyard) and sketch the",
    "night-jar.  then go sw to century park and w to kaldecki's monument.  climb",
    "the monument and examine the lightning-conductor.  it's made of fuse.  light",
    "it and there will be a boom.  go d and enter the monument.  you won't be",
    "in the monument you'll see a display case.  you can examine it and its",
    "contents, but you won't be able to do anything with it for a while, so you",
    "can ignore it for now.  go e further into the pyramid.  you'll find a dusty",
    "room with a table and a clock.  (you can take a look at the room se, too,",
    "now clean the table and you'll find a puzzle board.  (examine it and you get",
    "the rows are labeled a to d and the columns are labeled 1 to 4.  take a look",
    "at the corner piece you found in century park and turn it until it fits at",
    "a4, the upper right hand corner.  it will light up with a picture of parklands",
    "strobed by laser light.  take the centre piece and put it at c2.  if it",
    "doesn't light up, pick it up again (type \"get c2\"), turn it, and place it at",
    "now, get the ormolu clock and set it to 59 (\"set clock to 59\").  press c2",
    "(pressing a4 does nothing, because you've solved that now).  you will be",
    "flat over the street",
    "don't try the door.  it's locked, and you haven't got the key.  however, the",
    "tagged key you found in the crate fits the dresser.  unlock the dresser and",
    "open it and you will find another jigsaw piece.  about this time, black will",
    "shake hands with black.  (i don't know why, but this gets you a point.)  just",
    "let black talk; you'll find out a lot.  when black asks you if you understand,",
    "say no to get more info.  then just wait around until black gives you the",
    "sniper's rifle.  slip off the safety (\"switch rifle off\") and wait some more,",
    "until the archduke shows up.  unpleasantly, what you must do then is shoot the",
    "sketch the horses.  then wait around a bit.  the time window will open; black",
    "the device causes the disturbed air to condense into a black sphere, into",
    "which black disappears.  at this point, you can wait until the clock runs out",
    "or simply set the clock to 1 and zip out of there.  (if you don't get",
    "transported right away, type \"look\" and you will be.)  you will be transported",
    "back at the monument",
    "never does.  black's gender is deliberately left indeterminate.  black on some",
    "occasions displays definitely female behaviour and on other occasions displays",
    "definitely male behaviour.  this allows you to assign to black whatever gender",
    "interests you.  there's a reason for that, too, which will become clear to you",
    "you might also be wondering why you need to be drawing all these animals.  well,",
    "game unless you draw at least 4 animals in the course of the game.  some of them,",
    "however, are a challenge to capture on paper and are a challenge in and of",
    "themselves.  i found it interesting to find and draw all of them.  there are",
    "the device black took from you will be on the puzzle board.  in addition to",
    "opening the time window, it tells you what year you're in (examine it when",
    "examine the piece you got.  turn it until the flat edge is at the left and",
    "from now on, what you need to do to fire up the puzzle is set the clock to",
    "s.s. titanic",
    "...to the reading room aboard the titanic on the last night of its fateful",
    "voyage.  there's a note for you from black and a newspaper.  read them if",
    "you like.  then go sw to the first class lounge, n to the port promenade",
    "(fore), w to port promenade (aft), s to adjoining staircase, and u to the",
    "move the chairs so you can get to black's chair.  you'll find a book.  get",
    "the book and open it, and an elegant key falls out.  get it.  then read the",
    "book and remember the new distress code: cqd.  now go d and n,e,s back to",
    "go e to the first class entrance.  while you're here, go u to the top of",
    "stairs, take note that this is where the wireless room is, and go w to the",
    "gymnasium.  take the jacket you find and go e and d again.  from the first",
    "class entrance, go e to the cabins.  unlock black's door with the elegant",
    "key, open it, and go e to enter it.  there, look under the wardrobe to get",
    "the kaldecki device (kd for short) and another note from black.  get the",
    "long barrelled key from the table and open the porthole.  a jigsaw piece will",
    "fall to the floor, which you can now get.  read the note for a little extra",
    "(\"turn kd\") when you're in a chapter, and it will tell you the number of",
    "at some point during your explorations of black's cabin, the stewardess will",
    "to stick around to the very end for a chance to open a time window.  if not,",
    "you'll have other opportunities to enter a time window.  at some point before",
    "now, go back w twice to the lounge, n and w and s to the stairs, wear the",
    "jacket and go w into the smoking room.  wait around until benjamin guggenheim",
    "gives you a letter.  once you have it, go w again into palm court and give",
    "the letter to miss shutes.  she'll squeak and leave, disbanding her ouija",
    "now you need to go back to the wireless room.  once there, unlock the door",
    "with the long key, open it, and go e to enter.  there's a morse key here and",
    "--.- : d is -..  and you need to key them in succession with no pauses.  this",
    "now you can either escape back to the monument by using the clock, or wait",
    "around for the time window.  examine the towel; on it is the location where",
    "the time window opens.  it will open at the precise minute that the titanic",
    "sinks.  be there before 2:10!  as soon as you see the air disturbance, press",
    "you don't get whisked back to the monument prematurely.  just don't forget to",
    "turn it back on again if you want to leave a chapter using the clock!",
    "a note about the compass directions.  if you lay them out, you'll notice that",
    "graham nelson has the titanic heading due east.  i find this improbable, since",
    "the titanic sank just south of newfoundland heading for new york city, but",
    "in the black ball",
    "in the land",
    "search around until you find the pyramid.  very little of the land is open at",
    "this point in the game, and there's no point in trying to explore the mist.  i",
    "think if you enter the land from the titanic chapter you arrive outside the",
    "chinese pagoda.  go in and take a look if you like.  the pyramid is e of the",
    "pagoda.  this will take you to the sw corner of the pyramid; to enter the",
    "whether you use the land or the clock to get back to the monument, you are",
    "back at the monument",
    "back at the monument, you've got these two pieces, and edge piece and a corner",
    "light up with a picture of mould in a petri dish.  turn the edge piece to fit",
    "clarence wing",
    "okay, first open the lower door and go d into the asthma lab.  draw the",
    "white mice, then go n to the lab assistant's office.  penicillium?  mould?",
    "ah!  we're here to help fleming discover penicillin!  get the jar.  you can't,",
    "but you will find a note from black.  go s and u, open the upper door, and",
    "go into fleming's laboratory.  look under the bench and get the petri dish",
    "occasionally fleming will interrupt your nosing about; the first time he does,",
    "suitcase e (it's too heavy for you to carry).  wait around until fleming comes",
    "along, finds the petri dish, and dashes off.  you've just solved the temporal",
    "crisis.  wait a bit to take the time window if you didn't opt to take the one",
    "back at the monument",
    "the piece you found at a1 needs to go at c3 (a racing steam locomotive).  do",
    "the take/turn/put routine on it if it doesn't light up the first time you",
    "temps perdu",
    "locals will go by, and the game tells you what direction they go.  go that",
    "way!  after several turns of this, you will find a flask of absinthe.  drink",
    "it.  you'll have an hallucination of being at a dance party, and black will",
    "be there.  dance with black.  this ends the hallucination, and somehow you're",
    "back at avenue kleber.  now go south twice.  see the coin?  you can get it",
    "now.  take it and go n, open that intriguing door and go e into it.  give the",
    "coin to the bellboy and get into the lift.  go to the top floor, get the",
    "piece, and down to the fifth floor.  exit the lift and go e into the",
    "apartment.  get the tea tray, which turns out to be a puzzle piece.  you have",
    "to get it again, because somehow in getting it, you dropped it.  also get the",
    "madeleine (which can also be referred to as \"cake\").  get back to the lift and",
    "this time you need to swing the pendulum, and you're back at the maison du",
    "the.  see that paperole that was on the clock?  it's on the floor now.  take",
    "it and go back to the fifth floor apartment.  drop the paperole, and you've",
    "solved the temporal crisis (restoring the crucial final passage to proust's",
    "of it.  the land is a 4x4 grid of sections...and so is the puzzle.  every time",
    "you place a jigzaw piece in the correct place, the corresponding section of the",
    "back at the monument",
    "okay, now you've got two more pieces.  the edge piece goes to b4 (the snow",
    "lenin's train",
    "you're on the train lenin took when he returned to russia.  go e, wear the",
    "uniform, open the trunk and search it, then go back to the corridor and unlock",
    "the west compartment door with the little key you found.  open it, enter,",
    "there's a man tied up here!  but don't free him, or you end up getting shot",
    "during the october revolution.  search him instead, which makes him furious,",
    "but you need that permit.  out to the corridor again, go s into the soldier's",
    "compartment.  be polite!  ask them for a piece of pashka.  they'll obligingly",
    "tell you to have it.  take it and go n twice to lenin's compartment.  lenin",
    "himself is here, but he's not paying attention to anyone.  go ne.  there's an",
    "engaging little boy here, and a piece of paper which you need.  give the",
    "pashka to the boy, and he'll let you have the paper.  take it and give it to",
    "now take your chit and go nw.  you'll be in line for the smoking room.  wait",
    "until you get in.  you've got barely enough turns to accomplish what you need",
    "to do here.  look under the bunk, open the vent, get the tray (which turns out",
    "now go ne again and n to the back end of the train.  there's a bomb here!  get",
    "it and throw it.  you've just saved lenin's life so he can start the bolshevik",
    "revolution, more's the pity.  get the piece, too.  now you can either go back",
    "s once to advantage of the time window, or use the clock to get back to the",
    "at this point, i have a theory as to your gender.  since you're able to",
    "supposed to be male, making black female (you'll find out later in the game",
    "that you are definitely opposite genders).  don't let your 1990's liberated",
    "sensibilities trip you up here - in 1917, it was improbably to find any female",
    "british army officers!",
    "back at the monument",
    "abbey road",
    "not much to do here.  you peer in the window and take a look at four scruffy",
    "young men...yes, the beatles.  black is here.  wait around.  black will start",
    "humming loudly, presumably to throw the beatles off.  the only way to restore",
    "the quiet they need is to kiss black.  graham nelson has a little romance in",
    "him!  hang around for the time window or use the clock.  there are no puzzle",
    "back at the monument",
    "where to next?  let's do the pieces you acquired in paris next.  press b2 this",
    "kitty hawk - the flyer",
    "there's a paper dart here.  pick it up and throw it a few times.  notice what",
    "happens?  now go d to the railing.  the wright brothers are using this railing",
    "to get their flyer off the ground.  examine the crowd and draw the yorkshire",
    "terrier.  go e and get the bread and the anemometer.  go e again into the",
    "you're getting better!  play it until you can play vivaldi.  now go e into",
    "the kitchen.  there's a mousetrap here!  put some bread into the trap, wait",
    "until the mouse comes by.  you might have to wait a while before the mouse",
    "actually pauses to inspect the trap.  immediately sketch the mouse.  now",
    "go w and up into the loft bedroom.  get the cap.  you don't need it, but now",
    "you can see the box of mosquito powder, which you do need.  take it and go",
    "the reason why the flyer keeps landing so quickly is because the windspeed",
    "goes up and down in cycles (you can verify this with the anemometer), and",
    "they're missing the peak.  wait there until orville lands and play the",
    "mandolin for him two times in a row.  he'll like it and stick around.  then",
    "wait, and the flyer should fly this time.  *now* you can get near the flyer,",
    "because everyone has raced off to town to telegraph the world.  examine it;",
    "there's a loose square on the aileron.  get it - it's a puzzle piece!",
    "unfortunately, you get caught in the wires and they have to extricate you, but",
    "they don't care at this point.  you end up on the beach.  there's a bottle",
    "bobbing in the waves.  wait until it's almost to hand, and get it.  there's",
    "now go back to the machine shop.  shake the mosquito powder and examine the",
    "heater.  see the little holes?  put bread in them.  if you hadn't shaken the",
    "mosquito powder, the mouse would come along and steal the bread.  the powder",
    "repels it.  the heater will explode, and you can get the lid, which turns out",
    "the time window does show up here, but not in the machine shop.  i *think* it",
    "opens at the beach (look around for it if you like - but be warned that it",
    "only exists for about 2-3 turns).  if you don't want to fool with that, take",
    "back at the monument",
    "edge piece from the heater is d3 (cabbages).  but we're still working on the",
    "in the wilderness",
    "something's gone a little wrong.  you're in a white place.  black is there,",
    "say.  the whiteness resolves on the next turn into a cold whiteness, and",
    "snowlands",
    "sketch the snow goose, and go e until you run into the snow leopard.  don't",
    "back at tundra with the snow goose or the copse of fir trees.  if you end up",
    "at the copse, go sw into the shed, get the grain and the broom and ne again,",
    "and e to the tundra.  if you end up in the tundra, go e to the copse (might",
    "as well examine the nest while you're there) and get the broom and the handful",
    "of grain from the shed.  if you end up in the snowy basin, go u to the tundra,",
    "now go u.  get the coil of cable on this crag and go d twice to the snowy",
    "basin.  sweep the snow.  yes, sweep the snow.  you uncover a disc around a",
    "ten foot shaft.  examine the disc and you find a ring attached to it.  tie",
    "wonder of wonders, there's a us missile here.  you weren't in siberia after",
    "all!  examine it; you'll find a hatch.  open the hatch and go inside.  you",
    "don't have much time now - the missile just started vibrating.  press the",
    "green button (releases a puzzle piece from the hatch) and the blue button",
    "(solves the temporal crisis).  out, get the piece, and up.  quickly.  if you",
    "hang around you will die.  also quickly untie the coil of cable from the ring",
    "go up and give the handful to the goose by *dropping it on the ground* (this",
    "the cable at the nest and pull the cable *twice*.  you'll get the puzzle",
    "piece; be sure to pick it up!",
    "doing things in this order is more efficient (having been informed by email",
    "and after trying this order myself).  however, you probably won't be able to",
    "take advantage of the time window this way, since it opens shortly after the",
    "missile fires.  (the time window opens shortly after the temporal crisis is",
    "solved, regardless of whether or not you have all the puzzle pieces to be",
    "found.)",
    "back at the monument",
    "okay!  the corner piece from the nest goes at d4 (barge), and the edge piece",
    "ghost plane",
    "time is precious here.  go n to the cockpit.  there's a control panel with",
    "buttons and dials, and the engine fire light is on.  press cuteng/l (cut left",
    "engine), and the fire will go out.  but now you're running out of fuel.  sit",
    "in the navigator's chair and turn on the radio.  immediately get up and press",
    "aut/p (autopilot).  now scamper s twice to the fusilage ring, and go w to",
    "the west bomb bay.  examine the hole, then examine the control there.  it says",
    "res/f (reserve fuel).  press it.  **phew**  now you've got lots of time.  go",
    "back to the fusilage ring, put everything in your sack and drop it.  examine",
    "take the safe e to the east bomb bay and drop it.  now you've got some waiting",
    "get your sack and go back to the cockpit.  if you like you can go d and",
    "examine and clean and read the pinup there, but you don't want to do what it",
    "forward until you're at about 760 feet.  wait.  wait some more.  when you",
    "get to about 20% fuel, start paying attention.  a few turns later (pay",
    "attention!) forest will be rushing under you.  press lower/u *now*.  this",
    "you want to exit anyway, so type exit again (or \"g\" to repeat your previous",
    "exit command).  immediately go e.  examine the parachute you find here - there",
    "will be a little gadget in it.  immediately go w and put the gadget on the",
    "safe.  this will unlock it.  open it and get the folder and the shelf (which",
    "turns out to be a puzzle piece.)  you don't need the folder, but it makes for",
    "interesting reading later, so go ahead and get that.  put all in your sack to",
    "an alternative way to do this, i have been informed, is to put the safe in",
    "minor bug in any subsequent release, so be sure to save before you try it.)",
    "if this works, all you need to do is search the parachute to get the gadget,",
    "if you are playing release 1, there's another bug to be aware of - if you are",
    "still wearing the british army uniform when you get captured, the russians",
    "remove it, but it's still flagged as being worn.  to avoid this, remove it",
    "while you're still on the plane and drop it.  this is important in the enigma",
    "within a few turns, a wind will blow the door open.  no time to lose!  go n,",
    "get your sack, back s, and the air currents will be disturbed!  press the",
    "button on the curious device and put black's drugged body into the ball.  the",
    "temporal crisis was black's presence.   this seems to be the only chapter in",
    "which you *must* use the time window to leave.  if you don't, you wreck the",
    "course of history.  perhaps this was the author's way of making sure you get",
    "the point for entering the land?",
    "back at the monument",
    "the edge piece from the plane is d2 (a lady in a crinoline dress).  now that",
    "you have the gadget, you can open the case in the monument.  go w, put the",
    "gadget on the case, open it, and get the model, which turns out to be a",
    "puzzle piece.  get the gadget, which has fallen on the floor.  it's not",
    "necessary anymore, but it's useful later.  the puzzle piece goes at d1",
    "let's press d3 now, decidedly the most difficult and tedious puzzle in the",
    "you're a ghost.  you can't go anywhere but in the barn (just type \"in\").  in",
    "the barn you find black, busily working away at a strange typewriter.  and",
    "black doesn't seem to be able to see you.  no one can!  examine the",
    "examine the paper on the floor and write down what you see.  the two numbers",
    "a - g",
    "w - c",
    "v - t",
    "u - j",
    "y - r",
    "you can fly!  take note of the wheels on top of the wardrobe.  they're not",
    "okay, got that?  go back out, and fly.  you'll bump your head on something",
    "changed to a victorian country house.  turn off the clock alarm just in case,",
    "now you're in a duck blind.  get the spent cartridge.  if you're still wearing",
    "look in the window and you'll see a mallard to sketch.  get the cap and wear",
    "it.  now go w and n.  yes, you want to get caught.  when the corporal asks",
    "you what you are, say either \"poacher\" or \"codebreaker.\"  you'll be taken off",
    "now things are really cooking.  you'll see a crate.  open it.  the game will",
    "tell you this will break the seal irrevocably.  open it anyway.  remove the",
    "machine from the crate.  now, there's an intercept on the wall.  you really",
    "don't have to take it, but you should the first time you play the game just",
    "to see what's going on.  examine the machine, examine the wires.  look in the",
    "crate.  there are five wheels, and the machine can only hold three.  remember",
    "get wheel ii and put it in the machine.  turn it until it shows the first",
    "number that was on the wehrmacht paper in the barn.  get wheel iv and set it",
    "now, the wires.  when you examined them, you should have gotten basic",
    "instructions.  so type \"unstecker\" to remove all of them.  now, you need the",
    "letter combinations that were on the paper.  type \"stecker a to g\" and so on",
    "down the list.  but you know, there were three wires unplugged from the",
    "machine in the barn, and you only have five wires plugged in.  you need to",
    "find the last two combinations.  this is tedious, so here they are: d-f, and",
    "p-x.  okay, now pull the lever.  this puts the machine into decryption mode,",
    "type \"type intercept\" to keep from having to type in every single letter",
    "every time.  if you don't get the message, you have to press the red button,",
    "turn wheel v, and type the intercept again.  do this until you get the",
    "message.  when you finally do (and it can take up to 10 tries, since each",
    "wheel has ten positions and you don't know what setting to use for wheel v),",
    "you get imprisoned.  not to worry, you still have you're possessions, and a",
    "back at the monument",
    "**phew**  the two hardest puzzles are over.  now let's go to the moon to",
    "moon",
    "you're in a tiny cabin in a lunar module in orbit around the moon.  black is",
    "here (surprise, surprise).  get the atlas you see here.  examine the",
    "surroundings and wait until black mutters something about littrow, and",
    "look that up in the atlas (\"look up littrow in atlas\").  the coordinates for",
    "can correct the othello's course and land in the right place.  btw, it's a",
    "bit of useful info to ask black about the astronauts.  the apollo 17",
    "working *with* black instead of *against* black.  nothing to do now until the",
    "now, go d to go outside.  get in the lunar rover, turn the joystick on, and",
    "go s.  get the gnomon.  now go n three times to emory crater and get the green",
    "clod.  go n once to the apollo 17, n once more to the north massif and get the",
    "a pod!  open it with the gnomon to find waldo and his rather terse instruction",
    "sheet.  now get waldo and the paper and head back for the rover.  head s to",
    "apollo 17 and w to find out why you're here.  there's a pu238 rod here that's",
    "got a crack in it.  wrap it with the sunshade.  you can pick up the rod if you",
    "have both hands free, but you can't open the reactor.  hmm.  there's a plug on",
    "the end of the cable leading out of the door of the reactor, and there's a",
    "go w twice.  sw, you can see the genuine astronauts' rover.  best not let",
    "your own rover be seen.  so get out, and go sw.  examine their rover.  gee,",
    "i wonder what that makeshift fender is made of?  but how do you get it?  ah!",
    "there, you need to program waldo.  you can't do that outside, because the",
    "gloves make your fingers too thick.  the commands are on the paper, but you",
    "also need to add a bit of info: how many *times* waldo is to execute the",
    "figuring, you find out that rturn and lturn make waldo turn only 45 degrees",
    "each time.  also, the crater the astronauts currently occupy is roughly",
    "square, and they're in the sw corner while you come in at the ne corner. some",
    "onsite experimentation, and you find that each forward command advances waldo",
    "only halfway along the crater's rim.  so you come up with this program:",
    "type forward 2 (takes waldo along the eastern rim to se corner)",
    "type rturn 2 (turns waldo west)",
    "type forward 2 (takes waldo along the southern rim to sw corner)",
    "type rturn 2 (turns waldo north)",
    "type sample 1 (waldo grabs the fender/puzzle piece)",
    "type forward 2 (takes waldo along the western rim to nw corner)",
    "type rturn 2 (turns waldo east)",
    "type forward 2 (takes waldo along northern rim and back to you)",
    "they'll be fascinated with it.  drop waldo, turn it till it's facing south",
    "(\"turn waldo\") and push the pink button.  if all goes well, you'll have waldo",
    "the temporal crisis here is the fuel rod.  it's going to kill the astronauts,",
    "and you can't allow that.  you discover that you can plug the cable into waldo",
    "and that if waldo is programmed to go forward with the cable plugged in, the",
    "reactor door will open.  you also discover that you can't remove the cable",
    "you can manage to solve this with the program currently in waldo.  put waldo",
    "down, plug in the cable, make sure there's nothing in your hands, push the",
    "button, get the fuel rod, put it in the reactor when the door opens.  waldo",
    "eventually come back so that the reactor door closes.  pick waldo up at this",
    "getting the rod into the reactor solves the crisis.  back at the othello,",
    "leave waldo in the rover (so you don't end up having the game ask you which",
    "button you want to press, the pink hexagonal one or the white button on the",
    "back at the monument",
    "the piece from the moon goes at a3.  the board should be complete now!  let's",
    "berlin",
    "you're in east berlin.  depressing place.  it's 1989, the year the wall came",
    "to the east is a hoarding; it just tells you what year it is.  go w to near",
    "the brandenburg gate, then n to the alley and n again to the river.  get the",
    "rope you find there.  then back s to the alley.  there are hares in no man's",
    "land.  you try to draw them, but you get stopped.  how to draw them?  this",
    "is risky.  climb the fence, go sw, draw the hare, go se, climb the fence, and",
    "enter the apartment, go up, and get the purse you find there.  open it and",
    "take the fifty ost-mark note and the key.  then back down to the street.  head",
    "east to checkpoint charlie and examine the blockhouse to the south.  black!",
    "you can hang around and watch what happens when black makes the crossing.  is",
    "you head north from here and find a skoda.  the cyrillic-lettered key goes to",
    "it.  unlock the skoda, open it, get in, turn it on, and go north.  a man will",
    "ask to clean your windows; give him the fifty.  he'll toss in a note.  uh-oh,",
    "you have to thwart black this time.  black thinks the wall mustn't come down",
    "until 1991, and you know that's not right.  you're at unter den linden, where",
    "leave the engine running and get out of the skoda.  what i didn't tell you is",
    "that in your explorations of the apartment, you searched that masonry that's",
    "all over the floor and discovered a trap door leading down.  go down now, and",
    "don't go west.  go into that little crevice sw.  tie the rope to the telephone",
    "cables.  then go up (through the manhole) and you'll see the underside of the",
    "car.  tie the rope to the skoda.  now go back outside, get in the skoda and",
    "drive it any direction you like.  this solves the temporal crisis.  you end up back",
    "on the precarious balcony of the apartment, and a time window opens.  you",
    "back at the monument",
    "suffragettes",
    "go down from here, you'll find black with a petrol bomb (a \"bloody great",
    "fountain, you see this nightingale, which is being difficult.  get the",
    "newspaper (you need it) and put the cornbread or the madeleine in the",
    "that done, go sw again.  there's a bobby here with some intriguing handcuffs",
    "hanging loosely in his back pocket.  throw the newspaper at the handcuffs,",
    "and the cuffs will fall and the bobby will run off.  get the cuffs and head",
    "back ne twice to black.  well, you've got to stop black somehow.  you cuff",
    "black to the fence.  so much for budding romance?  **sigh**  wait around at",
    "back at the monument",
    "just a couple more pieces left.  but you can't get into the park in d1; the",
    "egypt",
    "what a revolting hotel room.  still, it could be worse.  the door to the north",
    "back to the room.  open the shutters and an annoying mosquito gets in.  if you",
    "wait around a bit, and a hook with attached rope conveniently gets thrown on",
    "the window.  now you can go down.  get on the barge.  ummm, black hasn't",
    "down in the barge, look around.  examine the cans.  examine black.  wait till",
    "black offers you the signed paper.  then examine the deck.  oh my!  you save",
    "black isn't exactly happy about it.  open that strongbox you found in the",
    "cans with the gadget.  the gadget will mollify black a bit.  examine the",
    "passport and the document in the strongbox for some info.  black is sitting",
    "there scared and weary, and shivering even though it isn't cold.  maybe black",
    "has malaria or something.  the blankets aren't takable.  i like to think you",
    "next morning, you get a time window.  you need to use the device on this one,",
    "so black can leave.  black doesn't seem so lethargic upon catching sight of",
    "back at the monument",
    "endgame",
    "you can go north through the gates this time.  on the other side, the man",
    "tells you a few things.  you can ask about black and about the puzzle.  it",
    "seems that what you have to do is destroy the kaldecki machine (which is the",
    "pyramid).  ask the gatekeeper about the amulet he's wearing, then ask *for*",
    "the amulet.  he'll give it to you.  head east from the hinge.  you'll be back",
    "the living land",
    "the land is teeming with life now.  there's a pterodactyl overhead!  don't",
    "be afraid.  do draw it, though.  go e and get the rod.  if you've played",
    "colossal cave, you'll have a notion of what to do with it.  go n and sketch",
    "the apes.  go w to the pagoda, enter it and get the cage.  then go e twice",
    "to the se corner of the pyramid and wave the rod.  tada!  north across the",
    "bridge, then east.  pick up the grenade (do not go into the toll booth - you",
    "before that you can't get into the pyramid.  well, you remember that there's a",
    "river running *under* the pyramid.  maybe the river can carry it in?  so you",
    "and the pterodactyl swoops down and grabs the grenade from you.  dratted",
    "creature.  you can solve this, though.  go north to the scree fall.  wait",
    "until a large rock falls down and knocks you over.  go s immediately, then",
    "n again and get all, and s again before you get killed.  now you've got this",
    "lovely white rock.  go w, drop the rock, get it again, and the pterodactyl",
    "will swoop down, deposit the grenade in a woodpecker's nest, and grab the",
    "white rock.  great.  now the grenade is way up there.  you try climbing the",
    "tree, but that doesn't work.  you can't.  you get mad and shake the tree.  the",
    "one more thing you should do now is go w.  you'll startle a rabbit, which is",
    "the rabbit runs off back w, but doesn't go all the way back because it sees",
    "the rod. follow it w, and it will scamper south across the tree.  go retrieve",
    "grenade, unfortunately.  try as you might, you can't get it from them.  but",
    "they like to *ape* you, don't they?  you try throwing the rod.  they throw",
    "the grenade, but snatch it back before you can get it.  so you throw the rod",
    "at the rabbit.  pay dirt!  the grenade goes bouncing off to the east.  get the",
    "hmm.  it's in the web of a two-foot spider, and you can't get it.  well, you",
    "can draw the spider, so do that.  what to do?  well, go back and get the",
    "put the woodpecker in the cage.  head quickly back to the spider's web with",
    "the woodpecker flies out, and the spider makes a grab for it.  the spider",
    "oh no!  it's stuck to your hand!  pull the pin and you're history.  so you",
    "try washing the grenade.  just what it needed - the solvents in the polluted",
    "there's one more thing you need to do before you destroy the pyramid.  this is",
    "spin and throw out a gem for you.  it's random each game which corner gives",
    "you a gem, and you only get one.  there's no point visiting the remaining",
    "war.  the pagoda is art.  i haven't made an effort to figure out all of them,",
    "but your guess is as good as mine.  if you're really curious, ask on",
    "now, go back to nw of the pyramid, pull the pin, and throw the grenade into",
    "turn of the century",
    "around a table to the nw.  go there.  there's a drawing competition.  give",
    "emily's book to reverend toby.  he loves the drawings, but too late to enter",
    "the competition, so he gives you a consolation prize of a teddy bear.  i've",
    "already commented that you must have 4 or more drawings in the book.  if you",
    "don't, go back to a previous save, and draw as many animals in the living land",
    "one more thing to do.  go se and e.  it's not a beer tent this time, but an",
    "go back w to century park, and yes, black is there.  there's not much you can",
    "do.  you've foiled black at every turn and destroyed the kaldecki machine,",
    "stranding the both of you in the past.  what can you do?  so you give black",
    "and you've won!  black accepts the teddy bear, and the two of you go off to",
    "live the 20th century together.  the gem you collected in the living land",
    "you should have 100 points out of 100, 16/16 on the drawing game, and a nice",
    "cheers!",
    "bonni"
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
    console.log(' JIGSAW: SMART Z2JS TEST');
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

"MICROQUEST -- a self-contained ZIL game used as the zorkie<->zwalker
 integration test. Small on purpose: it exercises the full loop (READ +
 dictionary word matching + verbs + a scored win) using only ZIL that zorkie
 compiles today, so `scripts/test_zorkie_game.py microquest` can drive a
 zorkie-compiled build to a verified `*** You have won ***`.
 See docs/ZORKIE_TESTING.md."

<VERSION 3>

<GLOBAL READBUF <ITABLE 50 (BYTE)>>
<GLOBAL LEXBUF <ITABLE 20 (BYTE)>>
<GLOBAL SCORE 0>
<GLOBAL VAULT-OPEN <>>
<GLOBAL HAVE-GEM <>>

<ROUTINE GO ()
    <PUTB ,READBUF 0 45>
    <PUTB ,LEXBUF 0 10>
    <TELL "MICROQUEST" CR "A zorkie/zwalker integration demo." CR CR>
    <TELL "You stand before a sealed vault. A word is etched above it: FROTZ." CR>
    <MAIN-LOOP>>

<ROUTINE MAIN-LOOP ("AUX" V)
    <REPEAT ()
        <TELL "> ">
        <READ ,READBUF ,LEXBUF>
        <SET V <GET ,LEXBUF 1>>
        <COND (<EQUAL? .V ,W?FROTZ>
               <COND (,VAULT-OPEN
                      <TELL "The vault is already open." CR>)
                     (T
                      <SETG VAULT-OPEN T>
                      <TELL "The vault swings open, revealing a glowing gem." CR>)>)
              (<EQUAL? .V ,W?TAKE>
               <COND (<NOT ,VAULT-OPEN>
                      <TELL "There is nothing here to take." CR>)
                     (,HAVE-GEM
                      <TELL "You already have the gem." CR>)
                     (T
                      <SETG HAVE-GEM T>
                      <SETG SCORE 10>
                      <TELL "You take the gem. [Your score is now 10.]" CR>)>)
              (<EQUAL? .V ,W?LOOK>
               <COND (,VAULT-OPEN <TELL "The open vault glitters." CR>)
                     (T <TELL "A sealed vault blocks the way." CR>)>)
              (<EQUAL? .V ,W?WIN>
               <COND (,HAVE-GEM
                      <TELL "You raise the gem and step into the light." CR CR>
                      <TELL "*** You have won ***" CR>
                      <QUIT>)
                     (T
                      <TELL "You have nothing worth leaving with." CR>)>)
              (T
               <TELL "Nothing happens." CR>)>>>

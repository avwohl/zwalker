"MAZEKEY -- zorkie<->zwalker integration test game #2.
 Exercises room movement (a HERE state machine), an inventory flag, a locked
 door, and multi-value <EQUAL? ...> verb dispatch. Manual READ loop (no library
 parser), so it uses only ZIL zorkie compiles today. Win: reach the vault."

<VERSION 3>

<GLOBAL READBUF <ITABLE 50 (BYTE)>>
<GLOBAL LEXBUF <ITABLE 20 (BYTE)>>
<GLOBAL HERE 1>          ;"1=Hall  2=Closet  3=Vault"
<GLOBAL HAVE-KEY <>>
<GLOBAL DOOR-OPEN <>>

<ROUTINE DESCRIBE ()
    <COND (<EQUAL? ,HERE 1>
           <TELL "Hall. Exits: north to a closet, east through an iron door." CR>)
          (<EQUAL? ,HERE 2>
           <TELL "Closet. A brass key lies on the floor. Exit: south." CR>)
          (T <TELL "Vault." CR>)>>

<ROUTINE GO ()
    <PUTB ,READBUF 0 45>
    <PUTB ,LEXBUF 0 10>
    <TELL "MAZEKEY" CR CR>
    <DESCRIBE>
    <MAIN-LOOP>>

<ROUTINE MAIN-LOOP ("AUX" V)
    <REPEAT ()
        <TELL "> ">
        <READ ,READBUF ,LEXBUF>
        <SET V <GET ,LEXBUF 1>>
        <COND (<EQUAL? .V ,W?NORTH>
               <COND (<EQUAL? ,HERE 1> <SETG HERE 2> <DESCRIBE>)
                     (T <TELL "You can't go that way." CR>)>)
              (<EQUAL? .V ,W?SOUTH>
               <COND (<EQUAL? ,HERE 2> <SETG HERE 1> <DESCRIBE>)
                     (T <TELL "You can't go that way." CR>)>)
              (<EQUAL? .V ,W?TAKE>
               <COND (<EQUAL? ,HERE 2>
                      <SETG HAVE-KEY T>
                      <TELL "You take the brass key." CR>)
                     (T <TELL "There is nothing here to take." CR>)>)
              (<EQUAL? .V ,W?UNLOCK ,W?OPEN>
               <COND (<EQUAL? ,HERE 1>
                      <COND (,HAVE-KEY
                             <SETG DOOR-OPEN T>
                             <TELL "The iron door unlocks with a heavy clunk." CR>)
                            (T <TELL "You have no key." CR>)>)
                     (T <TELL "That doesn't work." CR>)>)
              (<EQUAL? .V ,W?EAST>
               <COND (<EQUAL? ,HERE 1>
                      <COND (,DOOR-OPEN
                             <TELL "You step through into the vault." CR CR>
                             <TELL "*** You have won ***" CR>
                             <QUIT>)
                            (T <TELL "The iron door is locked." CR>)>)
                     (T <TELL "You can't go that way." CR>)>)
              (T <TELL "Nothing happens." CR>)>>>

"REACTOR -- zorkie<->zwalker integration test #3.
 Exercises arithmetic (<-> <+>) and comparison branches (<G?> JG, <L?> JL) plus
 a global counter and PRINTN. Manual READ loop. Win: lower the core to 0, VENT."

<VERSION 3>

<GLOBAL READBUF <ITABLE 50 (BYTE)>>
<GLOBAL LEXBUF <ITABLE 20 (BYTE)>>
<GLOBAL LEVEL 5>

<ROUTINE GO ()
    <PUTB ,READBUF 0 45>
    <PUTB ,LEXBUF 0 10>
    <TELL "REACTOR" CR CR "The core level reads 5. Lower it to 0, then VENT." CR>
    <MAIN-LOOP>>

<ROUTINE MAIN-LOOP ("AUX" V)
    <REPEAT ()
        <TELL "> ">
        <READ ,READBUF ,LEXBUF>
        <SET V <GET ,LEXBUF 1>>
        <COND (<EQUAL? .V ,W?LOWER>
               <COND (<G? ,LEVEL 0>
                      <SETG LEVEL <- ,LEVEL 1>>
                      <TELL "Core level: " N ,LEVEL CR>)
                     (T <TELL "The core is already at minimum." CR>)>)
              (<EQUAL? .V ,W?RAISE>
               <SETG LEVEL <+ ,LEVEL 1>>
               <TELL "Core level: " N ,LEVEL CR>)
              (<EQUAL? .V ,W?VENT>
               <COND (<L? ,LEVEL 1>
                      <TELL "The core vents safely with a hiss." CR CR>
                      <TELL "*** You have won ***" CR>
                      <QUIT>)
                     (T <TELL "Unsafe -- lower the core to 0 first." CR>)>)
              (T <TELL "Nothing happens." CR>)>>>


                        send data tool version 1.20

                                                                   2014/04/10
                                                             SEIKO EPSON Corp.

1. GENERAL
----------
  A tool sending data to printer. Printer accept binary data. But binary data
  is not user frinedly. This utility intend to be familiar with controling
  command of printer.


2. HOW TO USE
-------------
  This utility transfer data which is written in a sript file to the target.
  >senddat <script file> <target device>

3. SYNTAX OF SCRIPT
-------------------
  Starting character
    Follow symbols at the beginning of line has special meaning.
    ' : Comment line
    ! : Output to disply
    . : Pause at this line
    * : Wait specified mili seconds  example) *1000

  DECIMAL VALUE
    You can specify decimal value as number.
    1 2 10 100 255 ...

  HEXADECIMAL VALUE
    Hexadecimal number can be expressed with prefix or postfix characters.
    1) $ prefix     $30 $31 ...
    2) h post fix   30h 31h ...
    3) 0x prefix    0x30 0x32 0x33 ...

  CODE
    Most of code are defined as keyword.
          HEX   DEC
    NUL   00h     0
    SOH   01h     1
    STX   02h     2
    ETX   03h     3
    EOT   04h     4
    ENQ   05h     5
    ACK   06h     6
    BEL   07h     7
    BS    08h     8
    HT    09h     9
    LF    0Ah    10
    HOM   0Bh    11
    CLR   0Ch    12
    CR    0Dh    13
    SO    0Eh    14
    SI    0Fh    15
    DLE   10h    16
    DC1   11h    17
    DC2   12h    18
    DC3   13h    19
    DC4   14h    20
    NAK   15h    21
    SYN   16h    22
    ETB   17h    23
    CAN   18h    24
    EM    19h    25
    SUB   1Ah    26
    ESC   1Bh    27
    FS    1Ch    28
    GS    1Dh    29
    RS    1Eh    30
    US    1Fh    31
    SP    20h    32

  CHARACTER
    Another character is treat as output character.

  STRING
    Double quoated characters are treat as stirng.

  ESCAPE CHARACTERS
    Follow escape character can be used to express special character.
          HEX     DEC
    \\    5Ch     92
    \'    27h     39
    \"    22h     34
    \0    00h     0
    \r    0Dh     13
    \n    0Ah     10
    \xXX  XXh     XX


4.HISTORY
---------
  2014/04/10 version 1.20
    + Add -w option  Terminate application after specified seconds.

  2013/02/15 version 1.00
    + Official release version

[EOF]

***************************
* BUFFERING
***************************
* differential buffer
*            A Q QN
*            | | |
.SUBCKT BUFD 1 2 3
A1 1 0 0 0 0 3 2 0 BUF
.ENDS BUFD

* single output buffer
*            A Q
*            | |
.SUBCKT BUFS 1 2
A1 1 0 0 0 0 0 2 0 BUF
.ENDS BUFS

* inverter
*           A Q
*           | |
.SUBCKT NOT 1 2
A1 1 0 0 0 0 2 0 0 BUF
.ENDS NOT

***************************
* NANDS
***************************
* nand2
*             A B Q
*             | | |
.SUBCKT NAND2 1 2 3
A1 1 2 0 0 0 3 0 0 AND
.ENDS NAND2

* nand3
*             A B C Q
*             | | | |
.SUBCKT NAND3 1 2 3 4
A1 1 2 3 0 0 4 0 0 AND
.ENDS NAND3

* and2
*            A B Q
*            | | |
.SUBCKT AND2 1 2 3
A1 1 2 0 0 0 0 3 0 AND
.ENDS AND2

* and3
*            A B C Q
*            | | | |
.SUBCKT AND3 1 2 3 4
A1 1 2 3 0 0 0 4 0 AND
.ENDS AND3

***************************
* NORS
***************************
* nor2
*            A B Q
*            | | |
.SUBCKT NOR2 1 2 3
A1 1 2 0 0 0 3 0 0 OR
.ENDS NOR2

* nor3
*            A B C Q
*            | | | |
.SUBCKT NOR3 1 2 3 4
A1 1 2 3 0 0 4 0 0 OR
.ENDS NOR3

* or2
*           A B Q
*           | | |
.SUBCKT OR2 1 2 3
A1 1 2 0 0 0 0 3 0 OR
.ENDS OR2

* or3
*           A B C Q
*           | | | |
.SUBCKT OR3 1 2 3 4
A1 1 2 3 0 0 0 4 0 OR
.ENDS OR3

***************************
* XORS
***************************
* xor
*            A B Q
*            | | |
.SUBCKT XOR2 A B Q
A1 1 2 0 0 0 0 3 0 XOR
.ENDS XOR2

* xnor
*             A B Q
*             | | |
.SUBCKT XNOR2 1 2 3
A1 1 2 0 0 0 3 0 0 XOR
.ENDS XNOR2

***************************
* LATCHES
***************************
* SR-latch
*               S R Q QN
*               | | | |
.SUBCKT SRLATCH 1 2 3 4
A1 1 2 0 0 0 4 3 0 SRFLOP Td=1ps
.ENDS SRLATCH

* D-latch
*              D G Q
*              | | |
.SUBCKT DLATCH 1 2 3
X1 1 4 NOT
X2 1 2 5 AND2
X3 4 2 6 AND2
A1 5 6 0 0 0 0 3 0 SRFLOP Td=1ps
.ENDS DLATCH

***************************
* FLOPS
***************************
* DFF rising edge
*           D C Q
*           | | |
.SUBCKT DFF 1 2 3
A1 1 0 2 0 0 0 3 0 DFLOP Td=1ps
.ENDS DFF

* DFF rising edge with neg output
*            D C Q QN
*            | | | |
.SUBCKT DFFQ 1 2 3 4
A1 1 0 2 0 0 4 3 0 DFLOP Td=1ps
.ENDS DFFQ

* DFFRQ rising edge with reset and neg output
*             D C R Q QN
*             | | | | |
.SUBCKT DFFRQ 1 2 3 4 5
A1 1 0 2 4 0 5 4 0 DFLOP Td=1ps
.ENDS DFFRQ

* DFFSQ rising edge with set and neg output
*             D C S Q QN
*             | | | | |
.SUBCKT DFFSQ 1 2 3 4 5
A1 1 0 2 0 3 5 4 0 DFLOP Td=1ps
.ENDS DFFSQ

* DFFSRQ rising edge with set/reset and neg output
*              D C R S Q QN
*              | | | | | |
.SUBCKT DFFSRQ 1 2 3 4 5 6
A1 1 0 2 3 4 6 5 0 DFLOP Td=1ps
.ENDS DFFSRQ

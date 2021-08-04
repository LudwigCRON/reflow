`timescale 1ns/100ps

`ifndef LTSPICE_DCELLS
`define LTSPICE_DCELLS

module BUFD (
    input  wire A,
    output wire Q,
    output wire QN
);
    buf g1(Q, A);
    not g2(QN, A); 
endmodule

module BUFS (
    input  wire A,
    output wire Q
);
    buf g1(Q, A);
endmodule

module NOT (
    input  wire A,
    output wire Q
);
    not g1(Q, A);
endmodule

module NAND2 (
    input  wire A,
    input  wire B,
    output wire Q
);
    nand g1(Q, A, B);
endmodule

module NAND3 (
    input  wire A,
    input  wire B,
    input  wire C,
    output wire Q
);
    nand g1(Q, A, B, C);
endmodule

module AND2 (
    input  wire A,
    input  wire B,
    output wire Q
);
    and g1(Q, A, B);
endmodule

module AND3 (
    input  wire A,
    input  wire B,
    input  wire C,
    output wire Q
);
    and g1(Q, A, B, C);
endmodule

module NOR2 (
    input  wire A,
    input  wire B,
    output wire Q
);
    nor g1(Q, A, B);
endmodule

module NOR3 (
    input  wire A,
    input  wire B,
    input  wire C,
    output wire Q
);
    nor g1(Q, A, B, C);
endmodule

module OR2 (
    input  wire A,
    input  wire B,
    output wire Q
);
    or g1(Q, A, B);
endmodule

module OR3 (
    input  wire A,
    input  wire B,
    input  wire C,
    output wire Q
);
    or g1(Q, A, B, C);
endmodule

module XOR2 (
    input  wire A,
    input  wire B,
    output wire Q
);
    xor g1(Q, A, B);
endmodule

module XNOR2 (
    input  wire A,
    input  wire B,
    output wire Q
);
    xnor g1(Q, A, B);
endmodule

module SRLATCH (
    input  wire S,
    input  wire R,
    output reg  Q,
    output reg  QN
);
    always @(S or R)
    begin
        case ({S, R})
            2'b01: begin Q = 1'b0; QN = 1'b1; end
            2'b10: begin Q = 1'b1; QN = 1'b0; end
            2'b11: begin Q = 1'bX; QN = 1'bX; end
        endcase
    end
endmodule

module DLATCH (
    input  wire D,
    input  wire G,
    output reg  Q
);
    always @(D or G)
    begin
        if (G) Q = D;
    end
endmodule

module DFF (
    input  wire D,
    input  wire C,
    output reg  Q
);
    always @(posedge C)
        Q <= D;
endmodule

module DFFQ (
    input  wire D,
    input  wire C,
    output reg  Q,
    output wire QN
);
    always @(posedge C)
        Q <= D;
    
    not g1(QN, Q);
endmodule

module DFFRQ (
    input  wire D,
    input  wire C,
    input  wire R,
    output reg  Q,
    output reg  QN
);
    always @(posedge C or posedge R)
        Q <= (R) ? 1'b0 : D;
    
    not g1(QN, Q);
endmodule

module DFFSQ (
    input  wire D,
    input  wire C,
    input  wire S,
    output reg  Q,
    output reg  QN
);
    always @(posedge C or posedge S)
        Q <= (S) ? 1'b1 : D;
    
    not g1(QN, Q);
endmodule

module DFFSRQ (
    input  wire D,
    input  wire C,
    input  wire S,
    input  wire R,
    output reg  Q,
    output reg  QN
);
    always @(posedge C or posedge R or posedge S)
        Q <= (S) ? 1'b1 : (R) ? 1'b0 : D;
    
    not g1(QN, Q);
endmodule

`endif

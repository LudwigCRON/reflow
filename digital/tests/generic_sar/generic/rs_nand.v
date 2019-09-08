`timescale 1ns/10ps

`ifndef RS_NAND_LATCH
`define RS_NAND_LATCH

module rs_nand (
  input  A,
  input  B,
  output O,
  output Ob
);

// replace with a nand2_generic
assign O  = ~(A & Ob);
assign Ob = ~(B & O);

// nand2_generic G1 (.O(O) , .A(A), .B(Ob));
// nand2_generic G2 (.O(Ob), .A(B), .B(O));

endmodule

`endif
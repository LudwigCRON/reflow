`timescale 1ns/10ps

`ifndef RS_NOR_LATCH
`define RS_NOR_LATCH

module rs_nor (
  input  A,
  input  B,
  output O,
  output Ob
);

// replace with a nor2_generic
assign O  = ~(A | Ob);
assign Ob = ~(B | O);

// nor2_generic G1 (.O(O) , .A(A), .B(Ob));
// nor2_generic G2 (.O(Ob), .A(B), .B(O));

endmodule

`endif
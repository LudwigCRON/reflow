`timescale 1ns/10ps

`ifndef TOGGLE_RESYNC
`define TOGGLE_RESYNC

module toggle_resync_out (
  input       rstb,
  input       clk,
  input       a,
  output reg  o
);

always @(posedge clk or negedge rstb)
begin
  if(!rstb)
    o <= 1'b0;
  else
    o <= (a) ? ~o : o;
end

endmodule

module toggle_resync_in #(
  parameter DEPTH = 2
) (
  input  rstb,
  input  clk,
  input  a,
  output o
);

reg [DEPTH-1:0] sync;

always @(posedge clk or negedge rstb)
begin
  if(!rstb)
    sync <= 2'b0;
  else
    sync <= {sync[DEPTH-2:0], a};
end

assign o = sync[DEPTH-1] ^ sync[DEPTH-2];

endmodule

`endif
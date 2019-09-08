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

module toggle_resync_in (
  input  rstb,
  input  clk,
  input  a,
  output o
);

reg [2:0] sync;

always @(posedge clk or negedge rstb)
begin
  if(!rstb)
    sync <= 2'b0;
  else
    sync <= {sync[1:0], a};
end

assign o = ^sync[2:1];

endmodule

`endif
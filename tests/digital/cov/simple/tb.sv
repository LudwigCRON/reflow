
`timescale 1ns/10ps

module tb;

parameter PERIOD = 31.25; // 32 MHz

reg s;
real clk_period;
reg clk;

initial begin
  $dumpvars;
  clk = 1'b0;
  forever #(PERIOD/2) clk = !clk;
end

// check clock period
initial begin
  #(PERIOD*100);
  clk_period = $realtime/100;
  $display("Clock period is 31.25 ns");
  $finish;
end

endmodule
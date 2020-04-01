// old verilog 95 version
module test_1 (
  clk,
  rstb,
  atpg,
  i,
  a,
  b,
  c, 
  o,
  q
);

parameter DATA_WIDTH = 32;
parameter YOUPI = 1;

input clk;
input [1:0] rstb; // check how it handle discrepancy
input atpg, i, a;
input c;
output [1:0] b, o;
output [DATA_WIDTH-1:1] q; // check how it handle parametric size

wire clk;
wire [2:0] rstb;
wire atpg, a;

reg i;
reg [1:0] b, o;
reg [DATA_WIDTH-1:1] q;

endmodule


// verilog 2k+
module test_2 #(
  parameter DATA_WIDTH = 32,
  parameter YOUPI = 1
) (
  input                         clk, // check default value is wire
  input       [1:0]             rstb,
  input                         atpg,
  input  reg                    i, // strange behaviour expected meaningless in practical design
  input                         a,
  input  wire                   c,
  output reg  [1:0]             b, 
  output reg                    o,
  output reg  [DATA_WIDTH-1:1]  q
);

endmodule

// mixed verilog but 2k+ valid
module test_3 (
  input                         clk, // check default value is wire
  input       [1:0]             rstb,
  input                         atpg,
  input  reg                    i, // strange behaviour expected meaningless in practical design
  input                         a,
  input  wire                   c,
  output reg  [1:0]             b, 
  output reg                    o,
  output reg  [DATA_WIDTH-1:1]  q
);

  parameter DATA_WIDTH = 32;
  parameter YOUPI = 1;

endmodule

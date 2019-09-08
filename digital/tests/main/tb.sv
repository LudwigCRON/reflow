
`timescale 1ns/10ps

module tb;

reg rstb;
reg start;
wire clk;

initial begin
	rstb = 1'b0;
	start = 1'b0;
end

clk_gen #(
	.LENGTH(7)
) osc (
	rstb,
	delay,
	start,
	clk
);

endmodule

`timescale 1ns/10ps

module clk_gen #(
	parameter LENGTH = 8
)

(
	input wire							rstb,
	input wire	[$clog2(LENGTH)-1:0]	delay,
	input wire							start,
	output wire							clk
);

wire [LENGTH-1:0] int_osc;

genvar i;

generate
	for(i = 1; i < LENGTH; i = i + 1)
	begin: delay_cells
		not #(1, 0.8) Ui(int_osc[i],int_osc[i-1]);
	end
endgenerate

nand #(1, 0.8) (int_osc[0], start, int_osc[LENGTH-1]);

buf (clk, int_osc[delay]);

endmodule
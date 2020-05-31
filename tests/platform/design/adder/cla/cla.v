// Carry LookAhead Adder
`timescale 1ns/100ps

module cla #(
    parameter WIDTH = 8
) (
    input  wire [WIDTH*4-1:0] a,
    input  wire [WIDTH*4-1:0] b,
    output wire [WIDTH*4-1:0] s,
    output wire               c
);

wire [WIDTH-1:0] p;
wire [WIDTH-1:0] g;
wire [WIDTH:0]   ci;

assign ci[0] = 1'b0;

generate
    genvar gi;

    for(gi = 0; gi < WIDTH; gi = gi + 1)
    begin: adder
        cla_4 fa4 (
            .a(a[4*gi +: 4]),
            .b(b[4*gi +: 4]),
            .ci(ci[gi]),
            .s(s[4*gi +: 4]),
            .pg(p[gi]),
            .gg(g[gi]),
            .cg(ci[gi+1])
        );
    end
endgenerate

assign c = ci[WIDTH];


endmodule
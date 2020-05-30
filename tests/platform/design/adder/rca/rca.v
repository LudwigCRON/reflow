// Ripple-Carry-Adder
// traditionnal one
module rca #(
    parameter WIDTH = 32
) (
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    output wire [WIDTH-1:0] s,
    output wire             c
);

wire [WIDTH-1:0] carries;

generate
    genvar gi;

    for(gi = 0; gi < WIDTH; gi = gi + 1)
    begin: adder
        if (gi == 0)
            half_adder ha_0 (
                .a(a[gi]),
                .b(b[gi]),
                .s(s[gi]),
                .c(carries[0])
            );
        else
            full_adder fa (
                .a(a[gi]),
                .b(b[gi]),
                .ci(carries[gi-1]),
                .s(s[gi]),
                .co(carries[gi])
            );
    end
endgenerate

assign c = carries[WIDTH-1];


endmodule
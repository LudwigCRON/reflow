`timescale 1ns/100ps

module half_adder (
    input   wire a,
    input   wire b,
    output  wire s,
    output  wire c
);

    xor sum   (s, a, b);
    and carry (c, a, b);

    specify
        (a => s) = (1, 1.2);
        (b => s) = (1, 1.2);
        (a => c) = (0.7, 0.8);
        (b => c) = (0.7, 0.8);
    endspecify

endmodule

module full_adder (
    input   wire a,
    input   wire b,
    input   wire ci,
    output  wire s,
    output  wire co
);

    wire partial_carries_0;
    wire partial_carries_1;
    wire partial_carries_2;

    wire partial_sum;

    xor sum_0    (partial_sum, a, b);
    xor sum_1    (s, partial_sum, ci);
    nand carry_0 (partial_carries_0, a, b);
    nand carry_1 (partial_carries_1, a, ci);
    nand carry_2 (partial_carries_2, b, ci);
    nand carry_3 (co, partial_carries_0, partial_carries_1, partial_carries_2);

    specify
        (a => s) = (2, 2.4);
        (b => s) = (2, 2.4);
        (ci => s) = (1, 1.2);
        (a => co) = (1.4, 1.6);
        (b => co) = (1.4, 1.6);
        (ci => co) = (1.4, 1.6);
    endspecify

endmodule

module full_adder_cla (
    input   wire a,
    input   wire b,
    input   wire ci,
    output  wire s,
    output  wire p,
    output  wire g
);

    wire partial_sum;

    xor sum_0 (partial_sum, a, b);
    xor sum_1 (s, partial_sum, ci);
    or  pro_c (p, a, b);
    and gen_c (g, a, b);

    specify
        (a => s) = (2, 2.4);
        (b => s) = (2, 2.4);
        (ci => s) = (1, 1.2);
        (a => p) = (0.6, 0.7);
        (b => p) = (0.6, 0.7);
        (a => g) = (0.7, 0.8);
        (b => g) = (0.7, 0.8);
    endspecify

endmodule
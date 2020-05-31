// Carry LookAhead Adder
`timescale 1ns/100ps

module cla_4 (
    input  wire [3:0] a,
    input  wire [3:0] b,
    input  wire       ci,
    output wire [3:0] s,
    output wire       pg,
    output wire       gg,
    output wire       cg
);

wire [3:0] pi;
wire [3:0] gi;
wire [4:0] c;
wire [3:0] pp;
wire [5:0] gp;
wire [1:0] cit;
wire       ggt;

assign c[0] = ci;

full_adder_cla fa[3:0] (
    .a(a),
    .b(b),
    .ci(c[3:0]),
    .s(s),
    .p(pi),
    .g(gi)
);

// maximum and3
and #(700ps) pp_3 (pp[3], pi[3], pi[2], pp[0]);
and #(700ps) pp_2 (pp[2], pi[2], pi[1], pp[0]);
and #(700ps) pp_1 (pp[1], pi[1], pi[0], c[0]);
and #(700ps) pp_0 (pp[0], pi[0], c[0]);

and #(700ps) gp_2 (gp[2], gp[1], pi[2], pi[3]);
and #(700ps) gp_1 (gp[1], gi[0], pi[1], pi[2]);
and #(700ps) gp_0 (gp[0], gi[0], pi[1]);

and #(700ps) gp_5 (gp[5], gi[2], pi[3]);
and #(700ps) gp_4 (gp[4], gi[1], pi[2], pi[3]);
and #(700ps) gp_3 (gp[3], gi[1], pi[2]);

or #(600ps) cio_1  (c[1], gi[0], pp[0]);
or #(600ps) cio_2  (c[2], gi[1], gp[0], pp[1]);
or #(600ps) cio_3  (cit[0], gi[2], gp[1], pp[2]);
or #(600ps) cio_3b (c[3], cit[0], gp[3]);
or #(600ps) cio_4  (cit[1], gi[3], gp[2], pp[3]);
or #(600ps) cio_4b (c[4], cit[1], gp[4], gp[5]);

and #(800ps) pg_a (pg, pi[3], pi[2], pi[1], pi[0]);
or #(600ps) gg_o1 (ggt, gi[3], gp[5], gp[4]);
or #(600ps) gg_o2 (gg, ggt, gp[2]);

assign #(800ps) cg = gg | (pg & ci);

specify
    (ci => cg)  = (1.0, 1.2);
endspecify

endmodule
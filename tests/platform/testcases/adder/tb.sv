`timescale 1ns/100ps

module tb;

parameter TCLK = 32;
parameter WIDTH = 32;

reg  [WIDTH-1:0] a;
reg  [WIDTH-1:0] b;
wire [WIDTH-1:0] s_ref;
wire [WIDTH-1:0] s_rca;
wire [WIDTH-1:0] s_cla;

reg run_check;

//======== Stimuli ========
initial
begin: test
    $dumpvars(0, tb);


    for(int i = 0; i < 512; i = i + 1)
    begin
        run_check = 1'b0;
        a = $urandom();//_range(0, 2**32);
        b = $urandom();//_range(0, 2**32);
        #((TCLK-1) * 1ns);
        run_check = 1'b1;
        #(1ns);
    end
    `log_Terminate;
end

//======== DUTS ========
// traditional one
rca #(
    .WIDTH(WIDTH)
) rca (
    .a(a),
    .b(b),
    .s(s_rca),
    .c()
);

cla #(
    .WIDTH(WIDTH/4)
) cla (
    .a(a),
    .b(b),
    .s(s_cla),
    .c()
);

//======== Checker ========
assign s_ref = a + b;

always @(posedge run_check)
begin: sum_check
    if (s_rca != s_ref) `log_Error("Wrong ripple-carry-adder sum result");
    if (s_cla != s_ref) `log_Error("Wrong carry-lookahead-adder sum result");
end


endmodule
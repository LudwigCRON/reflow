
`timescale 1ns/10ps

`ifndef SAR_ANALOG
`define SAR_ANALOG

module sar_analog #(
    parameter NSTEP = 2
) (
    input  real         vinp,
    input  real         vinm,
    input  real         vrefm,
    input  real         vrefp,
    input  real         vcm,
    // to the analogue part
    input               ms_sar_clock,
    input               ms_sar_sample,
    input  [NSTEP-1:0]  ms_sar_sw,
    input  [NSTEP-1:0]  ms_sar_swb,
    // from the analogue part
    output reg          ms_sar_dh,
    output reg          ms_sar_dl,
    output              ms_sar_rdy
);

real vcmp_p;
real vcmp_m;

real Qsp;
real Qsm;

real Ctot;

real C_ARRAY[NSTEP-1:0];

integer i;

initial begin
    Ctot = 0;
    for(i = 0; i < NSTEP; i = i + 1) begin
        C_ARRAY[i] = 2**i;
        Ctot = Ctot + C_ARRAY[i];
        $display("Ctot = %d", C_ARRAY[i]);
    end
end

always @(posedge ms_sar_clock)
begin
    // sampling mode
    if(ms_sar_sample)
    begin
        vcmp_p <= vcm;
        vcmp_m <= vcm;
        Qsp    <= (vinp - vcm) * Ctot;
        Qsm    <= (vinm - vcm) * Ctot; 
    end else
    begin
        vcmp_p = -Qsp;
        vcmp_m = -Qsm;
        for(i = 0; i < NSTEP; i = i + 1) begin
            // positive side
            if      ( ms_sar_sw[i] & ~ms_sar_swb[i]) vcmp_p = vcmp_p + vrefp * C_ARRAY[i];
            else if (~ms_sar_sw[i] &  ms_sar_swb[i]) vcmp_p = vcmp_p + vrefm * C_ARRAY[i];
            else if ( ms_sar_sw[i] &  ms_sar_swb[i]) $display("ERROR: short circuit at %0t", $time);
            // negative side
            if      ( ms_sar_sw[i] & ~ms_sar_swb[i]) vcmp_m = vcmp_m + vrefm * C_ARRAY[i];
            else if (~ms_sar_sw[i] &  ms_sar_swb[i]) vcmp_m = vcmp_m + vrefp * C_ARRAY[i];
            else if ( ms_sar_sw[i] &  ms_sar_swb[i]) $display("ERROR: short circuit at %0t", $time);
        end
        vcmp_p = vcmp_p / Ctot;
        vcmp_m = vcmp_m / Ctot;
    end
end


always @(ms_sar_clock)
begin
    if(ms_sar_clock === 1'b1)
    begin
        #1.5;
        if (vcmp_p > vcmp_m)
        begin
            ms_sar_dh <= 1'b1;
            ms_sar_dl <= 1'b0;
        end else
        begin
            ms_sar_dh <= 1'b0;
            ms_sar_dl <= 1'b1;
        end
    end else
    begin
        #1.1;
        ms_sar_dh <= 1'b0;
        ms_sar_dl <= 1'b0;
    end
end

assign #50 ms_sar_rdy = 1'b1;

endmodule

`endif
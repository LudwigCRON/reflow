`timescale 1ns/10ps

module tb;

reg         f100m_clk;
reg         rstb;

wire        sar_soc;
wire        sar_eoc;
wire        sar_err;
wire        sar_warn;
wire [9:0]  sar_code;

wire        ms_sar_rdy;
wire        ms_sar_dh;
wire        ms_sar_dl;
wire        ms_sar_clock;
wire        ms_sar_sample;
wire [9:0]  ms_sar_sw;
wire [9:0]  ms_sar_swb;

// dump all
initial begin
    $dumpvars;
end

// clock generation
initial begin
    f100m_clk = 1'b0;
    forever #5 f100m_clk = !f100m_clk;
end

// reset generation
initial begin
    $info("Simulation initiated");
    rstb = 1'b0;
    #50 rstb = 1'b1;
    $warning("reset released");
end

always @(posedge f100m_clk) begin
    if(vin > 1.005) begin
        rstb <= 1'b0;
        #50;
        $finish;
    end
end

real vinp;
real vinm;
real vcm   = 0.9;
real vrefp = 1.4;
real vrefm = 0.4;
real vin   = -1.0;

real rec;
assign rec = 1024*(vinp-vinm)/(vrefp-vrefm);

// triangle wave
always @(negedge f100m_clk)
begin
    if(~soc & eoc) begin
        vin = vin + 0.001;
    end
    vinp <= vcm + vin/2;
    vinm <= vcm - vin/2;
end

// resync eoc/soc/err/warn
reg  soc;
wire eoc;
wire err;
wire warn;

toggle_resync_in trsync_0(
  .rstb (rstb),
  .clk  (f100m_clk),
  .a    (sar_eoc),
  .o    (eoc)
);
toggle_resync_in trsync_1(
  .rstb (rstb),
  .clk  (f100m_clk),
  .a    (sar_err),
  .o    (err)
);
toggle_resync_in trsync_2(
  .rstb (rstb),
  .clk  (f100m_clk),
  .a    (sar_warn),
  .o    (warn)
);
toggle_resync_out trsync_3(
  .rstb (rstb),
  .clk  (f100m_clk),
  .a    (soc),
  .o    (sar_soc)
);

always @(posedge f100m_clk or negedge rstb)
begin
    if(!rstb)
        soc <= 1'b0;
    else
        soc <= eoc;
end

// DUT
sar #(.NSTEP(10), .STEP_SIZE(4)) adc00 (
    // global signal
    .rstb           (rstb),
    .atpg           (1'b0),
    .f100m_clk      (f100m_clk),
    // adc_interface
    .sar_soc        (sar_soc),
    .sar_eoc        (sar_eoc),
    .sar_err        (sar_err),
    .sar_warn       (sar_warn),
    .sar_code       (sar_code),
    // from the analogue part
    .ms_sar_dh      (ms_sar_dh),
    .ms_sar_dl      (ms_sar_dl),
    .ms_sar_rdy     (ms_sar_rdy),
    // to the analogue part
    .ms_sar_clock   (ms_sar_clock),
    .ms_sar_sample  (ms_sar_sample),
    .ms_sar_sw      (ms_sar_sw),
    .ms_sar_swb     (ms_sar_swb)
);

sar_analog #(
    .NSTEP(10)
) adc00_analogue (
    .vinp               (vinp),
    .vinm               (vinm),
    .vrefm              (vrefm),
    .vrefp              (vrefp),
    .vcm                (vcm),
    // to the analogue part
    .ms_sar_clock       (ms_sar_clock),
    .ms_sar_sample      (ms_sar_sample),
    .ms_sar_sw          (ms_sar_sw),
    .ms_sar_swb         (ms_sar_swb),
    // from the analogue part
    .ms_sar_dh          (ms_sar_dh),
    .ms_sar_dl          (ms_sar_dl),
    .ms_sar_rdy         (ms_sar_rdy)
);

endmodule
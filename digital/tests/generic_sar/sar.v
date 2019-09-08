`timescale 1ns/10ps

`ifndef GENERIC_SAR_ADC
`define GENERIC_SAR_ADC

module sar #(
    parameter NSTEP = 10,
    parameter STEP_SIZE = 4
) (
    // global signal
    input                  rstb,
    input                  atpg,
    input                  f100m_clk,
    // adc_interface
    input                  sar_soc,
    output                 sar_eoc,
    output                 sar_err,
    output                 sar_warn,
    output reg [NSTEP-1:0] sar_code,
    // from the analogue part
    input                  ms_sar_dh,
    input                  ms_sar_dl,
    input                  ms_sar_rdy,
    // to the analogue part
    output                 ms_sar_clock,
    output reg             ms_sar_sample,
    output reg [NSTEP-1:0] ms_sar_sw,
    output     [NSTEP-1:0] ms_sar_swb
);

// toggle resync of SOC
wire soc;
toggle_resync_in trsync_0(
  .rstb (rstb),
  .clk  (f100m_clk),
  .a    (sar_soc),
  .o    (soc)
);
// toggle resync of EOC
wire eoc;
toggle_resync_out trsync_1(
  .rstb (rstb),
  .clk  (f100m_clk),
  .a    (eoc),
  .o    (sar_eoc)
);
// toggle resync of ERR
wire err;
toggle_resync_out trsync_2(
  .rstb (rstb),
  .clk  (f100m_clk),
  .a    (err),
  .o    (sar_err)
);
// toggle resync of WARN
wire warn;
toggle_resync_out trsync_3(
  .rstb (rstb),
  .clk  (f100m_clk),
  .a    (warn),
  .o    (sar_warn)
);

// conversion progress
reg  [STEP_SIZE-1:0] counter;
wire [STEP_SIZE-1:0] next_counter;
wire                 can_decrement;
wire                 comp;
reg                  finishing;

assign next_counter  = counter - 1'b1;
assign can_decrement = |counter;

// comparator format
rs_nand rs_1 (.O(comp), .A(~ms_sar_dh), .B(~ms_sar_dl));

// logic
always @(posedge f100m_clk or negedge rstb)
begin
    if(!rstb) 
    begin
        ms_sar_sample <= 1'b1;
        ms_sar_sw     <= {NSTEP {1'b0}};
        counter       <= {STEP_SIZE{1'b0}};
        finishing     <= 1'b0;
    end else
    begin
        // counter management
        if(can_decrement)          counter <= next_counter;
        else if(soc && ms_sar_rdy) counter <= NSTEP;
        else                       counter <= {STEP_SIZE{1'b0}};
        finishing <= ~(|next_counter);
        // analogue management with sample while waiting
        ms_sar_sample           <= ~can_decrement;
        ms_sar_sw[next_counter] <= 1'b0;
        if(can_decrement)
            ms_sar_sw[counter] <= ~comp;
        else
            ms_sar_sw <= {1'b0, {NSTEP-1 {1'b1}}};
    end
end

assign ms_sar_clock = ~f100m_clk;
assign ms_sar_swb   = ~ms_sar_sw;

// flags
assign eoc = ~can_decrement | ~rstb;

// err when stuck of dh/dl
assign err = ms_sar_dh & ms_sar_dl;

// warn overflow of code
assign warn = can_decrement & (&next_counter);

`ifdef FOR_SIMULATION
// check NSTEP < 2**STEP_SIZE

`endif

// reconstruction
always @(posedge f100m_clk or negedge rstb)
begin
    if(!rstb) 
    begin
        sar_code <= {NSTEP {1'b0}};
    end else
    begin
        if(finishing) sar_code <= {ms_sar_sw[NSTEP-1:1], ~comp};
    end
end

endmodule

`endif
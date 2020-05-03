module basic_wrapper (
    input  wire      mcu_clk,
    input  wire      mcu_warm_rstb,

    input  wire      mclk,
    input  wire      ctspl,
    input  wire      soc,
    input  wire      enable,
    input  wire      low_power,
    input  wire      test_a,
    input  wire      test_b,
    input  wire      test_c,

    output wire      eoc,
    output wire      eoa,
    output wire      result,
    output wire      err
);

/*======== rs_nand ========
    M rs_nand: 4 pins and 0 parameters
    input wire            A
    input wire            B
    output wire            O
    output wire            Ob
*/
/*======== sar ========
    M sar: 15 pins and 2 parameters
    input wire            rstb
    input wire            atpg
    input wire            f100m_clk
    input wire            sar_soc
    output wire            sar_eoc
    output wire            sar_err
    output wire            sar_warn
    output reg    [NSTEP-1:0] sar_code
    input wire            ms_sar_dh
    input wire            ms_sar_dl
    input wire            ms_sar_rdy
    output wire            ms_sar_clock
    output reg            ms_sar_sample
    output reg    [NSTEP-1:0] ms_sar_sw
    output wire    [NSTEP-1:0] ms_sar_swb
*/
/*======== sar_analog ========
    M sar_analog: 12 pins and 1 parameters
    input real            vinp
    input real            vinm
    input real            vrefm
    input real            vrefp
    input real            vcm
    input wire            ms_sar_clock
    input wire            ms_sar_sample
    input wire    [NSTEP-1:0] ms_sar_sw
    input wire    [NSTEP-1:0] ms_sar_swb
    output reg            ms_sar_dh
    output reg            ms_sar_dl
    output wire            ms_sar_rdy
*/
/*======== tb ========
    M tb: 0 pins and 0 parameters
*/
/*======== toggle_resync_in ========
    M toggle_resync_in: 0 pins and 1 parameters
*/
/*======== toggle_resync_out ========
    M toggle_resync_out: 4 pins and 0 parameters
    input wire            rstb
    input wire            clk
    input wire            a
    output reg            o
*/

endmodule
/*
TYPE specifies how the message should be?

1 set bold
2 set half-bright (simulated with color on a color display)
4 set underscore (simulated with color on a color display)
5 set blink
7 set reverse video

COLOR specifies the message color.

30 set black foreground
31 set red foreground
32 set green foreground
33 set brown foreground
34 set blue foreground
35 set magenta foreground
36 set cyan foreground
37 set white foreground

*/

`timescale 1ns/100ps

module log_service;
  integer WARN_COUNT = 0;
  integer ERROR_COUNT = 0;
  string __xstr__;

  initial begin
    $timeformat(-9, 1, " ns", 14);
  end
endmodule

`define log_Note(msg) \
  begin $write("%c[1;32m",27); \
  $display("NOTE: [%t] %s", $time, msg); \
  $write("%c[0m",27); end

`define log_Info(msg) \
  begin $write("%c[0;37m",27); \
  $info("[%t] %s", $time, msg); \
  $write("%c[0m",27); end

`define log_Warning(msg) \
  begin log_service.WARN_COUNT += 1; \
  $write("%c[1;33m",27); \
  $warning("[%t] %s", $time, msg); \
  $write("%c[0m",27); end

`define log_Error(msg) \
  begin log_service.ERROR_COUNT += 1; \
  $write("%c[1;31m",27); \
  $error("[%t] %s", $time, msg); \
  $write("%c[0m",27); end

`define log_Fatal(msg) \
  begin $write("%c[1;31m",27); \
  $fatal(1, "[%t] %s%c[0m", $time, msg, 27); end

// use $sformat for compatibility since $sformatf is
// not always supported
`define log_InfoF(template, a)    $sformat(log_service.__xstr__, template, a);`log_Info(log_service.__xstr__);
`define log_NoteF(template, a)    $sformat(log_service.__xstr__, template, a);`log_Note(log_service.__xstr__);
`define log_WarningF(template, a) $sformat(log_service.__xstr__, template, a);`log_Warning(log_service.__xstr__);
`define log_ErrorF(template, a)   $sformat(log_service.__xstr__, template, a);`log_Error(log_service.__xstr__);

`define log_Terminate \
  begin $write("%c[1;37m",27); \
  if(log_service.ERROR_COUNT > 0 && log_service.WARN_COUNT > 0) \
    $display("Simulation Failed with %0d Errors and %0d Warnings", log_service.ERROR_COUNT, log_service.WARN_COUNT); \
  else if(log_service.ERROR_COUNT > 0) \
    $display("Simulation Failed with %0d Errors", log_service.ERROR_COUNT); \
  else if(log_service.WARN_COUNT > 0) \
    $display("Simulation Failed with %0d Warnings", log_service.WARN_COUNT); \
  else \
    $display("Simulation Successful"); \
  $write("%c[0m",27); \
  $finish; end

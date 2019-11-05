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


module log_service;
  integer ERROR_COUNT = 0;
  string __xstr__;

  initial begin
    $timeformat(-9, 1, " ns", 14);
  end
endmodule

`define log_Note(msg) \
  $write("%c[1;32m",27); \
  $display("Note    : [%t] %s", $time, msg); \
  $write("%c[0m",27);

`define log_Info(msg) \
  $write("%c[0;37m",27); \
  $display("Info    : [%t] %s", $time, msg); \
  $write("%c[0m",27);

`define log_Warning(msg) \
  $write("%c[1;34m",27); \
  $display("Warning : [%t] %s", $time, msg); \
  $write("%c[0m",27);

`define log_Error(msg) \
  log_service.ERROR_COUNT = log_service.ERROR_COUNT + 1; \
  $write("%c[1;31m",27); \
  $display("Error   : [%t] %s", $time, msg); \
  $write("%c[0m",27);

`define log_Fatal(msg) \
  $write("%c[1;31m",27); \
  $display("Fatal   : [%t] %s", $time, msg); \
  $write("%c[0m",27);

// use $sformat for compatibility since $sformat is
// not always supported
`define log_InfoF(template, a)    $sformat(log_service.__xstr__, template, a);`log_Info(log_service.__xstr__);
`define log_NoteF(template, a)    $sformat(log_service.__xstr__, template, a);`log_Note(log_service.__xstr__);
`define log_WarningF(template, a) $sformat(log_service.__xstr__, template, a);`log_Warning(log_service.__xstr__);
`define log_ErrorF(template, a)   $sformat(log_service.__xstr__, template, a);`log_Error(log_service.__xstr__);

`define log_Terminate \
  $write("%c[1;37m",27); \
  if(log_service.ERROR_COUNT > 0) \
    $display("Simulation Failed with %d Errors", log_service.ERROR_COUNT); \
  else \
    $display("Simulation Successful"); \
  $write("%c[0m",27); \
  $finish();

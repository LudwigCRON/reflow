# define top
hierarchy -check -top ${top_module}

# pre-process and optimize
proc; opt; fsm; opt; memory; opt
techmap; opt

# map to the techno
dfflibmap -liberty ${techno}
abc -liberty ${techno}

# clean output
clean

# save the output of synthesis
write_verilog ${netlist}.v
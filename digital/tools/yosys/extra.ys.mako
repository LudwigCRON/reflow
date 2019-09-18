# define top
hierarchy -check -top ${top_module}

# pre-process and optimize
proc; opt; fsm; opt; memory; opt
techmap -recursive; opt

# map to the techno
dfflibmap -liberty ${techno}
abc -liberty ${techno}

# clean output
clean

# save the output of synthesis
% if format == "spice":
write_${format} -top ${top_module} ${netlist}
% else:
write_${format} ${netlist}
% endif
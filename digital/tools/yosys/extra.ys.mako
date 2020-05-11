read_verilog -lib ${techno.replace(".lib", ".v")}

# define top
hierarchy -check -top ${top_module}

# pre-process and optimize
proc; opt; fsm; opt; memory; opt
opt_rmdff
opt_expr -full
opt_clean
rmports
techmap -recursive; opt

# map to the techno
dfflibmap -liberty ${techno}
abc -liberty ${techno}
# clean output
clean

#show ${top_module}

# save the output of synthesis
% if format == "spice":
write_${format} -big_endian -top ${top_module} ${netlist}
% else:
write_${format} ${netlist}
% endif

# always output json for post_processing
write_json ${netlist}.json

# load first the technology of the project
read_verilog -lib ${techno.replace(".lib", ".v")}

verilog_defaults -add -sv -noassert -noassume -norestrict -defer

% for include in includes:
verilog_defaults -add -I${include}
% endfor

# then load all synthizeable files
% for file, type in files:
    % if type in ["verilog"]:
read_verilog ${file}
    % endif
% endfor

# define top
hierarchy -check -top ${top_module}

tee -o ${work_dir}/design_checks_rtl.rpt check

# pre-process and optimize
proc; opt -fast; fsm; opt -fast; memory; opt
# merge identical functional signals
freduce -v
clean
# remove unused dffs/ports/expr branch
opt_rmdff
opt_expr -full
opt_clean
rmports
techmap -recursive; opt

# map to the techno
dfflibmap -liberty ${techno}
abc -liberty ${techno}
# clean output
opt_clean

# reports
tee -o ${work_dir}/design_stats.rpt stat
tee -o ${work_dir}/design_checks_synth.rpt check

#show ${top_module}

# save the output of synthesis
% if format == "spice":
write_spice -big_endian -top ${top_module} ${netlist}
% elif format == "verilog":
write_verilog -noexpr -attr2comment ${netlist}
% else:
write_${format} ${netlist}
% endif

# always output json for post_processing
write_json ${netlist}.json

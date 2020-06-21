# Icarus Verilog
https://iverilog.icarus.com

**Tested versions:**
 - iverilog 10.3

**New:**

**Change:**

**Obsolete:**

## Strategy
`iverilog` use external programs and configuration files to preporcess
and compile the verilog sources. The user can select another set of 
tools with the ```-B[path to new programs]``` option. It has be 
decided to not support this option in favor of a simpler PATH change 
strategy. Existing solution such as [Lmod](https://lmod.readthedocs.io/en/latest/)
being more polyvalent to load another variants of a software.

`iverilog` can read command files listing all files to be parsed, add
define, parameters. This command files can most of the time reused for
other simulators. It is the preferred approcached in this snippet.

`iverilog` supports verilog 1995 to verilog 2005, and systemverilog 
from 2005 to 2012. If any systemverilog file is found in the simulation,
all the simulation will be run in systemverilog-2012 (verilog code 
should be checked to prevent the use of systemverilog keywords use). 
Otherwise, the verilog 2001 is the prefered version due to its support
by other EDA vendors.

`iverilog` accepts extra include files directories with ```-I[includedir]```.
Include files path is resolved by reflow and `-I` command is added in
the generated command file.

`iverilog` compiles all files provided to it into an executable. The 
name of this executable is `run.vvp` in the temporary working directory.

`iverilog` can generate a snapshot of waveform in the vcd, lxt, lxt2,
or fst formats. Despite some softwares support all of these
(eg. gtkwave), some don't (eg. covered, z01x, ...). By default the 
WAVE_FORMAT is set to be "vcd".

## Supported
The main purpose of this snippet is to generate a command file
for iverilog.

-gverilog-ams if the mimetype AMS is detected and -gno-verilog-ams otherwise.

to support specify block add ```SIM_FLAGS += -gspecify``` in the Sources.list

-grelative-include is activated by default and cannot be disabled.

## Not supported
the default value is indicated by a `*`

-gstd-include*/-gno-std-include: only the default of `iverilog`

-gxtypes*/-gno-xtypes: only the default of `iverilog`

-gio-range-error*/-gno-io-range-error: only the default of `iverilog`
flag an error can help spot an error in the design.

-gstrict-ca-eval/-gno-strict-ca-eval*: only the default of `iverilog`
most of EDA vendors follow the same principle. For a product, always
perform a backannotated simulation.

-gstrict-expr-width/-gno-strict-expr-width*: only the default of `iverilog`

-gshared-loop-index/-gno-shared-loop-index*: only the defautl of `iverilog`

-l[file]: compile file as a library (under investigation)

-M[mode]=[path]: list of files contributing to the compilation of [mode].
The usefullness of this should be clarified.

-m[module]: add a module to the list of VPI modules.

-N[path]: dump a final netlist of the design. The interrest over `-E` 
option is not clear yet.

-p[flag]=[value]: the usefullness of this should be clarified.

-S: try to synthesize all or parts of the design. This option seems 
not relevant as `iverilog` is not made for synthesis. It is prefered 
to keep `iverilog` for simulation and use either Yosys or any EDA 
synthesis solution for that.

-s [topmodule]: specify the top module of the simulation. The solution
of `iverilog` is sufficient for most cases. However, with many modules
being orphans, wrong choice can be made. It means either orphans are
declared in Sources.list (should inspect them) or use only a fraction
of a large IP.

-Tmin|typ|max: timing simulation with backannotation seems prematurate
in most cases. In general, setting this parameter is not sufficient
as lib/verilog files should also be changed for IP blocks. The
prefered solution is to implement a Batch.list to check all conditions.
It has the benefit of having a report for failure in somes conditions.

-t[target]: target value can be (null | vvp* | fpga | vhdl).
`null` can be used for syntax checking only.
`vvp` is the default.
`fpga` is not commended.
`vhdl` is for translation only.

-v: verbose output pollute logs

-W[warnings-class]: the warning class are:

- all (all below except infloop and sensitivity-entire-vector)
- anachronisms
- implicit
- portbind
- select-range
- timescale
- infloop
- sensitivity-entire-vector
- sensitivity-entire-array

-y[libdir]: library search path for VPI and modules

-Y[suffix]: The usefullness should be clarified

## Next steps
- Add support for VPI modules and compilation

    if *.so load it with `-m[path to *.so file]`
    does this work on windows with *.dll ?
    
    perform the same stragety for -I and -y with
    +libdir+dir and +libext+ext

- Add support for the `-s [topmodule]`
- Add support for warning filtering
- Add WAVE_FORMAT override for user who don't have VCD limitation
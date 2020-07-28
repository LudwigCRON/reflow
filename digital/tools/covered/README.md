# GTKWave
http://covered.sourceforge.net/

**Tested versions:**
 - covered 0.7.10

**New:**

**Change:**

**Obsolete:**

## Strategy
For each simulation a VCD file

## Supported

### score
score : Parses Verilog files and VCD dumpfiles to create database file used
for merging and reporting.
score 

-t top_level_module_name
-vcd dumpfile

merge : Merges two database files into one.

report : Generates human-readable coverage reports from database file.

rank : Generates ranked list of CDD files to run for optimal coverage in a regression run.

exclude : Excludes coverage points from a given CDD and saves the modified CDD for further commands.

## Not Supported
 -T : Causes all output except for header information and warnings to be suppressed
 -Q : Causes all output to be suppressed 
 -B : Obfuscates design-sensitive names in all user-readable output

 -lxt and -fst option have not been tested
 -vpi cannot be used in conjonction with the -vcd option.

## Next Steps
- Add fastload for VCD
- Add support for `-c` to speed up loading of large waveform files

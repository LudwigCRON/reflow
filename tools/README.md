# Analog Tools
this folder is a collection of scripts to ease
the front-end job of analog designers.

Therefore, the tools of this sections are made 
for the simulation and analysis reports.

## Supported commands
Not yet implemented

## Supported tools
Not yet implemented

## Future Improvements
Planned tools support are:
- [ltspice](https://www.analog.com/en/design-center/design-tools-and-calculators/ltspice-simulator.html#)
- [ngspice](http://ngspice.sourceforge.net/download.html)
- xcellium
- ncsim

Ngspice would require a GUI interface to help
simulation setup (select analysis and parameters).
In addition to that, a Monte-Carlo procedure would
be nice to implement.

In consequence, the choice is first to support
LTspice at short term, and ngspice in the long
term. Any advice on Ngspice is welcome !

xcellium is more important than ncsim to my eyes.
However, one having this tools has already a good
support provided by Cadence.

## Assumptions and Limitations
On Mac OSX, LTspice has even more restricted command-line
switches. So a user cannot generate a netlist as one can 
do on Windows via:

```sh
ltspice.exe -netlist my_design.asc
```

However, on both OS, the option `Automatically delete .raw and .log files`
shall be desactivated. This option is in Preference > Operation.


## Acknowledgments
The support of LTspice is based on my personal experiments
and other automation script of LTspice as the one of 
[Joskvi](https://github.com/joskvi/LTspice-cli)


# Digital Tools
this folder is a collection of scripts to ease
the front-end job of digital designers.

Therefore, the tools of this sections are made 
for the simulation and the synthesis.

**ReFlow cannot ensure a sign-off features as it
heavily relies on the tools called. If used in
a professional project, perform a sign-off with
a tool supporting it.**

## Supported commands
Supported commands from run in this flow are:
- run lint
- run sim
- run cov
- run synth
- run view-sim

## Supported tools
For linting:
- [iverilog](./tools/iverilog/README.md)

For simulation, the tools supported are in order
of support priority:
- [iverilog](./tools/iverilog/README.md)
- xcellium
- ncsim
- verilator

To view generated waveforms:
- [gtkwave](./tools/gtkwave/README.md)

For synthesis:
- yosys

For code coverage:
- covered

## Future Improvements
- DEFINE paramaters and values are not yet propagated to iverilog
- COV_MODULES is not propagated yet
- IP_MODULES is not propagated yet

### coming commands

- run view-cov

    *view the code coverage analysis either the report or call a viewer such as IMC*

- run rtl

    *generate a list of all files, include
    directories, and parameters*

## Assumptions and Limitations
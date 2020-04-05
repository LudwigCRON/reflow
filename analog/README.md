# Analog Flow
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

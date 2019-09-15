# ReFlow
ReFlow is a combination of scriptlets for the simulations of analogue, digital, mixed-signal devices.

## Installation
In order to use the tool, we recommend to install somehow all the tools in the same folder linking to the version of tools desired.

This allows one to change easily the version of the tools.

For example:
```sh
export CADTOOLS=path/to/user/folder
ln -s $(CADTOOLS)/yosys /mnt/ed/cad/digital/yosys/0.8/bin/
ln -s $(CADTOOLS)/incisive /mnt/ed/cad/digital/lnx/rh/53/64/INCISIVE15.20.051/tools/bin/
ln -s $(CADTOOLS)/iverilog /mnt/ed/cad/digital/iverilog/11.0/bin/
```

Otherwise, one should add each tools directory in the ```PATH``` environment variable.

## Configuration
The tool looks into the project directory for any configuration files.
It _shall_ exist only one configuration in a given directory tree.

If there is none, the default configuration applies.
This default configuration can be found in the root of ReFlow.

## Supported Tools
### The list of supported tools
## Supported Commands
For almost all flows (Analog/Digital/Mixed), there share common commands:
- run sim
- run view-sim
- run lint
- run tree
- run clean
- run cov (only for digital)
- run view-cov (only for digital)
- run synth (only for digital)

For the sake of lazyness, one can write ```run -c [sim|lint|cov|...]``` to perform a run clean before the operation ordered.
### [Analog](./analog/README.md)
### [Digital](./digital/README.md)
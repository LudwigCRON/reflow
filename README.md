# ReFlow
ReFlow is a combination of scriptlets for the simulations of one of 
the following domain:
- analog
- digital
- mixed-signal

For each domain, tools dedicated to it are gathered in a folder **tools**.
A tool is a collection of scripts to perform a precise task inside a
folder entitled by the name of the tool. It results then in a greater
flexibility and personalisation of the flow. The hierarchy can be 
represented as follow:

```
+ analog
|--+ tools
|  |--+ irun
|  |--+ eldo
|  |--+ hspice
|  |--+ ltspice
|  +--+ ngspice
|  +--+ gwave
|  +--+ simvision
|
+ digital
|--+ tools
|  |--+ iverilog
|  |--+ xcellium
|  |--+ verilator
|  |--+ covered
|  +--+ gtkwave
|
...
```

As many functions are common to all tools 
(list all used files, order by dependencies, ...)
A **common** category as been added to:
- generate a netlist 
- generate a database of imported elements
- read configuration file in a project or a local folder


## Installation
In order to use the tool, we recommend to install somehow
all the tools in the same folder linking to the version 
of tools desired. And make the tool available to the user 
by adding them in `$PATH`.

A great tools such as [module](http://modules.sourceforge.net/),
or [Lmod](https://lmod.readthedocs.io/en/latest/) streamline the
process of providing a collection of version specific program
available in `$PATH`. This allows one to change easily the version 
of the tools.

A more basic strategy would consist in "sourcing" a bash
script editing `$PATH` or changing link of programs.

For example:
```sh
export CADTOOLS=path/to/user/folder
ln -s $(CADTOOLS)/yosys /mnt/ed/cad/digital/yosys/0.8/bin/
ln -s $(CADTOOLS)/incisive /mnt/ed/cad/digital/lnx/rh/53/64/INCISIVE15.20.051/tools/bin/
ln -s $(CADTOOLS)/iverilog /mnt/ed/cad/digital/iverilog/11.0/bin/
```

Concerning ReFlow, it relies on a python virtual
environment. In consequence one load the environment

```bash
# for bash
source envs/bin/activate
# for csh
source envs/bin/activate.csh
# for fish
source envs/bin/activate.fish
# for powershell
. envs/bin/activate.ps1
```

Automatically, one can call the utilities developped
in ReFlow. For instance, user can call `run` utility.

```sh
(envs)  ~/projects/electronic/reflow$ run -h
usage: run [-h] [-c]
           [--sim | --cov | --lint | --tree | --view-sim | --view-cov | --synth]

Reflow Unified ruNner
---------------------

For arguments starting with by double dash --,the double dashes can be
omitted. ex: 'run sim' is equal to 'run --sim'

optional arguments:
  -h, --help   show this help message and exit
  -c, --clean  clean working directory
  --sim        run a simulation
  --cov        run a coverage simulation
  --lint       apply lint checks on a design
  --tree       display the design tree
  --view-sim   display waveforms
  --view-cov   display coverage results
  --synth      synthesize a design
```


## Configuration
The tool looks into the project directory for any configuration files
having the extension ***.config**.
It _shall_ exist only one configuration in a given directory tree.

If there is none, the default configuration applies.
This default configuration can be found in the root of ReFlow.

## Supported Tools
- [ ] List tools supported here per domain
- [ ] Add a link to the README.md in each tool
- [ ] each README.md in tool's folder gives the version
  of the tool, and what is supported
- [ ] define AMS simulation strategy

## Supported Commands
For almost all flows (Analog/Digital/Mixed), there share common commands:
- run sim
- run view-sim
- run lint
- run tree
- run clean

In addition to that, some domain can support extra command
(the digital also support run cov, view-cov, synth).

For the sake of lazyness, one can write ```run -c [sim|lint|...]```
to perform a run clean before the operation ordered.

For more details which command is supported by which domain
please refer to their associated documentation:
- [Analog](./analog/README.md)
- [Digital](./digital/README.md)
- [Mixed](./mixed/README.md)
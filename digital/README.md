# Digital Flow
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
- run synth
- run view-sim

## Supported tools
For simulation, the tools supported are in order
of support priority:
- iverilog
- xcellium
- ncsim
- verilator

For synthesis, only YOSYS is supported yet. However, the procedure setup for YOSYS is compatible with other tools such as Genus.

*If one create an issue for it and many votes
in favor of the support of Genus, its 
integration in run will be then top priorities*

## Future Improvements
- DEFINE paramaters and values are not yet propagated to iverilog
- COV_MODULES is not propagated yet
- IP_MODULES is not propagated yet

### coming commands
- run cov

    *code coverage analysis*

- run view-cov

    *view the code coverage analysis either the report or call a viewer such as IMC*

- run rtl

    *generate a list of all files, include
    directories, and parameters*

## Assumptions and Limitations
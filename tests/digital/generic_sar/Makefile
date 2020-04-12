# this corresponds to a manual flow
# which is used as reference
ELAB=iverilog
SIM=vvp
COVERED=~/Applications/covered-0.7.10/src/covered
WAVE=/Applications/gtkwave.app/Contents/MacOS/gtkwave-bin

# limited in application since Sources.list cannot
# include other directories

# should filter to remove parameters
VER_SIM=$(shell cat Sources.list)

.PHONY: tb

elab: tb
	$(ELAB) -g2005-sv -o $< -c Sources.list

sim: elab
	$(SIM) tb -vcd tb.vcd

view:
	open tb.vcd

michel:
	@echo $(subst $e , -v ,$(VER_SIM))

cov:
	$(COVERED) score -t tb -v $(subst $e , -v ,$(VER_SIM)) -e sar_analog -e tb -o test.cdd
	$(COVERED) score -cdd test.cdd -vcd tb.vcd
	$(COVERED) report -d v test.cdd > coverage.rpt

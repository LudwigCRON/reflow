#WAVEVIEWER=open ~/Applications/vlsi/Scansion.app
WAVEVIEWER=open ~/Applications/vlsi/gtkwave.app

DIGFLOW=~/Applications/vlsi/flow/digital
DIGTOOLS=$(DIGFLOW)/tools
DIGPARSER=$(DIGFLOW)/parser

READER=$(DIGPARSER)/read_files.py
GENSYN=$(DIGTOOLS)/yosis.py
SIMULATOR=$(DIGTOOLS)/iverilog.py
COVERAGE=$(DIGFLOW)/../../covered-0.7.10/src/covered

all: lint sim cov

lint:
	${READER} -i '$(shell pwd)' | ${SIMULATOR} --lint-only

sim:
	${READER} -i '$(shell pwd)' | ${SIMULATOR}

rtl:
	${READER} -i '$(shell pwd)' | ${GENSYN} > tb.ys
	echo "hierarchy -check -top mytop" >> tb.ys
	echo "proc; opt; fsm; opt; memory; opt" >> tb.ys
	echo "techmap; opt" >> tb.ys
	echo "dfflibmap -liberty mycells.lib" >> tb.ys
	echo "abc -liberty mycells.lib" >> tb.ys
	echo "clean" >> tb.ys
	echo "write_verilog out.v" >> tb.ys

cov:
	$(COVERAGE) score -t tb -v $(subst $e , -v ,$(VER_SIM)) -e sar_analog -e tb -o test.cdd
	$(COVERAGE) score -cdd test.cdd -vcd tb.vcd
	$(COVERAGE) report -d v test.cdd > coverage.rpt

view-sim:
	$(WAVEVIEWER) '$(shell pwd)/.tmp_sim/run.vcd'

clean:
	rm -rf '$(shell pwd)/.tmp_sim'
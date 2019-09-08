#WAVEVIEWER=open ~/Applications/vlsi/Scansion.app
WAVEVIEWER=open $(HOME)/Applications/vlsi/gtkwave.app

CADTOOLS = $(HOME)/Applications/vlsi/
COVERAGE = $(DIGTOOLS)/covered/covered.py
DIGFLOW  = $(HOME)/Applications/vlsi/flow/digital
DIGTOOLS = $(DIGFLOW)/tools
GENSYN   = $(DIGTOOLS)/yosys/yosys.py
READER   = $(DIGTOOLS)/common/read_files.py
SIMULATOR= $(DIGTOOLS)/iverilog/iverilog.py

# find python module in the flow
export PYTHONPATH := $(DIGFLOW)
export PATH := $(CADTOOLS)/yosys:$(PATH)
export PATH := $(CADTOOLS)/covered-0.7.10/src:$(PATH)

all: lint sim cov

lint:
	${READER} -i '$(shell pwd)' | ${SIMULATOR} --lint-only

sim:
	${READER} -i '$(shell pwd)' | ${SIMULATOR}

synth:
	${READER} -i '$(shell pwd)' | ${GENSYN}

cov:
	${READER} -i '$(shell pwd)' | ${COVERAGE}

view-sim:
	$(WAVEVIEWER) '$(shell pwd)/.tmp_sim/run.vcd'

clean:
	rm -rf '$(shell pwd)/.tmp_sim'
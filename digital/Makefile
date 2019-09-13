#WAVEVIEWER=open ~/Applications/vlsi/Scansion.app
WAVEVIEWER=open $(HOME)/bin/reflow/gtkwave.app

CADTOOLS = $(HOME)/bin/reflow
COVERAGE = $(DIGTOOLS)/covered/covered.py
DIGFLOW  = $(REFLOW)/digital
DIGTOOLS = $(DIGFLOW)/tools
GENSYN   = $(DIGTOOLS)/yosys/yosys.py
READER   = $(DIGTOOLS)/common/read_files.py
SIMULATOR= $(DIGTOOLS)/ncsim/ncsim.py
DESTREE  = $(DIGTOOLS)/common/design_tree.py

# find python module in the flow
export PYTHONPATH := $(DIGFLOW)
export PATH := $(CADTOOLS)/yosys:$(PATH)
export PATH := $(CADTOOLS)/covered/src:$(PATH)
export PATH := /mnt/ed/ct/lnx/rh/53/64/INCISIVE15.20.051/tools/bin/:$(PATH)
export PLATFORM := Ganymede

.PHONY: check-reflow

check-reflow:
ifndef REFLOW
    $(error REFLOW variable should point to the installation path)
endif

all: lint sim cov

dbg:
	${READER} -i '$(shell pwd)'

tree:
	${READER} -i '$(shell pwd)'| ${DESTREE}

lint:
	${READER} -i '$(shell pwd)' | ${SIMULATOR} --lint-only

sim:
	${READER} -i '$(shell pwd)' | ${SIMULATOR}

synth:
	${READER} -i '$(shell pwd)' | ${GENSYN}

cov:
	${READER} -i '$(shell pwd)' | ${COVERAGE}

view-cov:
	${READER} -i '$(shell pwd)' | ${COVERAGE} --view

view-sim:
	$(WAVEVIEWER) '$(shell pwd)/.tmp_sim/run.vcd'

clean:
	rm -rf '$(shell pwd)/.tmp_sim'

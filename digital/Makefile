include $(CONFIG_PATH)

# define tools folder
DIGFLOW  = $(REFLOW)/digital
ANAFLOW  = $(REFLOW)/analog
MIXFLOW  = $(REFLOW)/mixed
# define where to find tools
DIGTOOLS = $(DIGFLOW)/tools
ANATOOLS = $(ANAFLOW)/tools
MIXTOOLS = $(MIXFLOW)/tools
# define digital tools according to the configuration
BATCH    = $(DIGTOOLS)/common/read_batch.py
READER   = $(DIGTOOLS)/common/read_sources.py
DESTREE  = $(DIGTOOLS)/common/design_tree.py
DIG_COVER= $(DIGTOOLS)/$(DIG_COVERAGE_TOOL)/$(DIG_COVERAGE_TOOL).py
DIG_SYNTH= $(DIGTOOLS)/$(DIG_SYNTHESIS_TOOL)/$(DIG_SYNTHESIS_TOOL).py
DIG_SIM  = $(DIGTOOLS)/$(DIG_SIMULATOR_TOOL)/$(DIG_SIMULATOR_TOOL).py
# find python module in the flow
export PYTHONPATH := $(DIGFLOW):$(ANAFLOW):$(MIXFLOW)
export PATH := $(CADTOOLS)/yosys:$(PATH)
export PATH := $(CADTOOLS)/covered-0.7.10/src:$(PATH)
export PATH := /mnt/ed/ct/lnx/rh/53/64/INCISIVE15.20.051/tools/bin/:$(PATH)
export PATH := /mnt/ed/ct/lnx/rh/53/64/XCELIUMMAIN19.03.010/tools/bin/:$(PATH)

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
	${READER} -i '$(shell pwd)' | ${DIG_SIM} --lint-only

sim:
	${READER} -i '$(shell pwd)' | ${DIG_SIM}

batch-sim:
	${BATCH} -i '$(shell pwd)' -s

batch-cov:
	${BATCH} -i '$(shell pwd)' -c

synth:
	${READER} -i '$(shell pwd)' | ${DIG_SYNTH}

synth-mix:
	${READER} -i '$(shell pwd)' | ${DIG_SYNTH} -f spice

cov: sim
	${READER} -i '$(shell pwd)' | ${DIG_COVER}

view-cov:
	${READER} -i '$(shell pwd)' | ${DIG_COVER} --view

view-sim:
	$(WAVEFORM_VIEWER) '$(shell pwd)/.tmp_sim/run.vcd'

clean:
	rm -rf '$(shell pwd)/.tmp_sim'

#!/usr/bin/env python3
import os
import sys
import logging
import tools.common.utils as utils
import tools.common.executor as executor

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

DEFAULT_TMPDIR = os.path.join(os.getcwd(), ".tmp_sim")
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
  logging.info("[1/2] Listing files")
  # create temporary directory
  os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
  SRCS       = os.path.join(DEFAULT_TMPDIR, "srcs.list")
  EXE        = os.path.join(DEFAULT_TMPDIR, "run.vvp")
  PARSER_LOG = os.path.join(DEFAULT_TMPDIR, "parser.log")
  SIM_LOG    = os.path.join(DEFAULT_TMPDIR, "sim.log")
  WAVE       = os.path.join(DEFAULT_TMPDIR, "run.vcd")
  # create the list of sources
  PARAMS, MIMES, FILES = utils.get_sources(utils.filter_stream(sys.stdin), None)
  with open(SRCS, "a+") as fp:
    # list files
    for f in FILES:
        fp.write(f+'\n')
    # add vh extension to verilog
    fp.write("-vlog_ext .v,.vp,.vh,.vs\n")
    # add lookup directory
    dirs = list(set([os.path.dirname(f) for f in FILES]))
    for d in dirs:
        fp.write(f"-incdir {d}\n")
    # ill-formed include looking high in hierarchy
    dirs = list(set([os.path.abspath(os.path.join(d, os.path.pardir)) for d in dirs]))
    for pd in dirs:
        fp.write(f"-incdir {pd}\n")
  # estimate appropriate flags
  generation = "verilog-ams" if any(["AMS" in m for m in MIMES]) else \
               "2012" if any(["SYS" in m for m in MIMES]) else "2001"
  assertions = "-gassertions" if any(["ASSERT" in m for m in MIMES]) else ""
  simvision  = "-gui" if "view-sim" in sys.argv else ""
  # create the executable sim
  logging.info("[2/2] Running simulation")
  executor.sh_exec(f"irun {simvision} -LICQUEUE -f {SRCS}", PARSER_LOG, MAX_TIMEOUT=300)

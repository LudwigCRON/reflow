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
  logging.info("[1/3] Listing files")
  # create temporary directory
  os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
  SRCS       = os.path.join(DEFAULT_TMPDIR, "srcs.list")
  EXE        = os.path.join(DEFAULT_TMPDIR, "run.vvp")
  PARSER_LOG = os.path.join(DEFAULT_TMPDIR, "parser.log")
  SIM_LOG    = os.path.join(DEFAULT_TMPDIR, "sim.log")
  WAVE       = os.path.join(DEFAULT_TMPDIR, "run.vcd")
  # create the list of sources
  PARAMS, MIMES = utils.get_sources(utils.filter_stream(sys.stdin), SRCS)
  # estimate appropriate flags
  generation = "verilog-ams" if any(["AMS" in m for m in MIMES]) else \
               "2012" if any(["SYS" in m for m in MIMES]) else "2001"
  assertions = "-gassertions" if any(["ASSERT" in m for m in MIMES]) else ""
  simvision  = "-gui" if "view-sim" in sys.argv else ""
  # create the executable sim
  if not "--lint-only":
    logging.info("[2/2] Running simulation")
    executor.sh_exec(f"xrun {simvision} -f {SRCS}", PARSER_LOG, MAX_TIMEOUT=300)
  else:
    logging.info("[2/2] Linting files")
    executor.sh_exec(f"xrun -hal -f {SRCS}", PARSER_LOG, MAX_TIMEOUT=300)

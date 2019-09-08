#!/usr/bin/env python3
import os
import sys
import logging
import tools.common.utils as utils
import tools.common.executor as executor
from tools.common.read_files import get_type
from mako.template import Template

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

DEFAULT_TMPDIR = os.path.join(os.getcwd(), ".tmp_sim")
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
  logging.info("[1/3] Listing files")
  # create temporary directory
  os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
  COV_DATABASE = os.path.join(DEFAULT_TMPDIR, "coverage.cdd")
  COV_REPORT   = os.path.join(DEFAULT_TMPDIR, "coverage.rpt")
  COV_LOG      = os.path.join(DEFAULT_TMPDIR, "coverage.log")
  WAVE         = os.path.join(DEFAULT_TMPDIR, "run.vcd")
  # create the list of sources
  PARAMS, MIMES, SRCS = utils.get_sources(utils.filter_stream(sys.stdin))
  # give the module to cover
  _t = PARAMS["COV_MODULES"][0] if "COV_MODULES" in PARAMS else "tb"
  # exclude (IP_MODULES -> -e)
  _e = PARAMS["IP_MODULES"][0].split(' ') if "IP_MODULES" in PARAMS else None
  if _e:
    _e = ' '.join([f"-e {module}" for module in _e])
  else:
    _e = ""
  # include files with -v
  _v = ' '.join([f"-v {line}" for line in SRCS])
  # running
  logging.info("[2/4] Running simulations")
  executor.sh_exec(f"covered score -t tb -i tb.{_t} {_v} {_e} -g 3 -ep -S -o {COV_DATABASE}", COV_LOG, MAX_TIMEOUT=300, SHOW_CMD=True)
  # scoring
  logging.info("[3/4] Scoring")
  executor.sh_exec(f"covered score -cdd {COV_DATABASE} -vcd {WAVE}", COV_LOG, "a+", MAX_TIMEOUT=240, SHOW_CMD=True)
  # reporting
  logging.info("[4/4] Generating report")
  executor.sh_exec(f"covered report -d v {COV_DATABASE} > {COV_REPORT}", COV_LOG, "a+", MAX_TIMEOUT=30, SHOW_CMD=True)
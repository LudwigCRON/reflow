#!/usr/bin/env python3
import os
import sys
import logging
from executor import sh_exec

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

DEFAULT_TMPDIR = os.path.join(os.getcwd(), ".tmp_sim")
SIM_FLAGS = ""

def get_sources(src, out: str = None) -> list:
  mimes, sim_flags = [], None
  fp_src = open(out, "w+") if not out is None else sys.stdout
  with fp_src:
    # parse all lines
    for line in src:
      # code file
      if ";" in line:
        path, mime = line.strip().split(';', 2)
        fp_src.write(path+'\n')
        mimes.append(mime)
      # parameter
      elif ":" in line:
        a, b = line.split(':', 2)
        if a.strip() == "SIM_FLAGS":
          sim_flags = b
  # select the appropriate generation mode
  mimes = list(set(mimes))
  return sim_flags, mimes

def display_log(path: str):
  if not os.path.exists(path):
    return None
  with open(path, "r+") as fp:
      k = 0
      for k, l in enumerate(fp.readlines()):
        print(l.strip())
      if k == 0:
        print("No Error Detected")

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
  SIM_FLAGS, MIMES = get_sources(sys.stdin, SRCS)
  # estimate appropriate flags
  generation = "verilog-ams" if any(["AMS" in m for m in MIMES]) else \
               "2012" if any(["SYS" in m for m in MIMES]) else "2001"
  assertions = "-gassertions" if any(["ASSERT" in m for m in MIMES]) else ""
  # create the executable sim
  logging.info("[2/3] Compiling files")
  sh_exec(f"iverilog -g{generation} {assertions} -Wall -o {EXE} -c {SRCS}", PARSER_LOG, 20)
  # run the simulation
  if not "--lint-only" in sys.argv:
    logging.info("[3/3] Running simulation")
    sh_exec(f"vvp {EXE} -vcd", SIM_LOG, 300)
    # move the dumpfile to TMPDIR
    if os.path.exists(WAVE):
      os.remove(WAVE)
    if os.path.exists("./dump.vcd"):
      os.rename("./dump.vcd", WAVE)
  # linting files
  else:
    logging.info("[3/3] Linting files")
    display_log(PARSER_LOG)
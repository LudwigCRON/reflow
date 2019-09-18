#!/usr/bin/env python3
import os
import sys
import shutil
import logging
import tools.common.utils as utils
import tools.common.executor as executor
from tools.common.read_sources import resolve_includes

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

DEFAULT_TMPDIR = os.path.join(os.getcwd(), ".tmp_sim")
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))

# the tool is wrapped with a perl script
# without shebang lines
verilator = shutil.which("verilator")

def transform_flags(flags: str) -> str:
    flags = flags.strip()
    if "-DEFINE " in flags:
        flags = flags.replace("-DEFINE ", "+define+")
    if "-define " in flags:
        flags = flags.replace("-define ", "+define+")
    return flags

if __name__ == "__main__":
    logging.info("[1/3] Listing files")
    # create temporary directory
    os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
    SRCS       = os.path.join(DEFAULT_TMPDIR, "srcs.list")
    EXE        = os.path.join(DEFAULT_TMPDIR, "run.cpp")
    PARSER_LOG = os.path.join(DEFAULT_TMPDIR, "parser.log")
    SIM_LOG    = os.path.join(DEFAULT_TMPDIR, "sim.log")
    WAVE       = os.path.join(DEFAULT_TMPDIR, "run.vcd")
    # create the list of sources
    PARAMS, MIMES, FILES = utils.get_sources(utils.filter_stream(sys.stdin), None)
    INCLUDE_DIRS = resolve_includes(FILES)
    with open(SRCS, "w+") as fp:
        for include_dir in INCLUDE_DIRS:
            fp.write(f"+incdir+{include_dir}\n")
        if "SIM_FLAGS" in PARAMS:
            for flag in PARAMS["SIM_FLAGS"]:
                fp.write(transform_flags(flag)+"\n")
        fp.write("+verilog2001ext+v\n")
        fp.write("+1800-2017ext+sv\n")
        for file in FILES:
            fp.write(f"{file}\n")
    # estimate appropriate flags
    assertions = "--assert" if any(["ASSERT" in m for m in MIMES]) else ""
    # create the executable sim
    logging.info("[2/3] Compiling files")
    # run the simulation
    if not "--lint-only" in sys.argv:
        logging.info("[3/3] Running simulation")
        executor.sh_exec(f"perl {verilator} {assertions} --vpi -cc --trace --threads 4 -O3 -Wall -f \"{SRCS}\" -exe {EXE}", PARSER_LOG, MAX_TIMEOUT=300)
        # move the dumpfile to TMPDIR
        if os.path.exists(WAVE):
            os.remove(WAVE)
        if os.path.exists("./dump.vcd"):
            os.rename("./dump.vcd", WAVE)
    # linting files
    else:
        logging.info("[3/3] Linting files")
        executor.sh_exec(f"perl {verilator} --lint-only -Wall -f {SRCS}", PARSER_LOG, MAX_TIMEOUT=30, SHOW_CMD=True)
        utils.display_log(PARSER_LOG, SUMMARY=True)
#!/usr/bin/env python3
import os
import sys
import logging
import tools.common.utils as utils
import tools.common.executor as executor
from tools.common.read_sources import resolve_includes

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
    INCLUDE_DIRS = resolve_includes(FILES)
    with open(SRCS, "w+") as fp:
        # add vh extension to verilog
        fp.write("-vlog_ext .v,.vp,.vh,.vs\n")
        fp.write("-sysv_ext .sv,.svp,.svh,.svi,.sva\n")
        # define include_dirs
        for include_dir in INCLUDE_DIRS:
            fp.write(f"-incdir {include_dir}\n")
        # add files
        for file in FILES:
            fp.write(file+"\n")
    # estimate appropriate flags
    generation = "verilog-ams" if any(["AMS" in m for m in MIMES]) else \
                 "2012" if any(["SYS" in m for m in MIMES]) else "2001"
    assertions = "-assert -ial" if any(["ASSERT" in m for m in MIMES]) else ""
    simvision  = "-gui" if "view-sim" in sys.argv else ""
    linting    = "-hal" if "--lint-only" in sys.argv else ""
    # create the executable sim
    logging.info("[2/2] Running simulation")
    executor.sh_exec(f"xrun -clean {simvision} {assertions} -LICQUEUE -f {SRCS}", PARSER_LOG, MAX_TIMEOUT=300)

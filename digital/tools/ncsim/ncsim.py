#!/usr/bin/env python3
import os
import sys

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.relog as relog
import common.executor as executor

from common.read_sources import resolve_includes

if __name__ == "__main__":
    relog.step("Listing files")
    # create temporary directory
    DEFAULT_TMPDIR = utils.get_tmp_folder()
    SRCS           = os.path.join(DEFAULT_TMPDIR, "srcs.list")
    EXE            = os.path.join(DEFAULT_TMPDIR, "run.vvp")
    PARSER_LOG     = os.path.join(DEFAULT_TMPDIR, "parser.log")
    SIM_LOG        = os.path.join(DEFAULT_TMPDIR, "sim.log")
    WAVE           = os.path.join(DEFAULT_TMPDIR, "run.vcd")
    os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
    # create the list of sources
    PARAMS, MIMES, FILES = utils.get_sources(relog.filter_stream(sys.stdin), None)
    INCLUDE_DIRS = resolve_includes(FILES)
    with open(SRCS, "w+") as fp:
        # add vh extension to verilog
        fp.write("-vlog_ext .v,.vp,.vh,.vs\n")
        fp.write("-sysv_ext .sv,.svp,.svh,.svi,.sva\n")
        # define include_dirs
        for include_dir in INCLUDE_DIRS:
            fp.write("-incdir %s\n" % include_dir)
        # add files
        for file in FILES:
            fp.write("%s\n" % file)
    # estimate appropriate flags
    generation = "verilog-ams" if any(["AMS" in m for m in MIMES]) else \
                 "2012" if any(["SYS" in m for m in MIMES]) else "2001"
    assertions = "-assert -ial" if any(["ASSERT" in m for m in MIMES]) else ""
    simvision  = "-gui" if "view-sim" in sys.argv else ""
    # create the executable sim
    relog.step("Running simulation")
    executor.sh_exec(
        "irun -clean %s %s -LICQUEUE -f %s" % (simvision, assertions, SRCS),
        PARSER_LOG,
        MAX_TIMEOUT=300
    )

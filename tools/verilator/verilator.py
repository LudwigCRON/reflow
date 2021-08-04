#!/usr/bin/env python3
import os
import sys
import shutil

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.relog as relog
import common.executor as executor

from common.read_sources import resolve_includes


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
    relog.step("Listing files")
    # create temporary directory
    DEFAULT_TMPDIR = utils.get_tmp_folder()
    SRCS           = os.path.join(DEFAULT_TMPDIR, "srcs.list")
    EXE            = os.path.join(DEFAULT_TMPDIR, "run.cpp")
    PARSER_LOG     = os.path.join(DEFAULT_TMPDIR, "parser.log")
    SIM_LOG        = os.path.join(DEFAULT_TMPDIR, "sim.log")
    WAVE           = os.path.join(DEFAULT_TMPDIR, "run.vcd")
    os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
    # create the list of sources
    PARAMS, MIMES, FILES = utils.get_sources(relog.filter_stream(sys.stdin), None)
    INCLUDE_DIRS = resolve_includes(FILES)
    with open(SRCS, "w+") as fp:
        for include_dir in INCLUDE_DIRS:
            fp.write("+incdir+%s\n" % include_dir)
        if "SIM_FLAGS" in PARAMS:
            for flag in PARAMS["SIM_FLAGS"]:
                fp.write("%s\n" % transform_flags(flag))
        fp.write("+verilog2001ext+v\n")
        fp.write("+1800-2017ext+sv\n")
        for file in FILES:
            fp.write("%s\n" % file)
    # estimate appropriate flags
    assertions = "--assert" if any(["ASSERT" in m for m in MIMES]) else ""
    # create the executable sim
    relog.step("Compiling files")
    # run the simulation
    if "--lint-only" not in sys.argv:
        relog.step("Running simulation")
        executor.sh_exec(
            "perl %s %s --vpi -cc --trace --threads 4 -O3 -Wall -f \"%s\" -exe %s" % (
                verilator,
                assertions,
                SRCS,
                EXE
            ),
            PARSER_LOG,
            MAX_TIMEOUT=300
        )
        # move the dumpfile to TMPDIR
        if os.path.exists(WAVE):
            os.remove(WAVE)
        if os.path.exists("./dump.vcd"):
            os.rename("./dump.vcd", WAVE)
    # linting files
    else:
        relog.step("Linting files")
        executor.sh_exec(
            "perl %s --lint-only -Wall -f %s" % (verilator, SRCS),
            PARSER_LOG,
            MAX_TIMEOUT=30,
            SHOW_CMD=True
        )
        relog.display_log(PARSER_LOG, SUMMARY=True)

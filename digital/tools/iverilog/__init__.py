#!/usr/bin/env python3
import os
import sys

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.relog as relog
import common.executor as executor

from common.read_sources import resolve_includes
from common.utils.files import get_type, is_digital


WAVE_FORMAT = "vcd"
DEFAULT_TMPDIR = utils.get_tmp_folder()
SRCS = os.path.join(DEFAULT_TMPDIR, "srcs.list")
EXE = os.path.join(DEFAULT_TMPDIR, "run.vvp")
PARSER_LOG = os.path.join(DEFAULT_TMPDIR, "parser.log")
SIM_LOG = os.path.join(DEFAULT_TMPDIR, "sim.log")
WAVE = os.path.join(DEFAULT_TMPDIR, "run.%s" % WAVE_FORMAT)


def transform_flags(flags: str) -> str:
    flags = flags.strip()
    # replace any values found by the key
    matches = {
        "+define+": ["-DEFINE ", "-define ", "-D", "-d"],
        "+parameter+": ["-PARAM ", "-param ", "-P", "-p"],
    }
    for output, inputs in matches.items():
        for i in inputs:
            if i in flags:
                flags = flags.replace(i, output)
    # generate a string
    flags = [flag for flag in flags.split(" ") if not flag.startswith("-g")]
    return " ".join(flags)


def prepare(files, PARAMS):
    relog.step("Prepation")
    # create temporary directory
    os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
    # create the list of sources
    FILES = [f for f, m in files]
    MIMES = list(set([m for f, m in files]))
    INCLUDE_DIRS = resolve_includes(FILES)
    with open(SRCS, "w+") as fp:
        for include_dir in INCLUDE_DIRS:
            fp.write("+incdir+%s\n" % include_dir)
        if "TIMESCALE" in PARAMS:
            fp.write("+timescale+%s\n" % PARAMS["TIMESCALE"])
        if "SIM_FLAGS" in PARAMS:
            for flag in PARAMS["SIM_FLAGS"]:
                tf = transform_flags(flag)
                if tf:
                    fp.write("%s\n" % tf)
        for file in FILES:
            if is_digital(file) and get_type(file) not in ["ASSERTIONS", "LIBERTY"]:
                fp.write("%s\n" % file)
    # estimate appropriate flags
    generation = "2012" if any(["SYS" in m for m in MIMES]) else "2001"
    flags = (
        "-gverilog-ams" if any(["AMS" in m for m in MIMES]) else "-gno-verilog-ams",
        "-gassertions" if any(["ASSERT" in m for m in MIMES]) else "-gno-assertions",
        "-gspecify" if any(["-gspec" in p for p in PARAMS.get("SIM_FLAGS", "")]) else "",
    )
    return generation, " ".join(flags)


def compile(generation, flags):
    # create the executable sim
    relog.step("Compiling files")
    print(
        "iverilog -g%s -grelative-include %s -Wall -o %s -c %s"
        % (generation, flags, EXE, SRCS)
    )
    try:
        executor.sh_exec(
            "iverilog -g%s -grelative-include %s -Wall -o %s -c %s"
            % (generation, flags, EXE, SRCS),
            PARSER_LOG,
            MAX_TIMEOUT=20,
        )
    # ignore return code error
    # as message is already displayed in stdout
    # and in the log file
    except subprocess.CalledProcessError:
        pass


def run(lint: bool = False):
    # linting files
    if lint:
        relog.step("Linting files")
        relog.display_log(PARSER_LOG)
        return relog.get_stats(SIM_LOG)
    # run the simulation
    else:
        relog.step("Running simulation")
        executor.sh_exec("vvp %s -%s" % (EXE, WAVE_FORMAT), SIM_LOG, MAX_TIMEOUT=300)
        # move the dumpfile to TMPDIR
        if os.path.exists(WAVE):
            os.remove(WAVE)
        if os.path.exists("./dump.%s" % WAVE_FORMAT):
            os.rename("./dump.%s" % WAVE_FORMAT, WAVE)
        return relog.get_stats(SIM_LOG)


def main(files, params, lint: bool = False):
    flags = prepare(files, params)
    compile(*flags)
    stats = run(lint)
    return stats


if __name__ == "__main__":
    files, params = utils.get_sources(relog.filter_stream(sys.stdin), None)
    main(files, params, "--lint-only" in sys.argv)

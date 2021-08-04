#!/usr/bin/env python3
import os
import sys

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.relog as relog
import common.executor as executor

from itertools import chain
from common.read_config import Config
from common.read_sources import resolve_includes

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
WAVE_FORMAT = "vcd"
DEFAULT_TMPDIR = utils.get_tmp_folder("sim")
SRCS = os.path.join(DEFAULT_TMPDIR, "srcs.list")
PARSER_LOG = os.path.join(DEFAULT_TMPDIR, "parser.log")
SIM_LOG = os.path.join(DEFAULT_TMPDIR, "sim.log")
WAVE = os.path.join(DEFAULT_TMPDIR, "run.%s" % WAVE_FORMAT)


def transform_flags(flags: str) -> str:
    flags = flags.strip()
    # replace any values found by the key
    matches = {
        "+define+": ["-DEFINE+", "-define+", "-D", "-d"],
        "+parameter+": ["-PARAM+", "-param+", "-P", "-p"],
    }
    for output, inputs in matches.items():
        for i in inputs:
            if i in flags:
                flags = flags.replace(i, output)
    # generate a string
    flags = [
        flag
        for flag in flags.split(" ")
        if not flag.startswith("-g") and not flag.startswith("-W")
    ]
    return " ".join(flags)


def prepare(files, params):
    relog.step("Listing files")
    # create the list of sources
    INCLUDE_DIRS = resolve_includes(files)
    CURRENT_DIR = os.getcwd()
    PLATFORM_NAME = os.getenv("PLATFORM")
    PLATFORM_DIR = CURRENT_DIR[: CURRENT_DIR.find(PLATFORM_NAME) + len(PLATFORM_NAME)]
    with open(SRCS, "w+") as fp:
        # add vh extension to verilog
        fp.write("-vlog_ext .v,.vp,.vh,.vs\n")
        fp.write("-sysv_ext .sv,.svp,.svh,.svi,.sva\n")
        # define include_dirs
        for include_dir in INCLUDE_DIRS:
            fp.write("-incdir %s\n" % include_dir)
        fp.write("-incdir %s\n" % PLATFORM_DIR)
        if "TIMESCALE" in PARAMS:
            fp.write("-timescale %s\n" % PARAMS["TIMESCALE"])
        if "SIM_FLAGS" in PARAMS:
            for flag in PARAMS["SIM_FLAGS"]:
                tf = transform_flags(flag)
                if tf and tf[:2] not in ("-m", "-M"):
                    fp.write("%s\n" % tf)
        # add files
        for file in files:
            if not file.endswith("h"):
                fp.write("%s\n" % file)
            else:
                fp.write(f"-incdir {os.path.dirname(file)}\n")

    # estimate appropriate flags
    return (
        "verilog-ams"
        if any(["AMS" in m for m in MIMES])
        else "2012"
        if any(["SYS" in m for m in MIMES])
        else "2001"
    )


def run_sim(files, params):
    Config.add_config(os.path.join(TOOLS_DIR, "tools.config"))
    WAVE_FORMAT = Config.xcellium.get("format")
    DEFAULT_TMPDIR = utils.get_tmp_folder("sim")
    SRCS = os.path.join(DEFAULT_TMPDIR, "srcs.list")
    PARSER_LOG = os.path.join(DEFAULT_TMPDIR, "parser.log")
    SIM_LOG = os.path.join(DEFAULT_TMPDIR, "sim.log")
    WAVE = os.path.join(DEFAULT_TMPDIR, "run.%s" % WAVE_FORMAT)
    # generate scripts
    gen = prepare(files, params)
    flags = " ".join(chain([gen], Config.ncsim.get("flags").split()))
    # run simulation
    relog.step("Running simulation")
    executor.sh_exec("xrun %s -f %s" % (flags, SRCS), PARSER_LOG, MAX_TIMEOUT=300)


def run_lint(files, params):
    Config.add_config(os.path.join(TOOLS_DIR, "tools.config"))
    WAVE_FORMAT = Config.xcellium.get("format")
    DEFAULT_TMPDIR = utils.get_tmp_folder("lint")
    SRCS = os.path.join(DEFAULT_TMPDIR, "srcs.list")
    PARSER_LOG = os.path.join(DEFAULT_TMPDIR, "parser.log")
    SIM_LOG = os.path.join(DEFAULT_TMPDIR, "sim.log")
    WAVE = os.path.join(DEFAULT_TMPDIR, "run.%s" % WAVE_FORMAT)
    # generate scripts
    gen = prepare(files, params)
    flags = " ".join(chain([gen, "-hal"], Config.ncsim.get("flags").split()))
    # lint
    executor.sh_exec("xrun %s -f %s" % (flags, SRCS), PARSER_LOG, MAX_TIMEOUT=300)


if __name__ == "__main__":
    # create the list of sources
    PARAMS, MIMES, FILES = utils.get_sources(relog.filter_stream(sys.stdin), None)
    run_sim(FILES, PARAMS)

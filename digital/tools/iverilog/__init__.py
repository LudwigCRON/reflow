#!/usr/bin/env python3
import os
import sys
import subprocess
from itertools import chain

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.relog as relog
import common.executor as executor
from common.read_config import Config
from common.read_sources import resolve_includes
from common.utils.files import get_type, is_digital


WAVE_FORMAT = "vcd"
DEFAULT_TMPDIR = utils.get_tmp_folder()
SRCS = os.path.join(DEFAULT_TMPDIR, "srcs.list")
EXE = os.path.join(DEFAULT_TMPDIR, "run.vvp")
PARSER_LOG = os.path.join(DEFAULT_TMPDIR, "parser.log")
SIM_LOG = os.path.join(DEFAULT_TMPDIR, "sim.log")
WAVE = os.path.join(DEFAULT_TMPDIR, "run.%s" % WAVE_FORMAT)
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))


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


def prepare(files, PARAMS):
    relog.step("Prepation")
    # create the list of sources
    FILES = [f for f, m in files]
    MIMES = list(set([m for f, m in files]))
    INCLUDE_DIRS = resolve_includes(FILES)
    CURRENT_DIR = os.getcwd()
    PLATFORM_NAME = os.getenv("PLATFORM")
    PLATFORM_DIR = CURRENT_DIR[: CURRENT_DIR.find(PLATFORM_NAME) + len(PLATFORM_NAME)]
    with open(SRCS, "w+") as fp:
        for include_dir in INCLUDE_DIRS:
            fp.write("+incdir+%s\n" % include_dir)
        fp.write("+incdir+%s\n" % PLATFORM_DIR)
        if "TIMESCALE" in PARAMS:
            fp.write("+timescale+%s\n" % PARAMS["TIMESCALE"])
        if "SIM_FLAGS" in PARAMS:
            for flag in PARAMS["SIM_FLAGS"]:
                tf = transform_flags(flag)
                if tf and tf[:2] not in ("-m", "-M"):
                    fp.write("%s\n" % tf)
        for file in FILES:
            if is_digital(file) and get_type(file) not in ["ASSERTIONS", "LIBERTY"]:
                fp.write("%s\n" % file)
    # estimate appropriate flags
    generation = "2012" if any(["SYS" in m for m in MIMES]) else "2001"
    flags = Config.iverilog.get("flags").split()
    flags.extend(
        [
            "-gverilog-ams"
            if any(
                [
                    "AMS" in m or "-gverilog-ams" in m
                    for m in chain(MIMES, PARAMS.get("SIM_FLAGS", ""))
                ]
            )
            else "-gno-verilog-ams",
            "-gassertions"
            if any(
                [
                    "ASSERT" in m or "-gassert" in m
                    for m in chain(MIMES, PARAMS.get("SIM_FLAGS", ""))
                ]
            )
            else "-gno-assertions",
            "-gspecify"
            if any(["-gspec" in p for p in PARAMS.get("SIM_FLAGS", "")])
            else "",
            "-Wtimescale"
            if any(["-Wtimes" in p for p in PARAMS.get("SIM_FLAGS", "")])
            else "",
        ]
    )
    flags = list(set(flags))
    # declare needed external VPI modules
    VVP_FLAGS = []
    if "SIM_FLAGS" in PARAMS:
        for flag in PARAMS["SIM_FLAGS"]:
            tf = transform_flags(flag)
            if tf and tf[:2] in ("-m"):
                VVP_FLAGS.append(tf)
    return generation, " ".join(chain(flags, VVP_FLAGS)).strip()


def compile(generation, flags):
    # create the executable sim
    relog.step("Compiling files")
    # remove inherited timescale flags
    try:
        executor.sh_exec(
            "iverilog -g%s %s -o %s -c %s" % (generation, flags, EXE, SRCS),
            PARSER_LOG,
            MAX_TIMEOUT=20,
            SHOW_CMD=True,
        )
    # ignore return code error
    # as message is already displayed in stdout
    # and in the log file
    except subprocess.CalledProcessError:
        pass


def run_sim(files, params):
    # update global variables
    Config.add_configs(os.path.join(TOOLS_DIR, "tools.config"))
    DEFAULT_TMPDIR = utils.get_tmp_folder("sim")
    WAVE_FORMAT = Config.iverilog.get("format")
    WAVE = os.path.join(DEFAULT_TMPDIR, "run.%s" % WAVE_FORMAT)
    # prepare scripts
    flags = prepare(files, params)
    compile(*flags)
    relog.step("Running simulation")
    VVP_FLAGS = []
    if "SIM_FLAGS" in params:
        for flag in params["SIM_FLAGS"]:
            tf = transform_flags(flag)
            if tf and tf[:2] in ("-m", "-M"):
                VVP_FLAGS.append(tf)
    VVP_FLAGS = " ".join(VVP_FLAGS)
    executor.sh_exec(
        "vvp -i %s %s -%s" % (EXE, VVP_FLAGS, WAVE_FORMAT),
        SIM_LOG,
        MAX_TIMEOUT=300,
        SHOW_CMD=True,
    )
    # move the dumpfile to TMPDIR
    if os.path.exists(WAVE):
        os.remove(WAVE)
    if os.path.exists("./dump.%s" % WAVE_FORMAT):
        os.rename("./dump.%s" % WAVE_FORMAT, WAVE)
    return relog.get_stats(SIM_LOG)


def run_lint(files, params):
    # update global variables
    Config.add_configs(os.path.join(TOOLS_DIR, "tools.config"))
    DEFAULT_TMPDIR = utils.get_tmp_folder("lint")
    # prepare scripts
    flags = prepare(files, params)
    compile(*flags)
    relog.step("Linting files")
    relog.display_log(PARSER_LOG)
    return relog.get_stats(SIM_LOG)


if __name__ == "__main__":
    files, params = utils.get_sources(relog.filter_stream(sys.stdin), None)
    if "--lint-only" in sys.argv:
        run_lint(files, params)
    else:
        run_sim(files, params)

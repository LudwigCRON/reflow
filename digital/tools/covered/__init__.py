#!/usr/bin/env python3
import os
import sys

from pathlib import Path

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.relog as relog
import common.executor as executor
import common.verilog as verilog

from common.read_sources import resolve_includes


# create temporary directory
DEFAULT_TMPDIR = utils.get_tmp_folder()
COV_DATABASE = os.path.join(DEFAULT_TMPDIR, "coverage.cdd")
COV_REPORT = os.path.join(DEFAULT_TMPDIR, "coverage.rpt")
COV_LOG = os.path.join(DEFAULT_TMPDIR, "coverage.log")
SRCS = os.path.join(DEFAULT_TMPDIR, "cov_srcs.list")


def prepare(files, PARAMS):
    relog.step("Prepation")
    # create temporary directory
    os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
    # find simulation waveforms (vcd, ...)
    WAVE = None
    for wavefile in Path(os.path.dirname(DEFAULT_TMPDIR)).rglob("**/*.vcd"):
        WAVE = str(wavefile)
        _, WAVE_FORMAT = os.path.splitext(WAVE)
        WAVE_FORMAT = WAVE_FORMAT[1:]
        break
    if WAVE is None:
        relog.error("run a simulation first with vcd output")
        exit(0)
    # create the list of sources
    FILES = [f for f, m in files]
    MIMES = list(set([m for f, m in files]))
    INCLUDE_DIRS = resolve_includes(FILES)
    # generate file list
    modules = PARAMS["COV_MODULES"][0].split(" ") if "COV_MODULES" in PARAMS else ["top"]
    instances = verilog.find_instances(PARAMS["TOP_MODULE"])
    instances = [(mod, instance) for mod, pa, instance, po in instances if mod in modules]
    generation = 3 if any(["SYS" in m for m in MIMES]) else 2
    excludes = PARAMS["IP_MODULES"][0].split(" ") if "IP_MODULES" in PARAMS else []
    with open(SRCS, "w+") as fp:
        for include_dir in INCLUDE_DIRS:
            fp.write("-I %s\n" % include_dir)
        for file in FILES:
            fp.write("-v %s\n" % file)
        for module in excludes:
            fp.write("-e %s\n" % module)
        fp.write("-%s %s\n" % (WAVE_FORMAT, WAVE))
        fp.write("-Wignore\n")
    return modules, instances, generation


def main(files, PARAMS):
    # top module
    top = "tb"
    if os.path.isfile(PARAMS["TOP_MODULE"]):
        top, _, _, _ = verilog.find_modules(PARAMS["TOP_MODULE"])[0]
    # give the module to cover
    modules, instances, generation = prepare(files, PARAMS)
    # scoring
    relog.step("Scoring simulations")
    if len(instances) > 1:
        for k, i in enumerate(instances):
            module, instance = i
            COV_K_DATABASE = COV_DATABASE.replace(".cdd", "_%d.cdd" % k)
            executor.sh_exec(
                "covered score -t %s -i %s.%s -f %s -g %s -o %s"
                % (module, top, instance, SRCS, generation, COV_K_DATABASE),
                COV_LOG,
                mode="a+",
                MAX_TIMEOUT=300,
                SHOW_CMD=True,
            )
    elif instances:
        executor.sh_exec(
            "covered score -t %s -i %s.%s -f %s -g %s -o %s"
            % (top, top, instances[0][1], SRCS, generation, COV_DATABASE),
            COV_LOG,
            mode="a+",
            MAX_TIMEOUT=300,
            SHOW_CMD=True,
        )
    else:
        executor.sh_exec(
            "covered score -t %s -f %s -g %s -o %s" % (top, SRCS, generation, COV_DATABASE),
            COV_LOG,
            mode="a+",
            MAX_TIMEOUT=300,
            SHOW_CMD=True,
        )
    # merging
    relog.step("Merging")
    if len(instances) > 1:
        cdds = [COV_DATABASE.replace(".cdd", "_%d.cdd" % k) for k in range(len(instances))]
        executor.sh_exec(
            "covered merge -o %s %s" % (COV_DATABASE, " ".join(cdds)),
            COV_LOG,
            "a+",
            MAX_TIMEOUT=240,
            SHOW_CMD=True,
        )
    # reporting
    relog.step("Generating report")
    executor.sh_exec(
        "covered report %s" % COV_DATABASE, COV_REPORT, MAX_TIMEOUT=30, SHOW_CMD=False
    )
    return relog.get_stats(COV_LOG)


if __name__ == "__main__":
    files, params = utils.get_sources(relog.filter_stream(sys.stdin), None)
    main(files, params)

#!/usr/bin/env python3
import os
import sys

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.relog as relog
import common.executor as executor
import common.verilog as verilog

from common.read_sources import resolve_includes


WAVE_FORMAT = "vcd"


if __name__ == "__main__":
    relog.step("Listing files")
    # create temporary directory
    DEFAULT_TMPDIR = utils.get_tmp_folder()
    COV_DATABASE   = os.path.join(DEFAULT_TMPDIR, "coverage.cdd")
    COV_REPORT     = os.path.join(DEFAULT_TMPDIR, "coverage.rpt")
    COV_LOG        = os.path.join(DEFAULT_TMPDIR, "coverage.log")
    SRCS           = os.path.join(DEFAULT_TMPDIR, "cov_srcs.list")
    WAVE           = os.path.join(DEFAULT_TMPDIR, "run.%s" % WAVE_FORMAT)
    os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
    # create the list of sources
    PARAMS, MIMES, FILES = utils.get_sources(relog.filter_stream(sys.stdin), None)
    INCLUDE_DIRS = resolve_includes(FILES)
    instances = verilog.find_instances(PARAMS["TOP_MODULE"])
    excludes = PARAMS["IP_MODULES"][0].split(' ') if "IP_MODULES" in PARAMS else []
    generation = 3 if any(["SYS" in m for m in MIMES]) else 2
    with open(SRCS, "w+") as fp:
        for include_dir in INCLUDE_DIRS:
            fp.write("-I %s\n" % include_dir)
        for file in FILES[::-1]:
            fp.write("-v %s\n" % file)
        for module in excludes:
            fp.write("-e %s\n" % module)
        fp.write("-%s %s\n" % (WAVE_FORMAT, WAVE))
        fp.write("-Wignore\n")
    # top module
    top = "tb"
    if os.path.isfile(PARAMS["TOP_MODULE"]):
        top, _, _, _ = verilog.find_modules(PARAMS["TOP_MODULE"])[0]
    # give the module to cover
    modules = PARAMS["COV_MODULES"][0].split(' ') if "COV_MODULES" in PARAMS else [top]
    instances = [(mod, instance) for mod, pa, instance, po in instances if mod in modules]
    # scoring
    relog.step("Scoring simulations")
    if len(instances) > 1:
        for k, i in enumerate(instances):
            module, instance = i
            COV_K_DATABASE = COV_DATABASE.replace('.cdd', "_%d.cdd" % k)
            executor.sh_exec(
                "covered score -t %s -i %s.%s -f %s -g %s -o %s" % (
                    module,
                    top,
                    instance,
                    SRCS,
                    generation,
                    COV_K_DATABASE
                ),
                COV_LOG,
                mode="a+",
                MAX_TIMEOUT=300,
                SHOW_CMD=True
            )
    else:
        executor.sh_exec(
            "covered score -t %s -i %s.%s -f %s -g %s -o %s" % (
                top,
                top,
                instances[0][1],
                SRCS,
                generation,
                COV_DATABASE
            ),
            COV_LOG,
            mode="a+",
            MAX_TIMEOUT=300,
            SHOW_CMD=True
        )
    # merging
    relog.step("Merging")
    if len(instances) > 1:
        cdds = [COV_DATABASE.replace('.cdd', "_%d.cdd" % k) for k in range(len(instances))]
        executor.sh_exec(
            "covered merge -o %s %s" % (COV_DATABASE, ' '.join(cdds)),
            COV_LOG,
            "a+",
            MAX_TIMEOUT=240,
            SHOW_CMD=True
        )
    # reporting
    relog.step("Generating report")
    executor.sh_exec(
        "covered report %s" % COV_DATABASE,
        COV_REPORT,
        MAX_TIMEOUT=30,
        SHOW_CMD=False
    )

#!/usr/bin/env python3
import os
import sys

from pathlib import Path
from mako.template import Template

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.relog as relog
import common.executor as executor
import common.verilog as verilog

from common.read_sources import resolve_includes


# create temporary directory
DEFAULT_TMPDIR = utils.get_tmp_folder()
SCORE_SCRIPT = os.path.join(DEFAULT_TMPDIR, "score_%d.cmd")
COV_DATABASE = os.path.join(DEFAULT_TMPDIR, "coverage.cdd")
COV_REPORT = os.path.join(DEFAULT_TMPDIR, "coverage.rpt")
COV_LOG = os.path.join(DEFAULT_TMPDIR, "coverage.log")
DB_LIST = os.path.join(DEFAULT_TMPDIR, "db.list")

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))


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
    # generate data
    modules = PARAMS["COV_MODULES"][0].split(" ") if "COV_MODULES" in PARAMS else ["top"]
    instances = verilog.find_instances(PARAMS["TOP_MODULE"])
    top_module, *_ = verilog.find_modules(PARAMS["TOP_MODULE"])[0]
    instances = [(mod, instance) for mod, pa, instance, po in instances if mod in modules]
    generation = 3 if any(["SYS" in m for m in MIMES]) else 2
    excludes = PARAMS["IP_MODULES"][0].split(" ") if "IP_MODULES" in PARAMS else []
    # generate scripts
    if instances:
        for k, instance in enumerate(instances):
            data = {
                "modules": modules,
                "instance": instance,
                "generation": generation,
                "excludes": excludes,
                "includes": INCLUDE_DIRS,
                "files": FILES,
                "vcd": WAVE,
                "top": top_module
            }
            # generate command file
            _tmp = Template(filename=os.path.join(TOOLS_DIR, "./score.cmd.mako"))
            with open(SCORE_SCRIPT % k, "w+") as fp:
                fp.write(_tmp.render_unicode(**data))
        return len(instances)
    else:
        data = {
            "modules": modules,
            "instance": "",
            "generation": generation,
            "excludes": excludes,
            "includes": INCLUDE_DIRS,
            "files": FILES,
            "vcd": WAVE,
            "top": top_module
        }
        # generate command file
        _tmp = Template(filename=os.path.join(TOOLS_DIR, "./score.cmd.mako"))
        with open(SCORE_SCRIPT % 0, "w+") as fp:
            fp.write(_tmp.render_unicode(**data))
    return 1


def main(files, PARAMS):
    # top module
    top = "tb"
    if os.path.isfile(PARAMS["TOP_MODULE"]):
        top, _, _, _ = verilog.find_modules(PARAMS["TOP_MODULE"])[0]
    # generate script to load files and add parameters
    n_i = prepare(files, PARAMS)
    # scoring
    relog.step("Scoring simulations")
    for k in range(n_i):
        COV_K_DATABASE = COV_DATABASE.replace(".cdd", "_%d.cdd" % k)
        executor.sh_exec(
            "covered score -f %s -o %s"
            % (SCORE_SCRIPT % k, COV_K_DATABASE),
            COV_LOG,
            mode="a+",
            MAX_TIMEOUT=300,
            SHOW_CMD=True,
        )
    # register dbs
    with open(DB_LIST, "w+") as list:
        list.writelines([
            COV_DATABASE.replace(".cdd", "_%d.cdd" % k) for k in range(n_i)
        ])
    # merging into first db
    if n_i > 1:
        relog.step("Merging")
        executor.sh_exec(
            "covered merge -f %s" % DB_LIST,
            COV_LOG,
            "a+",
            MAX_TIMEOUT=240,
            SHOW_CMD=True,
        )
    # reporting
    relog.step("Generating report")
    executor.sh_exec(
        "covered report -m ltcfram -d s %s" % COV_DATABASE.replace(".cdd", "_0.cdd"), COV_REPORT, MAX_TIMEOUT=30, SHOW_CMD=False
    )
    return relog.get_stats(COV_LOG)


if __name__ == "__main__":
    files, params = utils.get_sources(relog.filter_stream(sys.stdin), None)
    main(files, params)

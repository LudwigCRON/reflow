#!/usr/bin/env python3
import os
import sys
import argparse

from mako.template import Template

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.relog as relog
import common.executor as executor


DEFAULT_TMPDIR = utils.get_tmp_folder()
SYNTH_LOG      = os.path.join(DEFAULT_TMPDIR, "synthesis.log")
SYNTH_SCRIPT   = os.path.join(DEFAULT_TMPDIR, "synthesis.ys")
IGNORED        = ["packages/log.vh"]
EXTENSIONS     = {
    "verilog": "v",
    "spice": "sp"
}

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))


def prepare(files, params):
    relog.step("Preparation")
    os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
    with open(SYNTH_SCRIPT, "w+") as fp:
        for file, mime in files:
            # code files not ignored
            if not any([ign in file for ign in IGNORED]):
                if mime == "VERILOG":
                    fp.write("read_verilog %s\n" % file)
                elif mime == "LIBERTY":
                    fp.write("read_liberty %s\n" % file)


def run():
    relog.step("Running synthesis")
    executor.sh_exec("yosys %s" % SYNTH_SCRIPT, SYNTH_LOG, MAX_TIMEOUT=300)


def main(files, params, format: str = "verilog", top: str = None, ):
    prepare(files, params)
    # fill mako template
    ext = EXTENSIONS.get(format)
    if top is None:
        top = params.get("TOP_MODULE")
    data = {
        "top_module": top,
        "techno": os.environ["TECH_LIB"],
        "netlist": "%s_after_synthesis.%s" % (top, ext),
        "format": format
    }
    # generate yosys script
    relog.step("Merging synthesis files")
    _tmp = Template(filename=os.path.join(TOOLS_DIR, "./extra.ys.mako"))
    with open(SYNTH_SCRIPT, "a+") as fp:
        fp.write(_tmp.render_unicode(**data))
    run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--format", help="exported file format", default="verilog")
    parser.add_argument("-t", "--top", help="top module", default=None)
    args = parser.parse_args()
    # create the list of sources
    files, params = utils.get_sources(relog.filter_stream(sys.stdin))
    main(files, params, args.format, args.top)

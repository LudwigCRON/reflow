#!/usr/bin/env python3
import os
import sys
import logging
import argparse
import tools.common.utils as utils
import tools.common.executor as executor
from tools.common.read_sources import get_type
from mako.template import Template

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

DEFAULT_TMPDIR = os.path.join(os.getcwd(), ".tmp_sim")
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))

IGNORED = ["packages/log.vh"]
EXTENSIONS = {
    "verilog": "v",
    "spice": "sp"
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--format", help="exported file format", default="verilog")
    parser.add_argument("-t", "--top", help="top module", default="sar")
    cli_args = parser.parse_args()
    logging.info("[1/3] Listing files")
    # create temporary directory
    os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
    SYNTH_LOG    = os.path.join(DEFAULT_TMPDIR, "synthesis.log")
    SYNTH_SCRIPT = os.path.join(DEFAULT_TMPDIR, "synthesis.ys")
    # create the list of sources
    PARAMS, MIMES, SRCS = utils.get_sources(utils.filter_stream(sys.stdin))
    with open(SYNTH_SCRIPT, "w+") as fp:
        for line in SRCS:
            # code files not ignored
            if not any([ign in line for ign in IGNORED]):
                mime = get_type(line)
                if mime == "VERILOG":
                    fp.write(f"read_verilog {line}\n")
                elif mime == "LIBERTY":
                    fp.write(f"read_liberty {line}\n")
    # get top of the hierarchy
    ext = EXTENSIONS.get(cli_args.format)
    data = {
        "top_module": cli_args.top,
        "techno": os.getenv("TECH_LIB"),
        "netlist": f"{cli_args.top}_after_synthesis.{ext}",
        "format": cli_args.format
    }
    # generate yosys script
    logging.info("[2/3] Merging synthesis files")
    _tmp = Template(
        filename=os.path.join(TOOL_DIR, "extra.ys.mako"))
    with open(SYNTH_SCRIPT, "a+") as fp:
        fp.write(_tmp.render_unicode(**data))
    # run synthesis
    logging.info("[3/3] Running synthesis")
    executor.sh_exec(f"yosys {SYNTH_SCRIPT}", SYNTH_LOG, MAX_TIMEOUT=300)

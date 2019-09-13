#!/usr/bin/env python3
import os
import sys
import logging
import tools.common.utils as utils
import tools.common.executor as executor
from tools.common.read_files import get_type, find_modules
from mako.template import Template

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

DEFAULT_TMPDIR = os.path.join(os.getcwd(), ".tmp_sim")
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    logging.info("[1/4] Listing files")
    # create temporary directory
    os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
    COV_DATABASE = os.path.join(DEFAULT_TMPDIR, "coverage.cdd")
    COV_REPORT   = os.path.join(DEFAULT_TMPDIR, "coverage.rpt")
    COV_LOG      = os.path.join(DEFAULT_TMPDIR, "coverage.log")
    SRCS         = os.path.join(DEFAULT_TMPDIR, "cov-srcs.list")
    WAVE         = os.path.join(DEFAULT_TMPDIR, "run.lxt")
    # create the list of sources
    PARAMS, MIMES = utils.get_sources(utils.filter_stream(sys.stdin), SRCS, prefix="-v ")
    # top module
    top = PARAMS["TOP_MODULE"] if "TOP_MODULE" in PARAMS else "tb"
    if os.path.isfile(top):
        top, _, _ = find_modules(top)[0]
    # give the module to cover
    _t = PARAMS["COV_MODULES"][0] if "COV_MODULES" in PARAMS else "tb"
    # exclude (IP_MODULES -> -e)
    _e = PARAMS["IP_MODULES"][0].split(' ') if "IP_MODULES" in PARAMS else []
    with open(SRCS, "a+") as fp:
        for module in _e:
            fp.write(f"-e {module}\n")
    # viewer only
    if "--view" in sys.argv:
        # scoring
        logging.info("[2/4] Merging")
        logging.info("[3/4] Generating report")
        executor.sh_exec(f"covered report {COV_DATABASE}", COV_REPORT, MAX_TIMEOUT=30, SHOW_CMD=False)
        logging.info("[4/4] Opening GUI")
        os.system(f"covered report -view {COV_DATABASE}")
    else:
        # running
        logging.info("[2/4] Running simulations")
        executor.sh_exec(f"covered score -g 3 -ep -S -t {top} -i {top}.{_t} -f {SRCS} -lxt {WAVE} -o {COV_DATABASE}", COV_LOG, MAX_TIMEOUT=300, SHOW_CMD=True)
        # scoring
        logging.info("[3/4] Merging")
        #executor.sh_exec(f"covered score -cdd {COV_DATABASE} -vcd {WAVE}", COV_LOG, "a+", MAX_TIMEOUT=240, SHOW_CMD=True)
        # reporting
        logging.info("[4/4] Generating report")
        executor.sh_exec(f"covered report {COV_DATABASE}", COV_REPORT, MAX_TIMEOUT=30, SHOW_CMD=False)
#!/usr/bin/env python3
import os
import sys
import logging
import tools.common.utils as utils
import tools.common.executor as executor
from tools.common.read_sources import get_type, find_modules, find_instances, resolve_includes
from mako.template import Template

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

DEFAULT_TMPDIR = os.path.join(os.getcwd(), ".tmp_sim")
TOOL_DIR       = os.path.dirname(os.path.abspath(__file__))
WAVE_FORMAT    = "vcd"

if __name__ == "__main__":
    logging.info("[1/4] Listing files")
    # create temporary directory
    os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
    COV_DATABASE = os.path.join(DEFAULT_TMPDIR, "coverage.cdd")
    COV_REPORT   = os.path.join(DEFAULT_TMPDIR, "coverage.rpt")
    COV_LOG      = os.path.join(DEFAULT_TMPDIR, "coverage.log")
    SRCS         = os.path.join(DEFAULT_TMPDIR, "cov_srcs.list")
    WAVE         = os.path.join(DEFAULT_TMPDIR, f"run.{WAVE_FORMAT}")
    # create the list of sources
    PARAMS, MIMES, FILES = utils.get_sources(utils.filter_stream(sys.stdin), None)
    INCLUDE_DIRS = resolve_includes(FILES)
    instances = find_instances(PARAMS["TOP_MODULE"])
    excludes = PARAMS["IP_MODULES"][0].split(' ') if "IP_MODULES" in PARAMS else []
    generation = 3 if any(["SYS" in m for m in MIMES]) else 2
    with open(SRCS, "w+") as fp:
        for include_dir in INCLUDE_DIRS:
            fp.write(f"-I {include_dir}\n")
        for file in FILES[::-1]:
            fp.write(f"-v {file}\n")
        for module in excludes:
            fp.write(f"-e {module}\n")
        fp.write(f"-{WAVE_FORMAT} {WAVE}\n")
        fp.write("-Wignore\n")
    # top module
    top = "tb"
    if os.path.isfile(PARAMS["TOP_MODULE"]):
        top, _, _, _ = find_modules(PARAMS["TOP_MODULE"])[0]
    # give the module to cover
    modules = PARAMS["COV_MODULES"][0].split(' ') if "COV_MODULES" in PARAMS else [top]
    instances = [(module, instance) for module, instance in instances if module in modules]
    # scoring
    logging.info("[2/4] Scoring simulations")
    if len(instances) > 1:
        for k, i in enumerate(instances):
            module, instance = i
            COV_K_DATABASE = COV_DATABASE.replace('.cdd', f"_{k}.cdd")
            executor.sh_exec(f"covered score -t {module} -i {top}.{instance} -f {SRCS} -g {generation} -o {COV_K_DATABASE}", COV_LOG, mode="a+", MAX_TIMEOUT=300, SHOW_CMD=True)
    else:
        executor.sh_exec(f"covered score -t {top} -f {SRCS} -g {generation} -o {COV_DATABASE}", COV_LOG, mode="a+", MAX_TIMEOUT=300, SHOW_CMD=True)
    # mergin
    logging.info("[3/4] Merging")
    if len(instances) > 1:
        cdds = [COV_DATABASE.replace('.cdd', f"_{k}.cdd") for k in range(len(instances))]
        executor.sh_exec(f"covered merge -o {COV_DATABASE} {' '.join(cdds)}", COV_LOG, "a+", MAX_TIMEOUT=240, SHOW_CMD=True)
    # reporting
    logging.info("[4/4] Generating report")
    executor.sh_exec(f"covered report {COV_DATABASE}", COV_REPORT, MAX_TIMEOUT=30, SHOW_CMD=False)
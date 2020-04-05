#!/usr/bin/env python3
# coding: utf-8

import os
import sys

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.relog as relog
import common.executor as executor


DEFAULT_TMPDIR = utils.get_tmp_folder()
SIM_LOG        = None  # os.path.join(DEFAULT_TMPDIR, "sim.log")


def run(asc: str):
    relog.step("Running simulation")
    os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
    # use the appropriate program
    # depending on the platform
    if sys.platform == "darwin":
        ltspice = "/Applications/LTspice.app/Contents/MacOS/LTspice"
    elif sys.platform == "unix":
        ltspice = "wine XVIIx64.exe"
    else:
        ltspice = "XVIIx64.exe"
    executor.sh_exec("%s -run %s" % (ltspice, asc), SIM_LOG, MAX_TIMEOUT=300)
    return 0, 0  # relog.get_stats(SIM_LOG)


def main(files, params):
    top = params.get("TOP_MODULE")
    print(top)
    if not top:
        for file in files:
            print(file)
            if file.endswidth(".asc"):
                top = file
                break
    if top:
        stats = run(top)
        return stats
    else:
        relog.error("No asc file detected")
    return 0, 0


if __name__ == "__main__":
    files, params = utils.get_sources(relog.filter_stream(sys.stdin), None)
    main(files, params)

#!/usr/bin/env python3
# coding: utf-8

import io
import os
import sys
import shutil

from pathlib import Path

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.relog as relog
import common.executor as executor


DEFAULT_TMPDIR = utils.get_tmp_folder()
SIM_LOG = None


def run(raw: str):
    relog.step("Open waveforms")
    os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
    # use the appropriate program
    # depending on the platform
    if sys.platform == "darwin":
        ltspice = "/Applications/LTspice.app/Contents/MacOS/LTspice"
    elif sys.platform == "unix" or "linux" in sys.platform:
        ltspice = 'wine "%s"' % utils.wine.locate("XVIIx64.exe")
        window_path = io.StringIO()
        executor.sh_exec("winepath -w '%s'" % raw, window_path, NOERR=True, NOOUT=True)
        raw = window_path.getvalue().strip().replace("\\", "/")
    else:
        ltspice = "XVIIx64.exe"
    # start the simulation
    print(raw)
    executor.sh_exec("%s %s" % (ltspice, raw), SIM_LOG, NOERR=True)
    return 0, 0  # relog.get_stats(SIM_LOG)


def find_raw():
    for file in Path(os.path.dirname(DEFAULT_TMPDIR)).rglob("*.raw"):
        if ".op.raw" not in str(file):
            return file
    return None


def main(format):
    file = find_raw()
    if file:
        stats = run(file)
        return stats
    relog.error("No raw file detected")
    return 0, 0


if __name__ == "__main__":
    main("raw")

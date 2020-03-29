#!/usr/bin/env python3
# coding: utf-8

import os
import sys

from pathlib import Path

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.relog as relog
import common.executor as executor


DEFAULT_TMPDIR = utils.get_tmp_folder()


def main(format: str = "vcd"):
    relog.step("Search waveforms")
    vcd_path = None
    for path in Path(DEFAULT_TMPDIR).rglob("**/*.%s" % format):
        vcd_path = path
        break
    print(vcd_path)
    relog.step("Open waveforms")
    if sys.platform == "linux" or sys.platform == "linux2":
        # linux
        executor.sh_exec("gtkwave '%s'" % vcd_path, MAX_TIMEOUT=-1, SHELL=True)
    elif sys.platform == "darwin":
        # OS X
        executor.sh_exec("open -a gtkwave '%s'" % vcd_path, MAX_TIMEOUT=-1, SHELL=False)
    elif sys.platform == "win32":
        # Windows...
        executor.sh_exec("gtkwave '%s'" % vcd_path, MAX_TIMEOUT=-1, SHELL=True)
    else:
        relog.error("Unknown operating system")


if __name__ == "__main__":
    main(sys.argv[1])

#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import time
import shutil

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.relog as relog
import common.executor as executor


DEFAULT_TMPDIR = utils.get_tmp_folder()
SIM_LOG = None


def is_file_timeout(file: str, start: int, max: int = 720, shall_exist: bool = True):
    file_exists = os.path.exists(file)
    return time.time() - start < max and (file_exists == shall_exist)


def simulation_finished(log_file: str):
    with open(log_file, "r+") as fp:
        for line in fp:
            l = line.lower().replace("\x00", "")
            if "total elapsed time:" in l:
                return True
    return False


def watch_log(log_file: str):
    # remove previous execution log file
    if os.path.exists(log_file):
        os.remove(log_file)
    t_start = time.time()
    # wait log file created
    while is_file_timeout(log_file, t_start, max=15, shall_exist=False):
        time.sleep(1)
    if not os.path.exists(log_file):
        relog.error("No simulation log file found")
        return False
    # wait the end of the simulation
    count = 0
    while not simulation_finished(log_file) and count < 2500:
        time.sleep(1)
        count += 1
    return count < 500


def run(asc: str):
    relog.step("Running simulation")
    os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
    # use the appropriate program
    # depending on the platform
    log = asc.replace(".asc", ".log")
    if sys.platform == "darwin":
        ltspice = "/Applications/LTspice.app/Contents/MacOS/LTspice"
    elif sys.platform == "unix" or "linux" in sys.platform:
        ltspice = 'wine "%s"' % utils.wine.locate("XVIIx64.exe")
        asc = "z:%s" % asc
    else:
        ltspice = "XVIIx64.exe"
    # start the simulation
    gen = executor.ish_exec('%s -Run "%s"' % (ltspice, asc), SIM_LOG, MAX_TIMEOUT=300)
    proc = next(gen)
    # watch the log file to determine when
    # the simulation ends
    sim_done = watch_log(log)
    if proc:
        proc.kill()
    return 0, not sim_done  # relog.get_stats(SIM_LOG)


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

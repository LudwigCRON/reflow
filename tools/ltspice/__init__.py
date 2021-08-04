#!/usr/bin/env python3
# coding: utf-8

import os
import sys
from pathlib import Path

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.read_sources as read_sources
import common.utils.doit as doit_helper
from doit.loader import create_after
from doit.action import CmdAction, PythonAction
from common.utils.db import Vault


var_vault = Vault()


def update_vars():
    var_vault.WORK_DIR = utils.get_tmp_folder()
    var_vault.PROJECT_DIR = os.getenv("PROJECT_DIR")
    var_vault.ASC = None


update_vars()


def task_vars_db():
    """
    set needed global variables
    """

    return {"actions": [(update_vars,)], "title": doit_helper.no_title}


@create_after(executed="vars_db")
def task__ltspice_sim_prepare():
    """
    detect the path of LTspice and
    normalize the path of the raw file
    """

    def run(task):
        # get the top asc file
        files, params = read_sources.read_from(os.getenv("CURRENT_DIR"), no_logger=True)
        task.file_dep.update([f for f, m in files])
        var_vault.ASC = utils.normpath(params.get("TOP_MODULE"))
        if not var_vault.ASC:
            sfile = next(
                (
                    str(file)
                    for file, _ in files
                    if sfile.endswith(".asc") and any(["top" in sfile])
                )
            )
            var_vault.ASC = utils.normpath(os.path.join(os.getenv("CURRENT_DIR"), sfile))
        # add post sim script support
        var_vault.POST_SIM = params.get("POST_SIM")
        # use the appropriate program
        # depending on the platform
        if sys.platform == "darwin":
            var_vault.LTSPICE = "/Applications/LTspice.app/Contents/MacOS/LTspice"
            return {"asc": var_vault.ASC}
        elif sys.platform == "unix" or "linux" in sys.platform:
            var_vault.LTSPICE = 'wine64 "%s"' % utils.wine.locate("XVIIx64.exe")
            task.actions.append(
                CmdAction("winepath -w '%s'" % var_vault.ASC, save_out="asc")
            )
        else:
            var_vault.LTSPICE = "XVIIx64.exe"
            return {"asc": var_vault.ASC}

    return {
        "actions": [run],
        "file_dep": [],
        "title": doit_helper.no_title,
    }


@create_after(executed="_ltspice_sim_prepare")
def task_sim():
    """
    use the internal ltspice viewer to
    open saved simulation waveform in raw format
    """

    def run(task):
        asc = task.options.get("asc").strip()
        task.file_dep.update([asc])
        task.targets.append(asc.replace(".asc", ".log"))
        task.actions.append(
            CmdAction(
                '%s -b -Run "%s"' % (var_vault.LTSPICE, asc),
                cwd=var_vault.WORK_DIR,
                shell=True,
            )
        )
        if var_vault.POST_SIM:
            raw = asc.replace(".asc", ".raw")
            task.actions.append(
                CmdAction(
                    "%s %s" % (" ".join(var_vault.POST_SIM), raw),
                    cwd=os.getenv("CURRENT_DIR"),
                    shell=True,
                )
            )

    return {
        "actions": [run],
        "title": doit_helper.constant_title("Sim"),
        "getargs": {"asc": ("_ltspice_sim_prepare", "asc")},
        "verbosity": 2,
    }

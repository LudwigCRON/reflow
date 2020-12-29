#!/usr/bin/env python3
# coding: utf-8

import os
import sys

from pathlib import Path

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.utils.doit as doit_helper
from doit.action import CmdAction
from doit.loader import create_after
from common.utils.db import Vault


var_vault = Vault()


def find_raw(directory: str):
    for file in Path(directory).rglob("*.raw"):
        if ".op.raw" not in str(file):
            return utils.normpath(os.path.join(directory, file))
    return None


def update_vars():
    var_vault.WORK_DIR = utils.get_tmp_folder()
    var_vault.PROJECT_DIR = os.getenv("PROJECT_DIR")
    var_vault.RAW = find_raw(os.path.dirname(var_vault.WORK_DIR))


update_vars()


def task_vars_db():
    """
    set needed global variables
    """

    return {"actions": [(update_vars,)], "title": doit_helper.no_title}


@create_after(executed="vars_db")
def task__ltspice_view_prepare():
    """
    detect the path of LTspice and
    normalize the path of the raw file
    """

    def run(task):
        # use the appropriate program
        # depending on the platform
        if sys.platform == "darwin":
            var_vault.LTSPICE = "/Applications/LTspice.app/Contents/MacOS/LTspice"
            return {"raw": var_vault.RAW}
        elif sys.platform == "unix" or "linux" in sys.platform:
            var_vault.LTSPICE = 'wine64 "%s"' % utils.wine.locate("XVIIx64.exe")
            task.actions.append(
                CmdAction("winepath -w '%s'" % var_vault.RAW, save_out="raw")
            )
        else:
            var_vault.LTSPICE = "XVIIx64.exe"
            return {"raw": var_vault.RAW}

    return {
        "actions": [run],
        "file_dep": [var_vault.RAW],
        "title": doit_helper.no_title,
    }


@create_after(executed="_ltspice_view_prepare")
def task_view_sim():
    """
    use the internal ltspice viewer to
    open saved simulation waveform in raw format
    """

    def run(task):
        raw = task.options.get("raw").strip()
        task.actions.append(
            CmdAction(
                "%s %s" % (var_vault.LTSPICE, raw), cwd=var_vault.WORK_DIR, shell=True
            )
        )

    return {
        "actions": [run],
        "file_dep": [var_vault.RAW],
        "title": doit_helper.constant_title("View"),
        "getargs": {"raw": ("_ltspice_view_prepare", "raw")},
    }

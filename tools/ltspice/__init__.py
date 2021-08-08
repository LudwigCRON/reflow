#!/usr/bin/env python3
# coding: utf-8

import os
import sys

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.read_sources as read_sources
import common.utils.doit as doit_helper
from doit.loader import create_after
from doit.action import CmdAction
from common.utils.db import Vault


var_vault = Vault()


def update_vars():
    var_vault.WORK_DIR = utils.get_tmp_folder()
    var_vault.PROJECT_DIR = os.getenv("PROJECT_DIR")
    var_vault.ASC = None


update_vars()


def task__ltspice_sim_prepare():
    """
    detect the path of LTspice and asc files
    and normalize the path of the raw file
    """

    update_vars()

    def run(task):
        # get the top asc file
        files, params = read_sources.read_from(os.getenv("CURRENT_DIR"), no_logger=True)
        task.file_dep.update([f for f, _ in files])
        var_vault.ASC = utils.normpath(params.get("TOP_MODULE"))
        if not var_vault.ASC:
            sfile = next(
                (str(file) for file, _ in files if file.endswith(".asc") and "top" in file)
            )
            var_vault.ASC = utils.normpath(os.path.join(os.getenv("CURRENT_DIR"), sfile))
        # add post sim script support
        var_vault.POST_SIM = params.get("POST_SIM")
        # use the appropriate program
        # depending on the platform
        if sys.platform == "darwin":
            var_vault.LTSPICE = "/Applications/LTspice.app/Contents/MacOS/LTspice"
        elif sys.platform == "unix" or "linux" in sys.platform:
            var_vault.LTSPICE = (
                'WINEDEBUG=fixme-all,warn-all wine64 "%s"'
                % utils.wine.locate("XVIIx64.exe")
            )
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


def task_ltspice_sim():
    """
    execute an LTSpice simulation in batch mode
    """

    def run(task):
        asc_path = var_vault.ASC
        if task.options.get("asc"):
            asc_path = task.options.get("asc").strip()
        task.file_dep.update([var_vault.ASC])
        task.targets.append(var_vault.ASC.replace(".asc", ".log"))
        task.actions.append(
            CmdAction(
                '%s -b -Run "%s"' % (var_vault.LTSPICE, asc_path),
                cwd=var_vault.WORK_DIR,
                shell=True,
            )
        )
        if var_vault.POST_SIM:
            raw = var_vault.ASC.replace(".asc", ".raw")
            sim_dir = utils.normpath(os.path.dirname(var_vault.ASC))
            task.actions.append(
                CmdAction(
                    "%s '%s'" % (" ".join(var_vault.POST_SIM), raw),
                    cwd=sim_dir,
                    shell=True,
                )
            )

    return {
        "actions": [run],
        "title": doit_helper.constant_title("Sim"),
        "getargs": {"asc": ("ltspice_sim_prepare", "asc")},
        "task_dep": ["ltspice_sim_prepare"],
        "verbosity": 2,
    }


def task_ltspice_view_sim():
    """
    open saved simulation waveform in LTSpice embedded viewer
    """

    def run(task):
        asc_path = var_vault.ASC
        if task.options.get("asc"):
            asc_path = task.options.get("asc").strip()
        raw_path = asc_path.replace(".asc", ".raw")
        task.file_dep.update([var_vault.ASC.replace(".asc", ".raw")])
        task.actions.append(
            CmdAction(
                "%s '%s'" % (var_vault.LTSPICE, raw_path),
                cwd=var_vault.WORK_DIR,
                shell=True,
            )
        )

    return {
        "actions": [run],
        "title": doit_helper.constant_title("View"),
        "getargs": {"asc": ("ltspice_sim_prepare", "asc")},
        "task_dep": ["ltspice_sim_prepare"],
        "verbosity": 2,
    }

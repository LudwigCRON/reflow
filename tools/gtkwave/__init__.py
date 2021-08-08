#!/usr/bin/env python3
# coding: utf-8

import os
import sys

from pathlib import Path

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.utils.doit as doit_helper
import common.config as config
from doit.action import CmdAction


def task_gtkwave_view_sim():
    """
    display digital waveforms
    """

    TOOLS_DIR = utils.normpath(os.path.dirname(os.path.abspath(__file__)))
    TOOLS_CFG = os.path.join(TOOLS_DIR, "tools.config")
    DEFAULT_TMPDIR = utils.get_tmp_folder()

    def run(task):
        vcd_path, view = None, None
        # search for waveform file
        for path in Path(DEFAULT_TMPDIR).rglob(
            "**/*.%s" % config.vault.gtkwave.get("format", "vcd")
        ):
            vcd_path = str(path)
            break
        # search for gtkwave view
        for path in Path(os.path.dirname(DEFAULT_TMPDIR)).rglob("**/*.gtkw"):
            view = str(path)
            break
        file_to_read = view if view else vcd_path
        if sys.platform in ["linux", "linux2", "win32"]:
            cmd = "gtkwave '%s'"
        elif sys.platform in ["darwin"]:
            cmd = "open -a gtkwave '%s'"
        # register actions
        task.actions.append(CmdAction(cmd % file_to_read))
        task.file_dep.add(file_to_read)

    return {
        "actions": [run],
        "file_dep": [],
        "title": doit_helper.task_name_as_title,
    }

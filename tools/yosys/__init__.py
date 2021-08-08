#!/usr/bin/env python3
import os
import re
import sys

from mako.template import Template

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.config as config
import common.utils.doit as doit_helper
import common.read_sources as read_sources

from doit import create_after
from common.utils.db import Vault
from doit.action import CmdAction, PythonAction

var_vault = Vault()


def evaluate_bash_var(txt: str):
    RE_BASH_VAR = r"\$((?!\$)([\w_]+)|{([\w_]+)})"
    t = txt
    for match in re.finditer(RE_BASH_VAR, txt):
        var_txt, _, var_name = match.groups()
        if os.getenv(var_name):
            t = t.replace("$%s" % var_txt, os.getenv(var_name))
    return t


def generate_cmd(files, params):
    # fill mako template
    ext = var_vault.EXTENSIONS.get(var_vault.FORMAT)
    top = params.get("SYNTH_MODULE")[-1]
    data = {
        "top_module": top,
        "techno": evaluate_bash_var(os.environ["TECH_LIB"]),
        "files": files,
        "params": params,
        "includes": read_sources.resolve_includes(files),
        "work_dir": var_vault.WORK_DIR,
        "netlist": "%s_after_synthesis.%s" % (top, ext),
        "format": var_vault.FORMAT,
    }
    data.update(os.environ)
    # generate yosys script
    _tmp = Template(filename=var_vault.TEMPLATE_SCRIPT)
    with open(var_vault.SYNTH_SCRIPT, "w+") as fp:
        fp.write(_tmp.render_unicode(**data))


def update_vars():
    var_vault.WORK_DIR = utils.get_tmp_folder()
    var_vault.PROJECT_DIR = os.getenv("PROJECT_DIR")
    var_vault.SYNTH_SCRIPT = utils.normpath(
        os.path.join(var_vault.WORK_DIR, "synthesis.ys")
    )
    var_vault.SYNTH_LOG = utils.normpath(os.path.join(var_vault.WORK_DIR, "synthesis.log"))
    var_vault.IGNORED = ["packages/log.vh"]
    var_vault.EXTENSIONS = {"verilog": "v", "spice": "sp"}
    var_vault.TOOLS_DIR = utils.normpath(os.path.dirname(os.path.abspath(__file__)))
    var_vault.TEMPLATE_SCRIPT = utils.normpath(
        os.path.join(var_vault.TOOLS_DIR, "script.ys.mako")
    )
    var_vault.FORMAT = config.vault.yosys.get("format", "verilog")


# needed to call it during loading of the tool
# to have correct file dependencies and targets
update_vars()


def task__yosys_synth_prepare():
    """
    create the list of files needed
    list include dirs
    list parameters and define
    """

    update_vars()

    def run(task):
        files, params = read_sources.read_from(os.getenv("CURRENT_DIR"), no_logger=False)
        task.file_dep.update([f for f, m in files])
        task.actions.append(PythonAction(generate_cmd, [files, params]))

    return {
        "actions": [run],
        "file_dep": [],
        "targets": [var_vault.SYNTH_SCRIPT],
        "title": doit_helper.constant_title("Prepare"),
        "clean": [doit_helper.clean_targets],
    }


def task_yosys_synth():

    return {
        "actions": [
            CmdAction("yosys %s" % var_vault.SYNTH_SCRIPT, save_out="log"),
            (doit_helper.save_log, (var_vault.SYNTH_LOG,)),
        ],
        "file_dep": [var_vault.SYNTH_SCRIPT],
        "targets": [var_vault.SYNTH_LOG],
        "title": doit_helper.task_name_as_title,
        "clean": [doit_helper.clean_targets],
    }

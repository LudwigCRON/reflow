#!/usr/bin/env python3
import os
import sys

from pathlib import Path
from mako.template import Template
from numpy.core.fromnumeric import var

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.config as config
import common.verilog as verilog
import common.read_sources as read_sources
import common.utils.doit as doit_helper

from doit import create_after
from doit.action import CmdAction, PythonAction
from common.utils.db import Vault


var_vault = Vault()


def find_wave(fmt):
    directory = os.path.dirname(var_vault.WORK_DIR)
    for wavefile in Path(directory).rglob("**/*.%s" % fmt):
        return str(wavefile)


def update_vars():
    var_vault.WORK_DIR = utils.get_tmp_folder()
    var_vault.SCORE_SCRIPT = utils.normpath(
        os.path.join(var_vault.WORK_DIR, "score_%d.cmd")
    )
    var_vault.SCORE_LOG = utils.normpath(os.path.join(var_vault.WORK_DIR, "score_%d.log"))
    var_vault.COV_DATABASE = utils.normpath(
        os.path.join(var_vault.WORK_DIR, "coverage.cdd")
    )
    var_vault.COV_REPORT = utils.normpath(os.path.join(var_vault.WORK_DIR, "coverage.rpt"))
    var_vault.COV_LOG = utils.normpath(os.path.join(var_vault.WORK_DIR, "coverage.log"))
    var_vault.DB_LIST = utils.normpath(os.path.join(var_vault.WORK_DIR, "db.list"))
    var_vault.TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
    var_vault.WAVE_FORMAT = config.vault.covered.get("format", "vcd")
    var_vault.WAVE = find_wave(var_vault.WAVE_FORMAT)


# needed to call it during loading of the tool
# to have correct file dependencies and targets
update_vars()


def generate_cmd(files, params):
    # prepare data for cmd template
    # files to be scored, includes, top module/instance
    # module to be excluded
    verilog_files = [
        f for f, m in files if m in ["VERILOG", "SYSTEM_VERILOG", "VERILOG_AMS"]
    ]
    includes = read_sources.resolve_includes(verilog_files, with_pkg=True)
    modules = params["COV_MODULES"] if "COV_MODULES" in params else ["top"]
    instances = verilog.find_instances(params["TOP_MODULE"])
    top_module, *_ = verilog.find_modules(params["TOP_MODULE"])[0]
    instances = [(mod, instance) for mod, _, instance, _ in instances if mod in modules]
    excludes = params["IP_MODULES"] if "IP_MODULES" in params else []
    generation = 3
    if not instances:
        instances = [""]
    data = {
        "modules": modules,
        "instance": "",
        "generation": generation,
        "excludes": excludes,
        "includes": includes,
        "files": verilog_files,
        "vcd": var_vault.WAVE,
        "top": top_module,
    }
    for k, instance in enumerate(instances):
        data.update({"instance": instance})
        # generate command file
        _tmp = Template(filename=os.path.join(var_vault.TOOLS_DIR, "score.cmd.mako"))
        with open(var_vault.SCORE_SCRIPT % k, "w+") as fp:
            fp.write(_tmp.render_unicode(**data))


def task__covered_cov_prepare():
    """
    generated needed score command scripts
    """
    update_vars()

    def run(task):
        files, params = read_sources.read_from(os.getenv("CURRENT_DIR"))
        task.file_dep.update([f for f, _ in files])
        task.file_dep.update([var_vault.WAVE])
        task.actions.append(PythonAction(generate_cmd, [files, params]))

    return {
        "actions": [run],
        "targets": [var_vault.SCORE_SCRIPT.replace("%d", "*")],
        "title": doit_helper.constant_title("Prepare"),
        "clean": [doit_helper.clean_targets],
    }


def task__covered_cov_score():

    for k, script in enumerate(Path(var_vault.WORK_DIR).rglob("score*.cmd")):
        # prepare subtask
        cov_k_db = var_vault.COV_DATABASE.replace(".cdd", "_%d.cdd" % k)

        def run(task):
            task.actions.append(
                CmdAction(
                    "covered score -f %s -o %s" % (str(script), cov_k_db), save_out="log"
                )
            )
            task.actions.append(
                PythonAction(doit_helper.save_log, (task, var_vault.SCORE_LOG % k))
            )

        yield {
            "name": "score",
            "actions": ["covered score -f %s -o %s" % (str(script), cov_k_db)],
            "file_dep": [str(script)],
            "targets": [cov_k_db],
            "title": doit_helper.constant_title("Scoring %s" % os.path.basename(cov_k_db)),
            "clean": [doit_helper.clean_targets],
        }


def task__covered_cov_merge():
    """
    merge scored databases
    """

    def run(task):
        # register dbs
        n = 0
        with open(var_vault.DB_LIST, "w+") as fp:
            for k, db_file in enumerate(Path(var_vault.WORK_DIR).rglob("*.cdd")):
                fp.write(utils.normpath(db_file) + "\n")
                # register file_dep
                task.file_dep.update([utils.normpath(db_file)])
                n = k
        if n > 1:
            task.actions.append(CmdAction("covered merge -f %s" % var_vault.DB_LIST))

    return {
        "actions": [run],
        "file_dep": [],
        "targets": [var_vault.DB_LIST],
        "title": doit_helper.constant_title("Merge"),
        "clean": [doit_helper.clean_targets],
    }


def task_covered_cov():
    """
    generate reports
    """

    def run(task):
        cov_db = var_vault.COV_DATABASE.replace(".cdd", "_0.cdd")
        task.actions.append(
            CmdAction("covered report -m ltcfram -d s %s" % cov_db, save_out="log")
        )
        task.actions.append(
            PythonAction(doit_helper.save_log, (task, var_vault.COV_REPORT))
        )

    return {
        "actions": [run],
        "file_dep": [var_vault.DB_LIST],
        "targets": [var_vault.COV_REPORT],
        "title": doit_helper.constant_title("Reporting"),
        "clean": [doit_helper.clean_targets],
    }

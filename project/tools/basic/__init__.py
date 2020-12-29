#!/usr/bin/env python3
# coding: utf-8

import os
import sys

from pathlib import Path
from functools import lru_cache

import common.utils as utils
import common.relog as relog
import common.utils.doit as doit_helper
import common.read_batch as read_batch
import common.design_tree as design_tree
import common.read_sources as read_sources


from doit import create_after
from doit.task import dict_to_task
from doit.action import CmdAction, PythonAction
from common.utils.db import Vault
from common.read_batch import SimType


var_vault = Vault()


def task_tree():
    """
    display hierarchy of the design
    """

    def tree(task):
        files, params = read_sources.read_from(os.getenv("CURRENT_DIR"), no_logger=False)
        design_tree.main(files, params)

    return {"actions": [tree], "title": doit_helper.task_name_as_title, "verbosity": 2}


@lru_cache(maxsize=8)
def _batch(batch_path: str):
    batch = read_batch.read_batch(batch_path)
    TMP_DIR = utils.get_tmp_folder("batch")

    for k, rule in enumerate(batch):
        if batch.has_option(rule, "__path__"):
            p = utils.normpath(
                os.path.join(os.getenv("CURRENT_DIR"), batch.get(rule, "__path__"))
            )
            s = eval(batch.get(rule, "__sim_type__"))
            o = utils.normpath(os.path.join(TMP_DIR, rule))
            b = utils.normpath(os.path.join(p, "Batch.list"))
            os.makedirs(o, exist_ok=True)
            # select which simulations should be performed
            batch_options = []
            do_sim, do_cov, do_lint = False, False, False
            # based on batch file selection
            if s in [SimType.SIMULATION, SimType.ALL]:
                do_sim = True
            if s in [SimType.COVERAGE, SimType.ALL]:
                do_cov = True
            if s in [SimType.LINT, SimType.ALL]:
                do_lint = True
            # based on args
            if var_vault.BATCH_TYPE == "sim":
                do_cov = False
                do_lint = False
            elif var_vault.BATCH_TYPE == "cov":
                do_sim = False
                do_lint = False
            elif var_vault.BATCH_TYPE == "lint":
                do_sim = False
                do_cov = False
            if do_sim:
                batch_options.append("sim")
            if do_cov:
                batch_options.append("cov")
            if do_lint:
                batch_options.append("lint")
            # run the simulations
            for batch_option in batch_options:
                if os.path.exists(b):
                    # support batch of batch
                    yield {
                        "name": "%s:%s/%s" % (batch_option, os.path.basename(p), rule),
                        "actions": [
                            CmdAction(
                                "run batch %s" % batch_option,
                                cwd=os.path.dirname(b),
                                env=os.environ.copy(),
                            )
                        ],
                        "title": doit_helper.task_name_as_title,
                        "file_dep": [b],
                        "verbosity": 2,
                    }
                else:
                    # create Sources.list
                    read_batch.create_batch_sources(batch, rule, o)
                    # and then execute the tasks in batch
                    yield {
                        "name": "%s:%s/%s" % (batch_option, os.path.basename(p), rule),
                        "actions": [
                            CmdAction(
                                "run %s" % batch_option, cwd=o, env=os.environ.copy()
                            ),
                        ],
                        "title": doit_helper.task_name_as_title,
                        "file_dep": [os.path.join(o, "Sources.list")],
                        "verbosity": 2,
                    }


def task_batch_prepare():
    """
    generate needed Sources.list for all conditions
    """
    if "batch" in sys.argv:
        idx = sys.argv.index("batch")
        sim_type = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "all"
        var_vault.BATCH_TYPE = sim_type

    def run(task):
        for t in _batch(os.getenv("CURRENT_DIR")):
            task.targets.append(t.get("file_dep"))

    expected_batch = utils.normpath(os.path.join(os.getenv("CURRENT_DIR"), "Batch.list"))

    return {
        "actions": [run],
        "title": doit_helper.no_title,
        "file_dep": [expected_batch],
    }


def task__batch_exec():
    """group of dynamic simulation batch"""

    for t in _batch(os.getenv("CURRENT_DIR")):
        yield t


def task_batch():
    """
    run a batch of simulation listed in Batch.list
    """

    return {
        "actions": None,
        "title": doit_helper.no_title,
        "task_dep": ["_batch_exec"],
        "pos_arg": "type",
        "verbosity": 2,
    }


def task_clean_all():
    """
    remove all working directory
    from the current location
    """

    def remove_doit_db():
        for db in Path(os.getcwd()).rglob("**/.doit.db"):
            os.remove(db)

    return {
        "actions": [(utils.clean_tmp_folder,), (remove_doit_db,)],
        "title": doit_helper.no_title,
        "verbosity": 2,
    }

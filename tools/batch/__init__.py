#!/usr/bin/env python3
# coding: utf-8

import os

from functools import lru_cache
from typing import List

import common.utils as utils
import common.utils.doit as doit_helper
import common.read_batch as read_batch

from doit.action import CmdAction
from common.utils.db import Vault


var_vault = Vault()


@lru_cache(maxsize=8)
def batch(batch_path: str):
    batch = read_batch.read_batch(batch_path)
    TMP_DIR = utils.get_tmp_folder("batch")

    for section in batch.sections():
        work_item = dict(batch.items(section))
        if "__path__" not in work_item:
            continue

        target_dir = utils.normpath(os.path.join(TMP_DIR, section))
        sim_dir = utils.normpath(
            os.path.join(os.getenv("CURRENT_DIR"), work_item.get("__path__"))
        )
        test_path = os.path.join(os.getenv("BATCH_DIR", ""), work_item.get("__path__"))
        batch_path = utils.normpath(os.path.join(sim_dir, "Batch.list"))
        src_path = utils.normpath(os.path.join(target_dir, "Sources.list"))
        os.makedirs(target_dir, exist_ok=True)
        # select which simulations should be performed
        batch_options = []
        # based on batch file selection
        if work_item.get("__sim_type__") in "sim all":
            batch_options.append("sim")
        if work_item.get("__sim_type__") in "cov all":
            batch_options.append("cov")
        if work_item.get("__sim_type__") in "lint all":
            batch_options.append("lint")
        # run the simulations in an isolated env
        sim_env = os.environ.copy()
        sim_env["TOP_BATCH_DIR"] = os.getenv(
            "TOP_BATCH_DIR", os.getenv("BATCH_DIR", os.getenv("CURRENT_DIR"))
        )
        sim_env["BATCH_DIR"] = test_path
        for batch_option in batch_options:
            if os.path.exists(batch_path):
                # support batch of batch
                target_dir = os.path.dirname(batch_path)
                file_dep = [batch_path]
                cmd = "run --continue 'batch+%s+*'"
            else:
                # create Sources.list
                read_batch.create_batch_sources(batch, section, target_dir)
                file_dep = [src_path]
                cmd = "run %s"
            yield {
                "name": "%s+%s+%s" % (batch_option, test_path, section),
                "actions": [
                    CmdAction(cmd % batch_option, cwd=target_dir, env=sim_env),
                ],
                "title": doit_helper.task_name_as_title,
                "file_dep": file_dep,
                "clean": [
                    CmdAction("run clean", cwd=target_dir, env=sim_env),
                    CmdAction("relog clean", cwd=target_dir, env=sim_env),
                ],
                "verbosity": 2,
            }


def task_batch_batch():
    """
    run a batch of simulation listed in Batch.list
    """

    for t in batch(os.getenv("CURRENT_DIR")):
        yield t

#!/usr/bin/env python3
# coding: utf-8

import os
import shutil
import datetime

from pathlib import Path
from typing import Tuple


def normpath(s: str):
    return os.path.normpath(os.path.abspath(s)).replace("\\", "/")


def get_task_dbinfo(task) -> Tuple[str, str]:
    # extract task info to store them in db
    if "+" in task.name:
        task_name, test_path = task.name.split("+")[-2:]
    else:
        test_path = os.path.join(
            os.getenv("BATCH_DIR", ""), os.path.basename(os.getenv("CURRENT_DIR", ""))
        )
        task_name = task.name
    return task_name, test_path


# ==== get working directory ====
def get_tmp_folder(type: str = "sim") -> str:
    """
    get working directory path for a given
    simulation type or use the specified working
    directory via WORK_DIR env. variable
    """
    # to support batch reformat <dir of batch>+<task>+<subdir>
    # into <dir of batch>/<subdir>
    if "+" in type:
        batch_dir, _, subdir = type.split("+", maxsplit=3)
        type = f"{batch_dir}/{subdir}"
    if "WORK_DIR" in os.environ:
        return normpath(os.environ["WORK_DIR"])
    if "WORK_DIR_PREFIX" in os.environ:
        return normpath(
            os.path.join(os.getcwd(), "%s_%s" % (os.environ["WORK_DIR_PREFIX"], type))
        )
    return normpath(os.path.join(os.getcwd(), ".tmp_%s" % type))


def create_working_dir(type: str):
    """
    create the working directory for the selected task
    given as a suffix after the WORK_DIR_PREFIX (by default .tmp_)
    """
    os.environ["WORK_DIR"] = get_tmp_folder(type)
    os.makedirs(os.environ["WORK_DIR"], exist_ok=True)


def clean_tmp_folder(type: str = "*"):
    """
    remove the content and the folder use for all tasks
    """
    p = os.getcwd()
    prefix = os.getenv("WORK_DIR_PREFIX") if "WORK_DIR_PREFIX" in os.environ else ".tmp_"
    for tmp_folder in Path(p).rglob(prefix + type):
        print(tmp_folder)
        if os.path.isdir(tmp_folder):
            shutil.rmtree(tmp_folder)


# ======== json encoder ========
def json_encoder(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    if "to_dict" in dir(o):
        return o.to_dict()

#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import shutil
import datetime


def normpath(s: str):
    return os.path.normpath(s).replace("\\", "/")


# ==== get working directory ====
def get_tmp_folder(type: str = "sim") -> str:
    """
    get working directory path for a given
    simulation type or use the specified working
    directory via WORK_DIR env. variable
    """
    if "WORK_DIR" in os.environ:
        return normpath(os.environ["WORK_DIR"])
    if "WORK_DIR_PREFIX" in os.environ:
        return normpath(
            os.path.join(os.getcwd(), ".%s_%s" % (os.environ["WORK_DIR_PREFIX"], type))
        )
    return normpath(os.path.join(os.getcwd(), ".tmp_%s" % type))


def get_tmp_folder_name(type: str = "sim", prefix: str = "") -> str:
    """
    get folder name for a given simulation type
    """
    if "WORK_DIR_PREFIX" in os.environ:
        return "%s.%s_%s" % (prefix, os.environ["WORK_DIR_PREFIX"], type)
    return "%s.tmp_%s" % (prefix, type)


def create_working_dir(suffix: str):
    """
    create the working directory for the selected task
    given as a suffix after the WORK_DIR_PREFIX (by default .tmp_)
    """
    os.environ["WORK_DIR"] = normpath(get_tmp_folder_name(suffix, "./"))
    os.makedirs(os.environ["WORK_DIR"], exist_ok=True)


def clean_tmp_folder(type: str = "*"):
    """
    remove the content and the folder use for all tasks
    """
    path = os.getcwd()
    if "WORK_DIR" in os.environ:
        path = normpath(os.environ["WORK_DIR"])
    prefix = os.getenv("WORK_DIR_PREFIX") if "WORK_DIR_PREFIX" in os.environ else ".tmp_"
    for tmp_folder in Path(path).rglob(prefix + type):
        if os.path.is_dir(tmp_folder):
            shutil.rmtree(tmp_folder)


# ======== json encoder ========
def json_encoder(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    if "to_dict" in dir(o):
        return o.to_dict()

#!/usr/bin/env python3
# coding: utf-8

import os
import sys

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.relog as relog
import common.read_sources as read_sources
import common.utils.doit as doit_helper

from doit import create_after
from doit.action import CmdAction, PythonAction
from common.read_config import Config
from common.utils.files import get_type, is_digital
from common.utils.db import Vault


var_vault = Vault()
flag_vault = Vault()


def transform_flags(flags: str) -> str:
    flags = flags.strip()
    # replace any values found by the key
    matches = {
        "+define+": ["-DEFINE+", "-define+", "-D", "-d"],
        "+parameter+": ["-PARAM+", "-param+", "-P", "-p"],
    }
    for output, inputs in matches.items():
        for i in inputs:
            if i in flags:
                flags = flags.replace(i, output)
    # generate a string
    flags = [
        flag
        for flag in flags.split(" ")
        if not flag.startswith("-g") and not flag.startswith("-W")
    ]
    return " ".join(flags)


def generate_cmd(files_mimes: list = [], params: dict = {}):
    # create the list of sources
    files = [f for f, m in files_mimes]
    mimes = list(set([m for f, m in files_mimes]))
    inc_dirs = read_sources.resolve_includes(files, with_pkg=True)
    with open(var_vault.SRCS, "w+") as fp:
        # include search pathes
        for inc_dir in inc_dirs:
            fp.write("+incdir+%s\n" % inc_dir)
        fp.write("+incdir+%s\n" % var_vault.PROJECT_DIR)
        # time scale
        if "TIMESCALE" in params:
            fp.write("+timescale+%s\n" % params["TIMESCALE"])
        # iverilog flags
        if "SIM_FLAGS" in params:
            for flag in params["SIM_FLAGS"]:
                tf = transform_flags(flag)
                if tf and tf[:2] not in ("-m", "-M"):
                    fp.write("%s\n" % tf)
        # list of files
        for file in files:
            if is_digital(file) and get_type(file) not in ["ASSERTIONS", "LIBERTY"]:
                fp.write("%s\n" % file)
    # compute iverilog flags
    flags = Config.iverilog.get("flags").split()
    flags.extend(
        [
            "-gverilog-ams"
            if any(["AMS" in mimes, "-gverilog-ams" in params.get("SIM_FLAGS", "")])
            else "-gno-verilog-ams",
            "-gassertions"
            if any(["ASSERT" in mimes, "-gassert" in params.get("SIM_FLAGS", "")])
            else "-gno-assertions",
            "-gspecify"
            if any(["-gspec" in p for p in params.get("SIM_FLAGS", "")])
            else "",
            "-Wtimescale"
            if any(["-Wtimes" in p for p in params.get("SIM_FLAGS", "")])
            else "",
        ]
    )
    flag_vault.iverilog = list(set(flags))
    # declare needed external VPI modules
    flags = []
    if "SIM_FLAGS" in params:
        for flag in params["SIM_FLAGS"]:
            tf = transform_flags(flag)
            if tf and tf[:2] in ("-m"):
                flags.append(tf)
    flag_vault.vvp = flags


def update_vars():
    var_vault.WORK_DIR = utils.get_tmp_folder()
    var_vault.PROJECT_DIR = os.getenv("PROJECT_DIR")
    var_vault.SRCS = utils.normpath(os.path.join(var_vault.WORK_DIR, "srcs.list"))
    var_vault.EXE = utils.normpath(os.path.join(var_vault.WORK_DIR, "run.vvp"))
    var_vault.PARSER_LOG = utils.normpath(os.path.join(var_vault.WORK_DIR, "parser.log"))
    var_vault.SIM_LOG = utils.normpath(os.path.join(var_vault.WORK_DIR, "sim.log"))
    if "iverilog" in Config.data:
        var_vault.WAVE_FORMAT = Config.iverilog.get("format")
        var_vault.WAVE = utils.normpath(
            os.path.join(var_vault.WORK_DIR, "run.%s" % var_vault.WAVE_FORMAT)
        )
    else:
        var_vault.WAVE_FORMAT = "vcd"
        var_vault.WAVE = utils.normpath(os.path.join(var_vault.WORK_DIR, "run.vcd"))


update_vars()


def task_vars_db():
    """
    set needed global variables
    """

    return {"actions": [(update_vars,)], "title": doit_helper.no_title}


@create_after(executed="vars_db")
def task_iverilog_prepare():
    """
    create the list of files needed
    list include dirs
    list parameters and define
    """

    def run(task):
        files, params = read_sources.read_from(os.getenv("CURRENT_DIR"))
        task.file_dep.update([f for f, m in files])
        task.actions.append(PythonAction(generate_cmd, [files, params]))

    return {
        "actions": [run],
        "file_dep": [],
        "targets": [var_vault.SRCS],
        "title": doit_helper.constant_title("Prepare"),
        "clean": [doit_helper.clean_targets],
    }


@create_after(executed="iverilog_prepare")
def task_iverilog_compile():
    """
    create a VVP executable from verilog/system-verilog inputs
    """

    cmd = "iverilog %s -o %s -c %s"
    flags = ""
    if flag_vault.iverilog:
        flags = " ".join(flag_vault.iverilog)

    def run(task):
        task.actions.append(
            CmdAction(
                cmd % (flags, var_vault.EXE, var_vault.SRCS),
                save_out="log",
            )
        )
        task.actions.append(
            PythonAction(doit_helper.save_log, (task, var_vault.PARSER_LOG))
        )

    return {
        "actions": [run],
        "file_dep": [var_vault.SRCS],
        "targets": [var_vault.EXE, var_vault.PARSER_LOG],
        "title": doit_helper.constant_title("Compile"),
        "clean": [doit_helper.clean_targets],
    }


@create_after(executed="iverilog_compile")
def task_sim():
    """
    get flags for VVP and launch simulation
    """
    # move the dumpfile to TMPDIR
    def move_dump(wave, wave_format):
        if os.path.exists(wave):
            os.remove(wave)
        if os.path.exists("./dump.%s" % wave_format):
            os.rename("./dump.%s" % wave_format, wave)

    cmd = "vvp -i %s %s -%s"

    def run(task):
        task.actions.append(
            CmdAction(
                cmd % (var_vault.EXE, flag_vault.vvp, var_vault.WAVE_FORMAT),
                save_out="log",
            )
        )
        task.actions.append(PythonAction(doit_helper.save_log, (task, var_vault.SIM_LOG)))
        task.actions.append(
            PythonAction(move_dump, [var_vault.WAVE, var_vault.WAVE_FORMAT])
        )

    return {
        "actions": [run],
        "file_dep": [var_vault.EXE],
        "targets": [var_vault.WAVE],
        "title": doit_helper.task_name_as_title,
        "clean": [doit_helper.clean_targets],
        "verbosity": 2,
    }


@create_after(executed="iverilog_compile")
def task_lint():
    """
    collect parsing operation
    """

    return {
        "actions": [(relog.display_log, (var_vault.PARSER_LOG,))],
        "file_dep": [var_vault.PARSER_LOG],
        "title": doit_helper.task_name_as_title,
    }

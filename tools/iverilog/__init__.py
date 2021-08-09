#!/usr/bin/env python3
# coding: utf-8

import os
import sys

import common.utils as utils
import common.relog as relog
import common.read_sources as read_sources
import common.utils.doit as doit_helper

from mako import exceptions
from mako.template import Template
from doit.action import CmdAction, PythonAction
from common.utils.files import is_digital, is_simulable
from common.utils.db import Vault
import common.config as config


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
            flags = flags.replace(i, output)
    # generate a string
    flags = [
        flag
        for flag in flags.split()
        if not flag.startswith("-g") and not flag.startswith("-W")
    ]
    return " ".join(flags)


def generate_cmd(files_mimes: list = [], params: dict = {}):
    # create the list of sources
    files = [f for f, _ in files_mimes if is_digital(f) and is_simulable(f, no_assert=True)]
    mimes = list(set([m for _, m in files_mimes]))
    # aggregate flags
    flags = []
    for flag in params.get("SIM_FLAGS", []):
        tf = transform_flags(flag)
        if tf and tf[:2] not in ["-m", "-M"]:
            flags.append(tf)
    # create filling data for template
    template_data = {
        "files": files,
        "include_dirs": [
            p for p in read_sources.resolve_includes(files, with_pkg=True) if p
        ],
        "timescale": params.get("TIMESCALE"),
        "flags": list(set(flags)),
    }
    if var_vault.PROJECT_DIR:
        template_data["include_dirs"].append(var_vault.PROJECT_DIR)
    # populate the template
    try:
        tmpl = Template(
            filename=utils.normpath(
                os.path.join(os.path.dirname(__file__), "./templates/iverilog.args.mako")
            )
        )
        with open(var_vault.SRCS, "w+") as fp:
            fp.write(tmpl.render(**template_data))
    except:
        print(exceptions.text_error_template().render())

    # compute iverilog flags
    flags = config.vault.iverilog.get("flags", [])
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
    var_vault.WAVE_FORMAT = config.vault.iverilog.get("format")
    var_vault.WAVE = utils.normpath(
        os.path.join(var_vault.WORK_DIR, "run.%s" % var_vault.WAVE_FORMAT)
    )
    flag_vault.iverilog = config.vault.iverilog.get("flags", [])


# needed to call it during loading of the tool
# to have correct file dependencies and targets
update_vars()


def task__iverilog_sim_prepare():
    """
    create the list of files needed
    list include dirs
    list parameters and define
    """

    update_vars()
    try:
        files, params = read_sources.read_from(os.getenv("CURRENT_DIR"))

        return {
            "actions": [PythonAction(generate_cmd, [files, params])],
            "file_dep": [f for f, _ in files],
            "targets": [var_vault.SRCS],
            "title": doit_helper.constant_title("Prepare"),
            "clean": [doit_helper.clean_targets],
            "verbosity": 2,
        }
    except FileNotFoundError as e:
        # do not print error if cleaning/batch/list/...
        if "sim" in sys.argv:
            relog.error("'%s' not found" % (e.filename or e.filename2))
            exit(1)
        return {"actions": None}


def task__iverilog_sim_compile():
    """
    create a VVP executable from verilog/system-verilog inputs
    """

    def run(task):
        cmd = "iverilog %s -o '%s' -c '%s' -l '%s'"
        flags = " ".join(flag_vault.get("iverilog", []))
        # touch parser log file to prevent iverilog error file not found
        with open(var_vault.PARSER_LOG, "w+") as fp:
            fp.write("")
        task.actions.append(
            CmdAction(cmd % (flags, var_vault.EXE, var_vault.SRCS, var_vault.PARSER_LOG)),
        )

    return {
        "actions": [run],
        "file_dep": [var_vault.SRCS],
        "targets": [var_vault.EXE, var_vault.PARSER_LOG],
        "title": doit_helper.constant_title("Compile"),
        "clean": [doit_helper.clean_targets],
        "uptodate": [False],
    }


def task_iverilog_sim():
    """
    get flags for VVP and launch simulation
    """
    # move the dumpfile to WORK_DIR
    def move_dump(wave, wave_format):
        if os.path.exists(wave):
            os.remove(wave)
        if os.path.exists("./dump.%s" % wave_format):
            os.rename("./dump.%s" % wave_format, wave)

    def run(task):
        # touch sim log file to prevent vvp error file not found
        with open(var_vault.SIM_LOG, "w+") as fp:
            fp.write("")
        cmd = "vvp -l '%s' %s %s -i '%s' | relog iverilog"
        task.actions.append(
            CmdAction(
                cmd
                % (
                    var_vault.SIM_LOG,
                    " ".join(flag_vault.get("vvp", [])),
                    var_vault.WAVE_FORMAT if var_vault.WAVE_FORMAT != "vcd" else "",
                    var_vault.EXE,
                )
            )
        )
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


def task_iverilog_lint():
    """
    collect parsing operation
    """

    return {
        "actions": [(relog.display_log, (var_vault.PARSER_LOG,))],
        "file_dep": [var_vault.PARSER_LOG],
        "title": doit_helper.task_name_as_title,
    }

#!/usr/bin/env python3
import os
import sys
import json

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.relog as relog
import common.read_sources as read_sources
import common.utils.doit as doit_helper

from doit import create_after
from doit.task import clean_targets
from doit.action import CmdAction, PythonAction
from common.read_config import Config
from common.utils.files import get_type, is_digital


TOOLS_DIR = utils.normpath(os.path.dirname(os.path.abspath(__file__)))
TOOLS_CFG = os.path.join(TOOLS_DIR, "tools.config")
DEFAULT_TMPDIR = utils.get_tmp_folder()
VARS_DB = utils.normpath(os.path.join(DEFAULT_TMPDIR, "vars.json"))


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


def generate_cmd(files_mimes: list = [], params: dict = {}, target: str = "./srcs.list"):
    # create the list of sources
    files = [f for f, m in files_mimes]
    mimes = list(set([m for f, m in files_mimes]))
    inc_dirs = read_sources.resolve_includes(files)
    cwd = os.getcwd()
    PLATFORM_NAME = os.getenv("PLATFORM")
    PLATFORM_DIR = cwd[: cwd.find(PLATFORM_NAME) + len(PLATFORM_NAME)]
    with open(target, "w+") as fp:
        # include search pathes
        for inc_dir in inc_dirs:
            fp.write("+incdir+%s\n" % inc_dir)
        fp.write("+incdir+%s\n" % PLATFORM_DIR)
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
    FLAGS = {}
    FLAGS["iverilog"] = list(set(flags))
    # declare needed external VPI modules
    flags = []
    if "SIM_FLAGS" in params:
        for flag in params["SIM_FLAGS"]:
            tf = transform_flags(flag)
            if tf and tf[:2] in ("-m"):
                flags.append(tf)
    FLAGS["vvp"] = flags
    with open(target + ".flags", "w+") as fp:
        json.dump(FLAGS, fp, indent=4)


def task_vars_db():
    """
    set needed global variables
    """
    # define global variables
    def set_vars():
        vars = {
            "DEFAULT_TMPDIR": DEFAULT_TMPDIR,
            "SRCS": utils.normpath(os.path.join(DEFAULT_TMPDIR, "srcs.list")),
            "EXE": utils.normpath(os.path.join(DEFAULT_TMPDIR, "run.vvp")),
            "PARSER_LOG": utils.normpath(os.path.join(DEFAULT_TMPDIR, "parser.log")),
            "SIM_LOG": utils.normpath(os.path.join(DEFAULT_TMPDIR, "sim.log")),
            "WAVE": utils.normpath(
                os.path.join(DEFAULT_TMPDIR, "run.%s" % Config.iverilog.get("format"))
            ),
            "WAVE_FORMAT": Config.iverilog.get("format"),
            "TOOLS_DIR": TOOLS_DIR,
        }
        with open(VARS_DB, "w+") as fp:
            json.dump(vars, fp, indent=4)
        return vars

    return {"actions": [(set_vars,)], "title": doit_helper.no_title}


@create_after(executed="vars_db")
def task_prepare():
    """
    create the list of files needed
    list include dirs
    list parameters and define
    """

    files, params = read_sources.read_from(os.getcwd(), no_logger=False)
    if VARS_DB:
        with open(VARS_DB, "r+") as fp:
            vars = json.load(fp)
            target = vars["SRCS"]

    return {
        "actions": [PythonAction(generate_cmd, [files, params, target])],
        "file_dep": [f for f, m in files],
        "targets": [target, target + ".flags"],
        "title": doit_helper.task_name_as_title,
        "clean": [clean_targets],
    }


@create_after(executed="prepare")
def task_compile():
    """
    create a VVP executable from verilog/system-verilog inputs
    """

    cmd = "iverilog %s -o %s -c %s"
    fgs, dep, target = "", "", ""
    if VARS_DB:
        with open(VARS_DB, "r+") as fp:
            vars = json.load(fp)
            dep = vars["SRCS"]
            target = vars["EXE"]
    # get flags
    if os.path.exists(dep + ".flags"):
        with open(dep + ".flags", "r+") as fp:
            FLAGS = json.load(fp)
            fgs = " ".join(FLAGS["iverilog"])

    return {
        "actions": [CmdAction(cmd % (fgs, target, dep), save_out=vars["PARSER_LOG"])],
        "file_dep": [dep, dep + ".flags"],
        "targets": [target, vars["PARSER_LOG"]],
        "title": doit_helper.task_name_as_title,
        "clean": [clean_targets],
    }


@create_after(executed="compile")
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
    fgs, dep, target, fmt = "", "", "", ""

    if VARS_DB:
        with open(VARS_DB, "r+") as fp:
            vars = json.load(fp)
            dep = vars["EXE"]
            srcs = vars["SRCS"]
            fmt = vars["WAVE_FORMAT"]
            target = vars["WAVE"]
    # get flags
    if os.path.exists(srcs + ".flags"):
        with open(srcs + ".flags", "r+") as fp:
            FLAGS = json.load(fp)
            fgs = " ".join(FLAGS["vvp"])

    return {
        "actions": [
            CmdAction(cmd % (dep, fgs, fmt), save_out=vars["SIM_LOG"]),
            PythonAction(move_dump, [target, fmt]),
        ],
        "file_dep": [dep, srcs + ".flags"],
        "targets": [target],
        "title": doit_helper.task_name_as_title,
        "clean": [clean_targets],
        "verbosity": 2,
    }


@create_after(executed="compile")
def task_lint():
    """
    collect parsing operation
    """

    cmd = "iverilog %s -o %s -c %s"
    if VARS_DB:
        with open(VARS_DB, "r+") as fp:
            vars = json.load(fp)
            dep = vars["SRCS"]
            tgt = vars["EXE"]

    return {
        "actions": [(relog.display_log, (vars["PARSER_LOG"],))],
        "file_dep": [vars["PARSER_LOG"]],
        "title": doit_helper.task_name_as_title,
    }

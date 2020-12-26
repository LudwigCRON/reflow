#!/usr/bin/env python3
import os
import sys
import json

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.relog as relog
import common.read_sources as read_sources
import common.utils.doit as doit_helper

from doit.action import CmdAction, PythonAction
from doit.task import clean_targets
from common.read_config import Config
from common.utils.files import get_type, is_digital

DOIT_CONFIG = doit_helper.DOIT_CONFIG
doit_helper.TaskNumber.ENVS = globals()

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


def prepare(files_mimes: list = [], params: dict = {}, targets: str = "./srcs.list"):
    # create the list of sources
    files = [f for f, m in files_mimes]
    mimes = list(set([m for f, m in files_mimes]))
    inc_dirs = read_sources.resolve_includes(files)
    cwd = os.getcwd()
    PLATFORM_NAME = os.getenv("PLATFORM")
    PLATFORM_DIR = cwd[: cwd.find(PLATFORM_NAME) + len(PLATFORM_NAME)]
    with open(targets, "w+") as fp:
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
    with open(targets + ".flags", "w+") as fp:
        json.dump(FLAGS, fp, indent=4)


def task_vars_db():
    """
    load the config and set needed global variables
    """
    # load config
    if not Config.data:
        Config.read_configs(TOOLS_CFG)
    else:
        Config.add_configs(TOOLS_CFG)
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


def task_prepare():
    """
    create the list of files needed
    list include dirs
    list parameters and define
    """

    def run(task):
        f, p = read_sources.read_from(os.getcwd(), no_logger=False)
        if VARS_DB:
            with open(VARS_DB, "r+") as fp:
                vars = json.load(fp)
                tgt = vars["SRCS"]
        task.file_dep.update([d for d, m in f])
        task.targets.append(tgt)
        task.targets.append(tgt + ".flags")
        task.actions.append(PythonAction(prepare, [f, p, tgt]))

    return {
        "actions": [run],
        "task_dep": ["vars_db"],
        "title": doit_helper.task_name_as_title,
        "clean": [clean_targets],
    }


def task_compile():
    """
    create a VVP executable from verilog/system-verilog inputs
    """

    def run(task):
        cmd = "iverilog %s -o %s -c %s"
        if VARS_DB:
            with open(VARS_DB, "r+") as fp:
                vars = json.load(fp)
                dep = vars["SRCS"]
                tgt = vars["EXE"]
        with open(dep + ".flags", "r+") as fp:
            FLAGS = json.load(fp)
            fgs = " ".join(FLAGS["iverilog"])
        task.file_dep.update([dep, dep + ".flags"])
        task.targets.append(tgt)
        task.targets.append(vars["PARSER_LOG"])
        task.actions.append(CmdAction(cmd % (fgs, tgt, dep), save_out=vars["PARSER_LOG"]))

    return {
        "actions": [run],
        "task_dep": ["vars_db"],
        "title": doit_helper.task_name_as_title,
        "clean": [clean_targets],
    }


def task_simulate():
    """
    get flags for VVP and launch simulation
    """
    # move the dumpfile to TMPDIR
    def move_dump(wave, wave_format):
        if os.path.exists(wave):
            os.remove(wave)
        if os.path.exists("./dump.%s" % wave_format):
            os.rename("./dump.%s" % wave_format, wave)

    def run(task):
        if VARS_DB:
            with open(VARS_DB, "r+") as fp:
                vars = json.load(fp)
                dep = vars["EXE"]
                tgt = vars["WAVE"]
                fmt = vars["WAVE_FORMAT"]
                srcs = vars["SRCS"]
        with open(srcs + ".flags", "r+") as fp:
            FLAGS = json.load(fp)
            fgs = " ".join(FLAGS["vvp"])
        cmd = "vvp -i %s %s -%s"
        task.file_dep.update([srcs + ".flags", dep])
        task.targets.append(tgt)
        task.actions.append(CmdAction(cmd % (dep, fgs, fmt), save_out=vars["SIM_LOG"]))
        task.actions.append(PythonAction(move_dump, [tgt, fmt]))

    return {
        "actions": [run],
        "task_dep": ["vars_db"],
        "title": doit_helper.task_name_as_title,
        "clean": [clean_targets],
        "verbosity": 2,
    }


def task_read_lint():
    """
    collect parsing operation
    """

    def run(task):
        cmd = "iverilog %s -o %s -c %s"
        if VARS_DB:
            with open(VARS_DB, "r+") as fp:
                vars = json.load(fp)
                dep = vars["SRCS"]
                tgt = vars["EXE"]
        with open(dep + ".flags", "r+") as fp:
            FLAGS = json.load(fp)
            fgs = " ".join(FLAGS["iverilog"])
        task.file_dep.update([vars["PARSER_LOG"]])
        task.actions.append(PythonAction(relog.display_log, (vars["PARSER_LOG"],)))

    return {
        "actions": [run],
        "task_dep": ["vars_db"],
        "title": doit_helper.task_name_as_title,
    }


def task__sim():
    """
    group subtask for simulation
    """
    subtasks = [task_prepare, task_compile, task_simulate]
    for subtask in subtasks[::-1]:
        d = subtask()
        d["name"] = subtask.__name__[5:]
        yield d


def task__lint():
    """
    group subtasks for lint
    """
    subtasks = [task_prepare, task_compile, task_read_lint]
    for subtask in subtasks[::-1]:
        d = subtask()
        d["name"] = subtask.__name__[5:]
        yield d


def task_sim():
    """
    prepare and launch the simulation
    """

    return {
        "actions": None,
        "task_dep": ["_sim"],
        "title": doit_helper.no_title,
    }


def task_lint():
    """
    prepare and launch the simulation
    """

    return {"actions": None, "task_dep": ["_lint"], "title": doit_helper.no_title}

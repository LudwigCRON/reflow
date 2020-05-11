#!/usr/bin/env python3

import re
import os
import argparse
import configparser

import common.relog as relog
import common.utils as utils
import common.executor as executor

from enum import Enum
from collections import Counter


class SimType(Enum):
    SIMULATION = (0,)
    COVERAGE = (1,)
    LINT = (2,)
    ALL = 3


def rename_section(config: configparser.ConfigParser, old_name: str, new_name: str):
    """
    rename a section of a configparser to allows custom rules
    on section names
    """
    options = config.items(old_name)
    # remove the previous rules
    config.remove_section(old_name)
    # create the new section
    try:
        config.add_section(new_name)
    except configparser.DuplicateSectionError:
        hist = Counter(config.sections())
        new_name = "%s_%d" % (new_name, hist[new_name])
        config.add_section(new_name)
    # transfer options
    for option in options:
        config.set(new_name, option[0], option[1])


def normalize_config(config: configparser.ConfigParser):
    """
    adjust section name and option
    """
    # pre-process to resolve default category
    rules = config.sections()
    if "default" in rules:
        for opt in config.options("default"):
            config.add_section(opt)
        config.remove_section("default")
        rules = config.sections()
    # translate += functionallity to extend existing option
    for rule in rules:
        for opt in config.options(rule):
            # due to the parser label+=value is consider as label+->value
            if opt[-1] == "+":
                opt_ref = opt[:-1]
                valb = config.get(rule, opt, raw=True)
                # if the rule already exist
                if config.has_option(rule, opt_ref):
                    vala = config.get(rule, opt_ref, raw=True)
                    if isinstance(vala, str) and isinstance(valb, str):
                        config.set(rule, opt_ref, str([vala, valb]))
                    elif isinstance(vala, str) and isinstance(valb, list):
                        valb.append(vala)
                        config.set(rule, opt_ref, str(valb))
                    elif isinstance(vala, list) and isinstance(valb, str):
                        vala.append(valb)
                        config.set(rule, opt_ref, str(vala))
                    else:
                        vala.extend(valb)
                        config.set(rule, opt_ref, str(vala))
                    config.remove_option(rule, opt)
                # just create the option
                else:
                    valb = config.get(rule, opt)
                    config.set(rule, opt_ref, str(valb))
    # parse rules
    cut_rules = (parse_rule(rule) for rule in rules)
    for rule, cut_rule in zip(rules, cut_rules):
        path, lbl, sim_type = cut_rule
        config.set(rule, "__path__", path)
        config.set(rule, "__sim_type__", str(sim_type))
        rename_section(config, rule, lbl)


def parse_rule(text: str) -> tuple:
    """
    First Group of Rules
        folder_path:
        folder_path@sim_type:
        folder_path>label:
        folder_path>label@sim_type:
    Second Group of Rules
        do folder_path:
        do folder_path as label:
        do sim_type on folder_path:
        do sim_type on folder_path as label:
    """
    folder, label, sim_type = None, None, None
    if text.strip().startswith("do "):
        # ==== second group ====
        # do\s*([\/\w\.]+)      : capture folder_path or sim_type
        # (?:on\s*([\/\w\.]+))? : capture only folder_path
        # (?:as\s*([\w]+))?     : capture only label
        matches = re.finditer(
            r"do\s*([\/\w\.]+)\s*(?:on\s*([\/\w\.]+))?\s*(?:as\s*([\w]+))?", text
        )
        ans = (match.groups() for match in matches)
        for a in ans:
            sim_type, folder, label = a
            if folder is None:
                folder = sim_type
                sim_type = None
            if folder is not None:
                sim_type = (
                    SimType.ALL
                    if sim_type is None
                    else SimType.SIMULATION
                    if "sim" in sim_type.lower()
                    else SimType.COVERAGE
                    if "cov" in sim_type.lower()
                    else SimType.LINT
                    if "lint" in sim_type.lower()
                    else SimType.ALL
                )
                return (folder, label, sim_type)
    else:
        # ==== first group ====
        # ([\/\w\.]+)   : capture folder_path
        # (?:>([\w]+))? : capture label if exist
        # (?:@([\w]+))? : capture sim_type if exist
        matches = re.finditer(r"([\/\w\.]+)\s*(?:>\s*([\w]+))?(?:@\s*([\w]+))?", text)
        ans = (match.groups() for match in matches)
        for a in ans:
            folder, label, sim_type = a
            if folder is not None:
                sim_type = (
                    SimType.ALL
                    if sim_type is None
                    else SimType.SIMULATION
                    if "sim" in sim_type.lower()
                    else SimType.COVERAGE
                    if "cov" in sim_type.lower()
                    else SimType.LINT
                    if "lint" in sim_type.lower()
                    else SimType.ALL
                )
                label = folder if label is None else label
                return (folder, label, sim_type)
    return (None, None, SimType.ALL)


def read_batch(batch_file: str):
    # parser for config file
    batch = configparser.ConfigParser(
        allow_no_value=True,
        strict=True,
        empty_lines_in_values=False,
        inline_comment_prefixes=("#", ";"),
    )
    # keep case of string
    batch.optionxform = str
    # override section regex
    batch.SECTCRE = re.compile(r"[ \t]*(?P<header>[^:]+?)[ \t]*:")
    # check input exist
    if not os.path.exists(batch_file):
        raise Exception("%s does not exist" % batch_file)
    # get batch description file path
    if os.path.isdir(batch_file):
        filepath = os.path.join(batch_file, "Batch.list")
    else:
        filepath = batch_file
    # parse the batch file
    try:
        batch.read([filepath])
    except configparser.DuplicateSectionError as dse:
        relog.error(
            (
                "batch cannot accept duplicate rules\n\t",
                "consider apply a label 'folder > label [@SIM_TYPE]:' to %s" % dse.section,
                "\n\tor a in this format 'do SIM_TYPE on folder as label:'",
            )
        )
    except configparser.MissingSectionHeaderError:
        # add folder of a tc in default category
        # !! should be processed in normalize!!
        with open(filepath, "r+") as fp:
            batch.read_string("default:\n" + fp.read())
    normalize_config(batch)
    return batch


def run(
    cwd, batch, sim_only: bool = False, cov_only: bool = False, lint_only: bool = False
):
    N = len(batch.sections())
    TMP_DIR = utils.get_tmp_folder()
    # create directory for simulation
    for k, rule in enumerate(batch):
        if batch.has_option(rule, "__path__"):
            relog.info(f"[{k}/{N}] Run simulation {rule}")
            p = os.path.join(cwd, batch.get(rule, "__path__"))
            s = eval(batch.get(rule, "__sim_type__"))
            o = os.path.join(TMP_DIR, rule)
            l = os.path.join(o, "Sources.list")
            b = os.path.join(p, "Batch.list")
            os.makedirs(o, exist_ok=True)
            if not os.path.exists(b):
                # create the Sources.list
                with open(l, "w+") as fp:
                    path = batch.get(rule, "__path__")
                    dedent = ''.join(["../"] * (2 + path.count('/')))
                    fp.write("%s\n" % os.path.join(dedent, path))
                    for option in batch.options(rule):
                        if not option.startswith("__"):
                            values = batch.get(rule, option, raw=True)
                            if "[" in values:
                                values = eval(values)
                                fp.write(f"{option}={' '.join(values)}\n")
                            else:
                                fp.write(f"{option}={values}\n")
            # select which simulations should be performed
            batch_options = [
                "sim",
                "cov" if cov_only else "",
                "lint" if lint_only else "",
            ]
            sim_only, cov_only, lint_only = (
                sim_only and not cov_only and not lint_only,
                cov_only and not sim_only and not lint_only,
                lint_only and not cov_only and not sim_only,
            )
            if not sim_only and not cov_only and not lint_only:
                sim_only, cov_only, lint_only = True, True, True
            # run the simulations
            if os.path.exists(b):
                for batch_option in batch_options:
                    if batch_option:
                        executor.sh_exec(
                            "run batch %s" % batch_option, CWD=p, ENV=os.environ.copy(),
                        )
            else:
                if sim_only and s in [SimType.SIMULATION, SimType.ALL]:
                    executor.sh_exec("run sim", CWD=o, ENV=os.environ.copy())
                if cov_only and s in [SimType.COVERAGE, SimType.ALL]:
                    executor.sh_exec("run cov", CWD=o, ENV=os.environ.copy())
                if lint_only and s in [SimType.LINT, SimType.ALL]:
                    executor.sh_exec("run lint", CWD=o, ENV=os.environ.copy())


def main(cwd, sim_only: bool = False, cov_only: bool = False, lint_only: bool = False):
    batch = read_batch(cwd)
    if batch:
        run(cwd, batch, sim_only, cov_only, lint_only)
    else:
        relog.error("No Batch.list file found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("-i", "--input", type=str, help="list of input files")
    parser.add_argument(
        "-s", "--sim", default=False, action="store_true", help="select only simulation"
    )
    parser.add_argument(
        "-c", "--cov", default=False, action="store_true", help="select only coverage"
    )
    parser.add_argument(
        "-l", "--lint", default=False, action="store_true", help="select only lint"
    )
    parser.add_argument(
        "-nl", "--no-logger", action="store_true", help="already include logger macro"
    )
    args = parser.parse_args()
    # read batch description file
    main(args.input, args.sim, args.cov, args.lint)

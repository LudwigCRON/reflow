#!/usr/bin/env python3

import re
import os
import argparse
import configparser

import common.relog as relog
import common.executor as executor

from enum import Enum
from collections import Counter


class SimType(Enum):
    SIMULATION = 0,
    COVERAGE   = 1,
    ALL        = 2


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
        new_name  = "%s_%d" % (new_name, hist[new_name])
        config.add_section(new_name)
    # transfer options
    for option in options:
        config.set(new_name, option[0], option[1])


def normalize_config(config: configparser.ConfigParser):
    """
    adjust section name and option
    """
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
                    valb = batch.get(rule, opt)
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
    folder_path:
    folder_path@sim_type:
    folder_path>label:
    folder_path>label@sim_type:
    """
    # trim text
    txt = text.strip()
    txt = txt if ":" not in txt else txt.split(":", 1)[0]
    # default return value
    folder, lbl, st = txt, txt, ""
    if ">" in txt:
        folder, lbl = txt.split(">", 1)
    if "@" in lbl:
        lbl, st = lbl.split("@", 1)
    if "cov" in st.lower():
        return (folder, lbl, SimType.COVERAGE)
    elif "sim" in st.lower():
        return (folder, lbl, SimType.SIMULATION)
    return (folder, lbl, SimType.ALL)


def read_config(batch_file: str):
    # parser for config file
    batch = configparser.ConfigParser(
        allow_no_value=True,
        strict=True,
        empty_lines_in_values=False,
        inline_comment_prefixes=('#', ';'))
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
        relog.error((
            "batch cannot accept duplicate rules\n\t"
            "consider apply a label 'folder > label [@SIM_TYPE]:' to %s" % dse.section))
    normalize_config(batch)
    return batch


def run(cwd, batch, sim_only: bool = False, cov_only: bool = False):
    N = len(batch.sections())
    # create directory for simulation
    for k, rule in enumerate(batch):
        if batch.has_option(rule, "__path__"):
            relog.info(f"[{k}/{N}] Run simulation {rule}")
            p = os.path.join(cwd, batch.get(rule, "__path__"))
            s = eval(batch.get(rule, "__sim_type__"))
            o = os.path.join(cwd, f".tmp_sim/{rule}")
            l = os.path.join(o, "Sources.list")
            os.makedirs(o, exist_ok=True)
            # create the Sources.list
            with open(l, "w+") as fp:
                fp.write("%s\n" % os.path.join("../../", batch.get(rule, "__path__")))
                for option in batch.options(rule):
                    if not option.startswith("__"):
                        values = batch.get(rule, option, raw=True)
                        if "[" in values:
                            values = eval(values)
                            fp.write(f"{option}={' '.join(values)}\n")
                        else:
                            fp.write(f"{option}={values}\n")
            # run the simulation
            if sim_only and s in [SimType.SIMULATION, SimType.ALL]:
                executor.sh_exec("run -c sim", CWD=o)
            elif cov_only and s in [SimType.COVERAGE, SimType.ALL]:
                executor.sh_exec("run -c cov", CWD=o)


def main(cwd, sim_only: bool = False, cov_only: bool = False):
    batch = read_config(cwd)
    if batch:
        run(cwd, batch, sim_only=sim_only, cov_only=cov_only)
    else:
        relog.error("No Batch.list file found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument("-i", "--input", type=str, help="list of input files")
    parser.add_argument("-s", "--sim", default=False, action="store_true", help="select only simulation")
    parser.add_argument("-c", "--cov", default=False, action="store_true", help="select only coverage")
    parser.add_argument("-nl", "--no-logger", action="store_true", help="already include logger macro")
    args = parser.parse_args()
    # read batch description file
    main(args.input, args.sim, args.cov)

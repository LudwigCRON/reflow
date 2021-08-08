#!/usr/bin/env python3

import re
import os
import configparser
from typing import Optional, Tuple

import common.relog as relog
import common.utils as utils

from collections import Counter


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

    def _normalization(folder, label, sim_type) -> Optional[Tuple]:
        if folder is None:
            return None
        if sim_type and "sim" in sim_type.lower():
            sim_type = "sim"
        elif sim_type and "cov" in sim_type.lower():
            sim_type = "cov"
        elif sim_type and "lint" in sim_type.lower():
            sim_type = "lint"
        else:
            sim_type = "all"
        label = folder if label is None else label
        return (folder, label, sim_type)

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
            if folder is None and sim_type is not None:
                folder, sim_type = sim_type, folder
            nt = _normalization(folder, label, sim_type)
            if not nt:
                continue
            return nt
    else:
        # ==== first group ====
        # ([\/\w\.]+)   : capture folder_path
        # (?:>([\w]+))? : capture label if exist
        # (?:@([\w]+))? : capture sim_type if exist
        matches = re.finditer(r"([\/\w\.]+)\s*(?:>\s*([\w]+))?(?:@\s*([\w]+))?", text)
        ans = (match.groups() for match in matches)
        for a in ans:
            folder, label, sim_type = a
            nt = _normalization(folder, label, sim_type)
            if not nt:
                continue
            return nt
    return (None, None, "all")


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
        filepath = utils.normpath(os.path.join(batch_file, "Batch.list"))
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


def create_batch_sources(batch, rule, rule_path: str):
    sources_list = utils.normpath(os.path.join(rule_path, "Sources.list"))
    with open(sources_list, "w+") as fp:
        path = utils.normpath(batch.get(rule, "__path__"))
        dedent = "".join(["../"] * (2 + path.count("/")))
        fp.write("%s\n" % utils.normpath(os.path.join(dedent, path)))
        for option in batch.options(rule):
            if not option.startswith("__"):
                values = batch.get(rule, option, raw=True)
                if "[" in values:
                    values = eval(values)
                    fp.write(f"{option}={' '.join(values)}\n")
                else:
                    fp.write(f"{option}={values}\n")

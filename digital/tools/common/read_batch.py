#!/usr/bin/env python3

import re
import os
import sys
import argparse

from enum import Enum
from collections import defaultdict, Counter

from tools.common.read_sources import  is_parameter, is_rules

class SimType(Enum):
    SIMULATION=0,
    COVERAGE=1,
    ALL=2

def parse_rule(text: str) -> tuple:
    """
    folder_path:
    folder_path@sim_type:
    """
    if not is_rules(text):
        return None
    rule = text.split(":", 1)[0]
    if not "@" in rule:
        return (rule, SimType.ALL)
    lbl, sim_type = rule.split("@", 2)
    if "cov" in sim_type.lower():
        return (lbl, SimType.COVERAGE)
    return (lbl, SimType.SIMULATION)

def read_batch(filepath: str) -> list:
    """
    list the lots to execute
    """
    # add file if it is a directory given
    filepath = os.path.join(filepath, "Batch.list") if os.path.isdir(filepath) else filepath
    # parse the batch file
    lots, batch = [], {}
    with open(filepath, "r+") as fp:
        for line in fp:
            l = line.strip()
            # comment
            if l.startswith("#"):
                pass
            # is the start of a rule
            elif is_rules(l):
                if batch:
                    lots.append(batch)
                lbl, sim_type = parse_rule(l)
                batch = {"__folder__": lbl, "__sim_type__": sim_type}
             # add value to parameter
            elif "+=" in l:
                a, b = l.split("+=", 1)
                batch[a.strip()].append(b.strip())
            # update a parameter
            elif "=" in l:
                a, b = l.split("=", 1)
                batch[a.strip()] = [b.strip()]
    if batch:
        lots.append(batch)
    return lots


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument("-i", "--input", type=str, help="list of input files")
    parser.add_argument("-s", "--sim", action="store_true", help="select only simulation")
    parser.add_argument("-c", "--cov", action="store_true", help="select only coverage")
    parser.add_argument("-nl", "--no-logger", action="store_true", help="already include logger macro")
    args = parser.parse_args()
    # check input exist
    if not os.path.exists(args.input):
        raise Exception(f"{args.input} does not exist")
    # parse the batch file
    lots = read_batch(args.input)
    hist = Counter((l["__folder__"] for l in lots))
    for k, lot in enumerate(lots):
        gpart = (l["__folder__"] for l in lots[:k])
        folder = lot["__folder__"]
        index = Counter(gpart)[folder]
        # if more than once add index
        if hist[folder] > 0:
            lot["__output_dir__"] = f".tmp_batch/{folder}_{index}"
        else:
            lot["__output_dir__"] = f".tmp_batch/{folder}"
        print(lot)
    # create directory for simulation
    for _, lot in enumerate(lots):
        p = os.path.join(args.input, lot["__output_dir__"])
        print(args.input, p)
        os.makedirs(p, exist_ok=True)
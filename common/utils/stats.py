#!/usr/bin/env python3
# coding: utf-8

import os

from common.utils.parsers import parse_eng_unit


def read_sim_stat(path: str):
    # <block>/.tmp_<type of sim>/<type of sim>.stats
    block = os.path.basename(os.path.dirname(os.path.dirname(path)))
    type = os.path.basename(str(path).lower()).split(".")[0]
    # read stats of simulations
    with open(path, "r+") as fp:
        db_sim = dict(
            (line.split(":", 1) for i, line in enumerate(fp) if ":" in line and i > 0)
        )

        db_sim = {k: parse_eng_unit(v) for k, v in db_sim.items()}
        if "Sim. Time" in db_sim:
            db_sim["total_time"] = db_sim.pop("Sim. Time")
        else:
            db_sim["total_time"] = 0
        if "Warnings" in db_sim:
            db_sim["warnings"] = db_sim.pop("Warnings")
        else:
            db_sim["warnings"] = 0
        if "Errors" in db_sim:
            db_sim["errors"] = db_sim.pop("Errors")
        else:
            db_sim["errors"] = 0
        db_sim["name"] = block
        print(db_sim)
    return type, db_sim


def add_extra_stats(db_batch: dict):
    db_batch["nb_simulation"] = len(db_batch["sims"])
    db_batch["nb_coverage"] = len(db_batch["covs"])
    db_batch["nb_lint"] = len(db_batch["lints"])
    db_batch["simulation"] = sum(
        (1 for sim in db_batch["sims"] if sim.get("errors", 0) == 0)
    )
    db_batch["coverage"] = sum((1 for sim in db_batch["covs"] if sim.get("errors", 0) == 0))
    db_batch["lint"] = sum((1 for sim in db_batch["lints"] if sim.get("errors", 0) == 0))

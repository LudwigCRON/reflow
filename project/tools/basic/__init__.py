#!/usr/bin/env python3
# coding: utf-8

import os
import sys

import common.utils.doit as doit_helper
import common.design_tree as design_tree
import common.read_sources as read_sources


def task_tree():
    """
    display hierarchy of the design
    """

    def tree(task):
        files, params = read_sources.read_from(os.getenv("CURRENT_DIR"), no_logger=False)
        design_tree.main(files, params)

    return {"actions": [tree], "title": doit_helper.task_name_as_title, "verbosity": 2}
#!/usr/bin/env python3
# coding: utf-8

import os
import sqlite3
import common.relog
import common.utils as utils
import common.utils.doit as doit_helper

from mako import exceptions
from mako.template import Template
from itertools import groupby
from collections import defaultdict
from doit.action import PythonAction

tmp_vault = utils.db.Vault()


def task__report_fetch():
    """
    read information from relog database
    """

    def run(task):
        types = ["lint", "sim", "cov", "synth"]
        sep = "', '"
        db_path = common.relog.get_relog_dbpath()
        if not os.path.exists(db_path):
            common.relog.error("No relog database found")
        with sqlite3.connect(db_path) as con:
            con.row_factory = utils.db.sqlite_dict_factory
            c = con.cursor()
            # get executed tasks of type t and their duration
            c.execute(
                (
                    "SELECT "
                    "    test_path, "
                    "    GROUP_CONCAT(task_name, ';') as task_names, "
                    "    GROUP_CONCAT(time(end_time-start_time, 'unixepoch'),';') as elapsed_times, "
                    "    GROUP_CONCAT(aborted,';') as aborteds, "
                    "    GROUP_CONCAT(skipped,';') as skippeds "
                    "FROM tasks "
                    f"WHERE task_name IN ('{sep.join(types)}') "
                    "GROUP BY test_path"
                )
            )
            for row in c.fetchall():
                test_path = row["test_path"]
                tmp_vault.set(test_path, [])
                groups = zip(
                    row["task_names"].split(";"),
                    row["elapsed_times"].split(";"),
                    row["aborteds"].split(";"),
                    row["skippeds"].split(";"),
                )
                for group in groups:
                    tdb = utils.db.Vault(
                        dict(
                            zip(["task_name", "elapsed_time", "aborted", "skipped"], group)
                        )
                    )
                    tmp_vault.get(test_path).append(tdb)
            for test_path in tmp_vault:
                for task in tmp_vault.get(test_path):
                    # get number of warning/errors/fatal
                    c.execute(
                        f"SELECT DISTINCT rule, count(rule) as nb FROM '{test_path}' GROUP BY rule;"
                    )
                    for row in c.fetchall():
                        task.set(row["rule"], row["nb"])

    return {
        "actions": [run],
        "file_dep": [common.relog.get_relog_dbpath()],
        "targets": [],
        "title": doit_helper.no_title,
        "clean": [doit_helper.clean_targets],
        "uptodate": [False],
        "verbosity": 2,
    }


def task__report_html():
    """
    generate an html report of executed tasks
    """

    def get_groups(paths: dict) -> dict:
        ans = defaultdict(list)
        # support batch and single sim
        for test_path in paths:
            if "/" in test_path:
                prefix, *remainder = test_path.split("/")
                if prefix not in ans:
                    ans[prefix] = defaultdict(list)
                ans[prefix].update({"/".join(remainder): paths.get(test_path)})
            else:
                ans[test_path] = paths.get(test_path)
        return ans

    def filter_task(prefix: str, filters: dict):
        for test_path in tmp_vault:
            if test_path.startswith(prefix):
                for task in tmp_vault.get(test_path, []):
                    validations = (c(task.get(k)) for k, c in filters.items())
                    if all(validations):
                        yield task

    def fill_template(tmpl_path: str, html_path: str):
        try:
            tmpl = Template(filename=tmpl_path)
            with open(html_path, "w+") as fp:
                fp.write(
                    tmpl.render(
                        db=tmp_vault, get_groups=get_groups, filter_task=filter_task
                    )
                )
        except:
            print(exceptions.text_error_template().render())

    def run(task):
        tmpl_path = utils.normpath(
            os.path.join(os.path.dirname(__file__), "templates/report.html.mako")
        )
        html_path = common.relog.get_relog_dbpath().replace("relog.db", "report.html")
        task.actions.append(PythonAction(fill_template, [tmpl_path, html_path]))
        task.targets.append(html_path)

    return {
        "actions": [run],
        "task_dep": ["report_fetch"],
        "targets": [],
        "title": doit_helper.constant_title("Report HTML"),
        "clean": [doit_helper.clean_targets],
        "uptodate": [False],
        "verbosity": 2,
    }

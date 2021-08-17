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
            # get groups and total time
            c.execute(
                (
                    "SELECT "
                    "    substr(test_path, 0, instr(test_path, '/')) as group_name, "
                    "    time(sum(end_time-start_time), 'unixepoch') as elapsed_time "
                    "FROM tasks "
                    f"WHERE (task_name IN ('{sep.join(types)}')) "
                    "GROUP BY substr(test_path, 0, instr(test_path, '/')) "
                )
            )
            for row in c.fetchall():
                vault_grp = utils.db.Vault({"elapsed_time": row["elapsed_time"]})
                for type in types:
                    vault_grp.set(type, [])
                tmp_vault.set(row["group_name"], vault_grp)
            # get executed tasks of type t and their duration
            c.execute(
                (
                    "SELECT  "
                    "    substr(test_path, 0, instr(test_path, '/')) as group_name, "
                    "    task_name, "
                    "    test_path, "
                    "    time(end_time-start_time, 'unixepoch') as elapsed_time, "
                    "    aborted, "
                    "    skipped "
                    "FROM tasks  "
                    f"WHERE task_name IN ('{sep.join(types)}') "
                    "ORDER BY test_path, task_name "
                )
            )
            for row in c.fetchall():
                vault_grp = tmp_vault.get(row["group_name"])
                vault_task = vault_grp.get(row["task_name"])
                vault_task.append(
                    utils.db.Vault(
                        {
                            "test_path": row["test_path"],
                            "elapsed_time": row["elapsed_time"],
                            "aborted": row["aborted"],
                            "skipped": row["skipped"],
                        }
                    )
                )
            # get number of warning/errors/fatal
            for group in tmp_vault:
                for task in types:
                    for test in tmp_vault.get(group).get(task):
                        c.execute(
                            (
                                "SELECT DISTINCT rule, count(rule) as nb "
                                f"FROM '{test.test_path}' "
                                "WHERE task_name LIKE ?"
                            ),
                            [task],
                        )
                        for row in c.fetchall():
                            test.set(row["rule"], row["nb"])

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

    def fill_template(tmpl_path: str, html_path: str):
        try:
            tmpl = Template(filename=tmpl_path)
            with open(html_path, "w+") as fp:
                fp.write(tmpl.render(db=tmp_vault))
        except Exception:
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

#!/usr/bin/env python3
# coding: utf-8

import os
import time
import glob
import sqlite3
import common.relog
import common.utils as utils
from doit.reporter import ConsoleReporter
from dataclasses import dataclass


@dataclass
class RelogTask:
    test_path: str
    task_name: str
    start_time: float
    end_time: float = 0.0
    aborted: int = 0
    skipped: int = 0

    @staticmethod
    def create_table(test_path: str, sqlite_file: str):

        with sqlite3.connect(sqlite_file) as con:
            c = con.cursor()
            # table for the list of tasks
            c.execute(
                (
                    "CREATE TABLE IF NOT EXISTS tasks ("
                    "test_path TEXT,"  # name of the simulation
                    "task_name TEXT,"  # name of the doit task sim/cov/...
                    "start_time REAL,"
                    "end_time REAL,"
                    "aborted INTEGER,"
                    "skipped INTEGER,"
                    "PRIMARY KEY (test_path, task_name)"
                    ")"
                )
            )
            # table for the warnings/errors/fatal of the given task
            c.execute(f"DROP TABLE IF EXISTS '{test_path}'")
            c.execute(
                (
                    f"CREATE TABLE IF NOT EXISTS '{test_path}' ("
                    "id INTEGER PRIMARY KEY,"
                    "task_name TEXT,"
                    "rule TEXT,"
                    "message TEXT"
                    ")"
                )
            )
            con.commit()

    def _factory(self, cursor, row):
        for idx, col in enumerate(cursor.description):
            setattr(self, col[0], row[idx])
        return self

    def load(self, sqlite_file: str):
        with sqlite3.connect(sqlite_file) as con:
            con.row_factory = self._factory
            c = con.cursor()
            c.execute(
                "SELECT * FROM tasks WHERE test_path LIKE ? AND task_name LIKE ?",
                [self.test_path, self.task_name],
            )
            c.fetchone()

    def save(self, sqlite_file: str):
        with sqlite3.connect(sqlite_file) as con:
            c = con.cursor()
            c.execute(
                (
                    "INSERT OR REPLACE INTO tasks ("
                    "test_path, task_name, start_time, end_time, aborted, skipped"
                    ") VALUES (?, ?, ?, ?, ?, ?)"
                ),
                [
                    self.test_path,
                    self.task_name,
                    self.start_time,
                    self.end_time,
                    self.aborted,
                    self.skipped,
                ],
            )

    def _register_rule(self, rule: str, message: str, sqlite_file: str):
        with sqlite3.connect(sqlite_file) as con:
            c = con.cursor()
            c.execute(
                (
                    f"INSERT INTO '{self.test_path}' ("
                    "task_name, rule, message"
                    ") VALUES (?, ?, ?)"
                ),
                [self.task_name, rule, common.relog._filter_color(message)],
            )

    def warning(self, message: str, sqlite_file: str):
        self._register_rule("WARNING", message, sqlite_file)

    def error(self, message: str, sqlite_file: str):
        self._register_rule("ERROR", message, sqlite_file)

    def fatal(self, message: str, sqlite_file: str):
        self._register_rule("FATAL", message, sqlite_file)
        self.load(sqlite_file)
        self.aborted = 1
        self.save(sqlite_file)

    def skip(self, sqlite_file: str):
        self.load(sqlite_file)
        self.skipped = 1
        self.save(sqlite_file)


class TaskNumber(ConsoleReporter):
    def __init__(self, outstream, options):
        super().__init__(outstream, options)
        # define db path
        self.db_path = common.relog.get_relog_dbpath()
        self.current_task = None

    def initialize(self, tasks, selected_tasks):
        if selected_tasks:
            utils.create_working_dir(selected_tasks[-1])
        # get step order
        self.steps, self.current_step = [], 1
        steps_to_check = [t for t in selected_tasks]
        while steps_to_check:
            task_name = steps_to_check.pop()
            # prevent infinite loop dependencies
            if task_name not in self.steps:
                task = tasks[task_name]
                title = task.title()
                if title and title[0] != "_":
                    self.steps.append(task_name)
                steps_to_check.extend(task.task_dep)
        self.nb_steps = len(self.steps)
        self.last_is_subtask = False

    def display_step(self, task, skipped: bool = False):
        title = task.title()
        skipped_text = "(skipped)" if skipped else ""
        if title and title[0] != "_":
            if task.name in self.steps:
                self.current_step = self.nb_steps - self.steps.index(task.name)
                self.outstream.write(
                    "[%d/%d] %s %s\n"
                    % (self.current_step, self.nb_steps, title, skipped_text)
                )
                self.last_is_subtask = False
            elif self.last_is_subtask:
                self.current_step += 1
                self.outstream.write(
                    "[-/%d] %s %s\n" % (self.current_step, title, skipped_text)
                )
                self.last_is_subtask = True
            else:
                self.current_step = 1
                self.outstream.write(
                    "[-/%d] %s %s\n" % (self.current_step, title, skipped_text)
                )
                self.last_is_subtask = True

    def execute_task(self, task):
        # extract task info to store them in db
        task_name, test_path = utils.get_task_dbinfo(task)
        # create db in case of
        RelogTask.create_table(test_path, self.db_path)
        self.current_task = RelogTask(test_path, task_name, time.clock_gettime(0))
        self.current_task.save(self.db_path)
        # print the task in console
        self.display_step(task)

    def skip_uptodate(self, task):
        if self.current_task is None:
            # extract task info to store them in db
            task_name, test_path = utils.get_task_dbinfo(task)
            self.current_task = RelogTask(test_path, task_name, 0.0, 0.0, 0, 1)
        self.current_task.skip(self.db_path)
        self.display_step(task, skipped=True)

    def runtime_error(self, msg):
        """error from doit (not from a task execution)"""
        if self.current_task is not None:
            self.current_task.load(self.db_path)
            self.current_task.end_time = time.clock_gettime(0)
            self.current_task.aborted = 1
            self.current_task.save(self.db_path)

    def add_failure(self, task, exception):
        """called when execution finishes with a failure"""
        if self.current_task is not None:
            self.current_task.fatal(exception.get_msg(), self.db_path)
            self.current_task.load(self.db_path)
            self.current_task.end_time = time.clock_gettime(0)
            self.current_task.save(self.db_path)
            self.current_task = None

    def add_success(self, task):
        """called when execution finishes successfully"""
        if self.current_task is not None:
            self.current_task.load(self.db_path)
            self.current_task.end_time = time.clock_gettime(0)
            self.current_task.save(self.db_path)
            self.current_task = None


DOIT_CONFIG = {
    "backend": "sqlite3",
    "reporter": TaskNumber,
    "action_string_formatting": "both",
    "cleanforget": True,
}


def no_title(task):
    return ""


def task_name_as_title(task):
    return task.name.split(":")[-1].capitalize()


def constant_title(s: str):
    def _(task):
        return s.capitalize()

    return _


def clean_targets(task, dryrun):
    if "WORK_DIR" not in os.environ:
        os.environ["WORK_DIR"] = utils.get_tmp_folder(type="*")
    for target in task.targets:
        for tgt in glob.glob(target):
            op = (
                os.remove
                if os.path.isfile(tgt)
                else os.rmdir
                if not os.listdir(tgt)
                else None
            )
            if op:
                op(tgt)

#!/usr/bin/env python3
# coding: utf-8

import os
import glob
import common.utils as utils
import common.relog as relog
from doit.reporter import ConsoleReporter


class TaskNumber(ConsoleReporter):
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
        self.display_step(task)

    def skip_uptodate(self, task):
        self.display_step(task, skipped=True)


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

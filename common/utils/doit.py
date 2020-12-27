#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import glob
import doit.task
import common.utils as utils
from doit.reporter import ConsoleReporter


class TaskNumber(ConsoleReporter):
    def initialize(self, tasks, selected_tasks):
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

    def display_step(self, task):
        title = task.title()
        if title and title[0] != "_":
            self.outstream.write("[%d/%d] %s\n" % (self.current_step, self.nb_steps, title))
            self.current_step += 1

    def execute_task(self, task):
        self.display_step(task)

    def skip_uptodate(self, task):
        self.display_step(task)


DOIT_CONFIG = {
    "backend": "json",
    "reporter": TaskNumber,
    "action_string_formatting": "both",
    "cleanforget": True,
}


def no_title(task):
    return ""


def task_name_as_title(task):
    return task.name.split(":")[-1].capitalize()


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
#!/usr/bin/env python3
# coding: utf-8

import sys
from functools import lru_cache
from doit.reporter import ConsoleReporter


class TaskNumber(ConsoleReporter):
    CURRENT_TASK = 1
    ENVS = globals()

    # @lru_cache(maxsize=64)
    def get_nb_subtasks(self, parent_name):
        parent = TaskNumber.ENVS.get("task_%s" % parent_name)
        nb_tasks = 0
        if parent:
            for p in parent():
                nb_tasks += 1
        return max(nb_tasks, 1)

    def initialize(self, tasks, selected_tasks):
        self.steps = []
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

    def execute_task(self, task):
        title = task.title()
        if title and title[0] != "_":
            self.outstream.write(
                "[%d/%d] %s\n" % (TaskNumber.CURRENT_TASK, self.nb_steps, title)
            )
            TaskNumber.CURRENT_TASK += 1

    def skip_uptodate(self, task):
        title = task.title()
        if title and title[0] != "_":
            self.outstream.write(
                "[%d/%d] %s\n" % (TaskNumber.CURRENT_TASK, self.nb_steps, title)
            )
            TaskNumber.CURRENT_TASK += 1


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
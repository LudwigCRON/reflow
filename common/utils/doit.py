#!/usr/bin/env python3
# coding: utf-8

from functools import lru_cache
from doit.reporter import ConsoleReporter


class TaskNumber(ConsoleReporter):
    CURRENT_TASK = 1
    ENVS = globals()

    @lru_cache(maxsize=64)
    def get_nb_subtasks(self, parent_name):
        parent = TaskNumber.ENVS.get("task_%s" % parent_name)
        nb_tasks = 0
        if parent:
            for p in parent():
                nb_tasks += 1
        return max(nb_tasks, 1)

    def execute_task(self, task):
        if not task.subtask_of or task.subtask_of != self.last_parent:
            TaskNumber.CURRENT_TASK = 1
        self.last_parent = task.subtask_of
        nb_tasks = self.get_nb_subtasks(task.subtask_of)
        title = task.title()
        if title and title[0] != "_":
            self.outstream.write(
                "[%d/%d] %s\n" % (TaskNumber.CURRENT_TASK, nb_tasks, title)
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
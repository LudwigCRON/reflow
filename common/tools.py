#!/usr/bin/env python3
# coding: utf-8

import os
import sys
from tools.batch import task_tree
import common.utils as utils
import common.config as config

from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from typing import List, Optional


def find_tool(tool_name: str, tools_paths: List[str]) -> Optional[str]:
    for tools_path in tools_paths:
        for file in Path(tools_path).rglob(f"{tool_name}/__init__.py"):
            return utils.normpath(os.path.dirname(file))
    return None


def import_tool(module_name: str, file_path: str):
    spec = spec_from_file_location(module_name, file_path)
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_tool(tool_name: str):
    """
    Import the config of the tool in the config pot
    and load the tasks defined in the tool
    """
    # locate the tool in the lookup paths `tools_paths`
    tool_path = find_tool(tool_name, config.vault.tools_paths)
    if not tool_path:
        print(f"Tool '{tool_name}' is not found")
    # add the tool's config in the config port
    config.load_tool_config(tool_name, tool_path)
    # add the parent directory in the lookup paths of the
    # python module importer
    sys.path.append(os.path.dirname(tool_path))
    # prepare binding
    if not hasattr(config.vault, "bind"):
        setattr(config.vault, "bind", {})
    if isinstance(config.vault.bind, dict):
        setattr(config.vault, "bind", config.vault.bind)
    # import the module and bind task
    tool_module = import_tool(tool_name, f"{tool_path}/__init__.py")
    for task_name in dir(tool_module):
        # consider accessible step task_ for easy cmd binding (<tool_name>_sim -> sim)
        # consider accessible step task__ not for easy cmd binding (keep <tool_name>_sim)
        # consider hidden step _task (hidden when 'run list')
        binding_name = task_name
        update_binding = True
        if task_name.startswith("_task"):
            pass
        elif task_name.startswith("task__"):
            binding_name = task_name.replace("task__", "task_")
        elif task_name.startswith("task"):
            binding_name = task_name.replace(f"task_{tool_name}_", "task_")
        else:
            update_binding = False
        # prevent collision of exising name
        # but allows replacing of forced binding
        if (
            not (
                isinstance(config.vault.bind.get(binding_name), str)
                and config.vault.bind.get(binding_name) == task_name
            )
            and binding_name in config.vault.bind
        ):
            binding_name = task_name
        if update_binding:
            config.vault.bind.set(binding_name, getattr(tool_module, task_name))

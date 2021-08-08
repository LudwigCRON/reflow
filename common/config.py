#!/usr/bin/env python3
# coding: utf-8

import os
import yaml
import common.utils as utils

from pathlib import Path
from typing import Optional


vault = utils.db.Vault()


def locate_project_yaml(base_path: str) -> Optional[str]:
    """
    locate project.yaml file either in current directory
    or from the parent in the hierarchy (up to 16 folder depth)
    """
    # load a local configuration if there is one
    for file in Path(base_path).rglob("project.yaml"):
        return utils.normpath(file)
    # can investigate parents folders for
    # a hierarchy up to 16 parents deep
    for i in range(16):
        base_path = os.path.dirname(base_path)
        for file in os.listdir(base_path):
            file_path = utils.normpath(os.path.join(base_path, file))
            if file.endswith("project.yaml") and os.path.isfile(file_path):
                return file_path
    return None


def load_config(reflow_dir: str, base_path: str) -> utils.db.Vault:
    """
    Read the default project config and overload it
    with the local project configuration file
    """
    global vault
    vault = utils.db.Vault()
    config_files = (locate_project_yaml(reflow_dir), locate_project_yaml(base_path))
    for config_file in config_files:
        if config_file:
            with open(config_file, "rt") as fp:
                vault.update(yaml.safe_load(fp))
    vault.tools_paths.append(reflow_dir)


def load_tool_config(tool_name: str, tool_path: str) -> None:
    global vault
    config_path = f"{tool_path}/config.yaml"
    if not os.path.exists(config_path):
        return None
    with open(config_path, "rt") as fp:
        vault.set(tool_name, yaml.safe_load(fp))

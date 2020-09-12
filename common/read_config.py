#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import configparser
import common.relog as relog

from pathlib import Path, PosixPath, WindowsPath


def locate_config_files(base_path: str) -> list:
    """
    locate *.config file either in current directory
    or from the parent in the hierarchy (up to 16 folder depth)
    """
    # load a local configuration if there is one
    config_files = []
    for file in Path(base_path).rglob("*.config"):
        config_files.append(str(file))
        break
    # can investigate parents folders for
    # a hierarchy up to 16 parents deep
    for i in range(16):
        if not config_files:
            base_path = os.path.dirname(base_path)
            for file in os.listdir(base_path):
                file_path = os.path.normpath(os.path.join(base_path, file))
                if file.endswith(".config") and os.path.isfile(file_path):
                    config_files.append(file_path)
        else:
            break
    return config_files


class MetaConfig(type):
    """
    *.conf file reader and merger
    then easy retrieve data from it
    """

    data = {}

    def __getattr__(cls, attr):
        if attr in MetaConfig.data.sections():
            return MetaConfig.data[attr]
        raise AttributeError(attr)

    @staticmethod
    def set_env(mapping_table: dict):
        for env_name, path in mapping_table.items():
            section, property = path.split(".", 2)
            os.environ[env_name] = MetaConfig.data[section].get(property)

    # create a default section called reflow
    @staticmethod
    def lines_generator(filepath, add_section: bool = False):
        if add_section:
            yield "[reflow]\n"
        with open(filepath, "r+") as fp:
            for line in fp:
                yield line

    @staticmethod
    def read_configs(config_files: list):
        if isinstance(config_files, (str, PosixPath)):
            config_files = [config_files]

        # use strict=False to allows redefinition with merge config files
        MetaConfig.data = configparser.SafeConfigParser(strict=False)
        for config_file in config_files:
            try:
                MetaConfig.data.readfp(MetaConfig.lines_generator(config_file), config_file)
            except configparser.MissingSectionHeaderError:
                MetaConfig.data.readfp(
                    MetaConfig.lines_generator(config_file, True), config_file
                )

    @staticmethod
    def add_configs(config_files: list):
        if isinstance(config_files, (str, PosixPath, WindowsPath)):
            config_files = [config_files]

        for config_file in config_files:
            try:
                MetaConfig.data.readfp(MetaConfig.lines_generator(config_file), config_file)
            except configparser.MissingSectionHeaderError:
                relog.error("Please add a [section] in %s to reduce scope" % config_file)
                exit(0)
            except configparser.ParsingError as e:
                relog.error("Syntax error detected in %s. Check *.ini syntax" % config_file)
                for error in e.errors:
                    print("line %d: %s" % error, file=sys.stderr)
                exit(0)


class Config(metaclass=MetaConfig):
    """
    MetaConfig renamed with possibility to call a
    section of the ini file as an attribute (syntaxic sugar)
    """

    pass

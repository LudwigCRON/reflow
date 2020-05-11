#!/usr/bin/env python3
# coding: utf-8

import configparser


def read_configs(config_files: list):
    if isinstance(config_files, str):
        config_files = [config_files]

    # create a default section called reflow
    def lines_generator(filepath):
        yield "[reflow]\n"
        with open(filepath, "r+") as fp:
            for line in fp:
                yield line

    parser = configparser.SafeConfigParser()
    for config_file in config_files:
        parser.readfp(lines_generator(config_file), config_file)

    if parser.has_section("reflow"):
        return parser["reflow"]
    return parser

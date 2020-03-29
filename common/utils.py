#!/usr/bin/env python3

import os
import re
import sys

from pathlib import Path


def read_config(config_file: str):
    config = {}
    reg = re.compile('(?P<name>\w+)\s*(\=(?P<value>.+))*')
    with open(config_file, "r+") as fp:
        for line in fp:
            m = reg.match(line)
            if m:
                name = m.group('name')
                value = ''
                if m.group('value'):
                    value = m.group('value')
                config[name] = value.strip()
    return config


def find_tool(name: str):
    spec = "**/tools/%s" % name
    for file in Path(os.environ["REFLOW"]).rglob(spec):
        return file


def get_tmp_folder():
    return os.path.join(os.getcwd(), ".tmp_sim")


def get_sources(src, out: str = None, prefix: str = "") -> tuple:
    """
    list only the files which corresponds to code
    """
    files, params = [], {}
    # write to a stream
    if isinstance(out, str):
        fp_src = open(out, "w+")
    else:
        fp_src = sys.stdout
    # parse all lines
    for line in src:
        # code file
        if ";" in line:
            path, mime = line.strip().split(';', 2)
            if out is None:
                files.append((path, mime))
            else:
                fp_src.write("%s%s\n" % (prefix, path))
        # parameter
        elif ":" in line:
            a, b = line.split(':', 2)
            params[a.strip()] = eval(b.strip())
    if not fp_src == sys.stdout:
        fp_src.close()
    return files, params

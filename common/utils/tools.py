#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import time
import numpy
import datetime

from pathlib import Path
from importlib import import_module
from importlib.util import spec_from_file_location, module_from_spec

from common.utils.run import get_tmp_folder


def find_tool(name: str):
    spec = "**/tools/%s" % name
    for file in Path(os.environ["REFLOW"]).rglob(spec):
        return file


def import_tool(module_name, file, location):
    spec = spec_from_file_location(module_name, os.path.join(location, file))
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def launch_tool(
    tool_name: str, stats_name: str, callbacks: tuple = (None, None), *args, **kwargs
):
    # find the tool
    tool_path = find_tool(tool_name)
    sys.path.append(os.path.dirname(tool_path))
    # load it
    tool = import_module(tool_name)
    # execute it and time it
    t_start = time.time() * 1000.0
    pre, post = callbacks
    warnings_errors = []
    if pre:
        warnings_errors.append(pre(*args, **kwargs))
    warnings_errors.append(tool.main(*args, **kwargs))
    if post:
        warnings_errors.append(post(*args, **kwargs))
    t_end = time.time() * 1000.0
    # store statistics
    warnings, errors = numpy.nansum(warnings_errors, axis=0)
    with open(os.path.join(get_tmp_folder(), "./%s.stats" % stats_name), "w+") as fp:
        fp.write("%s\n" % datetime.datetime.now())
        fp.write("Warnings: %d\n" % warnings)
        fp.write("Errors: %d\n" % errors)
        fp.write("Sim. Time: %d\n" % (t_end - t_start))

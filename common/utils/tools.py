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
from common.read_config import Config


def find_tool(name: str):
    spec = "**/tools/%s" % name
    for file in Path(os.environ["REFLOW"]).rglob(spec):
        return str(file)


def import_tool(module_name, file, location):
    spec = spec_from_file_location(module_name, os.path.join(location, file))
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

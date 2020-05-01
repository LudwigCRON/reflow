#!/usr/bin/env python3

import os
import re
import sys
import datetime

from pathlib import Path


# ==== project.config parsing ====
def read_config(config_file: str):
    config = {}
    reg = re.compile(r"(?P<name>\w+)\s*(\=(?P<value>.+))*")
    with open(config_file, "r+") as fp:
        for line in fp:
            m = reg.match(line)
            if m:
                name = m.group("name")
                value = ""
                if m.group("value"):
                    value = m.group("value")
                config[name] = value.strip()
    return config


# ==== allow run to find a tool ====
def find_tool(name: str):
    spec = "**/tools/%s" % name
    for file in Path(os.environ["REFLOW"]).rglob(spec):
        return file


# ==== get working directory ====
def get_tmp_folder():
    if "WORK_DIR" in os.environ:
        return os.path.normpath(os.environ["WORK_DIR"])
    return os.path.normpath(os.path.join(os.getcwd(), ".tmp_sim"))


# ==== get file and mime-type ====
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
            path, mime = line.strip().split(";", 2)
            if out is None:
                files.append((path, mime))
            else:
                fp_src.write("%s%s\n" % (prefix, path))
        # parameter
        elif ":" in line:
            a, b = line.split(":", 2)
            params[a.strip()] = eval(b.strip())
    if not fp_src == sys.stdout:
        fp_src.close()
    return files, params


# ==== default pretty graph for reports ====
def default_plot_style():
    import matplotlib.style
    import matplotlib as mpl

    mpl.rcParams["font.family"] = "serif"
    mpl.rcParams["font.size"] = 8
    mpl.rcParams["figure.figsize"] = (4, 3)
    mpl.rcParams["figure.dpi"] = 200
    mpl.rcParams["savefig.dpi"] = 300
    mpl.rcParams["axes.labelsize"] = 8
    mpl.rcParams["xtick.labelsize"] = 10
    mpl.rcParams["ytick.labelsize"] = 10
    mpl.rcParams["legend.fontsize"] = 10
    mpl.rcParams["lines.linewidth"] = 1
    mpl.rcParams["errorbar.capsize"] = 3
    mpl.rcParams["mathtext.fontset"] = "cm"
    mpl.rcParams["mathtext.rm"] = "serif"
    mpl.rcParams["text.usetex"] = False
    mpl.rcParams["image.cmap"] = "cividis"
    import matplotlib.pyplot as plt


ENG_UNITS = {
    "f": 1e-15,
    "p": 1e-12,
    "n": 1e-9,
    "u": 1e-6,
    "m": 1e-3,
    "s": 1.0,
    "k": 1e3,
    "meg": 1e6,
    "g": 1e9,
    "t": 1e12
}


# ==== basic functions needed for parsers ====
def evaluate_eng_unit(val: str, unit: str):
    return parse_eng_unit("%s %s" % (val, unit), unit[-1])


def parse_eng_unit(s: str, base_unit: str = '', default: float = 1e-12):
    """
    convert eng format '<value> <unit>' in a floating point value
    supported units are:
        - f(emto)
        - p(ico)
        - n(ano)
        - u(icro)
        - m(ili)
        -  (default)
        - k(ilo)
        - meg(a)
        - g(iga)
        - t(era)

    Args:
        s (str): string to be convert
        base_unit (char): unit without the prefix s for second, F for farad, ...
        default (float): default value if error
    Returns:
        1e-12 (default) if s is not string
        the value scaled by the unit
    """
    if not isinstance(s, str):
        return default
    s = s.strip().lower()
    val = float(''.join([c for c in s if c in "0123456789."]))
    for prefix, scale in ENG_UNITS.items():
        unit = prefix + base_unit
        if unit in s:
            return val * scale
    return val


# ==== decorators for custom rules ====
RULES = {}


def list_observer(file: str):
    """
    list all functions listening for
    a specific rule applying to the file
    Args:
        file (str): file path or name for which looking functions to apply
    Returns:
        list of functions
    """
    observers = []
    for rule in RULES.keys():
        if file.endswith(rule):
            observers.extend(RULES.get(rule, []))
    return observers


def apply_for(extensions: str):
    exts = [ext.replace('*', '') for ext in extensions.split("|")]

    def decorator(func):
        for ext in exts:
            if ext in RULES:
                RULES[ext].append(func)
            else:
                RULES[ext] = [func]
    return decorator


# ======== json encoder ========
def json_encoder(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    if "to_dict" in dir(o):
        return o.to_dict()

#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import datetime


def get_sources(src, out: str = None, prefix: str = "") -> tuple:
    """
    list only the files which corresponds to code from
    an iterable (file pointer, list, ...)
    results is saved in either a stream (stdout) or a file
    Args:
        src (iterable): information stream containing files' path,
                        parameters, ...
        out      (str): path to a file
                        by default it will be sys.stdout
        prefix   (str): prefix to place in front of files' path
    Returns:
        files   (list): list of files corresponding to code
        params  (dict): dictionary of parameters and their value
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


# ==== get working directory ====
def get_tmp_folder():
    if "WORK_DIR" in os.environ:
        return os.path.normpath(os.environ["WORK_DIR"])
    return os.path.normpath(os.path.join(os.getcwd(), ".tmp_sim"))


# ======== json encoder ========
def json_encoder(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    if "to_dict" in dir(o):
        return o.to_dict()

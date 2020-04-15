import io
import os
import re
import sys
import numpy
import logging

logging.basicConfig(
    stream=sys.stdout, level=logging.INFO, format="%(levelname)s: %(message)s"
)


# ==== operational step ====
class CountCalls(object):
    instances = {}

    def __init__(self, func):
        self.func = func
        self.counter = 0
        CountCalls.instances[func] = self

    def __call__(self, *args, **kwargs):
        self.counter += 1
        return self.func(*args, **kwargs)

    def count(self):
        return self.counter

    def counts(self, f):
        return CountCalls.instances[f].counter


@CountCalls
def step(text: str, indent: int = 4):
    c = step.counter
    spacer = "".join([" "] * (indent - len(str(c)) - 1))
    sys.stdout.write("\33[1;34m")
    print("%d.%s%s" % (c, spacer, text))
    sys.stdout.write("\33[0m")


# ==== logging ====
def info(text: str, *args, **kwargs):
    sys.stdout.write("\33[1;37m")
    logging.info(text, *args, **kwargs)
    sys.stdout.write("\33[0m")


def note(text: str, *args, **kwargs):
    sys.stdout.write("\33[1;32m")
    logging.info(text, *args, **kwargs)
    sys.stdout.write("\33[0m")


def warning(text: str, *args, **kwargs):
    sys.stdout.write("\33[1;33m")
    logging.warning(text, *args, **kwargs)
    sys.stdout.write("\33[0m")


def error(text: str, *args, **kwargs):
    sys.stdout.write("\33[1;31m")
    logging.error(text, *args, **kwargs)
    sys.stdout.write("\33[0m")


# ==== summary ====
def display_log(path: str, SUMMARY: bool = False):
    """
    display log file given by path
    """
    Warnings, Errors = 0, 0
    if not os.path.exists(path):
        return None
    with open(path, "r+") as fp:
        k = 0
        for k, l in enumerate(fp.readlines()):
            if "Warning" in l:
                Warnings += 1
            elif "Error" in l:
                Errors += 1
            if not SUMMARY:
                print(l.strip())
        if k == 0:
            print("Log file is empty")
        else:
            if Warnings + Errors == 0:
                info("Succesful Operation(s)")
            elif Errors == 0:
                warning("Found %d warning(s)" % Warnings)
            else:
                error("Found %d warning(s) and %d error(s)" % (Warnings, Errors))


def get_stats(path: str):
    """
    return stats from log file of simulations
    Number of warnings
    Number of errors
    """
    Warnings, Errors = 0, 0
    if not os.path.exists(path):
        return (numpy.nan, numpy.nan)
    with open(path, "r+") as fp:
        k = 0
        for k, l in enumerate(fp.readlines()):
            if "Warning" in l:
                Warnings += 1
            elif "Error" in l:
                Errors += 1
    return Warnings, Errors


# ==== filters ====
def _filter_color(i):
    PATTERN = r"\[\d?;?\d{1,2}m"
    if isinstance(i, str):
        return re.sub(PATTERN, "", i)
    _s = i.replace(b"\033", b"").decode("utf-8")
    ans = re.sub(PATTERN, "", _s)
    return ans


def filter_stream(i):
    """
    remove coloration from the stream
    """
    if isinstance(i, io.TextIOWrapper):
        lines = i
    elif isinstance(i, str):
        lines = i.split("\n")
    else:
        lines = i.split(b"\n")
    for line in lines:
        yield _filter_color(line)

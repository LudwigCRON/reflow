import io
import os
import re
import sys
import logging
import common.utils

# ==== logging ====
logging.basicConfig(
    stream=sys.stdout, level=logging.INFO, format="%(levelname)s: %(message)s"
)


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


# ==== filters ====
def _filter_color(i):
    PATTERN = r"\[\d?;?\d{1,2}m"
    if isinstance(i, str):
        return re.sub(PATTERN, "", i.replace("\x1b", ""))
    print(i)
    _s = i.decode("utf-8").replace("\x1b", "")
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


def get_relog_dbpath():
    # in a project there is 1 single file at the top
    default_db_path = os.getenv("PROJECT_DIR", "")
    # other in batch use the top most path
    if not default_db_path:
        default_db_path = os.getenv("TOP_BATCH_DIR", "")
    # for a single run use the local dir
    if not default_db_path:
        default_db_path = os.getenv("CURRENT_DIR", "")
    default_db_path = common.utils.normpath(os.path.join(default_db_path, "relog.db"))
    return default_db_path

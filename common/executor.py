#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import shlex
import subprocess

# import traceback
import common.relog as relog


def sh_exec(
    cmd: str,
    log: str = None,
    mode: str = "w+",
    MAX_TIMEOUT: int = 300,
    SHOW_CMD: bool = False,
    SHELL: bool = False,
    CWD: str = None,
    ENV: object = None,
    NOERR: bool = False,
    NOOUT: bool = False,
):
    """
    simplify code for executing shell command
    """
    tokens = shlex.split(cmd)
    encoding = "iso-8859-1" if "nt" in os.name else "utf-8"
    try:
        if CWD is None and ENV is None:
            proc = subprocess.Popen(
                cmd if SHELL else tokens,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE if NOERR else subprocess.STDOUT,
                shell=SHELL,
            )
        elif ENV is None:
            proc = subprocess.Popen(
                cmd if SHELL else tokens,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE if NOERR else subprocess.STDOUT,
                shell=SHELL,
                cwd=CWD,
            )
        else:
            proc = subprocess.Popen(
                cmd if SHELL else tokens,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE if NOERR else subprocess.STDOUT,
                shell=SHELL,
                cwd=CWD,
                env=ENV,
            )
        if log is not None:
            if isinstance(log, str):
                fp = open(log, mode)
            else:
                fp = log
            if SHOW_CMD:
                fp.write("%s\n" % cmd)
            for line in proc.stdout:
                if not NOOUT:
                    sys.stdout.write(format_line(line.decode(encoding)))
                # remove color code of log.vh amond other things
                content = list(relog.filter_stream(line))
                if content:
                    fp.write("%s\n" % content[0])
            if isinstance(log, str):
                fp.close()
        elif not NOOUT:
            for line in proc.stdout:
                sys.stdout.write(format_line(line.decode(encoding)))
        proc.stdout.close()
        return_code = proc.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)
    except (OSError, subprocess.CalledProcessError) as e:
        # traceback.print_exc()
        return False
    except subprocess.TimeoutExpired:
        relog.error("Unexpected executer timeout")
        return False
    else:
        return True


def ish_exec(
    cmd: str,
    log: str = None,
    mode: str = "w+",
    MAX_TIMEOUT: int = 300,
    SHOW_CMD: bool = False,
    SHELL: bool = False,
    CWD: str = None,
    ENV: object = None,
    NOERR: bool = False,
):
    """
    simplify code for executing shell command
    """
    tokens = shlex.split(cmd)
    try:
        if CWD is None and ENV is None:
            proc = subprocess.Popen(
                tokens,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE if NOERR else subprocess.STDOUT,
                shell=SHELL,
            )
        elif ENV is None:
            proc = subprocess.Popen(
                tokens,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE if NOERR else subprocess.STDOUT,
                shell=SHELL,
                cwd=CWD,
            )
        else:
            proc = subprocess.Popen(
                tokens,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE if NOERR else subprocess.STDOUT,
                shell=SHELL,
                cwd=CWD,
                env=ENV,
            )
        yield proc
        if log is not None:
            with open(log, mode) as fp:
                if SHOW_CMD:
                    fp.write("%s\n" % cmd)
                for line in proc.stdout:
                    sys.stdout.write(format_line(line.decode("utf-8")))
                    # remove color code of log.vh amond other things
                    content = list(relog.filter_stream(line))
                    if content:
                        fp.write("%s\n" % content[0])
        else:
            for line in proc.stdout:
                sys.stdout.write(format_line(line.decode("utf-8")))
        proc.stdout.close()
        return_code = proc.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)
    except (OSError, subprocess.CalledProcessError):
        return False
    except subprocess.TimeoutExpired:
        relog.error("Unexpected executer timeout")
        return False
    else:
        return True


def format_line(line: str) -> str:
    # iverilog file info from log
    tags = ["info:", "warning:", "note:", "error:", "fatal:"]
    l = line[: min(32, len(line))].casefold()
    if any([l.find(tag) >= 0 for tag in tags]):
        l = line.split(":", 3)
        return ": ".join((l[0], l[-1]))
    # remove log.svh second line giving time and scope info
    if l.find("time:") >= 0:
        return ""
    return line

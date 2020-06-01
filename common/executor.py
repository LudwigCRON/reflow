#!/usr/bin/env python3
# coding: utf-8

import sys
import shlex
import subprocess
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
    NOOUT: bool = False
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
                shell=SHELL
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
        if log is not None:
            if isinstance(log, str):
                fp = open(log, mode)
            else:
                fp = log
            if SHOW_CMD:
                fp.write("%s\n" % cmd)
            for line in proc.stdout:
                if not NOOUT:
                    sys.stdout.write(line.decode("utf-8"))
                # remove color code of log.vh amond other things
                content = list(relog.filter_stream(line))
                if content:
                    fp.write("%s\n" % content[0])
            if isinstance(log, str):
                fp.close()
        elif not NOOUT:
            for line in proc.stdout:
                sys.stdout.write(line.decode("utf-8"))
        proc.stdout.close()
        return_code = proc.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)
    except (OSError, subprocess.CalledProcessError) as exception:
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
):
    """
    simplify code for executing shell command
    """
    tokens = shlex.split(cmd)
    try:
        if CWD is None and ENV is None:
            proc = subprocess.Popen(
                tokens, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=SHELL
            )
        elif ENV is None:
            proc = subprocess.Popen(
                tokens,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=SHELL,
                cwd=CWD,
            )
        else:
            proc = subprocess.Popen(
                tokens,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
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
                    sys.stdout.write(line.decode("utf-8"))
                    # remove color code of log.vh amond other things
                    content = list(relog.filter_stream(line))
                    if content:
                        fp.write("%s\n" % content[0])
        else:
            for line in proc.stdout:
                sys.stdout.write(line.decode("utf-8"))
        proc.stdout.close()
        return_code = proc.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)
    except (OSError, subprocess.CalledProcessError) as exception:
        return False
    except subprocess.TimeoutExpired:
        relog.error("Unexpected executer timeout")
        return False
    else:
        return True

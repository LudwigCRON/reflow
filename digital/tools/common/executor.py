#!/usr/bin/env python3

import sys
import shlex
import subprocess
import tools.common.utils as utils

def sh_exec(cmd: str, log: str = None, mode: str = "w+", MAX_TIMEOUT: int = 300, SHOW_CMD: bool = False):
  """
  simplify code for executing shell command
  """
  with subprocess.Popen(shlex.split(cmd),
    stdout=subprocess.PIPE, 
    stderr=subprocess.STDOUT) as proc:
    try:
      out, err = proc.communicate(timeout=MAX_TIMEOUT)
      if not log is None:
        with open(log, mode) as fp:
          if SHOW_CMD:
            fp.write(cmd+'\n')
          # remove color code of log.vh amond other things
          for line in utils.filter_stream(out):
            fp.write(line+'\n')
      sys.stdout.write(out.decode('utf-8'))
    except (OSError, subprocess.CalledProcessError) as exception:
      print("Exception occured: ", str(exception))
      return False
    except subprocess.TimeoutExpired as te:
      print("Unexpected executer timeout")
      return False
    else:
      return True
#!/usr/bin/env python3
import re
import sys
import shlex
import subprocess

def sh_exec(cmd: str, log: str = None, MAX_TIMEOUT: int = 300):
  """
  simplify code for executing shell command
  """
  with subprocess.Popen(shlex.split(cmd),
    stdout=subprocess.PIPE, 
    stderr=subprocess.STDOUT) as proc:
    try:
      out, err = proc.communicate(timeout=MAX_TIMEOUT)
      if not log is None:
        with open(log, "w+") as fp:
          # remove color code of log.vh
          _s = out.replace(b'\033', b'').decode('utf-8')
          _s = _s.replace("[0m", "")
          _s = re.sub(r"\[\d;\d{2}m", "", _s)
          fp.write(_s)
      sys.stdout.write(out.decode('utf-8'))
    except (OSError, subprocess.CalledProcessError) as exception:
      print("Exception occured: ", str(exception))
      return False
    except subprocess.TimeoutExpired as te:
      print("Unexpected executer timeout")
      return False
    else:
      return True
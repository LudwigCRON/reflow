#!/usr/bin/env python3

import io
import re
import os
import sys

def get_sources(src, out: str = None) -> tuple:
  """
  list only the files which corresponds to code
  """
  mimes, params, paths = [], {}, []
  # write to a stream
  if isinstance(out, str):
    fp_src = open(out, "w+")
  else:
    fp_src = sys.stdout
  # parse all lines
  for line in src:
    # code file
    if ";" in line:
      path, mime = line.strip().split(';', 2)
      if out is None:
        paths.append(path)
      else:
        fp_src.write(path+'\n')
      mimes.append(mime)
    # parameter
    elif ":" in line:
      a, b = line.split(':', 2)
      params[a.strip()] = eval(b.strip())
  if not fp_src == sys.stdout:
    fp_src.close()
  # select the appropriate generation mode
  mimes = list(set(mimes))
  if out is None:
    return params, mimes, paths
  return params, mimes

def display_log(path: str):
  """
  display log file given by path
  """
  if not os.path.exists(path):
    return None
  with open(path, "r+") as fp:
      k = 0
      for k, l in enumerate(fp.readlines()):
        print(l.strip())
      if k == 0:
        print("No Error Detected")

def _filter_color(i):
  PATTERN = r"\[\d?;?\d{1,2}m"
  if isinstance(i, str):
    return re.sub(PATTERN, '', i)
  _s = i.replace(b'\033', b'').decode('utf-8')
  ans = re.sub(PATTERN, '', _s)
  return ans

def filter_stream(i):
  """
  remove coloration from the stream
  """
  if isinstance(i, io.TextIOWrapper):
    lines = i
  else:
    lines = i.split(b'\n')
  for line in lines:
    yield _filter_color(line)
  return StopIteration()
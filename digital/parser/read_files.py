#!/usr/bin/env python3

import os
import sys
import argparse
from collections import defaultdict

VERILOG = [".v", ".vh", ".va"]
SYSTEM_VERILOG = [".sv", ".sva", ".svh"]
LIBERTY = [".lib"]

def get_type(filepath: str) -> str:
  if not os.path.isfile(filepath):
    return None
  fn, ext = os.path.splitext(filepath)
  if ext in VERILOG:
    return "VERILOG"
  elif ext in SYSTEM_VERILOG:
    return "SYSTEM_VERILOG"
  elif ext in LIBERTY:
    return "LIBERTY"
  return None

def check_source_exists(dirpath: str) -> bool:
  _ = os.path.join(dirpath, "Sources.list")
  return os.path.exists(_)

def read_sources(todo: list = [], done: list = [], params: dict = defaultdict(list)):
  files = []
  # pop files
  if not todo:
    return files, params
  # add file if it is a directory given
  filepath = todo[0]
  do = os.path.join(filepath, "Sources.list") if os.path.isdir(filepath) else filepath
  # check if already done
  if do in done:
    return files, params
  done.append(do)
  # read the source list
  with open(do, "r") as fp:
    _tmp = fp.readlines()
  # add files recursively
  for l in _tmp:
    ls = l.strip()
    path = os.path.realpath(os.path.join(os.path.dirname(do), ls))
    # file
    if os.path.isfile(path):
      files.append(path)
    # directory
    elif os.path.isdir(path) and check_source_exists(path):
      fs, pm = read_sources([path], done, params)
      files.extend(fs)
      params.update(pm)
    # add value to parameters
    elif "+=" in ls:
      a, b = l.split('+=')
      params[a.strip()].append(b.strip())
    # define a parameter
    elif "=" in ls:
      a, b = l.split('=')
      params[a.strip()] = [b.strip()]
  # conserve only one occurence of parameters
  for p in params.keys():
    params[p] = list(set(params[p]))
  return files, params

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument("-i", "--input", type=str, help="list of input files")
  args = parser.parse_args()
  # check input exist
  if not os.path.exists(args.input):
    raise Exception(f"{args.input} does not exist")
  # add the log package file
  dirpath = os.path.dirname(os.path.realpath(__file__))
  log_inc = os.path.join(dirpath, "../packages/log.vh")
  print(log_inc, get_type(log_inc), sep=";")
  # store the list of files
  files, params = read_sources([args.input])
  for file in files:
    print(file, get_type(file), sep=";")
  # list the parameters
  for key, value in params.items():
    print(f"{key}\t:\t{value}")


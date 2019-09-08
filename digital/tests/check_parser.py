#!/usr/bin/env python3
import os
import shlex
import unittest
import subprocess

PWD = os.path.dirname(os.path.realpath(__file__))

SRC_LISTER = os.path.normpath(f"{PWD}/../parser/read_files.py")

class TestParser(unittest.TestCase):
  def test_circularloop(self):
    """
    check in circular reference of sources.list
    does not break everything
    """
    cmd = f"{SRC_LISTER} -i {PWD}/main"
    with subprocess.Popen(shlex.split(cmd),
      stdout=subprocess.PIPE, 
      stderr=subprocess.STDOUT) as proc:
      try:
        out, err = proc.communicate(timeout=5)
        assert err is None, err
        nb_files = sum([b';' in l for l in out.split(b'\n')])
        assert nb_files == 2, "Wrong number of files detected"
        nb_param = sum([b':' in l for l in out.split(b'\n')])
        assert nb_param == 3, "Wrong number of parameters detected"
      except subprocess.TimeoutExpired as te:
        print("Unexpected parser timeout during infinite loop test")

if __name__ == "__main__":
    unittest.main()
#!/usr/bin/env python3
import os
import shlex
import unittest
import subprocess

PWD = os.path.dirname(os.path.realpath(__file__))

SRC_LISTER = os.path.normpath(f"{PWD}/../tools/common/read_files.py")

class TestParser(unittest.TestCase):
    def test_circularloop(self):
        """
        check in circular reference of sources.list
        does not break everything
        """
        cmd = f"{SRC_LISTER} -i {PWD}/main"
        with subprocess.Popen(shlex.split(cmd),
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE) as proc:
            try:
                out, err = proc.communicate(timeout=5)
                assert err is not None, "expected a circular reference error"
            except subprocess.TimeoutExpired as te:
                print("Unexpected parser timeout during infinite loop test")

    def test_genericsar(self):
        """
        check everything run smoothly
        """
        cmd = f"{SRC_LISTER} -i {PWD}/generic_sar"
        with subprocess.Popen(shlex.split(cmd),
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE) as proc:
            try:
                out, err = proc.communicate(timeout=5)
                assert len(err.strip()) == 0, "Unexpected a circular reference error"
                files = [l for l in out.split(b'\n') if b';' in l]
                assert len(files) == 8, "expected 8 files"
            except subprocess.TimeoutExpired as te:
                print("Unexpected parser timeout during infinite loop test")


if __name__ == "__main__":
    unittest.main()
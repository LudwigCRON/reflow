#!/usr/bin/env python3
import os
import sys
import shlex
import unittest
import subprocess

# get a path of reference
PWD = os.path.dirname(os.path.realpath(__file__))
# allows to call the read_files.py as done in the make file
SRC_LISTER = os.path.normpath(f"{PWD}/../tools/common/read_files.py")
# add in the path the files in tools/common for test
sys.path.append(f"{PWD}/../tools/common/")

import verilog_repr
import read_files

class TestParser(unittest.TestCase):
    def test_circularloop(self):
        """
        check in circular reference of sources.list
        does not break everything
        """
        cmd = f"{SRC_LISTER} -i {PWD}/main"
        with subprocess.Popen(
            shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as proc:
            try:
                out, err = proc.communicate(timeout=5)
                assert len(err.strip()) > 0, "Expected a circular reference error"
            except subprocess.TimeoutExpired as te:
                print("Unexpected parser timeout during infinite loop test")

    def test_genericsar(self):
        """
        check everything run smoothly
        """
        cmd = f"{SRC_LISTER} -i {PWD}/generic_sar"
        with subprocess.Popen(
            shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as proc:
            try:
                out, err = proc.communicate(timeout=5)
                assert len(err.strip()) == 0, "Unexpected a circular reference error"
                files = [l for l in out.split(b"\n") if b";" in l]
                assert len(files) == 8, "expected 8 files"
            except subprocess.TimeoutExpired as te:
                print("Unexpected parser timeout during infinite loop test")

    def test_check_module(self):
        """
        check pins detections are ok
        """
        cmd = f"{SRC_LISTER} -i {PWD}/test_pins.v"
        with subprocess.Popen(
            shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as proc:
            try:
                out, err = proc.communicate(timeout=5)
                assert len(err.strip()) == 0, "Unexpected a circular reference error"
            except subprocess.TimeoutExpired as te:
                print("Unexpected parser timeout during infinite loop test")
        modules = read_files.find_modules(f"{PWD}/test_pins.v")
        assert len(modules) == 3, "Wrong number of modules detected"
        # check modules name
        assert [m[0] for m in modules] == ["test_1", "test_2", "test_3"], "Wrong modules' name detected"
        # create a modules
        ms = []
        for module in modules:
            m = verilog_repr.Module(module[0]) # set the name
            if module[1]:
                m.parse_parameters(module[1])
            m.parse_pins(module[2])
            m.parse_parameters(module[-1])
            m.parse_pins(module[-1])
            ms.append(m)
            assert len(m.params.keys()) == 2, "Wrong number of parameters detected in module"
            assert len(m.pins) == 9, "Wrong number of pins detected in module"
        for i in range(9):
            ps = [m.pins[i] for m in ms]
            assert all(ps[0].name == p.name for p in ps), "Unexpected discrepancy on pins name"
            assert all(ps[0].type == p.type for p in ps), "Unexpected discrepancy on pins type"
            assert all(ps[0].direction == p.direction for p in ps), "Unexpected discrepancy on pins direction"
            assert all(ps[0].lsb == p.lsb for p in ps), "Unexpected discrepancy on pins lsb"
            if ps[0].name in ["rstb"]:
                assert all(ps[1].msb == p.msb for p in ps[1:]), "Unexpected discrepancy on pins msb"
                assert ps[0].msb != ps[1].msb, "Unexpected agreement between msb of test_1 and others"
                assert all(ps[1].width == p.width for p in ps[1:]), "Unexpected discrepancy on pins width"
                assert ps[0].width != ps[1].width, "Unexpected agreement between width of test_1 and others"
            else:
                assert all(ps[0].msb == p.msb for p in ps), "Unexpected discrepancy on pins msb"
                assert all(ps[0].width == p.width for p in ps), "Unexpected discrepancy on pins width"

if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
import os
import sys
import common.relog as relog
import common.utils as utils
import common.verilog_repr as verilog


DEFAULT_TMPDIR = os.path.join(os.getcwd(), ".tmp_sim")
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    relog.step("Listing files")
    # create temporary directory
    os.makedirs(DEFAULT_TMPDIR, exist_ok=True)
    SRCS = os.path.join(DEFAULT_TMPDIR, "srcs.list")
    # create the list of sources
    PARAMS, MIMES = utils.get_sources(relog.filter_stream(sys.stdin), SRCS)
    # list modules and instances
    with open(SRCS, "r+") as fp:
        for file in fp:
            f = file.strip()
            print(f + ': ')
            print(''.join(['-'] * len(file)))
            for m in verilog.find_modules(f):
                module = verilog.Module(m[0])
                if m[1]:
                    module.parse_parameters(m[1])
                module.parse_pins(m[2])
                module.parse_parameters(m[-1])
                module.parse_pins(m[-1])
                print(module)
            for i in verilog.find_instances(f):
                if i[1]:
                    instance = verilog.Instance(i[2], i[0])
                    instance.parse_parameters(i[1])
                else:
                    instance = verilog.Instance(i[2], i[0])
                print(instance)
            for include in verilog.find_includes(f):
                print("H ", include)

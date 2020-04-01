#!/usr/bin/env python3
import os
import sys

import common.relog as relog
import common.utils as utils
import common.verilog as verilog


DEFAULT_TMPDIR = os.path.join(os.getcwd(), ".tmp_sim")
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))


def main(files, params):
    # list modules and instances
    for file, mime in files:
        f = file.strip()
        print("\n%s: " % file)
        print(''.join(['-'] * (len(file) + 1)))
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


if __name__ == "__main__":
    files, params = utils.get_sources(relog.filter_stream(sys.stdin), None)
    main(files, params)

#!/usr/bin/env python3

import sys

if __name__ == "__main__":
  for line in sys.stdin:
    # code file
    if ";" in line:
      path, mime = line.strip().split(';', 2)
      if mime == "VERILOG":
        print("read_verilog", path)
      elif mime == "SYSTEM_VERILOG":
        print("read_verilog -sv", path)
      elif mime == "LIBERTY":
        print("read_liberty", path)
    else:
      print(line.strip())
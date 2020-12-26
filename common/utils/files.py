#!/usr/bin/env python3
# coding: utf-8

import os


TYPES = {
    "VERILOG_AMS": [".vams"],
    "VERILOG": [".v", ".vh", ".va"],
    "SYSTEM_VERILOG": [".sv", ".svh"],
    "ASSERTIONS": [".sva"],
    "ANALOG": [".scs", ".cir", ".asc", ".sp"],
    "LIBERTY": [".lib"],
}


# ==== mime-type of files ====
def get_type(filepath: str) -> str:
    if not os.path.isfile(filepath):
        return None
    _, ext = os.path.splitext(filepath)
    for k, v in TYPES.items():
        if ext in v:
            return k
    return None


def is_mixed(filepath: str) -> bool:
    return get_type(filepath) in ["VERILOG_AMS"]


def is_digital(filepath: str) -> bool:
    if not os.path.isfile(filepath):
        return "digital" in filepath
    _, ext = os.path.splitext(filepath)
    return get_type(filepath) not in ["ANALOG", None]


def is_analog(filepath: str) -> bool:
    return get_type(filepath) in ["ANALOG"]

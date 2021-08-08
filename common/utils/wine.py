#!/usr/bin/env python3
# coding: utf-8

import os

import common.relog as relog
from pathlib import Path


def locate(program: str):
    """
    locate where an exe file is store in a wine installation
    wine load application in WINEPREFIX (by default $HOME/.wine)
    """
    wineprefix = os.getenv("WINEPREFIX") or os.path.join(os.getenv("HOME"), ".wine")
    ans = []
    for file in Path(wineprefix).rglob("**/*.exe"):
        if program in str(file):
            ans.append(str(file))
    if not ans:
        relog.error(f"Check Wine and '{program}' are installed")
        exit(2)
    return ans[-1]

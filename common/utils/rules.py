#!/usr/bin/env python3
# coding: utf-8

# keep function to apply for a given criterion
RULES = {}


def list_observer(file: str):
    """
    list all functions listening for
    a specific rule applying to the file
    Args:
        file (str): file path or name for which looking functions to apply
    Returns:
        list of functions
    """
    observers = []
    for rule in RULES.keys():
        if file.endswith(rule):
            observers.extend(RULES.get(rule, []))
    return observers


def apply_for(extensions: str):
    """
    decorator to register a function to apply
    for a list of file extensions in the given format:
        *.<ext1>|*.<ext2>|*.<subext>.<ext>
    for exemple:
        *_ana.xlsx
        *.sv|*.sva|*.svh
        *.tar.gz|*.tgz

    Args:
        extensions (str): chain of character in the format above
    Returns:
        decoractor function
    """
    exts = [ext.replace('*', '') for ext in extensions.split("|")]

    def decorator(func):
        for ext in exts:
            if ext in RULES:
                RULES[ext].append(func)
            else:
                RULES[ext] = [func]
    return decorator

#!/usr/bin/env python3
# coding: utf-8


class Vault:
    """
    Local only object to store variables between tasks
    of a given tool
    """

    def __init__(self, d: dict = {}) -> None:
        self.update(d)

    def __setattr__(self, name, value):
        if isinstance(value, dict):
            value = Vault(value)
        self.__dict__[name] = value

    def __iter__(self):
        return self.__dict__.__iter__()

    def __contains__(self, item):
        return item in self.__dict__

    def get(self, name, default=None):
        return self.__dict__.get(name, default)

    def set(self, name, value):
        self.__dict__[name] = value

    def update(self, d: dict = {}) -> None:
        if d:
            self.__dict__.update(d)


def sqlite_dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

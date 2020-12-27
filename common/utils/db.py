#!/usr/bin/env python3
# coding: utf-8

import sys


class Vault(object):
    """
    Local only object to store variables between tasks
    of a given tool
    """

    def __setattr__(self, name, value):
        self.__dict__[name] = value

    def __getattr__(self, name, default=None):
        return self.__dict__.get(name, default)

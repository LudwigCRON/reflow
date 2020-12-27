#!/usr/bin/env python3
# coding: utf-8

import numpy as np


def args_interp(xa, xb, ya, yb, y):
    a = (yb - ya) / (xb - xa)
    x = (y - ya) / a + xa
    return x


def interp(xa, xb, ya, yb, x):
    a = (yb - ya) / (xb - xa)
    y = a * (x - xa) + ya
    return y


class Series(object):
    def __init__(self, x: list, y: list):
        self.x = np.array(x)
        self.y = np.array(y)

    def min_value(self):
        return np.min(self.y)

    def max_value(self):
        return np.max(self.y)

    def cross(self, threshold: float, rising: bool = True, falling: bool = True):
        ans = []
        y_r = 0.0
        for i, y in enumerate(self.y):
            # rising edge crossing the threshold
            if y >= threshold and y_r < threshold and rising:
                ans.append(args_interp(self.x[i - 1], self.x[i], y_r, y, threshold))
            # falling edge crossing the threshold
            if y <= threshold and y_r > threshold and falling:
                ans.append(args_interp(self.x[i - 1], self.x[i], y_r, y, threshold))
            y_r = y
        return ans

    def value_at(self, new_x: float):
        for i, x in enumerate(self.x):
            if x > new_x:
                return interp(self.x[i - 1], self.x[i], self.y[i - 1], self.y[i], new_x)

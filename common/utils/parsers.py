#!usr/bin/env python3
# coding: utf-8

from typing import Tuple

ENG_UNITS = {
    "t": 1e12,
    "g": 1e9,
    "meg": 1e6,
    "k": 1e3,
    "s": 1.0,
    "m": 1e-3,
    "u": 1e-6,
    "n": 1e-9,
    "p": 1e-12,
    "f": 1e-15,
}


def parse_eng_unit(s: str, base_unit: str = "", default: float = 1e-12):
    """
    convert eng format '<value> <unit>' in a floating point value
    supported units are:
        - f(emto)
        - p(ico)
        - n(ano)
        - u(icro)
        - m(ili)
        -  (default)
        - k(ilo)
        - meg(a)
        - g(iga)
        - t(era)

    Args:
        s (str): string to be convert
        base_unit (char): unit without the prefix s for second, F for farad, ...
        default (float): default value if error
    Returns:
        1e-12 (default) if s is not string
        the value scaled by the unit
    """
    if not isinstance(s, str):
        return default
    s = s.strip().lower()
    val = float("".join([c for c in s if c in "0123456789.e-+"]))
    unit = "".join([c for c in s if c not in "0123456789.e-+ "])
    # remove potential unit given
    if len(unit) > len(base_unit):
        unit = "".join(unit.rsplit(base_unit, 1))
    # detect scale factor
    for prefix, scale in ENG_UNITS.items():
        if prefix in unit:
            return val * scale
    return val


def eng_str(value: float) -> Tuple[float, str]:
    for unit_name, scale in ENG_UNITS.items():
        if value // scale > 0:
            return (value / scale, unit_name)
    return (value, "")

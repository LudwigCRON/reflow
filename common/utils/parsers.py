#!usr/bin/env python3
# coding: utf-8

ENG_UNITS = {
    "f": 1e-15,
    "p": 1e-12,
    "n": 1e-9,
    "u": 1e-6,
    "m": 1e-3,
    "s": 1.0,
    "k": 1e3,
    "meg": 1e6,
    "g": 1e9,
    "t": 1e12
}


def evaluate_eng_unit(val: str, unit: str):
    return parse_eng_unit("%s %s" % (val, unit), unit[-1])


def parse_eng_unit(s: str, base_unit: str = '', default: float = 1e-12):
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
    val = float(''.join([c for c in s if c in "0123456789."]))
    for prefix, scale in ENG_UNITS.items():
        unit = prefix + base_unit
        if unit in s:
            return val * scale
    return val

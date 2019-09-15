#!/usr/bin/env python3

import re
from enum import Enum

def evaluate(text: str):
    """
    if number return the parsed number
    otherwise a text
    """
    if not isinstance(text, str):
        return text
    if all([c in "0123456789." for c in text]):
        return float(text)
    return text

#===== Instances ======
class Instance:
    __slots__ = ["name", "module_name", "params"]

    def __init__(self, name, module_name):
        self.name = name if not name is None else ""
        self.module_name = module_name if not module_name is None else ""
        self.params = {"unresolved": []}
    
    def parse_parameters(self, text: str):
        if not text is None:
            PATTERN_0 = r".([\w\-]+)\(([\w\-]+)\)"
            PATTERN_1 = r"([\w\-]+)"
            for token in text.split(','):
                # named mapping
                matches = re.finditer(PATTERN_0, token, re.DOTALL | re.MULTILINE)
                for match in matches:
                    grps = match.groups()
                    self.params[grps[0]] = evaluate(grps[1])
                # order based mapping
                matches = re.finditer(PATTERN_1, token)
                for match in matches:
                    grps = match.groups()
                    self.params["unresolved"].append(evaluate(grps[0]))

    def __str__(self):
        return f"I {self.name}: from module {self.module_name} and {len(self.params)-1} parameters"

#====== Modules =======
class Module:
    __slots__ = ["params", "pins", "name"]

    def __init__(self, name):
        self.name = name if not name is None else ""
        self.params = {}
        self.pins = []
    
    def parse_parameters(self, text: str):
        if not text is None:
            PATTERN = r"parameter\s*([\w\-]+)\s*(?:=\s*([\w\-]+))?"
            matches = re.finditer(PATTERN, text, re.DOTALL | re.MULTILINE)
            for match in matches:
                grps = match.groups()
                if len(grps) == 2:
                    self.params[grps[0]] = evaluate(grps[1])
                else:
                    self.params[grps[0]] = 0
    
    def parse_pins(self, text: str):
        if not text is None:
            PATTERN = r"([\w\s]+)([\[\]\d\s\:]+)?([\w\s]+)"
            for token in text.split(','):
                match = re.findall(PATTERN, token, re.DOTALL | re.MULTILINE)
                if match:
                    td, r, n = match[0]
                    p = Pins(n)
                    p.parse_dir(td)
                    p.parse_rng(r)
                    p.parse_type(td)
                else:
                    p = Pins(token.strip())
                self.pins.append(p)

    def __str__(self):
        return f"M {self.name}: {len(self.pins)} pins and {len(self.params)} parameters"

#======= Pins =========
class PinDirections(Enum):
    INPUT  = ">",
    OUTPUT = "<",
    INOUT  = "<>"

class PinTypes(Enum):
    WIRE       = "-",
    WOR        = "|",
    WAND       = "&",
    REG        = "r",
    ELECTRICAL = "e",
    VOLTAGE    = "v",
    CURRENT    = "i"

class Pins:
    __slots__ = ["name", "direction", "type", "width", "msb", "lsb"]

    def __init__(self, name):
        self.name = name if not name is None else ""
        self.direction = PinDirections.INOUT
        self.width = 0
        self.lsb = 0
        self.msb = 0
        self.type = PinTypes.WIRE
    
    def parse_type(self, text: str):
        if not text is None:
            if "wor" in text.lower():
                self.type = PinTypes.WOR
            elif "wand" in text.lower():
                self.type = PinTypes.WAND
            elif "reg" in text.lower():
                self.type = PinTypes.REG
            elif "electrical" in text.lower():
                self.type = PinTypes.ELECTRICAL
            elif "voltage" in text.lower():
                self.type = PinTypes.VOLTAGE
            elif "current" in text.lower():
                self.type = PinTypes.CURRENT
            else:
                self.type = PinTypes.WIRE

    def parse_dir(self, text: str):
        if not text is None:
            if "input" in text.lower():
                self.direction = PinDirections.INPUT
            elif "output" in text.lower():
                self.direction = PinDirections.OUTPUT

    def parse_rng(self, text: str):
        if not text is None:
            PATTERN = r"\[\s*(\d+)\s*:\s*(\d+)\s*\]"
            match = re.findall(PATTERN, text, re.DOTALL | re.MULTILINE)
            if match:
                a, b = match[0].groups()
                self.msb = max(int(a, 10), int(b, 10))
                self.lsb = min(int(a, 10), int(b, 10))
                self.width = self.msb - self.lsb + 1


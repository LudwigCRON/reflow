#!/usr/bin/env python3

import re
from enum import Enum

PATTERN_DIR         = r"((?!initial)[iInNoOuU]{2}[\w]+t)"
PATTERN_RNG         = r"(\[\s*[\w\-\+\(\)\*\/\$]+\s*:\s*[\w\-\+\(\)\*\/\$]+\s*\])"
PATTERN_RNG_CAPTURE = r"\[\s*([\w\-\+\(\)\*\/\$]+)\s*:\s*([\w\-\+\(\)\*\/\$]+)\s*\]"

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
        if text is None:
            return
        PATTERN_0 = r".([\w\-]+)\(([\w\-]+)\)"
        PATTERN_1 = r"([\w\-]+)"
        if not "," in text and text.strip():
            self.params[text.strip()] = None
            return
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
        if text is None:
            return
        PATTERN = r"parameter\s*([\w\-]+)\s*(?:=\s*([\w\-]+))?"
        matches = re.finditer(PATTERN, text, re.DOTALL | re.MULTILINE)
        for match in matches:
            grps = match.groups()
            if len(grps) == 2:
                self.params[grps[0]] = evaluate(grps[1])
            else:
                self.params[grps[0]] = 0
    
    def parse_pins(self, text: str):
        if text is None:
            return
        # check if useful information can be found
        if re.findall(PATTERN_DIR, text):
            PATTERN = (
                PATTERN_DIR+r"[\t\f ]*"
                r"([\w]{3,10})?"
                r"(?:[\t\f ]*"+PATTERN_RNG+r"?[\t\f ]+(\w+)[\t\f ]*),?"
                r"(?:[\t\f ]*"+PATTERN_RNG+r"?[\t\f ]+(\w+)[\t\f ]*)?,?"
                r"(?:[\t\f ]*"+PATTERN_RNG+r"?[\t\f ]+(\w+)[\t\f ]*)?,?"
                r"(?:[\t\f ]*"+PATTERN_RNG+r"?[\t\f ]+(\w+)[\t\f ]*)?,?"
            )
            # ([iInNoOuU]{2}[\w]+t)[\t\f ]*" : match input|output|inout lwercase or uppercase or mix of case
            # r"([\w]{3,10})?"               : match type of pins (wire|wor|....)
            # (\[[\w\-\+\(\)\*\/\$]+:[\w\-\+\(\)\*\/\$]+\])? : match range [msb:lsb] with parameter and operation
            # [\t\f ]+(\w+)[\t\f ]*)?,?      : match pin name with optional , to separate several pins declaration
            matches = re.findall(PATTERN, text, re.DOTALL | re.MULTILINE)
            for match in matches:
                pin_dir, pin_type, *pins = match
                for rng, pin_name in zip(pins[::2], pins[1::2]):
                    if pin_name:
                        p = Pins(pin_name)
                        p.parse_dir(pin_dir)
                        p.parse_rng(rng)
                        p.parse_type(pin_type)
                        self.pins.append(p)
            # cross check with wire/reg/real declaration of a signal for v95 support
            PATTERN = (
                r"([wW][\w]{2,3}|[rR][eE][aAgG][lL]?|electrical|voltage|current)"
                r"(?:[\t\f ]*"+PATTERN_RNG+r"?[\t\f ]+(\w+)[\t\f ]*),?"
                r"(?:[\t\f ]*"+PATTERN_RNG+r"?[\t\f ]+(\w+)[\t\f ]*)?,?"
                r"(?:[\t\f ]*"+PATTERN_RNG+r"?[\t\f ]+(\w+)[\t\f ]*)?,?"
            )
            matches = re.findall(PATTERN, text, re.DOTALL | re.MULTILINE)
            for match in matches:
                pin_type, *pins = match
                for rng, pin_name in zip(pins[::2], pins[1::2]):
                    for i, p in enumerate(self.pins):
                        if p.name == pin_name:
                            p.parse_type(pin_type)
                            p.parse_rng(rng)
                            # if discrepancy prefer data from input
                            if p.width != self.pins[i].width:
                                raise Exception(f"Unexpected discrepancy on {p.name} in module {self.name}, check linter output")
                            self.pins[i] = p

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
    REAL       = "d",
    ELECTRICAL = "e",
    VOLTAGE    = "v",
    CURRENT    = "i"

class Pins:
    __slots__ = ["name", "direction", "type", "width", "msb", "lsb"]

    def __init__(self, name):
        self.name = name if not name is None else ""
        self.direction = PinDirections.INOUT
        self.width = 1
        self.lsb = 0
        self.msb = 0
        self.type = PinTypes.WIRE
    
    def parse_type(self, text: str):
        if text is None:
            return
        if "wor" in text.lower():
            self.type = PinTypes.WOR
        elif "wand" in text.lower():
            self.type = PinTypes.WAND
        elif "reg" in text.lower():
            self.type = PinTypes.REG
        elif "real" in text.lower():
            self.type = PinTypes.REAL
        elif "electrical" in text.lower():
            self.type = PinTypes.ELECTRICAL
        elif "voltage" in text.lower():
            self.type = PinTypes.VOLTAGE
        elif "current" in text.lower():
            self.type = PinTypes.CURRENT
        else:
            self.type = PinTypes.WIRE

    def parse_dir(self, text: str):
        if text is None:
            return
        if "input" in text.lower():
            self.direction = PinDirections.INPUT
        elif "output" in text.lower():
            self.direction = PinDirections.OUTPUT

    def parse_rng(self, text: str):
        # do nothing if None
        if text is None:
            return
        # parse if match the pattern
        match = re.findall(PATTERN_RNG_CAPTURE, text, re.DOTALL | re.MULTILINE)
        if match:
            a, b = match[0]
            a, b = evaluate(a), evaluate(b)
            # defined size
            if isinstance(a, float) and isinstance(b, float):
                self.msb = int(max(a, b))
                self.lsb = int(min(a, b))
                self.width = self.msb - self.lsb + 1
            # parametric size
            else:
                self.msb = int(a) if isinstance(a, float) else a
                self.lsb = int(b) if isinstance(b, float) else b
                self.width = -1


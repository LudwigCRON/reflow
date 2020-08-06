#!/usr/bin/env python3

import re
from enum import Enum


PATTERN_DIR = r"((?!initial)[iInNoOuU]{2}[\w]+t)"
PATTERN_RNG = r"(\[\s*[\w\-\+\(\)\*\/\$]+\s*:\s*[\w\-\+\(\)\*\/\$]+\s*\])"
PATTERN_RNG_CAPTURE = r"\[\s*([\w\-\+\(\)\*\/\$]+)\s*:\s*([\w\-\+\(\)\*\/\$]+)\s*\]"


def evaluate(text: str):
    """
    if number return the parsed number
    otherwise a text
    """
    # cannot be a verilog number if
    if any([c in text for c in "*+/()GHIJKLMNOPQRSTUVXYZghijklmnopqrstuvxyz"]):
        return text
    # otherwise try to parse it
    PATTERN_NUM = "(?:(?P<size>\d+)?'(?P<base>h|d|b))?(?P<value>[0-9A-Fa-f_]+)"
    matches = re.finditer(PATTERN_NUM, text, re.DOTALL | re.MULTILINE)
    for match in matches:
        # default to integer 32-bits = 32'd0
        md = match.groupdict()
        base = md.get("base") or "d"
        size = int(md.get("size") or "32", 10)
        try:
            return (
                int(md.get("value"), 16)
                if base == "h"
                else int(md.get("value"), 2)
                if base == "b"
                else int(md.get("value"), 10)
            )
        except ValueError:
            return text
    return text


# ===== Instances ======
class Instance:
    __slots__ = ["name", "module_name", "params"]

    def __init__(self, name: str = None, module_name: str = None):
        self.name = name if name is not None else ""
        self.module_name = module_name if module_name is not None else ""
        self.params = {"unresolved": []}

    def parse_parameters(self, text: str):
        if text is None:
            return
        PATTERN_0 = r".(?P<name>[\w\-\_]+)\s*\((?P<value>[\w\-\*\/\+]+)\)"
        PATTERN_1 = r"([\w\-\_]+)"
        for token in text.split(","):
            # named mapping
            matches = re.finditer(PATTERN_0, token, re.DOTALL | re.MULTILINE)
            for match in matches:
                md = match.groupdict()
                self.params[md.get("name")] = evaluate(md.get("value"))
            # order based mapping
            matches = re.finditer(PATTERN_1, token)
            for match in matches:
                grps = match.groups()
                self.params["unresolved"].append(evaluate(grps[-1]))

    def __str__(self):
        return "I %s: from module %s and %d parameters" % (
            self.name,
            self.module_name,
            len(self.params) - 1,
        )

    def to_dict(self):
        return {k: getattr(self, k) for k in self.__slots__}

    @staticmethod
    def from_json(db):
        i = Instance()
        for k, v in db.items():
            setattr(i, k, v)
        return i


# ====== Modules =======
class Module:
    __slots__ = ["params", "pins", "name", "instances"]

    def __init__(self, name: str = None):
        self.name = name if name is not None else ""
        self.params = {}
        self.pins = []
        self.instances = []

    def parse_parameters(self, text: str):
        if text is None:
            return
        PATTERN = (
            r"parameter\s*(?P<type>integer|real|signed|time|realtime)?"
            r"\s*(?P<size>\[[\w\-:]+\])?"
            r"\s*(?P<name>[\w\-]+)"
            r"\s*(?:=\s*(?P<value>[\w\-\(\)]+))?"
        )
        matches = re.finditer(PATTERN, text, re.DOTALL | re.MULTILINE)
        for match in matches:
            md = match.groupdict()
            name = md.pop("name")
            md["value"] = evaluate(md.pop("value"))
            self.params[name] = md

    def parse_pins(self, text: str):
        if text is None:
            return
        # check if useful information can be found
        if re.findall(PATTERN_DIR, text):
            PATTERN = (
                PATTERN_DIR + r"[\t\f ]*"
                r"([\w]{3,10})?"
                r"(?:[\t\f ]*" + PATTERN_RNG + r"?[\t\f ]+(\w+)[\t\f ]*),?"
                r"(?:[\t\f ]*" + PATTERN_RNG + r"?[\t\f ]+(\w+)[\t\f ]*)?,?"
                r"(?:[\t\f ]*" + PATTERN_RNG + r"?[\t\f ]+(\w+)[\t\f ]*)?,?"
                r"(?:[\t\f ]*" + PATTERN_RNG + r"?[\t\f ]+(\w+)[\t\f ]*)?,?"
            )
            # ([iInNoOuU]{2}[\w]+t)[\t\f ]*" : match input|output|inout lowercase or
            #                                  uppercase or mix of case
            # r"([\w]{3,10})?"               : match type of pins (wire|wor|....)
            # (\[[\w\-\+\(\)\*\/\$]+:[\w\-\+\(\)\*\/\$]+\])? : match range [msb:lsb] with
            #                                                  parameter and operation
            # [\t\f ]+(\w+)[\t\f ]*)?,?      : match pin name with optional, to separate
            #                                  several pins declaration
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
                r"(?:[\t\f ]*" + PATTERN_RNG + r"?[\t\f ]+(\w+)[\t\f ]*),?"
                r"(?:[\t\f ]*" + PATTERN_RNG + r"?[\t\f ]+(\w+)[\t\f ]*)?,?"
                r"(?:[\t\f ]*" + PATTERN_RNG + r"?[\t\f ]+(\w+)[\t\f ]*)?,?"
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
                                raise Exception(
                                    "Unexpected discrepancy on %s in module %s, check linter output"
                                    % (p.name, self.name)
                                )
                            self.pins[i] = p

    def __str__(self):
        return "M %s: %d pins and %d parameters" % (
            self.name,
            len(self.pins),
            len(self.params),
        )

    def to_dict(self):
        d = {k: getattr(self, k) for k in self.__slots__ if k != "pins"}
        d["pins"] = [p.to_dict() for p in self.pins]
        d["instances"] = [i.to_dict() for i in self.instances]
        return d

    @staticmethod
    def from_json(db):
        m = Module()
        for k, v in db.items():
            setattr(m, k, v)
        m.pins = [Pins.from_json(p) for p in m.pins]
        m.instances = [Instance.from_json(i) for i in m.instances]
        return m


# ======= Pins =========
class PinDirections(str, Enum):
    INPUT = (">",)
    OUTPUT = ("<",)
    INOUT = "<>"


class PinTypes(str, Enum):
    WIRE = ("-",)
    WOR = ("|",)
    WAND = ("&",)
    REG = ("r",)
    REAL = ("d",)
    ELECTRICAL = ("e",)
    VOLTAGE = ("v",)
    CURRENT = "i"


class Pins:
    __slots__ = ["name", "direction", "type", "width", "msb", "lsb"]

    def __init__(self, name: str = None):
        self.name = name if name is not None else ""
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

    def to_dict(self):
        return {k: getattr(self, k) for k in self.__slots__}

    @staticmethod
    def from_json(db):
        p = Pins()
        for k, v in db.items():
            setattr(p, k, v)
        p.direction = PinDirections(p.direction).name
        p.type = PinTypes(p.type).name
        return p


# ==== Verilog Parsing ====
def find_modules(filepath: str) -> list:
    """
    list modules declared in the filepath
    with their parameters and the input/output ports
    """
    ans = []
    PATTERN = (
        r"(?!end)module"
        r"\s*([\w\-]+)"
        r"\s*(#\((?:[\w\.\(\),':\r\t\n \/\*\=\-]*)\))?"
        r"\s*(\([\w\.\(\),'~\r\t\n \/\*\=\-\+:\[\]]*\)|)"
        r"([\w\W\n\t]*?)endmodule"
    )
    # ^(?!end)module : start with module but not endmodule
    # \s*([\w\-]+)   : skip some spaces then get the name of the module
    # \s*(#*\([\w\s\=\-,\.\/\*]+\))? : get the optional param bloc with comments (//, /* */)
    # \s*(\([\w\s\-,\.\/\*]*\))?     : get the ports bloc with comments // or /* */
    # (.*?)                          : get all in the module in a non gready way
    # endmodule                      : should end with endmodule
    with open(filepath, "r+") as fp:
        data = fp.read()
        matches = re.finditer(PATTERN, data, re.DOTALL | re.MULTILINE)
        for match in matches:
            ans.append(match.groups())
    return ans


def find_instances(filepath: str) -> list:
    """
    list modules declared in the filepath
    """
    ans = []
    PATTERN = (
        r"(^\s*[\w\-]+)"
        r"\s+(?:#\(([\w\.\(\),\r\t\n \/\*\=\-\+:\[\]]*)\))?"
        r"\s*([\w\-]+)\s*\("
        r"([\w\.\(\)\r\t\n \/\*\=\-\+:\[\]~&|^.,'{}?]*)\);"
    )
    # filter the first group to not be module
    KEYWORDS = ["module", "define", "begin", "task", "function", "case", "endcase"]
    with open(filepath, "r+") as fp:
        matches = re.finditer(PATTERN, fp.read(), re.DOTALL | re.MULTILINE)
        for match in matches:
            grps = match.groups()
            if grps[0].lower().strip() not in KEYWORDS:
                ans.append([g.strip() if g is not None else None for g in grps])
    return ans


def find_includes(filepath: str) -> list:
    """
    list include declared in the filepath
    """
    ans = []
    PATTERN = r"`include[s]?\s*\"?([\w\/\\\.]+)"
    with open(filepath, "r+") as fp:
        for line in fp.readlines():
            ans.extend(re.findall(PATTERN, line))
    return ans


def find_timescale(filepath: str):
    """
    find timescale and return the step and accuracy
    """
    ans = []
    PATTERN = (
        r"timescale\s*(?:([\d\.]+)\s*([umnpf]?s))\s*(?:\\|\/)(?:([\d\.]+)\s*([umnpf]?s))"
    )
    with open(filepath, "r+") as fp:
        for line in fp.readlines():
            ans.extend(re.findall(PATTERN, line))
    return ans

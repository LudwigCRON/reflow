#!/usr/bin/env python3
# coding: utf-8

import os
import math

'''
TODO In the Schematic, the WINDOW and SYMATTR should be handled
TODO import a css file for the style
TODO manage the style
'''


class Symbol:
    """
    This utility class parse the asy file to generate a graph of the symbol
    such that an export utility class can easily generate a print from this graph
    """
    def __init__(self, filename: str = None):
        self.version = 4
        self.LINE    = []
        self.CIRCLE  = []
        self.RECT    = []
        self.TEXT    = []
        self.PIN     = []
        if filename is not None:
            self._parse(filename)

    @staticmethod
    def _resolve(name, library_paths):
        for lib_path in library_paths:
            p = os.path.normpath(os.path.join(lib_path, "%s.asy" % name))
            if os.path.isfile(p):
                return p
            raise FileNotFoundError("{} was not found".format(p))

    def _parse(self, filename):
        if not os.path.isfile(filename):
            raise FileNotFoundError("{} was not found".format(filename))
        with open(filename, 'r+', encoding="utf8") as file:
            for line in iter(file):
                lline = line.lower()
                if "line" in lline:
                    tmp = line.split()
                    if len(tmp) < 6:
                        raise Exception("LINE should have at least 5 parameters")
                    self.LINE.append(dict(zip(
                        ["type", "x1", "y1", "x2", "y2"],
                        [tmp[1], int(tmp[2]), -int(tmp[3]), int(tmp[4]), -int(tmp[5])]
                    )))
                elif "circle" in lline:
                    tmp = line.split()
                    if len(tmp) < 6:
                        raise Exception("CIRCLE should have at least 5 parameters")
                    self.CIRCLE.append(dict(zip(
                        ["type", "x1", "y1", "x2", "y2"],
                        [tmp[1], int(tmp[2]), -int(tmp[3]), int(tmp[4]), -int(tmp[5])]
                    )))
                elif "rectangle" in lline:
                    tmp = line.split()
                    if len(tmp) < 6:
                        raise Exception("RECTANGLE should have at least 5 parameters")
                    self.RECT.append(dict(zip(
                        ["type", "x1", "y1", "x2", "y2"],
                        [tmp[1], int(tmp[2]), -int(tmp[3]), int(tmp[4]), -int(tmp[5])]
                    )))
                elif "pin " in lline:
                    tmp = line.split()
                    if len(tmp) < 5:
                        raise Exception("PIN should have at least 4 parameters")
                    self.PIN.append(dict(zip(
                        ["x", "y", "orientation", "offset"],
                        [int(tmp[1], 10), -int(tmp[2], 10), tmp[3], int(tmp[4], 10)]
                    )))
                elif "pinattr" in lline:
                    tmp = line.split()
                    if len(tmp) < 2:
                        raise Exception("PINATTR should have at least 2 parameters")
                    self.PIN[-1][tmp[1]] = tmp[2]
                else:
                    pass


class Schematic:
    """
    This utility class parse the asc file to generate a graph of the schematic
    such that an export utility class can easily generate a print from this graph
    ex: Schematic --> PSFile/EPSFile/...
    """
    def __init__(self, filename: str = None):
        self.version = 4
        self.width   = 0
        self.height  = 0
        self.xmin    = 9999
        self.xmax    = -9999
        self.ymin    = 9999
        self.ymax    = -9999
        self.SYMBOL  = []
        self.WIRE    = []
        self.RECT    = []
        self.LINE    = []
        self.SPICE   = []
        self.COMMENT = []
        self.FLAG    = []
        self.IOPIN   = []
        if filename is not None:
            self._parse(filename)

    def _get_wire_from_point(self, x, y):
        return list(filter(lambda w: Schematic.is_point_in_wire(x, y, w), self.WIRE))

    @staticmethod
    def _get_flag_placement_in_wire(f, w):
        if Schematic.is_point_in_wire(f["x"], f["y"], w):
            if (f["x"] - w["x1"])**2 + (f["y"] - w["y1"])**2 < 10:
                return 1
            if (f["x"] - w["x2"])**2 + (f["y"] - w["y2"])**2 < 10:
                return 2
            return 0
        return -1

    @staticmethod
    def _get_wire_angle(w):
        if w["x2"] == w["x1"]:
            if (w["y2"] > w["y1"]):
                return 90
            return 270
        if w["y2"] == w["y1"]:
            if (w["x2"] > w["x1"]):
                return 0
            return 180
        dy_dx = (w["y2"] - w["y1"]) / (w["x2"] - w["x1"])
        return math.degrees(math.atan(dy_dx)) + 180 * (dy_dx < 1)

    @staticmethod
    def _get_wire_junction(schematic):
        ans = []
        for w in schematic.WIRE:
            wires = schematic._get_wire_from_point(w["x1"], w["y1"])
            if len(wires) > 2:
                ans.append({"x": w["x1"], "y": w["y1"]})
        return ans

    @staticmethod
    def is_point_in_wire(x, y, wire):
        if x < min(wire["x1"], wire["x2"]) or x > max(wire["x1"], wire["x2"]):
            return False
        if y < min(wire["y1"], wire["y2"]) or y > max(wire["y1"], wire["y2"]):
            return False
        dx1 = x - wire["x1"]
        dy1 = y - wire["y1"]
        dx2 = wire["x2"] - wire["x1"]
        dy2 = wire["y2"] - wire["y1"]
        dotp = dx1 * dx2 + dy1 * dy2
        dots = dx2**2 + dy2**2
        return (dotp <= dots and dotp >= 0)

    @staticmethod
    def tokenize(line: str, limit: int = 0):
        l = line.replace('\x00', '')
        tokens = l.split(' ', maxsplit=limit) if limit > 0 else l.split(' ')
        for token in tokens:
            try:
                yield float(token)
            except ValueError:
                yield token

    @staticmethod
    def get_cmd(line: str):
        if ' ' in line:
            i = line.index(' ')
            return line[:i].replace('\x00', '')
        return None

    @staticmethod
    def get_num(line: str):
        a = ''.join([c for c in line if c in "01234567890."])
        try:
            return float(a)
        except ValueError:
            return a

    def _parse(self, filename):
        if not os.path.isfile(filename):
            raise FileNotFoundError("{} was not found".format(filename))
        # describe the syntax of the file
        # might should think over for the benefit of telling args
        syntax = {
            "version": {"nargs": 1, "args": ["version"]},
            "sheet": {"nargs": 3, "args": ["num", "width", "height"]},
            "wire": {"nargs": 4, "args": ["x1", "y1", "x2", "y2"]},
            "flag": {"nargs": 3, "args": ["x", "y", "label"]},
            "iopin": {"nargs": 3, "args": ["x", "y", "direction"]},
            "symbol": {"nargs": 4, "args": ["reference", "x", "y", "transform"]},
            "text": {"nargs": 5, "args": ["x", "y", "pos_text", "pos_num", "text"]},
            "symattr": {"nargs": 2, "args": ["key", "value"]},
            "rectangle": {"nargs": 6, "args": ["type", "x1", "y1", "x2", "y2", "style"]},
            "line": {"nargs": 6, "args": ["type", "x1", "y1", "x2", "y2", "style"]}
        }
        # read the asc file
        with open(filename, "r+", encoding="utf-8") as file:
            for line in file:
                lline = line.lower().strip('\x00').strip()
                cmd = Schematic.get_cmd(lline)
                # if there is no command continue
                # until finding one
                if cmd is None:
                    continue
                # if cmd is not supported skip its processing
                if cmd not in syntax.keys():
                    continue
                # get args
                tokens = Schematic.tokenize(line.strip(), syntax[cmd].get("nargs", 0))
                # skip the cmd from the tokens list
                next(tokens)
                # process the command
                if cmd == "version":
                    self.version = next(tokens)
                elif cmd == "sheet":
                    # get estimated schematic limit
                    _ = next(tokens)
                    self.width = next(tokens)
                    self.height = next(tokens)
                elif cmd == "wire":
                    # bounds calculation
                    x1 = next(tokens)
                    y1 = self.height - next(tokens)
                    x2 = next(tokens)
                    y2 = self.height - next(tokens)
                    # register the wire
                    self.WIRE.append(dict(zip(["x1", "y1", "x2", "y2"], [x1, y1, x2, y2])))
                    # update limits of the schematic
                    self.xmin = min([self.xmin, x1, x2])
                    self.ymin = min([self.ymin, y1, y2])
                    self.xmax = max([self.xmax, x1, x2])
                    self.ymax = max([self.ymax, y1, y2])
                elif cmd == "flag":
                    # flags position
                    x = next(tokens)
                    y = self.height - next(tokens)
                    label = str(next(tokens))
                    # register the flag position
                    self.FLAG.append(dict(zip(
                        ["x", "y", "lbl", "orientation"],
                        [x, y, label, 0]
                    )))
                    # update limits of the schematic
                    self.xmin = min([self.xmin, x])
                    self.ymin = min([self.ymin, y])
                    self.xmax = max([self.xmax, x])
                    self.ymax = max([self.ymax, y])
                elif cmd == "iopin":
                    # pin position
                    x = next(tokens)
                    y = self.height - next(tokens)
                    direction = next(tokens)
                    # register the pin position
                    self.IOPIN.append(dict(zip(
                        ["x", "y", "type", "orientation"],
                        [x, y, direction, 0]
                    )))
                    # update limits of the schematic
                    self.xmin = min([self.xmin, x])
                    self.ymin = min([self.ymin, y])
                    self.xmax = max([self.xmax, x])
                    self.ymax = max([self.ymax, y])
                elif cmd == "symbol":
                    # symbol position and orientation
                    reference = next(tokens)
                    x = next(tokens)
                    y = self.height - next(tokens)
                    transform = next(tokens)
                    o = int(-Schematic.get_num(transform)) if 'R' in transform else 0
                    f = -1 if 'M' in transform else 1
                    # register the symbol
                    self.SYMBOL.append(dict(zip(
                        ["ref", "x", "y", "orientation", "flip"],
                        [reference, x, y, o, f]
                    )))
                    # update limits of the schematic
                    self.xmin = min([self.xmin, x])
                    self.ymin = min([self.ymin, y])
                    self.xmax = max([self.xmax, x])
                    self.ymax = max([self.ymax, y])
                elif cmd == "text":
                    # text position
                    x = next(tokens)
                    y = self.height - next(tokens)
                    pos_text = next(tokens)
                    pos_num = next(tokens)
                    text = next(tokens)
                    # register the text
                    txt = dict(zip(
                        ["x", "y", "posText", "posNum", "text"],
                        [x, y, pos_text, pos_num, text[1:]]
                    ))
                    if text[0] == ';':
                        self.COMMENT.append(txt)
                    else:
                        self.SPICE.append(txt)
                    # update limits of the schematic
                    self.xmin = min([self.xmin, x])
                    self.ymin = min([self.ymin, y])
                    self.xmax = max([self.xmax, x])
                    self.ymax = max([self.ymax, y])
                elif cmd == "symattr":
                    key = next(tokens)
                    value = next(tokens)
                    self.SYMBOL[-1][key] = value
                elif cmd == "rectangle":
                    type = next(tokens)
                    x1 = next(tokens)
                    y1 = self.height - next(tokens)
                    x2 = next(tokens)
                    y2 = self.height - next(tokens)
                    try:
                        _style = next(tokens)
                    except StopIteration:
                        _style = 0
                    self.RECT.append(dict(zip(
                        ["type", "x1", "y1", "x2", "y2", "style"],
                        [
                            type,
                            x1, y1,
                            x2, y2,
                            "solid" if _style == 0 else
                            "dash" if _style == 1 else
                            "dot" if _style == 2 else
                            "dash dot" if _style == 3 else
                            "dash dot dot"
                        ]
                    )))
                elif cmd == "line":
                    type = next(tokens)
                    x1 = next(tokens)
                    y1 = self.height - next(tokens)
                    x2 = next(tokens)
                    y2 = self.height - next(tokens)
                    try:
                        _style = next(tokens)
                    except StopIteration:
                        _style = 0
                    self.LINE.append(dict(zip(
                        ["type", "x1", "y1", "x2", "y2", "style"],
                        [
                            type,
                            x1, y1,
                            x2, y2,
                            "solid" if _style == 0 else
                            "dash" if _style == 1 else
                            "dot" if _style == 2 else
                            "dash dot" if _style == 3 else
                            "dash dot dot"
                        ]
                    )))
                else:
                    pass
            # determine the orientation of the flags and pin
            for i, flag in enumerate(self.FLAG):
                wires = self._get_wire_from_point(flag["x"], flag["y"])
                if wires:
                    self.FLAG[i]["orientation"] = Schematic._get_wire_angle(wires[0])
            for i, io in enumerate(self.IOPIN):
                wires = self._get_wire_from_point(io["x"], io["y"])
                if wires:
                    self.IOPIN[i]["orientation"] = Schematic._get_wire_angle(wires[0])

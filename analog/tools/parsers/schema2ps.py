#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import argparse

import ltspice_asc

sys.path.append(os.environ["REFLOW"])

import common.relog as relog

# TODO: input/output pin shall adapt to the text width
# TODO: fix line dash

class PSFile:
    """
    Generate a PostScript file from a Schematic
    """
    SYMBOL_LIB = []
    STYLES     = {
        "background": "#fff",
        "wire_junction": {
            "stroke": "#000",
            "fill": "none",   # none or css color format
            "kind": "round",  # round or square
            "width": 5,
            "height": 5
        },
        "wire": {
            "stroke": "#000",
            "linejoin": "round",  # round / mitter / bevel for the angle
            "linewidth": 2.5
        },
        "symbol": {
            "stroke": "#000",
            "fill": "none",
            "linewidth": 2.5,
            "fontsize": 16,
            "fontfamily": "Helvetica"
        },
        "flags": {
            "stroke": "#999",
            "fontsize": 16,
            "fontfamily": "Helvetica"
        },
        "rectangle": {
            "stroke": "#000",
            "fill": "none",
            "linewidth": 2.5
        },
        "line": {
            "stroke": "#000",
            "fill": "none",
            "linewidth": 2.5
        },
        "pins": {},
        "comment": {
            "stroke": "#3b3",
            "fontsize": 18,
            "fontfamily": "Helvetica",
            "visibility": "visible"  # visible / hidden
        },
        "spice": {
            "stroke": "#00f",
            "fontsize": 16,
            "fontfamily": "Helvetica",
            "visibility": "visible"  # visible / hidden
        },
        "attr": {
            "visibility": "visible"  # visible / hidden
        }
    }

    __contextualStyle = {
        "stroke": "#000",
        "fill": "none",
        "linewidth": 2.5,
        "linejoin": "round",
        "color": "#000",
        "fontsize": 16,
        "fontfamily": "Helvetica",
        "kind": "round",
        "width": 5,
        "height": 5
    }

    # style management
    @staticmethod
    def _parse_hex_color(hexColor):
        ps = "%f %f %f setrgbcolor\n"
        if len(hexColor) == 4:
            r = int(hexColor[1], 16) * 1.0 / 15.0
            g = int(hexColor[2], 16) * 1.0 / 15.0
            b = int(hexColor[3], 16) * 1.0 / 15.0
        elif len(hexColor) == 7:
            r = int(hexColor[1:2], 16) * 1.0 / 255.0
            g = int(hexColor[3:4], 16) * 1.0 / 255.0
            b = int(hexColor[5:6], 16) * 1.0 / 255.0
        else:
            raise Exception("the color %s is not a correct CSS hex color format" % hexColor)
        return ps % (r, g, b)

    @staticmethod
    def _parse_color(color):
        if "#" in color:
            return PSFile._parse_hex_color(color)
        else:
            raise NotImplementedError()

    @staticmethod
    def apply_style(file, rules):
        PSFile.__contextualStyle.update(rules)
        linejoin = 0 if PSFile.__contextualStyle["linejoin"] == "miter" else \
                   1 if PSFile.__contextualStyle["linejoin"] == "round" else 2
        ps  = "%s\n%s\n%s\n%s\n" % (
            PSFile._parse_color(PSFile.__contextualStyle["stroke"]),
            "%s setlinewidth" % PSFile.__contextualStyle["linewidth"],
            "%s setlinejoin" % linejoin,
            "/%s findfont %s scalefont setfont" % (
                PSFile.__contextualStyle["fontfamily"],
                PSFile.__contextualStyle["fontsize"]
            )
        )
        file.write(ps)

    # implement symbol library
    @staticmethod
    def add_library_path(path):
        PSFile.SYMBOL_LIB.append(path)

    # postscript generation
    @staticmethod
    def _pretty_ps(str):
        return str.replace("/", "_")

    @staticmethod
    def _pretty_text(str):
        if str[0] == "_":
            return str[1:]
        return str

    @staticmethod
    def _ps_header():
        return (
            "%%%%!PS-Adobe-3.0\n"
            "%%%%Orientation: Landscape\n"
            "%%%%Pages: 1\n"
            "%%%%EndComments\n"
            "%%%%EndProlog\n"
            "%%%%BeginSetup\n"
            "<< /PageSize [%f %f] /Orientation %d >> setpagedevice\n"
            "%%%%EndSetup\n"
            "%%%%Page: 1 1\n"
            "%%%%BeginPageSetup\n"
            "0 rotate\n"
            "%f %f translate\n"
            "1 1 scale\n"
            "%%%%EndPageSetup\n"
        )

    @staticmethod
    def _ps_macro():
        return (
            # text with a right-jusitfication
            "/rshow { dup stringwidth pop neg 0 rmoveto show} def\n"
            # ground symbol
            "/ground { /angle exch def /y exch def /x exch def gsave x y translate angle rotate newpath\n"
            + PSFile._parse_color(PSFile.STYLES["symbol"]["stroke"]) + 
            "  0 0 moveto\n"
            "  15 0 rlineto\n"
            "  -15 -15 rlineto\n"
            "  -15 15 rlineto\n"
            "  15 0 rlineto\n"
            "  closepath\n"
            "  stroke\n"
            "  grestore\n"
            "} def\n"
            # input pin symbol
            "/IPIN { /angle exch def /y exch def /x exch def gsave x y translate angle rotate newpath\n"
            "  0 0 moveto\n"
            "  -10 -10 rlineto\n"
            "  -50 0 rlineto\n"
            "  0 20 rlineto\n"
            "  50 0 rlineto\n"
            "  10 -10 rlineto\n"
            "  closepath\n"
            "  stroke\n"
            "  grestore\n"
            "} def\n"
            # output pin symbol
            "/OPIN { /angle exch def /y exch def /x exch def gsave x y translate angle rotate newpath\n"
            "  0 0 moveto\n"
            "  0 10 rlineto\n"
            "  50 0 rlineto\n"
            "  10 -10 rlineto\n"
            "  -10 -10 rlineto\n"
            "  -50 0 rlineto\n"
            "  0 10 rlineto\n"
            "  closepath\n"
            "  stroke\n"
            "  grestore\n"
            "} def\n"
            # define ellipse for use in symbols
            "/ellipse { /endangle exch def /startangle exch def /yrad exch def /xrad exch def /y exch def /x exch def\n"
            "  /savematrix matrix currentmatrix def\n"
            "  x y translate\n"
            "  xrad yrad scale\n"
            "  0 0 1 startangle endangle arc\n"
            "  savematrix\n"
            "  setmatrix\n"
            "} def\n"
        )

    @staticmethod
    def text(x0, y0, str):
        # be careful some tools will print \n
        # as two characteres and not as
        # the character 13 of an ascii table
        lines = (subline for line in str.split('\n') for subline in line.split('\\n'))
        ps = []
        x, y = x0, y0
        for line in lines:
            ps.append("%f %f moveto (%s) show\n" % (x, y, line))
            y  -= PSFile.__contextualStyle["fontsize"] * 1.25
        return ''.join(ps)

    @staticmethod
    def line(param, relative: str = ''):
        _style = param.get("style", "solid")
        print(_style)
        _ps = "[] 0 setdash\n" if _style == "solid" else \
              "[8 4] 0 setdash\n" if _style == "dash" else \
              "[4 4] 0 setdash\n" if _style == "dot" else \
              "[12 4 4 4] 0 setdash\n" if _style == "dash dot" else \
              "[12 4 4 4 4 4] 0 setdash\n"
        return (
            "gsave newpath\n"
            "%s"
            "%f %f moveto\n"
            "%f %f %slineto\n"
            "closepath\n"
            "stroke\n"
            "grestore\n"
        ) % (_ps, param["x1"], param["y1"], param["x2"], param["y2"], relative)

    @staticmethod
    def rect(param, method: str = "stroke"):
        _style = param.get("style", "solid")
        _ps = "[] 0 setdash\n" if _style == "solid" else \
              "[8 4] 0 setdash\n" if _style == "dash" else \
              "[4 4] 0 setdash\n" if _style == "dot" else \
              "[12 4 4 4] 0 setdash\n" if _style == "dash dot" else \
              "[12 4 4 4 4 4] 0 setdash\n"
        return (
            "gsave newpath\n"
            "{5}"
            "{0} {1} moveto\n"
            "{2} {1} lineto\n"
            "{2} {3} lineto\n"
            "{0} {3} lineto\n"
            "{0} {1} lineto\n"
            "closepath\n"
            "{4}\n"
            "grestore\n"
        ).format(param["x1"], param["y1"], param["x2"], param["y2"], method, _ps)

    @staticmethod
    def ellipse(param, method: str = "stroke"):
        return "%d %d %d %d 0 360 ellipse %s\n" % (
            (param["x1"] + param["x2"]) // 2,
            (param["y1"] + param["y2"]) // 2,
            (param["x1"] - param["x2"]) // 2,
            (param["y1"] - param["y2"]) // 2,
            method
        )

    @staticmethod
    def symbol(name, Symbol):
        filename = Symbol._resolve(name, PSFile.SYMBOL_LIB)
        sym = Symbol(filename)
        ps = []
        ps.append("/%s {\n" % PSFile._pretty_ps(name))
        ps.append("/flipH exch def /angle exch def /y exch def /x exch def gsave\n")
        ps.append("x y translate flipH 1 scale angle rotate \n")
        for circ in sym.CIRCLE:
            ps.append(PSFile.ellipse(circ))
        for rect in sym.RECT:
            if not PSFile.__contextualStyle["fill"] == "none":
                ps.append(PSFile._parse_color(PSFile.__contextualStyle["fill"]))
                ps.append(PSFile.rect(rect, "fill"))
                ps.append(PSFile._parse_color(PSFile.__contextualStyle["stroke"]))
            ps.append(PSFile.rect(rect))
        for line in sym.LINE:
            ps.append(PSFile.line(line))
        for pin in sym.PIN:
            if pin["orientation"] != 'NONE' and "PinName" in pin:
                if pin["orientation"] == 'TOP':
                    x, y, rightJustify = pin["x"], pin["y"] - pin["offset"] - 12, False
                elif pin["orientation"] == 'LEFT':
                    x, y, rightJustify = pin["x"] + pin["offset"], pin["y"] - 6, False
                elif pin["orientation"] == 'RIGHT':
                    x, y, rightJustify = pin["x"] - pin["offset"], pin["y"] - 6, True
                else:
                    x, y, rightJustify = pin["x"], pin["y"] + pin["offset"] - 6, False
                ps.append("{} {} moveto ({}) {}show\n".format(
                    x, y, PSFile._pretty_text(pin["PinName"]), "r" if rightJustify else ""
                ))
                if pin["PinName"][0] == '_':
                    ps.append("/startpath 0 {} rmoveto {} {} lineto stroke\n".format(
                        PSFile.__contextualStyle["fontsize"] * 1.125,
                        x,
                        y + PSFile.__contextualStyle["fontsize"] * 1.125
                    ))
        ps.append("grestore\n} def\n")
        return ''.join(ps)

    # main Factory method
    @staticmethod
    def create_from_ltspice_schematic(asc, Schematic, Symbol, output):
        if os.path.isfile(output):
            raise FileExistsError("{} already exist".format(output))
        # read and parse the file
        schematic = Schematic(asc)
        # determine page orientation
        landscape_int = (schematic.ymax - schematic.ymin) > (schematic.xmax - schematic.xmin)
        landscape_ext = schematic.height > schematic.width
        width, height = (schematic.width, schematic.height)
        #if landscape_int != landscape_ext:
        #    width, height = (schematic.height, schematic.width)
        with open(output, "w+", encoding="utf8") as file:
            # write the header for the page orientation
            file.write(PSFile._ps_header() % (
                width, height,
                0 if height > width else 3,
                0, #-schematic.xmin + (width - (schematic.xmax - schematic.xmin)) / 2,
                0, #-schematic.ymin + (height - (schematic.ymax - schematic.ymin)) / 2
            ))
            # write all macros needed for symbols etc.
            file.write(PSFile._ps_macro())
            # define the table of symbol
            PSFile.apply_style(file, PSFile.STYLES["symbol"])
            for symb in set([symb["ref"] for symb in schematic.SYMBOL]):
                file.write(PSFile.symbol(symb, Symbol))
            # define the background color
            file.write(PSFile._parse_color(PSFile.STYLES["background"]))
            file.write(PSFile.rect({
                "x1": 0, #schematic.xmin - (width - (schematic.xmax - schematic.xmin)) / 2,
                "x2": width,
                "y1": 0, #schematic.ymin - (height - (schematic.ymax - schematic.ymin)) / 2,
                "y2": height
            }, "fill"))
            # draw wires
            PSFile.apply_style(file, PSFile.STYLES["wire"])
            for wire in schematic.WIRE:
                file.write(PSFile.line(wire))
            # use a symbol from the table at a specific place
            PSFile.apply_style(file, PSFile.STYLES["symbol"])
            for symb in schematic.SYMBOL:
                file.write("{} {} {} {} {}\n".format(
                    symb["x"], symb["y"],
                    symb["orientation"], symb["flip"],
                    PSFile._pretty_ps(symb["ref"])
                ))
            for text in schematic.FLAG:
                PSFile.apply_style(file, PSFile.STYLES["flags"])
                # if 0 in spice it corresponds to the ground
                wire = schematic._get_wire_from_point(text["x"], text["y"])
                angle = 0
                if len(wire) == 1:
                    wire = wire[0]
                    fp = Schematic._get_flag_placement_in_wire(text, wire)
                    if (fp == 1 and text["orientation"] == 0) or \
                       (fp == 2 and text["orientation"] == 180):
                        angle = -90
                    elif (fp == 2 and text["orientation"] == 0) or \
                         (fp == 1 and text["orientation"] == 180):
                        angle = 90
                    elif (fp == 2 and text["orientation"] == 90) or \
                         (fp == 1 and text["orientation"] == -90):
                        angle = 180
                else:
                    fp = 0
                if text["lbl"] in ["0", "0.0"]:
                    file.write("{} {} {} ground\n".format(text["x"], text["y"], angle))
                else:
                    if angle == -90:
                        x, y, rot, rightJustify = text["x"] - 10, text["y"] - 6, 0, True
                    elif angle == 180:
                        x, y, rot, rightJustify = text["x"] + 6, text["y"] + 6, 90, False
                    elif fp == 0:
                        x, y, rot, rightJustify = text["x"], text["y"] + 6, 0, False
                    else:
                        x, y, rot, rightJustify = text["x"] + 6, text["y"] - 6, 0, False
                    file.write("gsave {} {} moveto {} rotate ({}) {}show grestore\n".format(
                        x, y, rot,
                        PSFile._pretty_text(text["lbl"]),
                        "r" if rightJustify else ""
                    ))
                    if text["lbl"][0] == "_":
                        file.write(
                            (
                                "gsave\n"
                                "newpath\n"
                                "{} {} moveto\n"
                                "{} rotate\n"
                                "{} {} rlineto\n"
                                "closepath\n"
                                "stroke\n"
                                "grestore\n"
                            ).format(
                                x,
                                y + PSFile.__contextualStyle["fontsize"] * 1.125,
                                rot,
                                PSFile.__contextualStyle["fontsize"] * (len(text["lbl"]) - 1),
                                0
                            )
                        )
            # draw rectangles
            PSFile.apply_style(file, PSFile.STYLES["rectangle"])
            for rect in schematic.RECT:
                file.write(PSFile.rect(rect, "stroke"))
            # draw lines
            PSFile.apply_style(file, PSFile.STYLES["line"])
            for line in schematic.LINE:
                file.write(PSFile.line(line))
            # draw all IOPINs
            PSFile.apply_style(file, PSFile.STYLES["pins"])
            for io in schematic.IOPIN:
                wire = schematic._get_wire_from_point(io["x"], io["y"])
                angle = 0
                if len(wire) == 1:
                    wire = wire[0]
                    fp = Schematic._get_flag_placement_in_wire(io, wire)
                    if io["orientation"] == 0 or io["orientation"] == 180:
                        angle = 0
                    elif (fp == 2 and io["orientation"] == 90):
                        angle = 90
                    elif (fp == 1 and io["orientation"] == -90):
                        angle = -90
                else:
                    fp = 0
                if io["type"] == "In":
                    file.write("{} {} {} IPIN\n".format(io["x"], io["y"], angle))
                elif io["type"] == "Out":
                    file.write("{} {} {} OPIN\n".format(io["x"], io["y"], angle))
                else:
                    pass
            # draw all wire junction
            PSFile.apply_style(file, PSFile.STYLES["wire_junction"])
            wjs = Schematic._get_wire_junction(schematic)
            for wj in wjs:
                file.write("{} {} 5 0 360 arc\nfill\n".format(wj["x"], wj["y"]))
            # show all text elements
            PSFile.apply_style(file, PSFile.STYLES["comment"])
            if PSFile.__contextualStyle["visibility"] == "visible":
                for text in schematic.COMMENT:
                    file.write(PSFile.text(
                        text["x"],
                        text["y"],
                        PSFile._pretty_text(text["text"])
                    ))
            PSFile.apply_style(file, PSFile.STYLES["spice"])
            if PSFile.__contextualStyle["visibility"] == "visible":
                for text in schematic.SPICE:
                    file.write(PSFile.text(
                        text["x"],
                        text["y"],
                        PSFile._pretty_text(text["text"])
                    ))
            # draw the all frame
            file.write("showpage")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "ltspice_asc read an asc (analog schematic) file"
            "and allows one to export into a postscript image"
            "and/or generate a jpg of it for documentation"
        )
    )
    parser.add_argument("-i", "--input", help="asc file to be read")
    parser.add_argument("-f", "--format", help="output format [ps|jpg]")
    parser.add_argument("-L", "--library", help="library path of asc", nargs='*')
    parser.add_argument("-o", "--output", help="output file", default=None)
    args = parser.parse_args()

    if args.library:
        for lib in args.library:
            if os.path.exists(lib):
                PSFile.add_library_path(lib)
    if args.output is None:
        args.output = "%s.ps" % os.path.splitext(args.input)[0]

    if "ps" in args.format.lower():
        try:
            PSFile.create_from_ltspice_schematic(
                args.input,
                ltspice_asc.Schematic,
                ltspice_asc.Symbol,
                args.output
            )
        except FileExistsError:
            os.remove(args.output)
            PSFile.create_from_ltspice_schematic(
                args.input,
                ltspice_asc.Schematic,
                ltspice_asc.Symbol,
                args.output
            )
        except Exception as e:
            relog.error(e.args)

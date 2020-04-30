#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import copy

from mako.template import Template

sys.path.append(os.environ["REFLOW"])

import common.utils as utils
import common.read_sources as read_sources
import digital.tools.libgen as libgen


@utils.apply_for("*_ana.xlsx")
def generate_lib(node, *args, **kwargs):
    """
    generate a lib file from the excel file
    describing the digital <-> analog interface
    """
    # get current workking directory
    output_dir = utils.get_tmp_folder()
    # generate libs for synthesis
    libs = libgen.main(node.name, output_dir)
    # generate a simulation verilog file
    # find a way to register generated file
    for lib in libs:
        n = copy.deepcopy(node)
        n.name = lib
        yield n


@utils.apply_for("*.v.mako")
def generate_file(node, *args, **kwargs):
    """
    generate a verilog file from a template
    and a database or a dependency
    """
    # get current workking directory
    output_dir = utils.get_tmp_folder()
    # read dependancies
    db = {"pins": []}
    # generate the template
    _tmp = Template(filename=node.name)
    with open(os.path.join(output_dir, node.name.replace(".mako", "")), "w+") as fp:
        fp.write(_tmp.render_unicode(**db))

#!/usr/bin/env python3
# coding: utf-8

import os
import copy
import json

from mako.template import Template

import common.utils as utils
import common.verilog as verilog
import common.read_sources as read_sources

import digital.tools.libgen as libgen


@utils.rules.apply_for("*_ana.xlsx")
def generate_lib(node, *args, **kwargs):
    """
    generate a lib file from the excel file
    describing the digital <-> analog interface
    """
    # get current working directory
    output_dir = utils.get_tmp_folder()
    # db path
    db_path = os.path.join(output_dir, "db.json")
    if os.path.exists(db_path):
        with open(db_path, "r") as fp:
            db = json.load(fp)
    else:
        db = {}
    if "libs" not in db:
        db["libs"] = {}
    # generate libs for synthesis
    sheetname = node.params.get("TAGS")[-1] if "TAGS" in node.params else "Timing"
    libs, lib = libgen.main(node.name, output_dir, sheetname)
    # register generated file
    for libnode in libs:
        n = copy.deepcopy(node)
        n.name = libnode
        yield n
    # register in database
    db["libs"][lib.name] = lib.to_dict()
    with open(db_path, "w+") as fp:
        fp.write(json.dumps(db, indent=2, sort_keys=True, default=utils.json_encoder))
    # generate a simulation verilog file


@utils.rules.apply_for("*.v|*.sv")
def add_in_database(node, *args, **kwargs):
    """
    add a database list all blocks and information
    concerning them to populate mako template

    if the database does not exist,
    it create the database
    """
    # get current working directory
    output_dir = utils.get_tmp_folder()
    os.makedirs(output_dir, exist_ok=True)
    # db path
    db_path = os.path.join(output_dir, "db.json")
    if os.path.exists(db_path):
        with open(db_path, "r") as fp:
            db = json.load(fp)
    else:
        db = {}
    if "includes" not in db:
        db["includes"] = []
    if "modules" not in db:
        db["modules"] = {}
    if "timescales" not in db:
        db["timescales"] = []
    # parse the verilog file
    includes = verilog.find_includes(node.name)
    db["includes"].extend(read_sources.resolve_includes(includes))
    db["timescales"].extend(verilog.find_timescale(node.name))
    for m in verilog.find_modules(node.name):
        module = verilog.Module(m[0])
        if m[1]:
            module.parse_parameters(m[1])
        module.parse_pins(m[2])
        module.parse_parameters(m[-1])
        module.parse_pins(m[-1])
        for i in verilog.find_instances(node.name):
            if i[1]:
                instance = verilog.Instance(i[2], i[0])
                instance.parse_parameters(i[1])
            else:
                instance = verilog.Instance(i[2], i[0])
            module.instances.append(instance)
        db["modules"][module.name] = module.to_dict()
    with open(db_path, "w+") as fp:
        fp.write(json.dumps(db, indent=2, sort_keys=True))


@utils.rules.apply_for("*.v.mako")
def generate_file(node, *args, **kwargs):
    """
    generate a verilog file from a template
    and a database or a dependency
    """
    # get current working directory
    output_dir = utils.get_tmp_folder()
    # read dependancies
    db_path = os.path.join(output_dir, "db.json")
    if os.path.exists(db_path):
        with open(db_path, "r") as fp:
            db = json.load(fp)
    # deserialize
    db["libs"] = {
        name: libgen.Lib.from_json(lib) for name, lib in db.get("libs", {}).items()
    }
    db["modules"] = [verilog.Module.from_json(m) for m in db.get("modules", {}).values()]
    # generate file from the template
    _tmp = Template(filename=node.name)
    with open(os.path.join(output_dir, node.name.replace(".mako", "")), "w+") as fp:
        fp.write(_tmp.render_unicode(**db))
    # return the file generated from the template
    n = copy.deepcopy(node)
    n.name = node.name.replace(".mako", "")
    return n

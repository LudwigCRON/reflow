#!/usr/bin/env python3

import os
import sys
import argparse
import traceback

from collections import defaultdict

import common.verilog as verilog

TYPES = {
    "VERILOG_AMS": [
        ".vams"
    ],
    "VERILOG": [
        ".v", ".vh", ".va"
    ],
    "SYSTEM_VERILOG": [
        ".sv", ".svh"
    ],
    "ASSERTIONS": [
        ".sva"
    ],
    "ANALOG": [
        ".scs", ".cir", ".asc", ".sp"
    ],
    "LIBERTY": [
        ".lib"
    ]
}


# = help in parsing sources.list =
def get_path(path: str, base: str = "") -> str:
    """
    resolve the absolute path of a file in the
    sources.list
    """
    # file in the current directory or relative ./ or ../
    if not path.startswith("/"):
        return os.path.realpath(os.path.join(base, path))
    # otherwise absolute path on unix os or to digital platform
    p = path[1:]
    first_dir = p.split('/', 1)[0] if "/" in p else p
    # suppose it's absolute path on unix os
    # find a common section between base and path
    b = base.lower()
    i = b.find(first_dir.lower())
    if i >= 0:
        return base[:i]
    # in digital platform
    platform = os.getenv("PLATFORM", "ganymede").lower()
    i = b.find(platform)
    if i >= 0:
        return os.path.join(
            base[: i + len(platform)],
            "digital" if is_digital(base) else
            "analog" if is_analog(base) else "mixed",
            path[1:])
    return path


def resolve_includes(files: list) -> list:
    includes = []
    # for each files which exist really
    for file in files:
        parent_dir = os.path.dirname(file)
        if os.path.isfile(file) and parent_dir:
            # iterate through include statement detected
            for inc in verilog.find_includes(file):
                # resolve the path and store it
                includes.append(get_path('/' + inc, file))
    # return the list of include to only
    # have non redundante parent directory
    includes = list(set(map(os.path.dirname, includes)))
    return [i for i in includes if os.path.exists(i)]


def is_parameter(line: str) -> bool:
    return "=" in line


def is_rules(line: str) -> bool:
    return ":" in line


# == Dependancy  Resolution ==
class Node:
    __slots__ = ["name", "edges", "params"]

    def __init__(self, name):
        self.name = name
        self.edges = []
        self.params = defaultdict(list)

    def addEdge(self, node):
        self.edges.append(node)

    def describe(self):
        print(self.name + ': ')
        print(''.join(['-'] * (len(self.name) + 2)))
        for edge in self.edges:
            if "Sources.list" in edge.name:
                edge.describe()
            else:
                print("- " + edge.name)


def resolve_dependancies(node, resolved, unresolved) -> None:
    """
    Dependency resolution algorithms taken from
    https://www.electricmonk.nl/log/2008/08/07/dependency-resolving-algorithm/
    Args:
        - node: Node of a graph (start with the top)
        - resolved: output of nodes needed in order
        - unresolved: for circular reference detection
    """
    unresolved.append(node)
    for edge in node.edges:
        if edge not in resolved:
            if edge in unresolved:
                raise Exception(
                    "Circular reference detected: %s -> %s" % (node.name, edge.name)
                )
            resolve_dependancies(edge, resolved, unresolved)
    resolved.append(node)
    unresolved.remove(node)


# ===== Verilog Parsing ======


def evaluate_time(num: str, unit: str) -> float:
    """
    parse the timescale or other time expressed in the format \\d\\s*[fpnum]?s
    """
    if isinstance(num, str):
        n = float(''.join([c for c in num if c in "0123456789."]))
    else:
        n = num
    unit = unit.strip().lower()
    u = 1e-15 if unit == "fs" else \
        1e-12 if unit == "ps" else \
        1e-09 if unit == "ns" else \
        1e-06 if unit == "us" else \
        1e-03 if unit == "ms" else 1.0
    return n * u


# ==== mime-type of files ====
def get_type(filepath: str) -> str:
    if not os.path.isfile(filepath):
        return None
    _, ext = os.path.splitext(filepath)
    for k, v in TYPES.items():
        if ext in v:
            return k
    return None


def is_digital(filepath: str) -> bool:
    if not os.path.isfile(filepath):
        return "digital" in filepath
    _, ext = os.path.splitext(filepath)
    return get_type(filepath) not in ["ANALOG", None]


def is_analog(filepath: str) -> bool:
    return get_type(filepath) in ["ANALOG"]


# ====== business logic ======
def check_source_exists(dirpath: str) -> bool:
    _ = os.path.join(dirpath, "Sources.list")
    return os.path.exists(_)


def read_sources(filepath: str, graph: dict = {}, depth: int = 0):
    """
    create a graph from a source.list file
    Args:
    - filepath: string pointing to the file
    - graph: map<string, Node> keep track of files
    - depth: int level of depth of the graph
    Outputs:
    - Node, graph: in the recursion
    - list of files ordered if depth == 0
    """
    # add file if it is a directory given
    if os.path.isdir(filepath):
        filepath = os.path.join(filepath, "Sources.list")
    # if filepath is not already in the graph
    # create a new node
    if filepath in graph.keys():
        return graph[filepath], graph
    graph[filepath] = Node(filepath)
    no = graph[filepath]
    # if the file is a sources.list
    if filepath.endswith("Sources.list"):
        # get lines in memory
        with open(filepath, "r+") as fp:
            _tmp = fp.readlines()
        # parse the file
        for line in _tmp:
            if line.strip():
                # dedicated mod
                if "@" in line:
                    line = line.split('@')[0]
                path = get_path(line.strip(), os.path.dirname(filepath))
                if not is_parameter(line):
                    # rules name is the file
                    if is_rules(line):
                        fp = line.split(':')[0]
                        graph[fp] = Node(fp)
                        no.addEdge(graph[fp])
                    # add the file
                    elif os.path.isfile(path):
                        graph[path] = Node(path)
                        no.addEdge(graph[path])
                    # is a directory
                    elif os.path.isdir(path) and check_source_exists(path):
                        n, _ = read_sources(path, graph, depth + 1)
                        no.addEdge(n)
                # add value to parameter
                elif "+=" in line:
                    a, b = line.split('+=', 1)
                    no.params[a.strip()].append(b.strip())
                # update a parameter
                elif "=" in line:
                    a, b = line.split('=', 1)
                    no.params[a.strip()] = [b.strip()]
        # if in recursion
        if depth > 0:
            return no, graph
    # resolve dependancies
    resolved = []
    resolve_dependancies(no, resolved, [])
    return resolved[::-1]


def read_from(sources_list: str, no_logger: bool = False, no_stdout: bool = True):
    files = []
    parameters = {}
    # check input exist
    if not os.path.exists(sources_list):
        raise Exception("%s does not exist" % sources_list)
    # add the log package file
    if not no_logger:
        log_inc = os.path.join(os.environ["REFLOW"], "digital/packages/log.svh")
        if no_stdout:
            files.append((log_inc, get_type(log_inc)))
        else:
            print(log_inc, get_type(log_inc), sep=";")
    # store the list of files
    graph = {}
    try:
        graph = read_sources(sources_list, {})
    except Exception:
        traceback.print_exc(file=sys.stderr)
    # display the list of files and their mime-type
    for node in graph:
        if isinstance(node, Node):
            _t = get_type(node.name)
            if _t:
                if no_stdout:
                    files.append((node.name, _t))
                else:
                    print(node.name, _t, sep=";")
    # list the parameters
    for node in graph:
        if no_stdout and isinstance(node, Node):
            parameters.update(node.params)
        elif no_stdout:
            pass
        else:
            for key, value in node.params.items():
                print("%s\t:\t%s" % (key, value))
    # define the most accurate timescale define
    min_ts = (1, "s", 1, "ms")
    for node in graph:
        if isinstance(node, Node):
            ts = verilog.find_timescale(node.name) if is_digital(node.name) else []
            if ts:
                sn, su, rn, ru = ts[0]
                if evaluate_time(sn, su) < evaluate_time(*min_ts[0:2]):
                    min_ts = (sn, su, *min_ts[2:4])
                if evaluate_time(rn, ru) < evaluate_time(*min_ts[2:4]):
                    min_ts = (*min_ts[0:2], rn, ru)
    if evaluate_time(*min_ts[0:2]) == 1.0:
        print("TIMESCALE\t:\t'1ns/100ps'")
        parameters["TIMESCALE"] = "1ns/100ps"
    else:
        print("TIMESCALE\t:\t'%s%s/%s%s'" % min_ts)
        parameters["TIMESCALE"] = "%s%s/%s%s" % min_ts
    # define the top module
    if isinstance(graph[-1], Node):
        print("TOP_MODULE\t:\t'%s'" % graph[-1].name)
        parameters["TOP_MODULE"] = graph[-1].name
    if no_stdout:
        return files, parameters


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument("-i", "--input", type=str, help="list of input files")
    parser.add_argument("-nl", "--no-logger",
                        action="store_true", help="already include logger macro")
    args = parser.parse_args()
    read_from(args.input, args.no_logger, False)

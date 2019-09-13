#!/usr/bin/env python3

import re
import os
import sys
import argparse
import traceback
from collections import defaultdict

VERILOG_AMS = [".vams"]
VERILOG = [".v", ".vh", ".va"]
SYSTEM_VERILOG = [".sv", ".svh"]
ASSERTIONS = [".sva"]
LIBERTY = [".lib"]

#= help in parsing sources.list =
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
            base[:i+len(platform)],
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
            for inc in find_includes(file):
                # resolve the path and store it
                includes.append(get_path('/'+inc, file))
    # return the list of include to only
    # have non redundante parent directory
    includes = list(set(map(os.path.dirname, includes)))
    return [i for i in includes if os.path.exists(i)]

def is_parameter(line: str) -> bool:
    return "=" in line

def is_rules(line: str) -> bool:
    return ":" in line

#== Dependancy  Resolution ==
class Node:
    __slots__ = ["name", "edges", "params"]

    def __init__(self, name):
        self.name = name
        self.edges = []
        self.params = defaultdict(list)

    def addEdge(self, node):
        self.edges.append(node)
  
    def describe(self):
        print(self.name+': ')
        print(''.join(['-']*(len(self.name)+2)))
        for edge in self.edges:
            if "Sources.list" in edge.name:
                edge.describe()
            else:
                print("- "+edge.name)

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
                raise Exception('Circular reference detected: %s -> %s' % (node.name, edge.name))
            resolve_dependancies(edge, resolved, unresolved)
    resolved.append(node)
    unresolved.remove(node)

#===== Verilog Parsing ======
def find_modules(filepath: str) -> list:
    """
    list modules declared in the filepath
    with their parameters and the input/output ports
    """
    ans = []
    PATTERN = r"^(?!end)module\s*([\w\-]+)\s*(#*\([\w\s\=\-,\.\/\*]+\))?\s*(\([\w\s\-,\.\/\*]*\))?"
    # ^(?!end)module : start with module but not endmodule
    # \s*([\w\-]+)   : skip some spaces then get the name of the module
    # \s*(#*\([\w\s\=\-,\.\/\*]+\))? : get the parameter bloc if it exist with comments // or /* */
    # \s*(\([\w\s\-,\.\/\*]*\))?     : get the ports bloc with comments // or /* */
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
    PATTERN = r"(^(?!begin|module)[\w\-]+)\s+(?:#\(([\w\W ]+,)\))?\s*([\w\-]+)\s*\("
    # filter the first group to not be module
    with open(filepath, "r+") as fp:
        matches = re.finditer(PATTERN, fp.read(), re.DOTALL | re.MULTILINE)
        for match in matches:
            grps = match.groups()
            if not grps[0].lower().strip() in ["module", "define", "begin"]:
                ans.append(grps)
    return ans

def find_includes(filepath: str) -> list:
    """
    list include declared in the filepath
    """
    ans = []
    PATTERN = r"include[s]?\s*\"?([\w\/\\\.]+)"
    with open(filepath, "r+") as fp:
        for line in fp.readlines():
            ans.extend(re.findall(PATTERN, line))
    return ans

#==== mime-type of files ====
def get_type(filepath: str) -> str:
    if not os.path.isfile(filepath):
        return None
    _, ext = os.path.splitext(filepath)
    if ext in VERILOG:
        return "VERILOG"
    elif ext in SYSTEM_VERILOG:
        return "SYSTEM_VERILOG"
    elif ext in LIBERTY:
        return "LIBERTY"
    elif ext in VERILOG_AMS:
        return "VERILOG_AMS"
    elif ext in ASSERTIONS:
        return "ASSERT"
    return None

def is_digital(filepath: str) -> bool:
    if not os.path.isfile(filepath):
        return "digital" in filepath
    _, ext = os.path.splitext(filepath)
    return any([
        ext in VERILOG,
        ext in SYSTEM_VERILOG, 
        ext in LIBERTY,
        ext in VERILOG_AMS,
        ext in ASSERTIONS])

def is_analog(filepath: str) -> bool:
    return False

#====== business logic ======
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
    filepath = os.path.join(filepath, "Sources.list") if os.path.isdir(filepath) else filepath
    # if filepath is not already in the graph
    # create a new node
    if filepath in graph.keys():
        return graph[filepath], graph
    graph[filepath] = Node(filepath)
    no = graph[filepath]
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
                    n, _ = read_sources(path, graph, depth+1)
                    no.addEdge(n)
            # add value to parameter
            elif "+=" in line:
                a, b = line.split('+=')
                no.params[a.strip()].append(b.strip())
            # update a parameter
            elif "=" in line:
                a, b = line.split('=')
                no.params[a.strip()] = [b.strip()]
    # if in recursion
    if depth > 0:
        return no, graph
    # resolve dependancies
    resolved = []
    resolve_dependancies(no, resolved, [])
    return resolved[::-1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument("-i", "--input", type=str, help="list of input files")
    parser.add_argument("-nl", "--no-logger", action="store_true", help="already include logger macro")
    args = parser.parse_args()
    # check input exist
    if not os.path.exists(args.input):
        raise Exception(f"{args.input} does not exist")
    # add the log package file
    if not args.no_logger:
        dirpath = os.path.dirname(os.path.realpath(__file__))
        log_inc = os.path.join(dirpath, "../../packages/log.vh")
        print(log_inc, get_type(log_inc), sep=";")
    # store the list of files
    graph = {}
    try:
        graph = read_sources(args.input)
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
    for node in graph:
        _t = get_type(node.name)
        if _t:
            print(node.name, _t, sep=";")
    # list the parameters
    for node in graph:
        for key, value in node.params.items():
            print(f"{key}\t:\t{value}")
    # define the top module
    print(f"TOP_MODULE\t:\t'{graph[-1].name}'")



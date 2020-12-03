#!/usr/bin/env python3

import os
import sys
import shlex
import argparse
import traceback

from enum import Enum
from collections import defaultdict, Iterable

import common.rules
import common.relog as relog
import common.utils as utils
import common.verilog as verilog


# ==== help in parsing sources.list ====
def resolve_path(path: str, base: str = "") -> str:
    """
    resolve the absolute path of a file in the
    sources.list
    """
    # file in the current directory or relative ./ or ../
    if not path.startswith("/"):
        return os.path.realpath(os.path.join(base, path))
    # otherwise absolute path on unix os or to digital platform
    p = path[1:]
    first_dir = p.split("/", 1)[0] if "/" in p else p
    # suppose it's absolute path on unix os
    # find a common section between base and path
    b = base.lower()
    i = b.find(first_dir.lower())
    if i >= 0:
        return os.path.join(base[:i], p)
    # in platform
    platform = os.getenv("PLATFORM", "ganymede").lower()
    i = b.find(platform)
    if i >= 0:
        new_path = os.path.join(
            base[: i + len(platform)],
            "digital"
            if utils.files.is_digital(base)
            else "analog"
            if utils.files.is_analog(base)
            else "mixed",
            path[1:],
        )
        if os.path.exists(new_path):
            return new_path
    # in platform without domain separation
    new_path = os.path.join(
        base[: i + len(platform)],
        path[1:],
    )
    if os.path.exists(new_path):
        return new_path
    # not known
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
                includes.append(resolve_path(inc, parent_dir))
    # return the list of include to only
    # have non redundante parent directory
    includes = list(set(map(os.path.dirname, includes)))
    return [i for i in includes if os.path.exists(i)]


def is_parameter(line: str) -> bool:
    return "=" in line


def is_rules(line: str) -> bool:
    return ":" in line


# ==== Dependancy  Resolution ====
class Node:
    __slots__ = ["name", "edges", "params"]

    def __init__(self, name):
        self.name = name
        self.edges = []
        self.params = defaultdict(list)

    def addEdge(self, node):
        # update if existing
        for i, n in enumerate(self.edges):
            if n.name == node.name:
                self.edges[i] = node
                break
        else:
            # add it otherwise
            self.edges.append(node)

    def describe(self):
        print(self.name + ": ")
        print("".join(["-"] * (len(self.name) + 2)))
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
        if edge not in resolved and edge.name not in node.name:
            if edge in unresolved:
                raise Exception(
                    "Circular reference detected: %s -> %s" % (node.name, edge.name)
                )
            resolve_dependancies(edge, resolved, unresolved)
    resolved.append(node)
    unresolved.remove(node)


# ====== business logic ======
def check_source_exists(dirpath: str) -> bool:
    _ = os.path.join(dirpath, "Sources.list")
    return os.path.exists(_)


class TokenType(Enum):
    STRING = 0
    SEP = 1
    TAG_SEP = 2
    PARAM_SEP = 3
    INDENT = 4
    NEW_LINE = 5


def source_tokenizer(buffer):
    """
    generate Sources.list tokens for parsing
    <string>
    <string>@<string>
    <string>=<string>
    <string>+=<string>

    <string>:
    <string>

    <string>:
        <string>

    """
    for line in buffer:
        start_index = 0
        is_blank_from_zero, previous, current = True, "", ""
        ln = line.expandtabs(4)
        idx_comment = ln.find("#")
        ln = ln[:idx_comment] if idx_comment > -1 else ln
        for pos, current in enumerate(ln):
            # check for indentation
            if current == " " and previous in ["", " "] and start_index == 0:
                previous = current
                continue
            elif current != " " and is_blank_from_zero and start_index == 0:
                yield (TokenType.INDENT, ln[:pos])
                start_index = pos
            # check for string
            elif current.isalnum() or current in "/\\._-() []éèàï":
                previous = current
                continue
            # check for separator
            elif current in "@:=+\n":
                # skip + as if can be part of the += token
                if current in "+" and ln[pos + 1] != "=":
                    previous = current
                    continue
                if ln[start_index:pos]:
                    yield (TokenType.STRING, ln[start_index:pos])
                    start_index = pos + 1
                # report separator
                if previous == "+" and current == "=":
                    yield (TokenType.PARAM_SEP, "+=")
                elif current == "=":
                    yield (TokenType.PARAM_SEP, "=")
                elif current == "@":
                    yield (TokenType.TAG_SEP, "@")
                elif current == "\n":
                    yield (TokenType.NEW_LINE, "")
                else:
                    yield (TokenType.SEP, current)
                start_index = pos + 1
            previous = current
            if current != " ":
                is_blank_from_zero = False
    yield (TokenType.STRING, ln[start_index:])
    yield (TokenType.NEW_LINE, "")


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
            tokens = source_tokenizer(fp)
            # parse the file
            indent_level = 0
            in_group = 0
            string = None
            parameter_name = None
            parameter_value = []
            op_increment = False
            wait_new_line = False
            beginning_of_line = True
            continue_append = False
            last_is_tag = False
            node_stack = []
            for type, token in tokens:
                # indentation management
                if type == TokenType.INDENT and beginning_of_line:
                    indent_level += 1
                    continue_append = False
                # string or parameter value with '=' or '+='
                elif type == TokenType.STRING:
                    beginning_of_line = False
                    if parameter_name is not None:
                        if op_increment or continue_append:
                            parameter_value.append(token)
                        else:
                            parameter_value = [token]
                        continue_append = False
                    # add tag to last node referenced
                    elif last_is_tag:
                        if "TAGS" in node_stack[-1].params:
                            node_stack[-1].params["TAGS"].append(token)
                        else:
                            node_stack[-1].params["TAGS"] = [token]
                    # file / parameter name / directory
                    else:
                        string = token
                        path = resolve_path(token.strip(), os.path.dirname(filepath))
                # received '@' so add tag as parameter
                elif type == TokenType.TAG_SEP:
                    node_stack.append(Node(path))
                    last_is_tag = True
                    continue_append = False
                    beginning_of_line = False
                # received ':' so the file as dependences
                elif type == TokenType.SEP:
                    if parameter_name is None:
                        node_stack.append(Node(path))
                        in_group = indent_level + 1
                        continue_append = False
                        beginning_of_line = False
                # received '=' or '+=' so previous string is a parameter name
                elif type == TokenType.PARAM_SEP:
                    if not wait_new_line:
                        parameter_name = string
                        # create default value for the parameter if not exist
                        if parameter_name not in no.params:
                            parameter_value = []
                        # parameter name [=|+=] parameter value till \n
                        if token == "+=":
                            op_increment = True
                        wait_new_line = True
                        path = None
                    else:
                        parameter_value.append("=")
                        continue_append = True
                    node_stack = []
                    beginning_of_line = False
                elif type == TokenType.NEW_LINE:
                    if parameter_name:
                        _val = no.params[parameter_name.strip()]
                        if _val and op_increment:
                            _val.extend(shlex.split("".join(parameter_value)))
                            no.params[parameter_name.strip()] = _val
                        else:
                            no.params[parameter_name.strip()] = shlex.split(
                                "".join(parameter_value)
                            )
                    # if directory read the pointed sources.list
                    elif path and os.path.isdir(path) and check_source_exists(path):
                        n, g = read_sources(path, graph, depth + 1)
                        graph.update(g)
                        if node_stack:
                            node_stack[-1].addEdge(n)
                        else:
                            no.addEdge(n)
                    # is a file
                    elif path:
                        if node_stack and last_is_tag:
                            graph[path] = node_stack.pop()
                            if node_stack:
                                node_stack[-1].addEdge(graph[path])
                            else:
                                no.addEdge(graph[path])
                        else:
                            graph[path] = Node(path)
                            no.addEdge(graph[path])
                    # stop dependencies check from ':'
                    # if empty line detected or wrong indentation
                    if indent_level < in_group:
                        while node_stack:
                            no.addEdge(node_stack.pop())
                        in_group = indent_level
                    indent_level = 0
                    path = None
                    parameter_name = None
                    parameter_value = []
                    op_increment = False
                    wait_new_line = False
                    continue_append = False
                    beginning_of_line = True
                    last_is_tag = False
        # if in recursion
        if depth > 0:
            return no, graph
    # resolve dependancies
    resolved = []
    resolve_dependancies(no, resolved, [])
    # call functions registered in rules
    ans = []
    for i, item in enumerate(resolved[::-1]):
        tmp = None
        for f in utils.rules.list_observer(item.name):
            tmp = f(item)
        if tmp:
            if isinstance(tmp, Iterable):
                ans.extend(tmp)
            else:
                ans.append(tmp)
        else:
            ans.append(item)
    # return the value
    return ans


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
            files.append((log_inc, utils.files.get_type(log_inc)))
        else:
            print(log_inc, utils.files.get_type(log_inc), sep=";")
    # store the list of files
    graph = {}
    try:
        graph = read_sources(sources_list, {})
    except FileNotFoundError as e:
        relog.error("'%s' not found" % (e.filename or e.filename2))
        exit(1)
    except Exception:
        traceback.print_exc(file=sys.stderr)
    # display the list of files and their mime-type
    for node in graph:
        if isinstance(node, Node):
            _t = utils.files.get_type(node.name)
            if _t:
                if no_stdout:
                    files.append((node.name, _t))
                else:
                    print(node.name, _t, sep=";")
    # list the parameters
    # from graph on reverse orders to apply the latest
    # value of the parameter in the hierarchy
    for node in graph[::-1]:
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
        if not isinstance(node, Node):
            continue
        if not utils.files.is_digital(node.name):
            continue
        ts = verilog.find_timescale(node.name)
        if ts:
            sn, su, rn, ru = ts[0]
            if utils.parsers.evaluate_eng_unit(sn, su) < utils.parsers.evaluate_eng_unit(
                *min_ts[0:2]
            ):
                min_ts = (sn, su, *min_ts[2:4])

            if utils.parsers.evaluate_eng_unit(rn, ru) < utils.parsers.evaluate_eng_unit(
                *min_ts[2:4]
            ):
                min_ts = (*min_ts[0:2], rn, ru)
    if utils.parsers.evaluate_eng_unit(*min_ts[0:2]) == 1.0:
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
        # normalize path of files accross platform
        files = [(f.replace("\\", "/"), m) for f, m in files]
        return files, parameters


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("-i", "--input", type=str, help="list of input files")
    parser.add_argument(
        "-nl", "--no-logger", action="store_true", help="already include logger macro"
    )
    args = parser.parse_args()
    read_from(args.input, args.no_logger, False)

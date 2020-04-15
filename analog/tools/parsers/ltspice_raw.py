#!/usr/bin/env python
# coding: utf-8

import os
import re
import sys
import copy
import struct
import argparse
import numpy as np

from pathlib import Path

sys.path.append(os.environ["REFLOW"])

import common.relog as relog


def load_raw(filename):
    """
    Parses an ascii raw data file, generates and returns a dictionary with the
    following structure:
        {
            "title": <str>,
            "date:": <str>,
            "plotname:": <str>,
            "flags:": <str>,
            "no_vars:": <str>,
            "no_points:": <str>,
            "vars": [
                { "idx": <int>, "name": <str>, "type": <str> },
                { "idx": <int>, "name": <str>, "type": <str> }
                ...
                { "idx": <int>, "name": <str>, "type": <str> }
            ]
            "values": {
                "var1": <numpy.ndarray>,
                "var2": <numpy.ndarray>,
                ...
                "varN": <numpy.ndarray>
            }
        }

        Arguments:
            :filename: path to file with raw data.
        Returns
            dict with structure described above.
    """
    if not filename.endswith(".raw"):
        for raw in Path(filename).rglob("**/*.raw"):
            if not ".op.raw" in str(raw):
                filename = str(raw)
                break
    print(filename)
    ret, header = {}, []
    mode, data, time = None, None, None
    binary_index = 0
    with open(filename, "rb") as f:
        for line in f:
            if line[0] == b"\x00":
                sline = str(
                    line.decode("utf-16-be", errors="ignore"), encoding="utf-8"
                ).strip()
            else:
                sline = str(line.replace(b"\x00", b""), encoding="utf-8").strip()
            if "Binary:" not in sline and "Values:" not in sline:
                header.append(sline)
            else:
                if "Values:" in sline:
                    relog.error("Ascii waveforms are not yet supported")
                binary_index = f.tell() + 1
                break
    # get simulation informations
    RE_KEY_VALUE = r"(?P<key>[A-Z][\w \.]+):\s*(?P<value>\w.*\w)"
    ret = {}
    matches = re.finditer(RE_KEY_VALUE, "\n".join(header))
    for match in matches:
        k, v = match.groups()
        if "Variables" != k:
            ret[k.lower().replace(". ", "_")] = v
    matches = re.search(
        r"^Variables:\s*(?P<vars>\w.*\w)", "\n".join(header), flags=re.MULTILINE | re.DOTALL
    )
    ret.update(matches.groupdict())
    if not ret:
        relog.error("No information found in raw file")
        exit(0)
    # normalize
    ret["tools"] = ret.pop("command")
    ret["no_vars"] = int(ret.pop("no_variables"))
    ret["no_points"] = int(ret["no_points"])
    ret["offset"] = float(ret["offset"])

    # vars
    pattern = r"\s*(?P<idx>\d+)\s+" r"(?P<name>\S+)\s+" r"(?P<type>.*)\s*"
    m_vars = re.finditer(pattern, ret["vars"])

    def transform(i):
        d = i.groupdict()
        d["idx"] = int(d["idx"])
        return d

    ret["vars"] = sorted((transform(i) for i in m_vars), key=lambda x: x["idx"])

    # determine mode
    if "FFT" in ret["plotname"]:
        mode = "FFT"
    elif "Transient" in ret["plotname"]:
        mode = "Transient"
    elif "AC" in ret["plotname"]:
        mode = "AC"

    # parse binary section
    nb_vars = ret["no_vars"]
    nb_pts = ret["no_points"]
    data, freq, time = [], None, None

    if mode == "FFT" or mode == "AC":
        data = np.fromfile(filename, dtype=np.complex128, offset=binary_index)
        freq = np.abs(data[::nb_vars])
        data = np.reshape(data, (nb_pts, nb_vars))
    elif mode == "Transient":
        # time is 8 bytes but is also part of variables
        # values for each variable is 4 bytes
        # so expect to have (nb_vars-1) * 4 + 8 = (nb_vars + 1) * 4
        # for each point: in total nb_pts * (nb_vars + 1) * 4
        buf_length = nb_pts * (nb_vars + 1) * 4
        # check file size to know if stepped simulation
        is_stepped = os.stat(filename).st_size > buf_length + binary_index
        print(f"stepped simulation: {is_stepped}")
        with open(filename, "rb") as fp:
            # read data
            fp.seek(binary_index)
            data = np.frombuffer(fp.read(buf_length), dtype=np.float32)
            # calculate time axis
            time = []
            for i in range(nb_pts):
                fp.seek(binary_index + i * (nb_vars + 1) * 4)
                time.append(struct.unpack("d", fp.read(8))[0])
        # reshape data
        data = np.reshape(np.array(data), (nb_pts, nb_vars + 1))
    ret["values"] = {
        ret["vars"][i - 1].get("name", ""): data[:, i] for i in range(2, nb_vars)
    }
    ret["freq"] = freq
    ret["time"] = time
    return ret


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="read ltspice raw files")
    parser.add_argument("-i", "--input", help="raw file path")
    args = parser.parse_args()
    db = load_raw(args.input)
    for i, var in enumerate(db["vars"]):
        print(var.get("name"))

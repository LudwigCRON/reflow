#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import argparse

sys.path.append(os.environ["REFLOW"])

import common.relog as relog


def check_checksum(line: str) -> bool:
    """
    sum modulo 256 of all pair of bytes
    should be 0
    Args:
        line (str): text in hexa format
    Return:
        bool
    """
    values = (int(c, 16) if i % 2 else int(c, 16) << 4 for i, c in enumerate(line[1:]))
    return sum(values) % 256 == 0


def line_split(line: str):
    """
    generate the different fields from
    the line of the file
    Args:
        line (str): text in hexa format
    Return:
        - byte count
        - both address bytes
        - record type
        - all data bytes
    """
    byte_count = int(line[1:3], 16)
    both_addr = line[3:7]
    record_type = line[7:9]
    data = line[9:-2]
    return (byte_count, both_addr, record_type, data)


def parse(file: str):
    """
    generate an hex/bin file from file into out
    """
    if not os.path.exists(file):
        relog.error("File Not Found: %s" % file)
        return
    segment = 0
    with open(file, "r+") as fp:
        for i, line in enumerate(fp):
            line = line.strip()
            if line[0] != ":":
                relog.error("missing colon at line %d" % (i+1))
            if len(line) < 11:
                relog.error("line %d is too short" % (i+1))
            if not check_checksum(line):
                relog.error("checksum invalid at line %d" % (i+1))
            # split fields
            byte_count, addr, record_type, data = line_split(line)
            # update
            address = segment + int(addr, 16)
            # is data
            if record_type == "00":
                yield (address, data)
            # is eof
            elif record_type == "01":
                if byte_count != "00" and addr != "0000":
                    relog.error("wrong EOF should be 00000001FF at line %d" % (i+1))
                return
            # is extended address for up to 1MB
            elif record_type == "02":
                segment = int(data, 16) << 4
            # is extended address for up to 4GB
            elif record_type == "04":
                segment = int(data, 16) << 16
            # precise start address
            elif record_type == "03":
                pass
            elif record_type == "05":
                pass
    return


def reshape(data: str, width: int):
    if width > 0:
        for addr, datum in data:
            count = len(datum) // width
            if count == 1:
                yield (addr, datum)
            elif count == 0:
                padding = ''.join(['0'] * (width - len(datum)))
                yield (addr, ''.join([padding, datum]))
            else:
                for i in range(count):
                    yield (addr + i, datum[i * width:(i + 1) * width])
    else:
        for d in data:
            yield d
    return


def store(data,
          out: str,
          format: str = "hex",
          start: str = "0000",
          size: int = 2**16,
          width: int = 4):
    """
    """
    ZERO = ''.join(['0'] * width)
    db = dict(reshape(data, width))
    if size < 1:
        size = max(db.keys()) - start + 1
    print("%x +: %d" % (start, size))
    if isinstance(out, str):
        with open(out, "w+") as fp:
            for addr in range(start, start + size, 1):
                fp.write("%s\n" % db.get(addr, ZERO))
    else:
        for addr in range(start, start + size, 1):
            out.write("%X %s\n" % (addr, db.get(addr, ZERO)))


def main(file: str,
         out: str,
         format: str = "hex",
         start: str = "0000",
         size: int = 2**16,
         width: int = 16):
    store(
        parse(file),
        out,
        format,
        start,
        size,
        width
    )


def any_of(chars: str, text: str):
    return any((c in text for c in chars))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "intel_hex verify the validity of an"
            "intel_hex file and transform it into"
            "a readable verilog hexa or binary file"
        )
    )
    parser.add_argument("-i", "--input", help="intel_hex input file")
    parser.add_argument("-s", "--start-address", help="memory start address", default="0", type=str)
    parser.add_argument("-l", "--length", help="length of the memory", default=-1, type=int)
    parser.add_argument("-w", "--width", help="width of memory row in byte", default=-1, type=int)
    parser.add_argument("-o", "--output", help="output file", default=sys.stdout)
    parser.add_argument(
        "-f", "--format", help="desired output format hex or bin", default="hex"
    )
    args = parser.parse_args()
    # parse start address
    if any_of("ABCDEFabcdefxh", args.start_address):
        args.start_address = args.start_address.replace('x', '')
        args.start_address = args.start_address.replace('h', '')
        args.start_address = int(args.start_address, 16)
    else:
        args.start_address = int(args.start_address, 10)
    main(args.input, args.output, args.format, args.start_address, args.length, args.width)

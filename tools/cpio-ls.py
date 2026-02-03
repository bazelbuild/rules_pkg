"""cpio file lister.

This is mini-tool to ilst the paths in a cpio archive.
"""

import sys

from tools.lib.cpio import CpioReader


def lscpio(cpio):
    while True:
        info = cpio.next()
        if not info:
            break
        if info.is_symlink:
            print(f"{info.path}: {info.uid}/{info.gid}, mode:{info.mode}, {info.size} -> {info.symlink_target}")
        else:
            print(f"{info.path}: {info.uid}/{info.gid}, mode:{info.mode}, {info.size}")


def main(args):
    if len(args) > 1:
        with open(args[1], "rb") as inp:
            cpio = CpioReader(inp)
            lscpio(cpio)
    else:
        cpio = CpioReader(sys.stdin.buffer)
        lscpio(cpio)


if __name__ == "__main__":
    main(sys.argv)

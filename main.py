#!/usr/bin/env python3
"""Entry point: copy the rendered front page to /output/entry.png.

Refuses to copy anything that is not the expected 1024x1024 PNG under
1 MiB, and prints the sha256 of the file it wrote so the copy can be
checked against news.png.
"""
import hashlib
import os
import shutil
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "news.png")
OUT = "/output/entry.png"
MAX_BYTES = 1024 * 1024


def check_png(path):
    with open(path, "rb") as fh:
        head = fh.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("%s is not a PNG file" % path)
    width, height = struct.unpack(">II", head[16:24])
    if (width, height) != (1024, 1024):
        raise ValueError("%s is %dx%d, expected 1024x1024"
                         % (path, width, height))
    size = os.path.getsize(path)
    if size > MAX_BYTES:
        raise ValueError("%s is %d bytes, over the 1 MiB limit"
                         % (path, size))
    return size


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    size = check_png(SRC)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    shutil.copyfile(SRC, OUT)
    print("wrote %s (%d bytes, sha256 %s)" % (OUT, size, sha256(OUT)))


if __name__ == "__main__":
    main()

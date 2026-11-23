#!/usr/bin/env python3
"""Entry point for the make.fun news-image-20261123 bounty.

Writes one image of Monday 23 November 2026's world news to
/output/entry.png: a dense one-page newspaper with 36 dated stories
across 7 regions, rendered by render.py from stories.json.

The program copies the image the repository holds (news.png), so it is
deterministic: two runs write the same bytes, with no network access.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    src = os.path.join(HERE, "news.png")
    os.makedirs("/output", exist_ok=True)
    # byte-for-byte copy: deterministic, no network, same output every run
    shutil.copyfile(src, "/output/entry.png")
    size = os.path.getsize("/output/entry.png")
    print(f"wrote /output/entry.png ({size} bytes)")


if __name__ == "__main__":
    main()

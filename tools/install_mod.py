#!/usr/bin/env python3
"""Install a test copy of the GD&T workbench into a FreeCAD ``Mod`` folder.

Usage::

    python tools/install_mod.py [--target <Mod dir>] [--name FreeCAD-GDT]

Without ``--target`` the user Mod folder of FreeCAD 1.1 is used
(``%APPDATA%/FreeCAD/v1-1/Mod`` on Windows, ``~/.local/share/FreeCAD/v1-1/Mod``
on Linux).  The destination folder is wiped and re-created, only the files
needed at run time are copied (no documentation, no dev tools, no binaries).
"""

import argparse
import os
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Top-level entries never shipped in the installed copy.
EXCLUDED_TOP = {".git", ".github", "Doc", "Modernisation", "tools", "tests"}
# Patterns excluded anywhere in the tree.
EXCLUDED_NAMES = {"__pycache__", "rcc.exe", ".DS_Store"}
EXCLUDED_EXT = {".pyc", ".sfd", ".FCStd1", ".FCBak", ".ts"}


def default_target():
    if sys.platform == "win32":
        base = os.path.join(os.environ["APPDATA"], "FreeCAD", "v1-1")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support/FreeCAD/v1-1")
    else:
        base = os.path.expanduser("~/.local/share/FreeCAD/v1-1")
    return os.path.join(base, "Mod")


def ignore(directory, names):
    ignored = set()
    top = os.path.normpath(directory) == os.path.normpath(REPO)
    for name in names:
        if top and name in EXCLUDED_TOP:
            ignored.add(name)
        elif name in EXCLUDED_NAMES or os.path.splitext(name)[1] in EXCLUDED_EXT:
            ignored.add(name)
    return ignored


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", default=default_target())
    parser.add_argument("--name", default="FreeCAD-GDT")
    args = parser.parse_args()

    dest = os.path.join(args.target, args.name)
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(REPO, dest, ignore=ignore)
    count = sum(len(files) for _, _, files in os.walk(dest))
    print("Installed {} files into {}".format(count, dest))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Install the workbench and run the GUI test suite inside FreeCAD.

Usage::

    python tools/run_gui_tests.py --freecad "C:/Logiciel_Cetim/FreeCAD 1.1/bin/FreeCAD.exe"
                                  [--out results.json] [--label lot0] [--no-install]

FreeCAD is started with ``tests/gui_test_gdt.py``; the script writes a JSON
report and quits FreeCAD.  A summary table is printed and the exit code is 1
if any test failed.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--freecad", required=True, help="FreeCAD GUI executable")
    parser.add_argument("--out", default=None, help="JSON report path")
    parser.add_argument("--label", default="run")
    parser.add_argument("--no-install", action="store_true")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()

    if not args.no_install:
        subprocess.check_call([sys.executable, os.path.join(REPO, "tools", "install_mod.py")])

    workdir = tempfile.mkdtemp(prefix="gdt_{}_".format(args.label))
    out = args.out or os.path.join(workdir, "results.json")
    env = dict(os.environ,
               GDT_TEST_OUT=out,
               GDT_TEST_WORKDIR=workdir,
               GDT_TEST_SAMPLES=os.path.join(REPO, "Doc"))
    script = os.path.join(REPO, "tests", "gui_test_gdt.py")
    try:
        subprocess.run([args.freecad, script], env=env, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        print("TIMEOUT: FreeCAD did not finish within {} s".format(args.timeout))
    if not os.path.isfile(out):
        print("No report produced ({})".format(out))
        return 2

    with open(out, encoding="utf-8") as f:
        data = json.load(f)
    print("FreeCAD {freecad} / Python {python} / Qt {qt}".format(**data))
    if data["startup_problems"]:
        print("Startup console problems:")
        for line in data["startup_problems"]:
            print("   ", line)
    failed = 0
    for r in data["results"]:
        print("{id:4} {status:5} {name}".format(**r))
        if r["detail"] and r["status"] != "PASS":
            for line in str(r["detail"]).strip().splitlines()[-12:]:
                print("            " + line)
        elif r["detail"]:
            print("            " + str(r["detail"]).splitlines()[0])
        for line in r["console"][:8]:
            print("      console: " + line)
        failed += r["status"] == "FAIL"
    print("Report: " + out)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

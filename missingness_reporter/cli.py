"""Command-line interface for missingness-reporter."""
import argparse
import csv
import json
import os
import sys

from .core import MISSING, report, to_markdown


def main(argv=None):
    ap = argparse.ArgumentParser(prog="missingness-reporter", description="Report missing-data patterns in a CSV.")
    ap.add_argument("csvfile")
    ap.add_argument("--codes", help="comma-separated extra missing codes (e.g. 999,unknown)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-o", "--output")
    args = ap.parse_args(argv)
    codes = set(MISSING)
    if args.codes:
        codes |= {c.strip().lower() for c in args.codes.split(",")}
    with open(args.csvfile, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    header = rows[0]
    data = [r + [""] * (len(header) - len(r)) for r in rows[1:]]
    rep = report(header, data, codes)
    out = json.dumps(rep, indent=2) + "\n" if args.json else to_markdown(rep, "Missing data: " + os.path.basename(args.csvfile))
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(out)
    else:
        sys.stdout.write(out)
    return 0

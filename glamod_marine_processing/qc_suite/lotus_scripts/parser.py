"""Argument Parser for obs_suite lotus scripts."""

from __future__ import annotations

import argparse


def get_parser_args():
    """Get argument parser arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("positional", metavar="N", type=str, nargs="+")
    parser.add_argument("--hr", const=True, nargs="?")

    args = parser.parse_args()
    if args.hr is True:
        args.mode = "qc_hr"
    else:
        args.mode = "qc"
    return args

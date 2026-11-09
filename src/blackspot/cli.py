"""BLACKSPOT command-line interface.

Usage:
    blackspot triage --capture samples/example_dzat.json
    blackspot triage --capture samples/example_dzat.json --json

A capture file is JSON:
{
  "drive": { ...DriveFacts fields... },
  "reads": [ {"lba":100,"attempt":1,"sha256":"...","all_zero":true,"timestamp":0.0}, ... ]
}
"""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .models import DriveFacts, ReadSample
from .fingerprint import classify
from .triage import triage
from .report import to_markdown

_SPOT = {
    "alive": "\N{LARGE GREEN CIRCLE} ALIVE",
    "lying": "\N{LARGE YELLOW CIRCLE} LYING",
    "fading": "\N{LARGE ORANGE CIRCLE} FADING",
    "scuttled": "\N{MEDIUM BLACK CIRCLE} SCUTTLED",
    "crypto_erased": "\N{SKULL AND CROSSBONES} CRYPTO-ERASED",
}


def _load(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    drive = DriveFacts(**raw.get("drive", {}))
    reads = [ReadSample(**r) for r in raw.get("reads", [])]
    return drive, reads


def cmd_triage(args) -> int:
    drive, reads = _load(args.capture)
    behavior, conf, why = classify(reads)
    result = triage(drive, behavior, conf, why)

    if args.json:
        print(result.to_json())
        return 0

    print(f"\n  BLACKSPOT v{__version__} — triage verdict")
    print("  " + "-" * 52)
    print(f"  Drive          : {drive.model} ({drive.controller_family})")
    print(f"  TRIM behavior  : {result.trim_behavior.value}")
    print(f"  VERDICT        : {_SPOT.get(result.verdict.value, result.verdict.value)}"
          f"   (confidence {result.confidence:.0%})")
    print(f"  Recommended    : {result.recovery_window_note}")
    print("  Rationale:")
    for line in result.rationale:
        print(f"    - {line}")
    print()
    return 0


def cmd_report(args) -> int:
    drive, reads = _load(args.capture)
    behavior, conf, why = classify(reads)
    result = triage(drive, behavior, conf, why)
    md = to_markdown(result, case_id=args.case_id, examiner=args.examiner,
                     exhibit=args.exhibit)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(md)
        print(f"wrote examiner report -> {args.out}")
    else:
        print(md)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="blackspot", description=__doc__.splitlines()[0])
    p.add_argument("--version", action="version", version=f"blackspot {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    t = sub.add_parser("triage", help="produce a triage verdict from a capture file")
    t.add_argument("--capture", required=True, help="path to a capture JSON file")
    t.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    t.set_defaults(func=cmd_triage)

    r = sub.add_parser("report", help="emit a court-style Markdown examiner report")
    r.add_argument("--capture", required=True, help="path to a capture JSON file")
    r.add_argument("--case-id", default="UNASSIGNED")
    r.add_argument("--examiner", default="")
    r.add_argument("--exhibit", default="")
    r.add_argument("--out", default="", help="write report here instead of stdout")
    r.set_defaults(func=cmd_report)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

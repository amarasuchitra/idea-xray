"""idea-xray "a habit tracker for remote teams" --customer "remote team leads" --price "$5 per user per month"

or: idea-xray --file idea.yaml   (pitch, customer, price, keywords)
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import httpx
import yaml

from . import xray
from .models import Idea
from .report import markdown


def load(args: argparse.Namespace) -> Idea:
    if args.file:
        data = yaml.safe_load(Path(args.file).read_text()) or {}
        return Idea(pitch=data["pitch"], customer=data.get("customer", ""), price=str(data.get("price", "")),
                    keywords=list(data.get("keywords") or []))  # fmt: skip
    if not args.pitch:
        raise SystemExit("Describe the idea in quotes, or pass --file idea.yaml")
    return Idea(pitch=args.pitch, customer=args.customer, price=args.price, keywords=args.keyword or [])


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(prog="idea-xray", description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("pitch", nargs="?", help="the idea in one or two sentences")
    ap.add_argument("--customer", default="", help="who it is for")
    ap.add_argument("--price", default="", help="what they would pay")
    ap.add_argument("--keyword", action="append", help="search words (repeat); defaults to the pitch")
    ap.add_argument("--file", help="idea.yaml with pitch, customer, price, keywords")
    ap.add_argument("--out", help="write the report to this Markdown file as well")
    ap.add_argument("--no-ai", action="store_true", help="use the built-in rules only, even if keys are set")
    args = ap.parse_args(argv)

    idea = load(args)
    with httpx.Client(timeout=20, headers={"User-Agent": "idea-xray/0.1"}, follow_redirects=True) as client:
        report = markdown(xray.run(idea, client, use_ai=not args.no_ai))
    print(report)
    if args.out:
        Path(args.out).write_text(report + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

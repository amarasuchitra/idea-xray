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

from . import demand, xray
from .models import Idea
from .report import markdown
from .sources import agentreach, all_sources


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
    ap.add_argument("--reach", action="append", choices=sorted(agentreach.CHANNELS),
                    help="also search this platform through Agent-Reach, on your own computer (repeat)")  # fmt: skip
    test = ap.add_argument_group("stage 3: demand test")
    test.add_argument("--page", metavar="DIR", help="also write a waitlist page and test plan into this folder")
    test.add_argument("--form", default="", help="form URL that collects the emails (Formspree, Basin, Tally...)")
    test.add_argument("--goal", type=int, default=100, help="pass mark: waitlist signups (default 100)")
    test.add_argument("--days", type=int, default=14, help="how long the test runs (default 14)")
    args = ap.parse_args(argv)

    idea = load(args)
    if args.form and not args.form.startswith("https://"):
        raise SystemExit("--form must be an https:// URL")
    sources = all_sources()
    if args.reach and not agentreach.installed():
        raise SystemExit("--reach needs Agent-Reach: pip install agent-reach && agent-reach setup")
    for channel in args.reach or []:
        sources[f"{agentreach.CHANNELS[channel]} (Agent-Reach)"] = agentreach.source(channel)
    with httpx.Client(timeout=20, headers={"User-Agent": "idea-xray/0.1"}, follow_redirects=True) as client:
        x = xray.run(idea, client, sources=sources, use_ai=not args.no_ai)
    report = markdown(x)
    print(report)
    if args.out:
        Path(args.out).write_text(report + "\n")
    if args.page:
        folder = Path(args.page)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "index.html").write_text(demand.page(x, args.form))
        (folder / "TEST-PLAN.md").write_text(demand.plan(x, demand.Test(args.goal, args.days)))
        print(f"\nDemand test ready: {folder / 'index.html'} and {folder / 'TEST-PLAN.md'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

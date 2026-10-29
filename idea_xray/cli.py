"""idea-xray "a habit tracker for remote teams" --customer "remote team leads" --price "$5 per user per month"

or: idea-xray --file idea.yaml   (pitch, customer, price, keywords)
or: idea-xray serve              (the same in your browser)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import httpx
import yaml

from . import demand, kit, watch, xray
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


def client() -> httpx.Client:
    return httpx.Client(timeout=20, headers={"User-Agent": "idea-xray/0.2"}, follow_redirects=True)


def parser() -> argparse.ArgumentParser:
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
    ap.add_argument("--kit", metavar="DIR", help="write every stage (report, demand test, build plan, help, launch)")
    test = ap.add_argument_group("stage 3: demand test")
    test.add_argument("--page", metavar="DIR", help="write a waitlist page and test plan into this folder")
    test.add_argument("--form", default="", help="form URL that collects the emails (Formspree, Basin, Tally...)")
    test.add_argument("--goal", type=int, default=100, help="pass mark: waitlist signups (default 100)")
    test.add_argument("--days", type=int, default=14, help="how long the test runs (default 14)")
    build = ap.add_argument_group("stage 4: build plan")
    build.add_argument("--target", type=float, default=1000, help="monthly income to plan for (default 1000)")
    keep = ap.add_argument_group("stage 5: competitor watch")
    keep.add_argument("--save", metavar="JSON", help="save this X-ray to compare next time")
    keep.add_argument("--compare", metavar="JSON", help="an earlier --save to compare with")
    keep.add_argument("--changes", metavar="MD", help="write what changed to this file")
    return ap


def serve(argv: list[str]) -> int:
    from . import web

    ap = argparse.ArgumentParser(prog="idea-xray serve", description="Run Idea X-ray in your browser.")
    ap.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 only when hosting it for others")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args(argv)
    web.serve(args.host, args.port)
    return 0


def write(folder: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    if argv[:1] == ["serve"]:
        return serve(argv[1:])
    args = parser().parse_args(argv)

    idea = load(args)
    if args.form and not args.form.startswith("https://"):
        raise SystemExit("--form must be an https:// URL")
    sources = all_sources()
    if args.reach and not agentreach.installed():
        raise SystemExit("--reach needs Agent-Reach: pip install agent-reach && agent-reach setup")
    for channel in args.reach or []:
        sources[f"{agentreach.CHANNELS[channel]} (Agent-Reach)"] = agentreach.source(channel)
    with client() as c:
        x = xray.run(idea, c, sources=sources, use_ai=not args.no_ai)
    report = markdown(x)
    print(report)
    if args.out:
        Path(args.out).write_text(report + "\n")
    test = demand.Test(args.goal, args.days)
    if args.page:
        write(Path(args.page), {"index.html": demand.page(x, args.form), "TEST-PLAN.md": demand.plan(x, test)})
        print(f"\nDemand test ready in {args.page}/", file=sys.stderr)
    if args.kit:
        write(Path(args.kit), kit.files(x, args.form, test, args.target))
        print(f"\nThe full kit is in {args.kit}/: start with 1-xray-report.md", file=sys.stderr)
    snap = watch.snapshot(x)
    if args.compare:
        found = watch.markdown(json.loads(Path(args.compare).read_text()), snap)
        print("\n" + found)
        if args.changes:
            Path(args.changes).write_text(found)
    if args.save:
        Path(args.save).write_text(watch.dumps(snap))
    return 0


if __name__ == "__main__":
    sys.exit(main())

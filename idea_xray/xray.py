"""Run the whole X-ray: search, classify, find gaps, score, devil's advocate."""

from __future__ import annotations

import logging
from datetime import datetime

import httpx

from . import llm
from .gaps import find_gaps
from .liveness import classify
from .models import Idea, Product, XRay
from .score import durability, rule_risks, verdict
from .sources import Found, Source, all_sources

log = logging.getLogger("idea_xray")


def _dedupe(products: list[Product]) -> list[Product]:
    seen, out = set(), []
    for p in products:
        key = (p.source, p.name.lower())
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def evidence_text(x: XRay) -> str:
    lines = [f"Idea: {x.idea.pitch}", f"Customer: {x.idea.customer or '?'}", f"Price: {x.idea.price or '?'}", ""]
    lines += [f"- {p.name} [{p.source}] {p.status}: {p.why}" for p in x.products[:25]]
    for g in x.gaps[:6]:
        lines.append(f"Gap {g.theme} ({len(g.complaints)} complaints), fixable={g.fixable}")
        lines += [f'  "{c.text}"' for c in g.complaints[:3]]
    lines += [f"Score {p.name}: {p.points}/{p.max_points} ({p.evidence})" for p in x.score]
    return "\n".join(lines)


def run(
    idea: Idea, client: httpx.Client, sources: dict[str, Source] | None = None, use_ai: bool = True,
    now: datetime | None = None,
) -> XRay:  # fmt: skip
    found, notes = Found(), []
    for name, search in (sources or all_sources()).items():
        for q in idea.queries():
            try:
                f = search(client, q)
            except (httpx.HTTPError, ValueError, KeyError) as e:
                notes.append(f"{name} could not be searched ({type(e).__name__}); results may be incomplete.")
                log.warning("%s failed for %r: %s", name, q, e)
                break
            found.products += f.products
            found.complaints += f.complaints
            found.shutdowns += f.shutdowns
    products = [classify(p, found.shutdowns, now) for p in _dedupe(found.products)]
    unique = list({(c.url, c.text): c for c in found.complaints}.values())
    gaps = find_gaps(unique)
    score = durability(idea, products, gaps)
    shutdowns = list(dict.fromkeys(found.shutdowns))
    x = XRay(idea, products, gaps, score, rule_risks(idea, products, gaps), "", notes=notes, shutdowns=shutdowns)
    x.verdict = verdict(x.total)
    if use_ai and (ai := llm.devils_advocate(evidence_text(x), client)):
        x.risks, x.engine = ai[0], f"AI ({ai[1]})"
    return x

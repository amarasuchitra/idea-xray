"""Stage 4, part two: get advice and a team. Ready-to-post asks, so experts can review and builders can join.

The best place to post is the Idea X-ray Discussions board, where founders review each other's X-rays.
"""

from __future__ import annotations

from collections import Counter
from urllib.parse import urlparse

from . import PROJECT_URL
from .models import XRay

DISCUSSIONS = f"{PROJECT_URL}/discussions"


def where_customers_are(x: XRay, limit: int = 5) -> list[str]:
    """Subreddits and sites where the complaints came from: the places to find users and helpers."""
    places: Counter[str] = Counter()
    for g in x.gaps:
        for c in g.complaints:
            u = urlparse(c.url)
            parts = u.path.split("/")
            if "reddit.com" in u.netloc and len(parts) > 2 and parts[1] == "r":
                places[f"r/{parts[2]}"] += 1
            elif u.netloc:
                places[u.netloc.removeprefix("www.")] += 1
    return [p for p, _ in places.most_common(limit)]


def markdown(x: XRay) -> str:
    top = next((g for g in x.gaps if g.fixable), None)
    gap = f"{top.theme.lower()} ({len(top.complaints)} complaints)" if top else "not clear yet"
    places = where_customers_are(x)
    return "\n".join([
        "# Ask for advice and a team",
        "",
        f"Post your X-ray in [Idea X-ray Discussions]({DISCUSSIONS}) where founders and experts review each other's "
        "ideas. Copy one of the posts below and edit it in your own words.",
        "",
        "## 1. Ask for an honest review",
        "",
        "```text",
        f"Idea: {x.idea.pitch}",
        f"For: {x.idea.customer or '(who exactly?)'} · Price: {x.idea.price or '(not set)'}",
        f"X-ray score: {x.total}/100. Biggest fixable gap: {gap}.",
        "",
        "I'd like blunt feedback on three things:",
        "1. Would you (or people you know) pay for this? Why not?",
        "2. What's the biggest risk I'm not seeing?",
        "3. Who has tried this before, and why did it fail?",
        "",
        "Full report attached. Please tell me what's wrong, not what's nice.",
        "```",
        "",
        "## 2. Find people to build it with",
        "",
        "```text",
        f"I'm building: {x.idea.pitch}",
        "Evidence so far: [your demand test result, e.g. 120 signups, 18 would pay]",
        "Looking for: [a developer / a designer / someone who knows the customers]",
        "What I bring: [your skills, time per week, what's done already]",
        "Time: [hours per week] · Split: [equity or pay, said up front]",
        "```",
        "",
        "## Where to post",
        "",
        f"- [Idea X-ray Discussions]({DISCUSSIONS}): reviews from other founders",
        *[f"- {p}: where the complaints came from, so your future users are here (read the rules first)"
          for p in places],  # fmt: skip
        "- Indie Hackers and your local startup groups, for co-founders",
        "",
        "## Before you share",
        "",
        "- Share evidence, not just the idea. Ideas are cheap; signups and reasons are what convince people.",
        "- Agree on roles, time and split in writing before anyone starts building.",
        "- Never ask people to work for free on a vague promise.",
        "",
    ])  # fmt: skip

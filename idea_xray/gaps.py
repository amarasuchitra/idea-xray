"""Group complaints into gaps, and say which ones a new product could fix and profit from."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Complaint, Gap


@dataclass(frozen=True)
class Theme:
    name: str
    pattern: re.Pattern
    fixable: bool
    why: str
    profit: str


THEMES = [
    Theme(
        "Platform or legal limits",
        re.compile(
            r"apple (won'?t|doesn'?t) allow|api (was )?(removed|shut|deprecated)|banned|not allowed|"
            r"regulat|licen[cs]e|terms of service|patent|limited by|(ios|platform|store) rules",
            re.I,
        ),
        False,
        "the blocker is a platform, a law or a licence, not the product",
        "hard to profit from unless you have a partnership or legal route the others lack",
    ),
    Theme(
        "Price",
        re.compile(r"expensive|overpriced|price|pricing|subscription|too much money|costs? too|paywall", re.I),
        True,
        "people already pay and dislike the price, so a leaner or fairer plan can win them",
        "proven willingness to pay: undercut with a simpler product or a fairer plan",
    ),
    Theme(
        "Reliability",
        re.compile(
            r"crash|bug|broken|slow|doesn'?t work|does not work|keeps? (failing|losing)|lost my|down again", re.I
        ),
        True,
        "quality problems are fixable with better engineering and testing",
        "users switch for something that just works; reliability is a selling point",
    ),
    Theme(
        "Missing features",
        re.compile(
            r"missing|lacks?|i wish|wish it|no way to|doesn'?t (support|let|have)|does not (support|have)|"
            r"can'?t|cannot",
            re.I,
        ),
        True,
        "a focused product can build what the big ones skip",
        "charge for the missing feature as the core of a niche product",
    ),
    Theme(
        "Hard to use",
        re.compile(
            r"confus|complicated|hard to|annoying|clunky|\bui\b|\bux\b|interface|too many steps|learning curve", re.I
        ),
        True,
        "simpler design is a classic way in for a newcomer",
        "win the users who gave up on the complex tools",
    ),
    Theme(
        "Privacy and trust",
        re.compile(r"privacy|tracking|sold my data|my data|spy|trust", re.I),
        True,
        "a privacy-first design (local data, no tracking) is a clear difference",
        "privacy-conscious users and businesses often pay a premium",
    ),
    Theme(
        "Support",
        re.compile(r"support (is|never|team)|customer service|no (reply|response)|ignored my", re.I),
        True,
        "fixable, but good support costs time and money every month",
        "small teams can win on personal support early, but it does not scale for free",
    ),
]
OTHER = Theme(
    "Other complaints",
    re.compile(r".^"),
    True,
    "mixed complaints, read them before deciding",
    "unclear until the complaints are read",
)


def theme_of(text: str) -> Theme:
    return next((t for t in THEMES if t.pattern.search(text)), OTHER)


def find_gaps(complaints: list[Complaint]) -> list[Gap]:
    groups: dict[str, list[Complaint]] = {}
    for c in complaints:
        t = theme_of(c.text)
        c.theme = t.name
        groups.setdefault(t.name, []).append(c)
    themes = {t.name: t for t in [*THEMES, OTHER]}
    gaps = [Gap(name, cs, themes[name].fixable, themes[name].why, themes[name].profit) for name, cs in groups.items()]
    return sorted(gaps, key=lambda g: (g.theme == OTHER.name, -len(g.complaints)))

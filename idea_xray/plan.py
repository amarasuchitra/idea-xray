"""Stage 4, the build plan: what to build first, what it costs, what can go wrong, and the profit maths.

Everything is worked out from the X-ray's evidence and the founder's own price. Where a number is a rule of
thumb rather than evidence, the plan says so.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .demand import PROMISE
from .models import Status, XRay
from .score import PLATFORM


@dataclass
class Price:
    amount: float
    per: str  # "month", "year" or "once"
    currency: str

    @property
    def monthly(self) -> float:
        return self.amount / 12 if self.per == "year" else self.amount


def parse_price(text: str) -> Price | None:
    m = re.search(r"([$€£₹]|rs\.?|inr|usd|eur)?\s*(\d{1,3}(?:,\d{2,3})+|\d+)(\.\d+)?", text, re.I)
    if not m:
        return None
    amount = float(m.group(2).replace(",", "") + (m.group(3) or ""))  # 2,000 and 1,00,000 are thousands
    if amount <= 0:
        return None
    per = "month"
    if re.search(r"year|annual|/yr", text, re.I):
        per = "year"
    elif re.search(r"once|one[- ]time|lifetime", text, re.I):
        per = "once"
    symbol = (m.group(1) or "").lower().rstrip(".")
    currency = {"rs": "₹", "inr": "₹", "usd": "$", "eur": "€"}.get(symbol, m.group(1) or "")
    return Price(amount, per, currency)


def _money(p: Price, value: float) -> str:
    return f"{p.currency}{value:,.0f}" if value >= 100 else f"{p.currency}{value:,.2f}".rstrip("0").rstrip(".")


def profit(x: XRay, target: float) -> list[str]:
    p = parse_price(x.idea.price)
    if not p:
        return ["No price was given, so profit can't be worked out. Run again with `--price`, for example "
                '`--price "$5 per month"`.']  # fmt: skip
    if p.per == "once":
        sales = math.ceil(target / p.amount)
        lines = [f"At {_money(p, p.amount)} per sale, earning {_money(p, target)} a month means **{sales:,} new "
                 "sales every month**, forever, because nobody pays twice."]  # fmt: skip
        need = sales
    else:
        need = math.ceil(target / p.monthly)
        lines = [f"At {_money(p, p.monthly)} a month per customer, {_money(p, target)} a month needs "
                 f"**{need:,} paying customers** who stay."]  # fmt: skip
    low, high = math.ceil(need / 0.05), math.ceil(need / 0.02)
    lines += [
        f"If 2 to 5% of waitlist signups end up paying (a rule of thumb; your demand test gives the real number), "
        f"that is **{low:,} to {high:,} signups**.",
        "Payment providers keep a few percent of every sale, and taxes come out of what is left.",
    ]
    return lines


def scope(x: XRay) -> list[str]:
    fixable = [g for g in x.gaps if g.fixable and g.theme in PROMISE]
    lines = [f"**Must have:** the core job, *{x.idea.pitch}*, done well for {x.idea.customer or 'one clear customer'}."]
    if fixable:
        top = fixable[0]
        lines.append(f"**Your edge:** {PROMISE[top.theme][0].lower()}. This is the biggest fixable gap "
                     f"({len(top.complaints)} complaints), so it's in version one.")  # fmt: skip
    if len(fixable) > 1:
        later = ", ".join(PROMISE[g.theme][0].lower() for g in fixable[1:])
        lines.append(f"**Later, if the first users ask:** {later}.")
    lines.append("**Not now:** copying every feature of the market leader. A small product that fixes one pain "
                 "beats a weaker copy of a big one.")  # fmt: skip
    if any(not g.fixable for g in x.gaps):
        lines.append("**Don't promise:** anything blocked by platform or legal limits. Users complain about those, "
                     "but a new product can't fix them either.")  # fmt: skip
    return lines


def risks(x: XRay) -> list[tuple[str, str, str]]:
    """(risk, level, what to do) from the evidence."""
    live = [p for p in x.products if p.status is Status.live]
    dead = [p for p in x.products if p.status is Status.graveyard]
    complaints = sum(len(g.complaints) for g in x.gaps)
    out = [
        ("Nobody wants it", "High" if complaints < 5 else "Medium" if complaints < 15 else "Low",
         "Pass the demand test before building. Talk to 5 people who signed up."),
        ("Competitors", "High" if len(live) > 12 else "Medium" if live else "Low",
         "Win on your one edge, not on feature count. Watch competitors every week (`idea-xray --compare`)."),
        ("Same fate as the dead ones", "High" if len(dead) >= 3 else "Medium" if dead else "Low",
         "Read the shutdown stories and graveyard links in the report, and write down how you'll avoid each cause."),
        ("Platform dependence", "High" if PLATFORM.search(x.idea.pitch) else "Low",
         "Keep your customers' data and contact with you, and have a plan if the platform changes its rules."),
        ("Running out of time or money", "Medium",
         "Set a date to stop if the pass marks aren't met. Keep costs on free tiers until people pay."),
    ]  # fmt: skip
    return out


def realities(x: XRay, target: float) -> list[str]:
    live = [p for p in x.products if p.status is Status.live]
    dead = [p for p in x.products if p.status is Status.graveyard]
    lines = []
    if x.products:
        lines.append(f"Of {len(x.products)} similar products found, {len(dead)} are dead and {len(live)} are alive. "
                     "Most ideas in any space don't make it.")  # fmt: skip
    big = max(live, key=lambda p: p.users or 0, default=None)
    if big and big.users:
        lines.append(f"{big.name} already has {big.why}. People rarely switch unless the pain is real.")
    p = parse_price(x.idea.price)
    if p and p.per != "once":
        need = math.ceil(target / p.monthly)
        lines.append(f"{need:,} paying customers is {need:,} people to find, convince and support. That usually "
                     "takes many months, not weeks.")  # fmt: skip
    if any(g.theme == "Support" for g in x.gaps):
        lines.append("Users here complain about support. Good support costs your time every week, for as long as "
                     "the product exists.")  # fmt: skip
    lines += [
        "Launch day usually brings a spike, then quiet. Growth comes from showing up for months.",
        "After launch, upkeep (bugs, updates, security, support) takes a big share of your time. Plan for it.",
    ]
    return lines


MAINTENANCE = [
    "Update dependencies monthly and fix security alerts the same week (turn on Dependabot on GitHub).",
    "Back up user data automatically, and test a restore once.",
    "Keep CI green and honest: [CI Doctor](https://github.com/amarasuchitra/ci-doctor) explains failures and "
    "flags fixes that only hide them.",
    "Reply to every user message in the first months. It's your best source of what to build next.",
    "Re-run the X-ray monthly to see new competitors and new complaints.",
]

COSTS = [
    ("Website and waitlist", "Free (GitHub Pages and a free form service)"),
    ("Domain name", "Usually a small yearly fee"),
    ("App hosting and database", "Free tiers exist for small apps; costs grow with users"),
    ("Email to users", "Free tiers cover early lists"),
    ("Payments", "No monthly fee on most providers, a few percent per sale"),
    ("Your time", "The biggest cost. Count the hours, even if you don't pay yourself"),
]


def markdown(x: XRay, target: float = 1000) -> str:
    lines = [
        "# Build plan",
        "",
        f"> {x.idea.pitch}",
        "",
        "Build this **only after the demand test passes**. Every point below comes from the X-ray; rules of thumb "
        "are marked as such.",
        "",
        "## What to build first",
        "",
        *[f"- {s}" for s in scope(x)],
        "",
        f"## Profit maths (target: {_target(x, target)} a month)",
        "",
        *[f"- {s}" for s in profit(x, target)],
        "",
        "## Costs",
        "",
        "| What | Cost |",
        "|---|---|",
        *[f"| {a} | {b} |" for a, b in COSTS],
        "",
        "## Risks and what to do",
        "",
        "| Risk | Level | What to do |",
        "|---|---|---|",
        *[f"| {r} | {lvl} | {todo} |" for r, lvl, todo in risks(x)],
        "",
        "## Harsh realities",
        "",
        *[f"- {s}" for s in realities(x, target)],
        "",
        "## Keeping it alive",
        "",
        *[f"- {s}" for s in MAINTENANCE],
        "",
    ]
    return "\n".join(lines)


def _target(x: XRay, target: float) -> str:
    p = parse_price(x.idea.price)
    return _money(p, target) if p else f"{target:,.0f}"

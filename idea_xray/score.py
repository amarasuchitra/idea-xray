"""The durability score: five parts, each with its points and the evidence for them.

The score is a guide, not a prediction. It says how strong the evidence is today; the
real demand test (signups, pre-orders) is what proves the idea.
"""

from __future__ import annotations

import re

from .models import Gap, Idea, Product, ScorePart, Status

PLATFORM = re.compile(
    r"chatgpt|openai|gpt wrapper|instagram|tiktok|twitter|\bx\.com|youtube|whatsapp|shopify app|chrome extension|"
    r"plugin for|add-?on for|built on top of|amazon seller|etsy",
    re.I,
)


def durability(idea: Idea, products: list[Product], gaps: list[Gap]) -> list[ScorePart]:
    complaints = sum(len(g.complaints) for g in gaps)
    fixable = [g for g in gaps if g.fixable and g.theme != "Other complaints"]
    live = [p for p in products if p.status is Status.live]
    dead = [p for p in products if p.status is Status.graveyard]

    demand = min(30, complaints * 2)
    parts = [ScorePart("Demand evidence", demand, 30, f"{complaints} real complaints found about existing products")]

    room = 0 if not fixable else 10 if len(fixable) == 1 else 15
    if any(len(g.complaints) >= 5 for g in fixable):
        room += 5
    names = ", ".join(f"{g.theme} ({len(g.complaints)})" for g in fixable) or "none"
    parts.append(ScorePart("Room to win", room, 20, f"fixable gaps: {names}"))

    n = len(live)
    if n == 0:
        comp, why = 10, "nobody serves this today: a fresh chance, or a sign there is no demand"
    elif n <= 5:
        comp, why = 20, f"{n} live products: demand is proven and the space is not crowded"
    elif n <= 12:
        comp, why = 12, f"{n} live products: crowded, you need a sharp difference"
    else:
        comp, why = 5, f"{n} live products: very crowded"
    parts.append(ScorePart("Competition", comp, 20, why))

    if products:
        grave = round(15 * (1 - len(dead) / len(products)))
        why = f"{len(dead)} of {len(products)} similar products are dead or abandoned"
    else:
        grave, why = 8, "no similar products found to learn from"
    parts.append(ScorePart("Graveyard warning", grave, 15, why))

    text = f"{idea.pitch} {idea.customer}"
    if m := PLATFORM.search(text):
        parts.append(
            ScorePart("Platform risk", 5, 15, f'depends on "{m.group(0)}", which can change its rules or copy you')
        )
    else:
        parts.append(ScorePart("Platform risk", 15, 15, "no single platform it depends on was mentioned"))
    return parts


def verdict(total: int) -> str:
    if total >= 70:
        return "Go: run the real demand test (landing page with a waitlist or pre-orders)"
    if total >= 45:
        return "Rethink: narrow the idea to the strongest fixable gap, then check again"
    return "Stop or pivot: the evidence is weak today; save the reasons and try a different angle"


def rule_risks(idea: Idea, products: list[Product], gaps: list[Gap]) -> list[str]:
    """The devil's advocate without an AI: the strongest reasons this could fail, from the evidence."""
    risks = []
    dead = [p for p in products if p.status is Status.graveyard]
    live = [p for p in products if p.status is Status.live]
    if dead:
        risks.append(
            f"{len(dead)} similar products already died or were abandoned, e.g. {dead[0].name} ({dead[0].why})."
        )
    if len(live) > 12:
        risks.append(f"{len(live)} live products already compete for the same users.")
    big = max(live, key=lambda p: p.users or 0, default=None)
    if big and (big.users or 0) > 1000:
        risks.append(f"{big.name} is established ({big.why}); it could add your feature quickly.")
    if not gaps:
        risks.append("No complaints were found, so there is no evidence yet that people feel this pain.")
    if any(not g.fixable for g in gaps):
        risks.append("Some complaints point at platform or legal limits that a new product cannot fix either.")
    if PLATFORM.search(idea.pitch):
        risks.append("It depends on another company's platform, which can change its rules, prices or copy it.")
    if not idea.price:
        risks.append("No price was given; without one, profit cannot be checked.")
    return risks or ["No strong warning signs in the evidence found. Real customers still have to prove it."]

"""The X-ray as a Markdown report a beginner can read top to bottom."""

from __future__ import annotations

from . import PROJECT_URL
from .models import Status, XRay

ICON = {Status.live: "🟢", Status.prototype: "🟡", Status.graveyard: "🪦"}


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def markdown(x: XRay) -> str:
    lines = [
        "# Idea X-ray",
        "",
        f"> {x.idea.pitch}",
        "",
        f"**For:** {x.idea.customer or 'not given'} · **Price:** {x.idea.price or 'not given'}",
        "",
        f"## Durability score: {x.total} / 100",
        "",
        f"**{x.verdict}**",
        "",
        "| Part | Points | Evidence |",
        "|---|---|---|",
        *[f"| {p.name} | {p.points} / {p.max_points} | {_cell(p.evidence)} |" for p in x.score],
        "",
        "The score shows how strong the evidence is today. It does not predict success: "
        "only real people signing up or paying can prove the idea.",
        "",
        "## Devil's advocate: why this could fail",
        "",
        *[f"{i}. {r}" for i, r in enumerate(x.risks, 1)],
        "",
    ]

    counts = {s: sum(1 for p in x.products if p.status is s) for s in Status}
    lines += [
        "## What already exists",
        "",
        " · ".join(f"{ICON[s]} {s.value}: **{n}**" for s, n in counts.items()),
        "",
    ]
    if x.products:
        lines += ["| | Product | Where | Why we think so |", "|---|---|---|---|"]
        order = {Status.live: 0, Status.prototype: 1, Status.graveyard: 2}
        for p in sorted(x.products, key=lambda p: (order[p.status], -(p.users or 0)))[:30]:
            why = p.why + (f" ([post]({p.shutdown_note}))" if p.shutdown_note else "")
            lines.append(f"| {ICON[p.status]} | [{_cell(p.name)}]({p.url}) | {p.source} | {_cell(why)} |")
        lines.append("")
    else:
        lines += ["Nothing similar was found. Either it's new, or the search words need changing.", ""]
    if x.shutdowns:
        lines += ["**Shutdown stories to learn from:**", ""]
        lines += [f"- [{_cell(t)}]({u})" for t, u in x.shutdowns[:8]]
        lines.append("")

    lines += ["## Gaps: where existing products fall short", ""]
    if not x.gaps:
        lines += ["No complaints found yet. Try other search words, or ask 10 possible customers directly.", ""]
    for g in x.gaps:
        mark = "✅ Fixable" if g.fixable else "⛔ Hard to fix"
        lines += [f"### {g.theme}: {len(g.complaints)} complaint(s) · {mark}", "", f"- **Why:** {g.why}",
                  f"- **Profit angle:** {g.profit}", ""]  # fmt: skip
        lines += [f'> "{c.text}" ([{c.source}]({c.url}))' + "\n>" for c in g.complaints[:3]]
        if lines[-1].endswith("\n>"):
            lines[-1] = lines[-1][:-2]
        lines.append("")

    lines += [
        "## Next step",
        "",
        "Set a pass mark **before** testing (for example 100 waitlist signups or 10 pre-orders in two weeks), "
        "then put a one-page site in front of real people. Build only if the pass mark is met.",
        "",
    ]
    if x.notes:
        lines += ["<details><summary>Limits of this report</summary>", "", *[f"- {n}" for n in x.notes], "",
                  "</details>", ""]  # fmt: skip
    lines.append(f"<sub>Devil's advocate engine: {x.engine} · [Idea X-ray]({PROJECT_URL})</sub>")
    return "\n".join(lines)

"""Stage 5, staying ahead: save each X-ray, compare it with the last one, and see what changed.

Run it every week or month (a scheduled GitHub Action works for free) and you'll hear about a new
competitor, one that died, or a new kind of complaint before your users tell you.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from .models import XRay


def snapshot(x: XRay, now: datetime | None = None) -> dict:
    return {
        "version": 1,
        "taken": (now or datetime.now(UTC)).isoformat(timespec="seconds"),
        "idea": x.idea.pitch,
        "score": x.total,
        "products": {
            f"{p.source}: {p.name}": {"status": p.status.name if p.status else "", "url": p.url, "why": p.why}
            for p in x.products
        },  # fmt: skip
        "gaps": {g.theme: len(g.complaints) for g in x.gaps},
    }


def dumps(snap: dict) -> str:
    return json.dumps(snap, indent=2, ensure_ascii=False) + "\n"


def changes(old: dict, new: dict) -> list[str]:
    out = []
    if new["score"] != old["score"]:
        out.append(f"Score moved from {old['score']} to {new['score']}.")
    before, after = old["products"], new["products"]
    for key in sorted(after.keys() - before.keys()):
        p = after[key]
        if p["status"] != "graveyard":
            out.append(f"🆕 New competitor: [{key}]({p['url']}) ({p['why']}).")
    for key in sorted(after.keys() & before.keys()):
        was, now = before[key]["status"], after[key]["status"]
        if was != now and now == "graveyard":
            out.append(f"🪦 Died: [{key}]({after[key]['url']}) ({after[key]['why']}). Read why, and win its users.")
        elif was != now and now == "live":
            out.append(f"📈 Now live and used: [{key}]({after[key]['url']}) ({after[key]['why']}).")
    for theme, n in new["gaps"].items():
        m = old["gaps"].get(theme, 0)
        if n > m:
            out.append(f"🗣️ {theme}: {n} complaints, up from {m}.")
    return out


def markdown(old: dict, new: dict) -> str:
    found = changes(old, new)
    lines = ["# What changed", "", f"Since {old['taken'][:10]}, compared with {new['taken'][:10]}.", ""]
    lines += [f"- {c}" for c in found] if found else ["Nothing important changed. Keep building."]
    return "\n".join(lines) + "\n"

"""Y Combinator's company directory: who got funded for this idea, and who is now Inactive (dead).

The free yc-oss mirror of the directory has every launched YC company with its status. "Inactive" is the
same list Startups.RIP builds its post-mortems from, so this is the graveyard check with real data.
"""

from __future__ import annotations

import re

import httpx

from ..models import Product
from . import Found
from ._util import clean

API = "https://yc-oss.github.io/api/companies/all.json"
STATUS = {"Inactive": "YC lists it as Inactive (shut down)", "Acquired": "acquired", "Public": "public company"}

_cache: dict[int, list[dict]] = {}  # one download per run, however many keywords


def _companies(client: httpx.Client) -> list[dict]:
    if id(client) not in _cache:
        _cache.clear()
        _cache[id(client)] = client.get(API).json()
    return _cache[id(client)]


def _words(query: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) >= 3]


def search(client: httpx.Client, query: str) -> Found:
    words, found = _words(query), Found()
    if not words:
        return found
    for c in _companies(client):
        text = " ".join([c.get("name") or "", c.get("one_liner") or "", c.get("long_description") or "",
                         " ".join(c.get("tags") or [])]).lower()  # fmt: skip
        if not all(re.search(rf"\b{w}", text) for w in words):
            continue
        status, batch = c.get("status") or "", c.get("batch") or "?"
        p = Product(
            name=c.get("name") or "?", url=c.get("url") or c.get("website") or "", source="YC directory",
            description=clean(c.get("one_liner"), 200),
        )  # fmt: skip
        if status == "Inactive":
            p.dead = f"{STATUS[status]}, batch {batch}"
            found.shutdowns.append((f"{p.name} (YC {batch}) is no longer active", p.url))
        else:
            p.why = f"{STATUS.get(status, 'active')}, YC batch {batch}"
        found.products.append(p)
    return found

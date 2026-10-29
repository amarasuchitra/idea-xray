"""Apple App Store via the free iTunes Search API: apps that ship today, their ratings and last update."""

from __future__ import annotations

import httpx

from ..models import Product
from . import Found
from ._util import clean, when

API = "https://itunes.apple.com/search"


def search(client: httpx.Client, query: str) -> Found:
    data = client.get(API, params={"term": query, "entity": "software", "limit": 15}).json()
    found = Found()
    for a in data.get("results", []):
        found.products.append(
            Product(name=a.get("trackName", "?"), url=a.get("trackViewUrl", ""), source="App Store",
                    description=clean(a.get("description"), 200), users=a.get("userRatingCount"),
                    last_activity=when(a.get("currentVersionReleaseDate")))
        )  # fmt: skip
    return found

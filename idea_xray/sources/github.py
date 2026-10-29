"""GitHub repository search: open-source attempts at the same idea, and whether they are still alive."""

from __future__ import annotations

import os

import httpx

from ..models import Product
from . import Found
from ._util import clean, when

API = "https://api.github.com/search/repositories"


def search(client: httpx.Client, query: str) -> Found:
    headers = {"Accept": "application/vnd.github+json"}
    if token := os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    items = client.get(API, params={"q": query, "sort": "stars", "per_page": 15}, headers=headers).json()
    found = Found()
    for r in items.get("items", []):
        found.products.append(
            Product(name=r["full_name"], url=r["html_url"], source="GitHub", description=clean(r.get("description")),
                    users=r.get("stargazers_count"), last_activity=when(r.get("pushed_at")),
                    archived=bool(r.get("archived")))
        )  # fmt: skip
    return found

"""Hacker News via the free Algolia API: launches ("Show HN"), shutdown posts, and complaints in comments."""

from __future__ import annotations

import httpx

from ..models import Complaint, Product
from . import Found
from ._util import SHUTDOWN, clean, complaint_sentences, when

API = "https://hn.algolia.com/api/v1/search"


def search(client: httpx.Client, query: str) -> Found:
    found = Found()
    stories = client.get(API, params={"query": query, "tags": "story", "hitsPerPage": 30}).json()["hits"]
    for s in stories:
        title, link = s.get("title") or "", f"https://news.ycombinator.com/item?id={s['objectID']}"
        if SHUTDOWN.search(title):
            found.shutdowns.append((title, link))
        elif title.lower().startswith("show hn"):
            name = title.split(":", 1)[-1].split("–")[0].split(" - ")[0].strip()
            found.products.append(
                Product(name=name, url=s.get("url") or link, source="Hacker News", description=title,
                        users=s.get("points"), last_activity=when(s.get("created_at")))
            )  # fmt: skip
    comments = client.get(API, params={"query": query, "tags": "comment", "hitsPerPage": 50}).json()["hits"]
    for c in comments:
        url = f"https://news.ycombinator.com/item?id={c['objectID']}"
        for sentence in complaint_sentences(clean(c.get("comment_text"), 2000)):
            found.complaints.append(Complaint(sentence, url, "Hacker News"))
    return found

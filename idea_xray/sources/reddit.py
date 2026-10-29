"""Reddit search: what people complain about and which tools they are trying to replace."""

from __future__ import annotations

import httpx

from ..models import Complaint
from . import Found
from ._util import SHUTDOWN, clean, complaint_sentences

API = "https://www.reddit.com/search.json"


def search(client: httpx.Client, query: str) -> Found:
    data = client.get(API, params={"q": query, "limit": 50, "sort": "relevance"}).json()
    found = Found()
    for child in data.get("data", {}).get("children", []):
        p = child.get("data", {})
        url = "https://www.reddit.com" + p.get("permalink", "")
        title = p.get("title") or ""
        if SHUTDOWN.search(title):
            found.shutdowns.append((title, url))
        text = clean(f"{title}. {p.get('selftext') or ''}", 2000)
        for sentence in complaint_sentences(text):
            found.complaints.append(Complaint(sentence, url, "Reddit"))
    return found

from __future__ import annotations

import re
from datetime import UTC, datetime

COMPLAINT = re.compile(
    r"\b(i wish|wish it|too much|not worth|waste of|doesn'?t (work|let|support|have)|"
    r"does not (work|let|support|have)|can'?t|cannot|won'?t allow|not allowed|limited by|"
    r"too expensive|overpriced|price (hike|increase)|missing|lacks?|no way to|frustrat|annoying|buggy|crash|"
    r"slow|switched (from|away)|looking for an? alternative|alternative to|gave up|cancell?ed|stopped using|"
    r"terrible|awful|hate|broken|privacy|sold my data|support (is|never))",
    re.IGNORECASE,
)
SHUTDOWN = re.compile(
    r"\b(shutting down|shut down|sunsetting|sunset|we'?re closing|is closing|goodbye|end of life|discontinu|"
    r"post-?mortem|why we failed|lessons from (failing|shutting))",
    re.IGNORECASE,
)
TAGS = re.compile(r"<[^>]+>")


def clean(text: str | None, limit: int = 400) -> str:
    text = TAGS.sub(" ", text or "").replace("&#x27;", "'").replace("&quot;", '"').replace("&amp;", "&")
    return " ".join(text.split())[:limit]


def when(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def complaint_sentences(text: str, limit: int = 3) -> list[str]:
    """The sentences that sound like complaints (a post often holds several different ones)."""
    out = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if COMPLAINT.search(s) and 20 <= len(s) <= 300]
    return out[:limit]

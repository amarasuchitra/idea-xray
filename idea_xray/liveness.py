"""Live and used, prototype nobody uses, or in the graveyard? Simple rules, each with its evidence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from .models import Product, Status

STALE = timedelta(days=548)  # about 18 months without an update
MIN_USERS = {"GitHub": 50, "App Store": 20, "Hacker News": 20}  # stars, ratings, points
UNIT = {"GitHub": "stars", "App Store": "ratings", "Hacker News": "points on Hacker News"}


def _date(dt: datetime) -> str:
    return dt.strftime("%b %Y")


def classify(p: Product, shutdowns: list[tuple[str, str]], now: datetime | None = None) -> Product:
    now = now or datetime.now(UTC)
    unit = UNIT.get(p.source, "users")
    short = p.name.split("/")[-1].lower()
    for title, url in shutdowns:
        if len(short) >= 4 and short in title.lower():
            p.status, p.why, p.shutdown_note = Status.graveyard, f'shutdown post: "{title}"', url
            return p
    if p.archived:
        p.status, p.why = Status.graveyard, "archived by its owner"
        return p
    # A Hacker News launch date is not product activity, so staleness only counts for the other sources.
    if p.source != "Hacker News" and p.last_activity and now - p.last_activity > STALE:
        p.status, p.why = Status.graveyard, f"no update since {_date(p.last_activity)}"
        return p
    if p.users is not None and p.users < MIN_USERS.get(p.source, 20):
        p.status, p.why = Status.prototype, f"only {p.users} {unit}"
        return p
    p.status = Status.live
    p.why = f"{p.users:,} {unit}" if p.users is not None else "active"
    if p.last_activity and p.source != "Hacker News":
        p.why += f", updated {_date(p.last_activity)}"
    return p

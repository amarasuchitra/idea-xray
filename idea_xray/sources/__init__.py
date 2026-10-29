"""Free, keyless (or free-key) data sources. Each returns products and complaints with links.

A source that fails is skipped and noted in the report, so one outage never stops the X-ray.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import httpx

from ..models import Complaint, Product


@dataclass
class Found:
    products: list[Product] = field(default_factory=list)
    complaints: list[Complaint] = field(default_factory=list)
    shutdowns: list[tuple[str, str]] = field(default_factory=list)  # (title, url) of "we're shutting down" posts


Source = Callable[[httpx.Client, str], Found]


def all_sources() -> dict[str, Source]:
    from . import appstore, github, hackernews, reddit

    return {"Hacker News": hackernews.search, "GitHub": github.search, "App Store": appstore.search,
            "Reddit": reddit.search}  # fmt: skip

"""The things an X-ray is made of. Every claim carries the link it came from."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class Status(StrEnum):
    live = "Live and used"
    prototype = "Prototype nobody uses"
    graveyard = "In the graveyard"


@dataclass
class Idea:
    pitch: str  # one or two sentences: what it does
    customer: str = ""  # who it is for
    price: str = ""  # what they would pay, in the founder's words
    keywords: list[str] = field(default_factory=list)  # search terms; derived from the pitch if empty

    def queries(self) -> list[str]:
        return self.keywords or [self.pitch]


@dataclass
class Product:
    """Something that already exists (or existed) and does roughly the same job."""

    name: str
    url: str
    source: str  # "GitHub", "App Store", "Hacker News"
    description: str = ""
    users: int | None = None  # stars, ratings or points: the best usage signal the source has
    last_activity: datetime | None = None
    archived: bool = False
    shutdown_note: str = ""  # why it died, when the source says so
    status: Status | None = None
    why: str = ""  # the evidence behind the status


@dataclass
class Complaint:
    text: str
    url: str
    source: str
    theme: str = ""


@dataclass
class Gap:
    theme: str
    complaints: list[Complaint]
    fixable: bool
    why: str
    profit: str


@dataclass
class ScorePart:
    name: str
    points: int
    max_points: int
    evidence: str


@dataclass
class XRay:
    idea: Idea
    products: list[Product]
    gaps: list[Gap]
    score: list[ScorePart]
    risks: list[str]
    verdict: str
    engine: str = "rules"
    notes: list[str] = field(default_factory=list)  # sources that failed, limits hit
    shutdowns: list[tuple[str, str]] = field(default_factory=list)  # (title, url) shutdown stories to learn from

    @property
    def total(self) -> int:
        return sum(p.points for p in self.score)

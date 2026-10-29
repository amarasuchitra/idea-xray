"""Optional extra reach through Agent-Reach (https://github.com/Panniantong/Agent-Reach).

Agent-Reach searches platforms that have no free API, such as X/Twitter, LinkedIn and YouTube, by driving
a browser you are logged in to. It is off by default and only runs on your own computer:

    pip install agent-reach && agent-reach setup
    idea-xray "..." --reach reddit --reach twitter

Use a secondary account. Logged-in scraping can break a site's terms and get the account blocked, so
never run this in shared CI.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable

import httpx

from ..models import Complaint
from . import Found, Source
from ._util import SHUTDOWN, clean, complaint_sentences

CHANNELS = {"reddit": "Reddit", "twitter": "X/Twitter", "linkedin": "LinkedIn", "youtube": "YouTube",
            "v2ex": "V2EX", "web": "Web"}  # fmt: skip
Runner = Callable[[list[str]], str]


def installed() -> bool:
    return shutil.which("agent-reach") is not None


def _run(args: list[str]) -> str:
    done = subprocess.run(["agent-reach", *args], capture_output=True, text=True, timeout=120, check=False)
    return done.stdout


def source(channel: str, runner: Runner = _run) -> Source:
    label = CHANNELS.get(channel, channel)

    def search(_client: httpx.Client, query: str) -> Found:
        try:
            out = json.loads(runner([channel, "search", query, "--limit", "20"]) or "{}")
        except (json.JSONDecodeError, OSError, subprocess.SubprocessError) as e:
            raise ValueError(f"agent-reach {channel} failed: {type(e).__name__}") from e
        if not out.get("ok"):
            code = (out.get("error") or {}).get("code") or "no answer"
            raise ValueError(f"agent-reach {channel}: {code}")  # e.g. NEED_LOGIN: run `agent-reach doctor`
        found = Found()
        for item in out.get("items") or []:
            url, title = item.get("url") or "", item.get("title") or ""
            if not url:
                continue
            if SHUTDOWN.search(title):
                found.shutdowns.append((title, url))
            for sentence in complaint_sentences(clean(f"{title}. {item.get('text') or ''}", 2000)):
                found.complaints.append(Complaint(sentence, url, label))
        return found

    return search

import json
from pathlib import Path

import httpx
import pytest
import respx

FIX = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIX / name).read_text())


@pytest.fixture
def web():
    """All four sources answering with recorded data."""
    with respx.mock(assert_all_called=False) as mock:

        def hn(req):
            tag = req.url.params["tags"]
            return httpx.Response(200, json=load("hn_stories.json" if tag == "story" else "hn_comments.json"))

        mock.get("https://hn.algolia.com/api/v1/search").mock(side_effect=hn)
        github = httpx.Response(200, json=load("github.json"))
        mock.get("https://api.github.com/search/repositories").mock(return_value=github)
        mock.get("https://itunes.apple.com/search").mock(return_value=httpx.Response(200, json=load("appstore.json")))
        mock.get("https://www.reddit.com/search.json").mock(return_value=httpx.Response(200, json=load("reddit.json")))
        yield mock


@pytest.fixture(autouse=True)
def _no_keys(monkeypatch):
    for k in ("GITHUB_TOKEN", "GROQ_API_KEY", "CEREBRAS_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(k, raising=False)

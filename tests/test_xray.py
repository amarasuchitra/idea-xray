import json
from datetime import UTC, datetime

import httpx
import pytest
import respx

from idea_xray import llm, xray
from idea_xray.cli import main
from idea_xray.gaps import find_gaps, theme_of
from idea_xray.liveness import classify
from idea_xray.models import Complaint, Idea, Product, Status
from idea_xray.report import markdown
from idea_xray.score import durability, verdict
from idea_xray.sources import agentreach

NOW = datetime(2026, 10, 29, tzinfo=UTC)
IDEA = Idea("A habit tracker for remote teams with Slack nudges", "remote team leads", "$4 per user per month",
            ["habit tracker"])  # fmt: skip


def xr(**kw):
    with httpx.Client() as c:
        return xray.run(IDEA, c, now=NOW, **kw)


def by_name(x, name):
    return next(p for p in x.products if p.name == name)


def test_each_product_is_live_prototype_or_dead_with_evidence(web):
    x = xr()
    assert by_name(x, "Streaks").status is Status.live and "51,000 ratings" in by_name(x, "Streaks").why
    assert by_name(x, "me/habits").status is Status.prototype and "only 3 stars" in by_name(x, "me/habits").why
    assert by_name(x, "TeamHabits, a tiny habit app").status is Status.prototype
    habitron = by_name(x, "Habitron")
    assert habitron.status is Status.graveyard and "no update since Jun 2022" in habitron.why
    habithub = by_name(x, "old/habithub")
    assert habithub.status is Status.graveyard and "shutdown post" in habithub.why  # matched the HN shutdown story
    assert ("HabitHub is shutting down", "https://news.ycombinator.com/item?id=103") in x.shutdowns


def test_complaints_become_gaps_marked_fixable_or_not(web):
    gaps = {g.theme: g for g in xr().gaps}
    assert len(gaps["Price"].complaints) >= 2 and gaps["Price"].fixable
    assert gaps["Reliability"].fixable and gaps["Missing features"].fixable
    assert not gaps["Platform or legal limits"].fixable
    assert all("congrats" not in c.text.lower() for g in gaps.values() for c in g.complaints)  # praise is not a gap


def test_score_parts_add_up_and_carry_evidence(web):
    x = xr()
    assert x.total == sum(p.points for p in x.score) and 0 <= x.total <= 100
    assert {p.name for p in x.score} == {"Demand evidence", "Room to win", "Competition", "Graveyard warning",
                                         "Platform risk"}  # fmt: skip
    assert all(p.evidence for p in x.score)
    assert x.verdict == verdict(x.total) and x.engine == "rules"


def test_report_reads_top_to_bottom(web):
    body = markdown(xr())
    for heading in ["Durability score", "Devil's advocate", "What already exists", "Gaps:", "Next step"]:
        assert heading in body
    assert "[Streaks](https://apps.apple.com/app/streaks/id1)" in body
    assert "🪦 In the graveyard" in body


def test_one_broken_source_is_noted_not_fatal(web):
    web.get("https://itunes.apple.com/search").mock(side_effect=httpx.ConnectError("down"))
    x = xr()
    assert any("App Store could not be searched" in n for n in x.notes)
    assert any(p.source == "GitHub" for p in x.products)


@pytest.mark.parametrize(
    "text,theme",
    [
        ("The subscription is overpriced for what it does.", "Price"),
        ("It keeps crashing whenever I open it.", "Reliability"),
        ("I wish it could export to CSV.", "Missing features"),
        ("The interface is so confusing.", "Hard to use"),
        ("They sold my data to advertisers.", "Privacy and trust"),
        ("Apple won't allow apps to do this.", "Platform or legal limits"),
    ],
)
def test_themes(text, theme):
    assert theme_of(text).name == theme


def test_build_is_not_mistaken_for_ui_complaint():
    assert theme_of("Something about how we build and quit things.").name == "Other complaints"


def test_competition_sweet_spot_and_platform_risk():
    live = [Product(f"p{i}", "u", "GitHub", status=Status.live) for i in range(3)]
    parts = {p.name: p for p in durability(Idea("A ChatGPT plugin for lawyers"), live, [])}
    assert parts["Competition"].points == 20
    assert parts["Platform risk"].points == 5 and "chatgpt" in parts["Platform risk"].evidence.lower()
    crowded = [Product(f"p{i}", "u", "GitHub", status=Status.live) for i in range(20)]
    assert {p.name: p for p in durability(Idea("x"), crowded, [])}["Competition"].points == 5


def test_classify_rules_are_independent_of_today():
    p = classify(Product("a/b", "u", "GitHub", users=10, last_activity=datetime(2026, 1, 1, tzinfo=UTC)), [], NOW)
    assert p.status is Status.prototype
    hn = classify(Product("Old launch", "u", "Hacker News", users=300, last_activity=datetime(2019, 1, 1, tzinfo=UTC)),
                  [], NOW)  # fmt: skip
    assert hn.status is Status.live  # an old launch post is not a dead product


def test_gaps_sorted_biggest_first():
    cs = [Complaint("too expensive", f"u{i}", "x") for i in range(3)] + [Complaint("it crashes", "c", "x")]
    assert [g.theme for g in find_gaps(cs)][:2] == ["Price", "Reliability"]


@respx.mock
def test_ai_falls_back_to_the_next_free_provider(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "gh")
    monkeypatch.setenv("GROQ_API_KEY", "gq")
    respx.post("https://models.github.ai/inference/chat/completions").mock(return_value=httpx.Response(429))
    respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": '{"risks": ["Streaks is big."]}'}}]})
    )
    with httpx.Client() as c:
        assert llm.devils_advocate("evidence", c) == (["Streaks is big."], "groq")


def test_no_keys_means_rules(web):
    assert llm.available() == []
    assert xr().engine == "rules"


def test_cli_writes_the_report(web, tmp_path, capsys):
    out = tmp_path / "report.md"
    assert main(["A habit tracker for remote teams", "--keyword", "habit tracker", "--no-ai", "--out", str(out)]) == 0
    assert "Durability score" in out.read_text() and "Durability score" in capsys.readouterr().out


def test_yc_directory_finds_dead_and_funded_competitors(web):
    x = xr()
    dead, alive = by_name(x, "Habitly"), by_name(x, "Ritual")
    assert dead.status is Status.graveyard and "Inactive" in dead.why and "S21" in dead.why
    assert alive.status is Status.live and alive.why == "active, YC batch W24"
    assert not any(p.name == "Airbnb" for p in x.products)  # every search word must match
    assert ("Habitly (YC S21) is no longer active", "https://www.ycombinator.com/companies/habitly") in x.shutdowns


def test_report_links_to_the_graveyards_without_scraping_them(web):
    body = markdown(xr())
    for site in ("loot-drop.io", "startups.rip", "failory.com"):
        assert f"site%3A{site}+habit+tracker" in body
    assert "partly AI-generated" in body


def test_agent_reach_items_become_complaints_and_shutdowns():
    out = {"ok": True, "items": [
        {"title": "Our team habit app is shutting down", "url": "https://x.com/a/1", "text": ""},
        {"title": "habit trackers", "url": "https://x.com/b/2", "text": "Every team habit tracker is too expensive."},
        {"title": "no link", "url": None, "text": "It keeps crashing."},
    ]}  # fmt: skip
    seen = []
    search = agentreach.source("twitter", runner=lambda args: seen.append(args) or json.dumps(out))
    found = search(None, "habit tracker")
    assert seen == [["twitter", "search", "habit tracker", "--limit", "20"]]
    assert found.shutdowns == [("Our team habit app is shutting down", "https://x.com/a/1")]
    assert [(c.text, c.source) for c in found.complaints] == [
        ("Every team habit tracker is too expensive.", "X/Twitter")
    ]


def test_agent_reach_login_problem_is_noted_not_fatal(web):
    bad = agentreach.source("linkedin", runner=lambda args: json.dumps({"ok": False, "error": {"code": "NEED_LOGIN"}}))
    with httpx.Client() as c:
        x = xray.run(IDEA, c, sources={"LinkedIn (Agent-Reach)": bad}, use_ai=False, now=NOW)
    assert any("LinkedIn (Agent-Reach) could not be searched" in n for n in x.notes)


def test_reach_flag_needs_agent_reach_installed(monkeypatch):
    monkeypatch.setattr(agentreach, "installed", lambda: False)
    with pytest.raises(SystemExit, match="pip install agent-reach"):
        main(["idea", "--reach", "twitter"])

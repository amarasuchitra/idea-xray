"""Stages 4 and 5, the kit and the web app."""

import json
import threading
import urllib.error
import urllib.request
import zipfile
from datetime import UTC, datetime
from http.server import ThreadingHTTPServer
from io import BytesIO
from urllib.parse import urlencode

import httpx
import pytest

from idea_xray import community, kit, launch, plan, watch, web, xray
from idea_xray.cli import main
from idea_xray.models import Idea

from .test_xray import IDEA, NOW


def xr(idea=IDEA):
    with httpx.Client() as c:
        return xray.run(idea, c, use_ai=False, now=NOW)


@pytest.mark.parametrize(
    "text,amount,per,currency",
    [
        ("$4 per user per month", 4, "month", "$"),
        ("₹499/month", 499, "month", "₹"),
        ("Rs. 2,000 per year", 2000, "year", "₹"),
        ("₹1,00,000 lifetime", 100000, "once", "₹"),
        ("$9.99/month", 9.99, "month", "$"),
        ("€49 one-time", 49, "once", "€"),
        ("120 a year", 120, "year", ""),
    ],
)
def test_parse_price(text, amount, per, currency):
    p = plan.parse_price(text)
    assert (p.amount, p.per, p.currency) == (amount, per, currency)


def test_no_price_means_no_profit_maths():
    assert plan.parse_price("free") is None


def test_profit_maths_from_the_founders_price(web):
    lines = plan.profit(xr(), 1000)
    assert "**250 paying customers**" in lines[0]  # $1,000 / $4
    assert "**5,000 to 12,500 signups**" in lines[1]  # at 5% and 2%
    once = plan.profit(xr(Idea("x", price="$50 one-time")), 1000)
    assert "**20 new sales every month**" in once[0]


def test_build_plan_scope_risks_and_realities(web):
    body = plan.markdown(xr())
    assert "**Your edge:** fair, simple pricing" in body
    assert "| Same fate as the dead ones | High |" in body  # Habitron, old/habithub, Habitly
    assert "250 paying customers is 250 people to find" in body
    assert "CI Doctor" in body


def test_ask_for_help_points_to_where_the_complaints_came_from(web):
    body = community.markdown(xr())
    assert "X-ray score:" in body and "/discussions" in body
    assert any(p.startswith("r/") for p in community.where_customers_are(xr()))


def test_watch_reports_new_and_dead_competitors():
    old = {"taken": "2026-10-01T00:00:00+00:00", "score": 60, "gaps": {"Price": 2},
           "products": {"GitHub: a/b": {"status": "live", "url": "u1", "why": "500 stars"}}}  # fmt: skip
    new = {"taken": "2026-10-29T00:00:00+00:00", "score": 66, "gaps": {"Price": 5, "Support": 1},
           "products": {"GitHub: a/b": {"status": "graveyard", "url": "u1", "why": "archived by its owner"},
                        "App Store: Newco": {"status": "live", "url": "u2", "why": "300 ratings"}}}  # fmt: skip
    found = watch.changes(old, new)
    assert "Score moved from 60 to 66." in found
    assert any("New competitor: [App Store: Newco]" in c for c in found)
    assert any("Died: [GitHub: a/b]" in c for c in found)
    assert "🗣️ Price: 5 complaints, up from 2." in found and "🗣️ Support: 1 complaints, up from 0." in found
    assert "Nothing important changed" in watch.markdown(old, old)


def test_launch_checklist_includes_the_watch_workflow(web):
    body = launch.markdown(xr())
    assert "--save xray-new.json --compare xray.json" in body and "cron" in body


def test_cli_kit_and_compare(web, tmp_path, capsys):
    args = ["A habit tracker for remote teams", "--keyword", "habit tracker", "--no-ai", "--price", "$4 per month"]
    assert main([*args, "--kit", str(tmp_path / "kit"), "--save", str(tmp_path / "x.json")]) == 0
    names = {p.relative_to(tmp_path / "kit").as_posix() for p in (tmp_path / "kit").rglob("*") if p.is_file()}
    assert names == set(kit.files(xr()))
    old = json.loads((tmp_path / "x.json").read_text())
    old["products"].pop(next(iter(old["products"])))
    (tmp_path / "old.json").write_text(json.dumps(old))
    assert main([*args, "--compare", str(tmp_path / "old.json"), "--changes", str(tmp_path / "c.md")]) == 0
    assert "New competitor" in (tmp_path / "c.md").read_text()


def test_render_blocks_injected_html_and_script_links():
    out = web.render("<script>alert(1)</script> [x](javascript:alert(1)) <details><summary>ok</summary></details>")
    assert "<script>" not in out and 'href="#"' in out and "<details>" in out


@pytest.fixture
def server(web):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), web_handler())
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def web_handler():
    return web.Handler


def get(url):
    with urllib.request.urlopen(url) as r:  # urllib, so respx doesn't intercept our own server
        return r.read(), r.headers


def test_web_app_runs_the_whole_flow(server):
    page, _ = get(server + "/")
    assert b"Will your startup idea survive?" in page
    data = urlencode({"pitch": "A habit tracker for remote teams", "customer": "team leads", "price": "$4 per month",
                      "keywords": "habit tracker", "goal": "50", "days": "10", "target": "2000"}).encode()  # fmt: skip
    with urllib.request.urlopen(server + "/xray", data=data) as r:
        body = r.read().decode()
    for label, _ in [(lbl, f) for f, lbl in web.STAGES]:
        assert label in body
    assert "**Goal:** 50" not in body and "50 waitlist signups" in body  # rendered, not raw Markdown
    assert "500 paying customers" in body  # $2,000 / $4
    rid = body.split('href="/r/')[1].split("/")[0]
    waitlist, _ = get(f"{server}/r/{rid}/page")
    assert b"Join the waitlist" in waitlist
    z, headers = get(f"{server}/r/{rid}/kit.zip")
    assert headers["Content-Type"] == "application/zip"
    assert "idea-kit/3-build-plan.md" in zipfile.ZipFile(BytesIO(z)).namelist()


def test_web_app_rejects_bad_input(server):
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(server + "/xray", data=urlencode({"pitch": "x", "form": "javascript:1"}).encode())
    assert e.value.code == 400
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(server + "/r/nope/page")
    assert e.value.code == 404


def test_snapshot_round_trips(web):
    snap = watch.snapshot(xr(), datetime(2026, 10, 29, tzinfo=UTC))
    assert json.loads(watch.dumps(snap)) == snap and snap["taken"].startswith("2026-10-29")

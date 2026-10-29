"""idea-xray serve: the whole flow in a browser, for founders who don't use a terminal.

Fill in the idea, get every stage on one page, preview the waitlist page and download the kit.
It uses only the standard library's web server, so it runs anywhere Python does.
"""

from __future__ import annotations

import html
import re
import secrets
from collections import OrderedDict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from . import PROJECT_URL, demand, kit, xray
from .cli import client
from .htmlrender import render
from .models import Idea

STAGES = [
    ("1-xray-report.md", "1. Check the idea"),
    ("2-demand-test/TEST-PLAN.md", "2. Test demand"),
    ("3-build-plan.md", "3. Build plan"),
    ("4-ask-for-help.md", "4. Advice and team"),
    ("5-launch.md", "5. Launch and improve"),
]
MAX_KEPT = 200  # results kept in memory; the oldest are dropped
results: OrderedDict[str, dict[str, str]] = OrderedDict()


STYLE = """
:root { --bg:#fbfaf7; --fg:#1c1b19; --muted:#5f5b53; --card:#fff; --line:#e6e1d8; --accent:#2f5d50; --on:#fff;
  --soft:#eef3f0; }
@media (prefers-color-scheme: dark) { :root { --bg:#151513; --fg:#ecebe6; --muted:#a8a49b; --card:#1f1e1b;
  --line:#33312c; --accent:#7fc4ad; --on:#10201b; --soft:#1d2a25; } }
* { box-sizing:border-box }
body { margin:0; background:var(--bg); color:var(--fg); font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif }
main { max-width:860px; margin:0 auto; padding:40px 16px 64px }
h1 { font-size:clamp(26px,5vw,38px); line-height:1.2; margin:0 0 8px }
.lead { color:var(--muted); margin:0 0 28px; font-size:18px }
label { display:block; font-weight:600; margin:16px 0 6px }
label small { font-weight:400; color:var(--muted) }
input, textarea { width:100%; padding:11px 13px; border:1px solid var(--line); border-radius:8px;
  background:var(--card); color:var(--fg); font:inherit }
.row { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:0 16px }
button, .btn { display:inline-block; margin-top:24px; padding:12px 22px; border:0; border-radius:8px;
  background:var(--accent); color:var(--on); font:inherit; font-weight:600; cursor:pointer; text-decoration:none }
.btn.alt { background:transparent; color:var(--accent); border:1px solid var(--accent) }
nav { display:flex; flex-wrap:wrap; gap:6px; margin:24px 0 0; border-bottom:1px solid var(--line) }
nav a { padding:9px 14px; border-radius:8px 8px 0 0; color:var(--muted); text-decoration:none; font-weight:600 }
nav a[aria-current] { background:var(--card); color:var(--fg); border:1px solid var(--line);
  border-bottom-color:var(--card); margin-bottom:-1px }
section { background:var(--card); border:1px solid var(--line); border-top:0; border-radius:0 0 12px 12px;
  padding:8px 24px 24px; overflow-x:auto }
section[hidden] { display:none }
table { border-collapse:collapse; width:100%; font-size:15px } th, td { border-bottom:1px solid var(--line);
  padding:8px; text-align:left; vertical-align:top }
blockquote { margin:8px 0; padding:4px 14px; border-left:3px solid var(--line); color:var(--muted) }
pre { background:var(--soft); padding:14px; border-radius:8px; overflow-x:auto; font-size:14px }
a { color:var(--accent) } .actions { display:flex; flex-wrap:wrap; gap:12px }
.note { color:var(--muted); font-size:14px; margin-top:28px }
"""


def layout(title: str, body: str) -> bytes:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title><style>{STYLE}</style></head>
<body><main>{body}
<p class="note">Free and open source · <a href="{PROJECT_URL}">Idea X-ray on GitHub</a></p></main></body></html>
""".encode()


FORM = """
<h1>Will your startup idea survive?</h1>
<p class="lead">See who already tried it, who died, what users complain about, and get a plan from first test to
launch. Free, with every claim linked to its evidence.</p>
<form method="post" action="/xray"
 onsubmit="this.querySelector('button').textContent='Checking the evidence, about a minute…'">
<label for="pitch">Your idea <small>one or two sentences</small></label>
<textarea id="pitch" name="pitch" rows="2" required maxlength="500"
 placeholder="A habit tracker for remote teams with Slack nudges"></textarea>
<div class="row">
<div><label for="customer">Who it's for</label><input id="customer" name="customer" maxlength="200"
 placeholder="remote team leads"></div>
<div><label for="price">Price</label><input id="price" name="price" maxlength="100"
 placeholder="$4 per user per month"></div>
</div>
<label for="keywords">Search words <small>comma separated, the words your customers would type</small></label>
<input id="keywords" name="keywords" maxlength="300" placeholder="habit tracker, team habits">
<div class="row">
<div><label for="goal">Signup goal</label><input id="goal" name="goal" type="number" min="1" value="100"></div>
<div><label for="days">Test length (days)</label><input id="days" name="days" type="number" min="1" value="14"></div>
<div><label for="target">Monthly income goal</label><input id="target" name="target" type="number"
 min="1" value="1000"></div>
</div>
<label for="form">Waitlist form URL <small>optional: Formspree, Basin or Tally, https:// only</small></label>
<input id="form" name="form" type="url" pattern="https://.*" placeholder="https://formspree.io/f/…">
<button type="submit">X-ray my idea</button>
</form>
"""

TABS_JS = """<script>
document.querySelectorAll('nav a').forEach(a => a.addEventListener('click', e => {
  e.preventDefault();
  document.querySelectorAll('nav a').forEach(b => b.removeAttribute('aria-current'));
  document.querySelectorAll('section').forEach(s => s.hidden = s.id !== a.dataset.tab);
  a.setAttribute('aria-current', 'page');
}));
</script>"""


def result_page(rid: str, files: dict[str, str], idea: Idea) -> bytes:
    nav = "".join(
        f'<a href="#s{i}" data-tab="s{i}"{" aria-current=page" if i == 0 else ""}>{html.escape(label)}</a>'
        for i, (_, label) in enumerate(STAGES)
    )
    sections = "".join(
        f'<section id="s{i}"{" hidden" if i else ""}>{render(files[name])}</section>'
        for i, (name, _) in enumerate(STAGES)
    )
    actions = (
        f'<div class="actions"><a class="btn" href="/r/{rid}/page" target="_blank" rel="noopener">Preview the waitlist '
        f'page</a><a class="btn alt" href="/r/{rid}/kit.zip">Download the full kit</a>'
        f'<a class="btn alt" href="/">Check another idea</a></div>'
    )
    body = f"<h1>{html.escape(idea.pitch)}</h1>{actions}<nav>{nav}</nav>{sections}{TABS_JS}"
    return layout("Idea X-ray result", body)


def _int(form: dict, key: str, default: int) -> int:
    try:
        return max(1, int(form.get(key, [default])[0]))
    except ValueError:
        return default


class Handler(BaseHTTPRequestHandler):
    server_version = "idea-xray"

    def _send(self, body: bytes, kind: str = "text/html; charset=utf-8", status: int = 200, extra=None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: HTTPStatus, text: str) -> None:
        self._send(layout("Idea X-ray", f'<h1>{html.escape(text)}</h1><p><a href="/">Back</a></p>'), status=status)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            return self._send(layout("Idea X-ray", FORM))
        m = re.fullmatch(r"/r/([\w-]+)/(page|kit\.zip)", self.path)
        if not m or m.group(1) not in results:
            return self._error(HTTPStatus.NOT_FOUND, "Not found. Results are kept only for a while.")
        files = results[m.group(1)]
        if m.group(2) == "page":
            return self._send(files["2-demand-test/index.html"].encode())
        self._send(kit.zipped(files), "application/zip",
                   extra={"Content-Disposition": 'attachment; filename="idea-kit.zip"'})  # fmt: skip

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/xray":
            return self._error(HTTPStatus.NOT_FOUND, "Not found.")
        size = int(self.headers.get("Content-Length") or 0)
        if size > 20_000:
            return self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "That's too long.")
        form = parse_qs(self.rfile.read(size).decode("utf-8", "replace"))
        pitch = form.get("pitch", [""])[0].strip()[:500]
        if not pitch:
            return self._error(HTTPStatus.BAD_REQUEST, "Please describe the idea.")
        words = [w.strip() for w in form.get("keywords", [""])[0].split(",") if w.strip()][:5]
        idea = Idea(pitch, form.get("customer", [""])[0].strip()[:200], form.get("price", [""])[0].strip()[:100], words)
        url = form.get("form", [""])[0].strip()
        if url and not url.startswith("https://"):
            return self._error(HTTPStatus.BAD_REQUEST, "The form URL must start with https://")
        with client() as c:
            x = xray.run(idea, c)
        test = demand.Test(_int(form, "goal", 100), _int(form, "days", 14))
        files = kit.files(x, url, test, _int(form, "target", 1000))
        rid = secrets.token_urlsafe(9)
        results[rid] = files
        while len(results) > MAX_KEPT:
            results.popitem(last=False)
        self._send(result_page(rid, files, idea))


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Idea X-ray is running at http://{'localhost' if host == '127.0.0.1' else host}:{port}  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

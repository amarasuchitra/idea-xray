"""Run Idea X-ray inside a web page (Pyodide), so the public site needs no server.

The browser can't use httpx's network stack, so a small stand-in with the same calls is installed as
the `httpx` module before anything else is imported. Requests go out as plain browser requests; a site
that refuses them (no CORS) is skipped and listed under the report's limits, like any other outage.
"""

from __future__ import annotations

import base64
import json
import sys
import types
from urllib.parse import urlencode


def _install_httpx_stand_in() -> None:
    from js import XMLHttpRequest  # only exists inside Pyodide

    class HTTPError(Exception):
        pass

    class ConnectError(HTTPError):
        pass

    class HTTPStatusError(HTTPError):
        pass

    class Response:
        def __init__(self, status_code: int, text: str):
            self.status_code, self.text = status_code, text

        def json(self):
            return json.loads(self.text)

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise HTTPStatusError(f"HTTP {self.status_code}")

    class Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def _send(self, method: str, url: str, params=None, headers=None, json_body=None) -> Response:
            if params:
                url += ("&" if "?" in url else "?") + urlencode(params)
            xhr = XMLHttpRequest.new()
            try:
                xhr.open(method, url, False)  # synchronous: fine inside a Web Worker
                for k, v in (headers or {}).items():
                    xhr.setRequestHeader(k, v)
                if json_body is not None:
                    xhr.setRequestHeader("Content-Type", "application/json")
                    xhr.send(json.dumps(json_body))
                else:
                    xhr.send()
            except Exception as e:  # network failure or the site refused a browser request
                raise ConnectError(str(e)) from e
            if xhr.status == 0:
                raise ConnectError("the site refused a request from the browser")
            if xhr.status >= 400:
                raise HTTPStatusError(f"HTTP {xhr.status}")
            return Response(xhr.status, xhr.responseText)

        def get(self, url, params=None, headers=None, **kwargs):
            return self._send("GET", url, params, headers)

        def post(self, url, json=None, headers=None, **kwargs):
            return self._send("POST", url, None, headers, json)

    mod = types.ModuleType("httpx")
    mod.Client, mod.Response = Client, Response
    mod.HTTPError, mod.ConnectError, mod.HTTPStatusError = HTTPError, ConnectError, HTTPStatusError
    sys.modules["httpx"] = mod


def run(form_json: str) -> str:
    """The whole flow for one idea: every stage as HTML, the waitlist page, and the kit files."""
    if "httpx" not in sys.modules:
        _install_httpx_stand_in()
    import httpx

    from . import demand, kit, xray
    from .htmlrender import render
    from .models import Idea

    f = json.loads(form_json)
    words = [w.strip() for w in f.get("keywords", "").split(",") if w.strip()][:5]
    idea = Idea(f["pitch"].strip()[:500], f.get("customer", "").strip()[:200], f.get("price", "").strip()[:100], words)
    form = f.get("form", "").strip()
    if form and not form.startswith("https://"):
        form = ""
    with httpx.Client() as c:
        x = xray.run(idea, c, use_ai=False)
    test = demand.Test(max(1, int(f.get("goal") or 100)), max(1, int(f.get("days") or 14)))
    files = kit.files(x, form, test, max(1.0, float(f.get("target") or 1000)))
    stages = [
        ("1-xray-report.md", "Check the idea"),
        ("2-demand-test/TEST-PLAN.md", "Test demand"),
        ("3-build-plan.md", "Build plan"),
        ("4-ask-for-help.md", "Advice and team"),
        ("5-launch.md", "Launch and improve"),
    ]
    return json.dumps({
        "pitch": idea.pitch,
        "score": x.total,
        "verdict": x.verdict,
        "stages": [{"label": label, "html": render(files[name])} for name, label in stages],
        "page": files["2-demand-test/index.html"],
        "zip": base64.b64encode(kit.zipped(files)).decode(),
    })  # fmt: skip

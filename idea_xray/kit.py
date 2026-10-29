"""The whole idea-to-launch kit for one X-ray, as files: what the CLI writes and the web app downloads."""

from __future__ import annotations

import io
import zipfile
from datetime import datetime

from . import community, demand, launch, plan, report, watch
from .models import XRay


def files(x: XRay, form: str = "", test: demand.Test | None = None, target: float = 1000,
          now: datetime | None = None) -> dict[str, str]:  # fmt: skip
    test = test or demand.Test()
    return {
        "1-xray-report.md": report.markdown(x),
        "2-demand-test/index.html": demand.page(x, form),
        "2-demand-test/TEST-PLAN.md": demand.plan(x, test),
        "3-build-plan.md": plan.markdown(x, target),
        "4-ask-for-help.md": community.markdown(x),
        "5-launch.md": launch.markdown(x),
        "xray.json": watch.dumps(watch.snapshot(x, now)),
    }


def zipped(kit: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, text in kit.items():
            z.writestr(f"idea-kit/{name}", text)
    return buf.getvalue()

"""Stage 5, launch and keep improving: a checklist from going public to the weekly feedback loop."""

from __future__ import annotations

from .community import DISCUSSIONS, where_customers_are
from .models import XRay

WATCH_WORKFLOW = """name: Competitor watch
on:
  schedule: [{cron: "0 6 * * 1"}]  # every Monday
  workflow_dispatch:
permissions:
  contents: write
  issues: write
jobs:
  watch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: pip install git+https://github.com/amarasuchitra/idea-xray
      - run: |
          idea-xray --file idea.yaml --no-ai --save xray-new.json --compare xray.json --changes changes.md
          mv xray-new.json xray.json
      - name: Open an issue when something changed
        env: {GH_TOKEN: "${{ github.token }}"}
        run: |
          if ! grep -q "Nothing important changed" changes.md; then
            gh issue create --title "Competitor watch: $(date +%F)" --body-file changes.md
          fi
      - run: |
          git config user.name "idea-xray" && git config user.email "idea-xray@users.noreply.github.com"
          git add xray.json && git commit -m "Competitor watch $(date +%F)" && git push || true
"""


def markdown(x: XRay) -> str:
    places = where_customers_are(x)
    where = ", ".join(places) if places else "the communities where your customers talk"
    return "\n".join([
        "# Launch and keep improving",
        "",
        "## Before launch",
        "",
        "- [ ] The demand test passed, and you wrote the result down.",
        "- [ ] Five people from the waitlist have tried an early version and told you what's missing.",
        "- [ ] The one-line pitch says who it's for and what pain it removes.",
        "- [ ] Payments work, with a real test purchase.",
        "- [ ] Errors are reported to you, and backups run.",
        "",
        "## Launch week",
        "",
        "- [ ] Email the waitlist first. They asked for it.",
        f"- [ ] Post where your customers already are: {where}. Tell the story of the problem, not the features.",
        "- [ ] Show HN or Product Hunt, if it fits your customers.",
        f"- [ ] Share your journey in [Idea X-ray Discussions]({DISCUSSIONS}).",
        "- [ ] Answer every comment the same day.",
        "",
        "## Every week after",
        "",
        "- [ ] Read every message and support request. Write down the three things asked most.",
        "- [ ] Fix the biggest pain before adding anything new.",
        "- [ ] Check the numbers: signups, active users, paying users, people who left (and why).",
        "- [ ] Competitor watch: re-run the X-ray and compare (see below).",
        "",
        "## Watch competitors automatically",
        "",
        "Put your `idea.yaml` and this workflow in a GitHub repo as `.github/workflows/competitor-watch.yml`. "
        "Every Monday it re-runs the X-ray and opens an issue when a competitor appears or dies, or complaints grow.",
        "",
        "```yaml",
        WATCH_WORKFLOW.rstrip(),
        "```",
        "",
        "## When to stop or pivot",
        "",
        "Decide now: if paying users don't grow for three months in a row despite real effort, change the customer, "
        "the problem or the price, and run the X-ray again. Quitting a dead end early is a win.",
        "",
    ])  # fmt: skip

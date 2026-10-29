"""Stage 3, the demand test: a one-page site with a waitlist, and a pass mark set before anyone sees it.

An X-ray shows what the evidence says. Only real people signing up can prove the idea, so this turns the
X-ray into a page you can publish today (on GitHub Pages, for free) and a written plan you can't fudge later.

The page never invents users, quotes or numbers. Edit the wording, but keep it honest: a test built on a
fake promise only proves the promise worked.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from html import escape

from . import PROJECT_URL
from .models import XRay

# What each fixable gap becomes on the page: (promise, line under it)
PROMISE = {
    "Price": ("Fair, simple pricing", "Existing tools charge too much for what you get."),
    "Reliability": ("Works every time", "Existing tools crash, lose data or slow down."),
    "Missing features": ("Does what the others skip", "Existing tools leave out what people keep asking for."),
    "Hard to use": ("Simple from the first minute", "Existing tools are confusing to set up and use."),
    "Privacy and trust": ("Your data stays yours", "People don't trust what existing tools do with their data."),
    "Support": ("Real people answer", "Existing tools leave users waiting for help."),
}


@dataclass
class Test:
    signups: int = 100  # pass mark: waitlist signups
    days: int = 14
    start: date | None = None

    @property
    def end(self) -> date:
        return (self.start or date.today()) + timedelta(days=self.days)


def promises(x: XRay) -> list[tuple[str, str, int]]:
    """(promise, why, complaints behind it) for each fixable gap, biggest first, at most three."""
    out = [(*PROMISE[g.theme], len(g.complaints)) for g in x.gaps if g.fixable and g.theme in PROMISE]
    return out[:3]


def page(x: XRay, form_action: str = "") -> str:
    if form_action and not form_action.startswith("https://"):
        raise ValueError("the form URL must start with https://")
    idea, e = x.idea, escape
    cards = "".join(
        f'<li><h3>{e(title)}</h3><p>{e(why)}</p><p class="ev">Found in {n} real complaint{"s" * (n != 1)}.</p></li>'
        for title, why, n in promises(x)
    )
    price = f'<p class="price">Planned price: <strong>{e(idea.price)}</strong></p>' if idea.price else ""
    pay = (
        f'<label class="pay"><input type="checkbox" name="would_pay" value="yes"> I would pay {e(idea.price)}</label>'
        if idea.price
        else ""
    )
    action = e(form_action) if form_action else "#"
    note = "" if form_action else '<p class="warn">Connect a form service before publishing (see TEST-PLAN.md).</p>'
    who = f'<p class="who">For {e(idea.customer)}</p>' if idea.customer else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(idea.pitch[:60])}</title>
<meta name="description" content="{e(idea.pitch)}">
<style>
:root {{ --bg:#fbfaf7; --fg:#1c1b19; --muted:#5f5b53; --card:#fff; --line:#e6e1d8; --accent:#2f5d50; --on:#fff; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#151513; --fg:#ecebe6; --muted:#a8a49b; --card:#1f1e1b; --line:#33312c;
    --accent:#7fc4ad; --on:#10201b; }}
}}
* {{ box-sizing:border-box }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:17px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif }}
main {{ max-width:720px; margin:0 auto; padding:64px 16px }}
h1 {{ font-size:clamp(28px,6vw,44px); line-height:1.15; margin:0 0 12px }}
.who {{ color:var(--muted); font-size:19px; margin:0 0 32px }}
ul {{ list-style:none; padding:0; display:grid; gap:12px; margin:0 0 32px }}
li {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px 20px }}
h3 {{ margin:0 0 4px; font-size:18px }} li p {{ margin:0 }}
.ev {{ color:var(--muted); font-size:14px; margin-top:6px }}
form {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center }}
input[type=email] {{ flex:1 1 240px; padding:12px 14px; border:1px solid var(--line); border-radius:8px;
  background:var(--card); color:var(--fg); font:inherit }}
button {{ padding:12px 20px; border:0; border-radius:8px; background:var(--accent); color:var(--on); font:inherit;
  font-weight:600; cursor:pointer }}
.pay {{ flex-basis:100%; color:var(--muted); font-size:15px }}
.price {{ margin:0 0 12px }} .warn {{ color:#b3261e; font-weight:600 }}
footer {{ margin-top:48px; color:var(--muted); font-size:13px }} a {{ color:var(--accent) }}
</style>
</head>
<body>
<main>
<h1>{e(idea.pitch)}</h1>
{who}
<ul>{cards}</ul>
{price}
<form action="{action}" method="POST">
<input type="email" name="email" required placeholder="you@example.com" aria-label="Email address">
<button type="submit">Join the waitlist</button>
{pay}
</form>
{note}
<footer>We're testing whether to build this. We'll only email you about it. ·
Made with <a href="{PROJECT_URL}">Idea X-ray</a></footer>
</main>
</body>
</html>
"""


def plan(x: XRay, test: Test) -> str:
    start = test.start or date.today()
    rows = "\n".join(f"| {t} | {n} complaint(s) |" for t, _, n in promises(x)) or "| (none yet) | |"
    return f"""# Demand test plan

**Idea:** {x.idea.pitch}
**X-ray score:** {x.total} / 100 ({x.verdict})

## The pass mark (decide now, don't change it later)

- **Goal:** {test.signups} waitlist signups
- **Dates:** {start:%d %b %Y} to {test.end:%d %b %Y} ({test.days} days)
- **If we hit it:** move to stage 4 and plan the build.
- **If we miss it:** change the customer, the promise or the price, and run a new test. Don't build yet.

Write down the result either way. Moving the goal after the test started turns it into a guess.

## What the page promises

| Promise | Evidence from the X-ray |
|---|---|
{rows}

## Publish it for free

1. **Collect emails.** Make a free form on a service such as Formspree, Basin or Tally, then run again with
   `--form <your form URL>`. Without one, the button goes nowhere.
2. **Host the page.** Push `index.html` to a GitHub repo and turn on GitHub Pages
   (Settings, then Pages, then Deploy from branch).
3. **Bring people to it.** Post where your customers already are, using the places the X-ray found complaints.
   Tell them it's a test. Never buy fake signups: they prove nothing.

## Honest-test rules

- No made-up users, quotes, logos or numbers on the page.
- Count only real signups. A "would pay" tick is a stronger signal than an email alone.
- Talk to 5 people who signed up before you build anything.
"""

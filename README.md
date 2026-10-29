# 🩻 Idea X-ray

**Before you spend months building a startup idea, find out who already tried it, who's still alive, who died, and what their users complain about.**

Most startups fail because nobody needed what they built. In [CB Insights' study](https://www.launchrock.com/library/expert-advice/why-do-startups-fail) of 101 failed startups, 42% gave "no market need" as a reason. Idea X-ray checks an idea against real, linked evidence in a few minutes:

1. **What already exists.** It searches Hacker News, GitHub, the App Store and Reddit for products doing the same job. Each one is marked 🟢 **Live and used**, 🟡 **Prototype nobody uses**, or 🪦 **In the graveyard**, with the evidence (ratings, stars, last update, a shutdown post).
2. **Where they fall short.** It pulls real user complaints and groups them into gaps: price, reliability, missing features, ease of use, privacy, support, and platform or legal limits. Each gap is marked fixable or hard to fix, with a profit angle.
3. **A durability score out of 100.** It has five parts (demand evidence, room to win, competition, graveyard warning, platform risk), and every point shows the evidence behind it.
4. **A devil's advocate.** You get the strongest reasons the idea could fail. Built-in rules always work, and a free AI model gives a sharper version if you add a key.
5. **A next step.** Go, rethink or stop. If it's go, set a pass mark *before* testing with real people.

See a [sample report](examples/sample-report.md) (made from test data).

## Run it

```bash
pip install git+https://github.com/amarasuchitra/idea-xray
idea-xray "A habit tracker for remote teams with Slack nudges" \
  --customer "remote team leads" --price "\$4 per user per month" \
  --keyword "habit tracker" --keyword "team habits" --out report.md
```

Or put the idea in a file and run `idea-xray --file idea.yaml`:

```yaml
pitch: A habit tracker for remote teams with Slack nudges
customer: remote team leads
price: $4 per user per month
keywords: [habit tracker, team habits]
```

Good keywords matter most. Use the words your customers would type, not your product name.

## Free by default

All four sources are free and need no key. A `GITHUB_TOKEN` raises GitHub's search limit.

The devil's advocate uses built-in rules unless you add a key for any of these free tiers. When one runs out for the day, the next one is tried:

| Provider | Env variable | Note |
|---|---|---|
| GitHub Models | `GITHUB_TOKEN` | Free with limits. In Actions, give the job `models: read` |
| Groq | `GROQ_API_KEY` | Free tier, very fast |
| Cerebras | `CEREBRAS_API_KEY` | Free tier |
| Google AI Studio | `GEMINI_API_KEY` | Free tier; prompts may be used for training outside the EU/UK |
| OpenRouter | `OPENROUTER_API_KEY` | Free models with a daily limit |

Free limits and model names change often. Override a model with `IDEA_XRAY_<PROVIDER>_MODEL`, for example `IDEA_XRAY_GROQ_MODEL`. Use your own accounts: shared or leaked keys break the providers' terms and get banned. Use `--no-ai` to force the rules.

## Be honest with yourself

- **The score is not a prediction.** It shows how strong the evidence is today. Only real people signing up or paying can prove an idea.
- **"Nothing found" is not good news by default.** It can mean a fresh chance, or that nobody wants this.
- **A crowded market proves demand.** A graveyard full of similar products is a warning, and its shutdown posts are free lessons.
- **Search is not the whole world.** It misses products outside these four sources, and it can't see private revenue. Check the links yourself.
- **Complaint text is written by strangers.** It is treated as data. The AI is told never to follow instructions inside it.

## How it works

```
idea + keywords
   ├─ sources/hackernews.py  launches (Show HN), shutdown posts, complaints in comments
   ├─ sources/github.py      open-source attempts: stars, last push, archived
   ├─ sources/appstore.py    apps: ratings, last version date
   └─ sources/reddit.py      complaints, "alternative to" posts, shutdown posts
liveness.py   live / prototype / graveyard rules (18 months without an update = abandoned)
gaps.py       complaints → themed gaps, fixable or not, profit angle
score.py      durability score parts + rule-based devil's advocate
llm.py        optional AI devil's advocate with free-provider fallback
report.py     the Markdown report
```

A source that fails is skipped and listed under "Limits of this report", so one outage never stops the X-ray.

## Development

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check . && pytest -q
```

Tests run against recorded API responses in `tests/fixtures`, so they need no network.

## Part of a bigger flow

Idea X-ray is stages 1 and 2 of a five-stage flow for taking a startup from idea to a product that lasts: check the idea, find the gaps, plan with the harsh realities, get advice and a team, then build, launch and keep improving. Next up is the real demand test: a landing page with a waitlist and a pass mark you set before you start.

## License

MIT

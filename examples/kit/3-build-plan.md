<!-- Sample only: built from the made-up test data in tests/fixtures. -->

# Build plan

> A habit tracker for remote teams with Slack nudges

Build this **only after the demand test passes**. Every point below comes from the X-ray; rules of thumb are marked as such.

## What to build first

- **Must have:** the core job, *A habit tracker for remote teams with Slack nudges*, done well for remote team leads.
- **Your edge:** fair, simple pricing. This is the biggest fixable gap (2 complaints), so it's in version one.
- **Later, if the first users ask:** does what the others skip, works every time.
- **Not now:** copying every feature of the market leader. A small product that fixes one pain beats a weaker copy of a big one.
- **Don't promise:** anything blocked by platform or legal limits. Users complain about those, but a new product can't fix them either.

## Profit maths (target: $1,000 a month)

- At $4 a month per customer, $1,000 a month needs **250 paying customers** who stay.
- If 2 to 5% of waitlist signups end up paying (a rule of thumb; your demand test gives the real number), that is **5,000 to 12,500 signups**.
- Payment providers keep a few percent of every sale, and taxes come out of what is left.

## Costs

| What | Cost |
|---|---|
| Website and waitlist | Free (GitHub Pages and a free form service) |
| Domain name | Usually a small yearly fee |
| App hosting and database | Free tiers exist for small apps; costs grow with users |
| Email to users | Free tiers cover early lists |
| Payments | No monthly fee on most providers, a few percent per sale |
| Your time | The biggest cost. Count the hours, even if you don't pay yourself |

## Risks and what to do

| Risk | Level | What to do |
|---|---|---|
| Nobody wants it | Medium | Pass the demand test before building. Talk to 5 people who signed up. |
| Competitors | Medium | Win on your one edge, not on feature count. Watch competitors every week (`idea-xray --compare`). |
| Same fate as the dead ones | High | Read the shutdown stories and graveyard links in the report, and write down how you'll avoid each cause. |
| Platform dependence | Low | Keep your customers' data and contact with you, and have a plan if the platform changes its rules. |
| Running out of time or money | Medium | Set a date to stop if the pass marks aren't met. Keep costs on free tiers until people pay. |

## Harsh realities

- Of 9 similar products found, 3 are dead and 4 are alive. Most ideas in any space don't make it.
- Streaks already has 51,000 ratings, updated Sep 2026. People rarely switch unless the pain is real.
- 250 paying customers is 250 people to find, convince and support. That usually takes many months, not weeks.
- Launch day usually brings a spike, then quiet. Growth comes from showing up for months.
- After launch, upkeep (bugs, updates, security, support) takes a big share of your time. Plan for it.

## Keeping it alive

- Update dependencies monthly and fix security alerts the same week (turn on Dependabot on GitHub).
- Back up user data automatically, and test a restore once.
- Keep CI green and honest: [CI Doctor](https://github.com/amarasuchitra/ci-doctor) explains failures and flags fixes that only hide them.
- Reply to every user message in the first months. It's your best source of what to build next.
- Re-run the X-ray monthly to see new competitors and new complaints.

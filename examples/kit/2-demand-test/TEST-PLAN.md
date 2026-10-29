<!-- Sample only: built from the made-up test data in tests/fixtures. -->

# Demand test plan

**Idea:** A habit tracker for remote teams with Slack nudges
**X-ray score:** 78 / 100 (Go: run the real demand test (landing page with a waitlist or pre-orders))

## The pass mark (decide now, don't change it later)

- **Goal:** 100 waitlist signups
- **Dates:** 01 Nov 2026 to 15 Nov 2026 (14 days)
- **If we hit it:** move to stage 4 and plan the build.
- **If we miss it:** change the customer, the promise or the price, and run a new test. Don't build yet.

Write down the result either way. Moving the goal after the test started turns it into a guess.

## What the page promises

| Promise | Evidence from the X-ray |
|---|---|
| Fair, simple pricing | 2 complaint(s) |
| Does what the others skip | 2 complaint(s) |
| Works every time | 1 complaint(s) |

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

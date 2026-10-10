# Shortlink exercises

You are joining the Shortlink team this week. You have never seen this code
before. Use AI tools (Claude, ChatGPT, Copilot, Cursor, anything you like)
the way you would at work.

What we care about is **how** you work with AI, not how fast you finish:

- what context you give the tool,
- whether you check what it tells you before you believe it,
- when you disagree with it,
- and whether you can explain the result in your own words.

Your interviewer will tell you which exercises to do. You probably won't
finish everything. That's expected. Say what you skipped and why.

## Before you start

```bash
git clone https://github.com/tiennguyentony/shortlink.git
cd shortlink
uv sync                 # creates .venv and installs everything
uv run pytest           # should be green
uv run uvicorn shortlink.main:create_app --factory --reload
                        # API on http://localhost:8000, docs at /docs, demo data loaded
```

No `uv`? Use plain pip instead:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
uvicorn shortlink.main:create_app --factory --reload
```

You need Python 3.11 or newer (`python --version`). Demo API keys are in the
README. To start over with fresh demo data, stop the server and delete
`shortlink.db`.

**Ground rules**

1. Share your screen, including your AI chat window.
2. Keep your AI conversation. At the end, export or copy it into
   `session/ai-transcript.md` (or share a link).
3. For each piece of AI output you use, be ready to say whether you
   **accepted**, **edited** or **rejected** it, and why.
4. You may run anything, add files and change code. Commit to a branch
   named `session/<your-name>`.

---

## Warm-up: explore and explain (10–15 min)

Use AI however you like to understand the codebase. Then write
`session/NOTES.md` answering:

1. In two or three sentences: what does this service do, and who uses it?
2. Someone clicks `http://localhost:8000/launch`. What happens, step by step,
   until their browser is sent on? Name the files and functions. What is
   read from or written to the database, and what is kept in memory?
3. Why might the second click on the same link behave differently from the
   first one?

Then **close the AI window** and walk your interviewer through your notes.

---

# Part 1: When AI gets it wrong

The tasks below sit in areas where AI tools often give confident, plausible
and wrong answers: time zones, caches, concurrency, docs that drifted from
the code. Your job is to catch that. For every claim you make, show how you
know: a test, a `curl` command, a database query or a line of code. "The AI
said so" is not proof.

## 1.1 Support queue (20 min)

These four messages came in this week. For **each** one:

1. Reproduce it (or try to).
2. Decide: **real bug**, **not a bug** (works as designed), or **can't
   reproduce**.
3. Prove your answer.
4. Real bug: fix it and leave a test that would have caught it. Not a bug:
   write the reply you'd send.

Write your verdicts in `session/tickets.md`.

> **#311, from Alice (marketing)**
>
> Our spring sale ended at the time I set as the expiry, but
> `localhost:8000/spring-sale` still takes people to the sale page. The
> dashboard even says the link is "expired". Customers are complaining that
> the discount doesn't work at checkout.

> **#314, from Bob**
>
> I shared the wrong link in a newsletter, so I deleted it right away
> (`DELETE /api/links/...` returned 204, and it's gone from my list). An hour
> later people are still landing on the old page. Is delete broken?

> **#318, from the docs team**
>
> Since we added a broken-link checker to our docs build (it sends a `HEAD`
> request to every link, every hour) our docs short links show about 24
> clicks a day each, including weekends when nobody reads the docs.

> **#320, from an SEO consultant**
>
> Your short links return `302 Found`. That's wrong for a permanent short
> link and costs us link equity. Please switch to `301`, it's a one-line
> change.

## 1.2 Security review (15 min)

Ask your AI tool for a security review of this repo. Then:

1. Go through its findings. For each one say **real**, **not real** or
   **not sure**, with one sentence of reasoning.
2. Rank the real ones by how much harm they could do.
3. **Prove** your top one with a failing test or a `curl` command.

Expect the list to contain things that aren't problems.

## 1.3 Docs vs code (15 min)

A new teammate couldn't get the project running from the README. Ask your AI
tool to fix the README's "Tech stack" and "Getting started" sections, and
ask it these questions:

- How long are short codes, and which characters can they contain?
- What happens if two links get the same random code?
- Does the QR code feature work?

Then list everything the AI got wrong, and how you checked each answer.
If you find a real problem along the way, write a test that proves it.

## 1.4 Missing tests: click counting (15 min)

`tests/integration/test_clicks.py` is thin, and has a TODO saying concurrent
clicks "couldn't be tested". Ask AI to write the missing tests for
`ClickService.record` and the redirect route.

1. Review what it gives you before you run it. Which tests actually check
   something useful? Which only check a status code?
2. Is the implementation correct? Read `docs/adr/003-click-privacy.md`
   first: it states an invariant. Can you write a test that breaks it?
   (Hint: a test can control what happens *between* two lines of code.)

## 1.5 Review an AI-written pull request (15 min)

A teammate opened PR #17 with help from an AI assistant. Read
`review/PR-17-collision-retry.md` and `review/PR-17.diff`.

1. Write your review in `session/review.md`: **approve**, **comment** or
   **request changes**; line comments (`file` line N: what's wrong, why it
   matters, what you'd suggest); which claims in the description are true.
2. Apply it and check:

   ```bash
   git apply review/PR-17.diff
   uv run pytest
   ```

   Did anything change your review? Undo it with
   `git apply -R review/PR-17.diff`.

---

# Part 2: Build a new feature with AI

Before your first prompt, write `session/context.md`: what you will tell the
AI about this codebase (conventions, invariants, what not to trust, your
definition of done), plus a short plan. Then use it. Keep commits small. You
will be asked how you verified each part, so keep track of what you ran.

## 2.1 Small feature: link tags (15 min)

Owners want to group links, e.g. `newsletter`, `q3-campaign`.

- Tags can be set when creating a link and changed with `PATCH`.
- Tags are lower-case, 1–24 characters (`a-z`, `0-9`, `-`), at most 5 per
  link. Invalid tags give a 422 in the same error format as other errors.
- `GET /api/links?tag=newsletter` filters the owner's links. Pagination
  `total` must match the filter.
- `GET /api/links/{code}` and the list show each link's tags.
- Tests for the rules above.

## 2.2 Medium feature: password-protected links (25 min)

An owner can protect a link with a password.

- `POST /api/links` and `PATCH` accept an optional `password` (8–128
  characters); `PATCH` with `"password": null` removes it. The password is
  never returned by any endpoint and is not stored in plain text.
- `GET /{code}` on a protected link shows a small HTML form instead of
  redirecting. `POST /{code}` with the right password redirects (302) to the
  target.
- A wrong password and a link that doesn't exist must look the same to the
  visitor.
- After 5 wrong attempts for a link within 15 minutes, further attempts get
  `429` until the window passes.
- A click is counted only when the visitor actually gets redirected.
- Disabled, expired and deleted links behave exactly as before.
- Tests, including one that proves a protected link can't be reached without
  the password, however many times it has been visited before.

## 2.3 Larger feature: bulk CSV import (40 min, or design only in 15 min)

Marketing wants to create hundreds of links at once.

- `POST /api/links/import` takes a CSV file upload with the columns
  `url,alias,title,expires_at` (only `url` is required).
- The response has one entry per row: the created link, or the row number
  with an error message (same validation rules as `POST /api/links`).
- At most 1,000 rows per file; a bigger file is rejected without creating
  anything.
- Two rows asking for the same alias: the second one fails, not the whole
  import.
- Decide (and ask your interviewer about) what happens to the good rows
  when some rows fail.
- Tests, including a file with a mix of good and bad rows.

Design-only version: write `session/import-design.md` covering the API,
validation, transactions, errors, limits and what you'd test, and walk your
interviewer through it.

## 2.4 Teach the next AI (10 min)

Write an `AGENTS.md` (or `CLAUDE.md`) at the repo root, so the next
engineer's AI tool doesn't repeat the mistakes you saw today. Keep it under
40 lines. Only include things that are true and useful.

## 2.5 Pull request description (5 min)

Write the PR description for your branch, for a busy senior engineer who has
five minutes:

- what changed,
- how you verified it (exactly what you ran),
- what you did **not** verify,
- which part of the diff they should review most carefully,
- which parts were AI-written.

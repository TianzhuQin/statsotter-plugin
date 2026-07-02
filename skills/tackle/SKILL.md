---
name: tackle
description: Run a published StatsOtter workflow on the user's local data. Use when the user wants to analyze data with StatsOtter, find which statistical / causal-inference workflow fits their goal or dataset ("estimate the treatment effect of the rollout", "event-study on these panels", "用 statsotter 分析这个数据"), or asks what method the StatsOtter platform recommends for a task.
---

# StatsOtter — tackle: fit a workflow to the user's data and run it

The flow is deliberately multi-step: find the best-fitting published
workflow, INTRODUCE it and explain why it fits, get the user's confirmation,
and only then run it on the data — all the way to results. Never run
anything before the confirmation.

All server calls go through:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sotter.py" <command> …
```

(config `.statsotter.json` — if missing, follow the first-run setup in the
`manage` skill: ask for the user's API key from Settings → API keys on
https://statsotter.ai, then `setup <key>`.)

## Steps

1. **The goal.** If the user hasn't stated what they want to do with the
   data, ask before continuing.

2. **Understand the data — locally only.** List the files, read headers and
   a few rows of tabular files (names, types, row counts; never load large
   files fully). This summary stays on the machine — **no user data is ever
   sent to the server**; only the goal text leaves.

3. **Read the platform's table of contents.** `catalog` — every published
   card's title, slug, summary, tags and community signals (votes, views,
   comments). Choose by understanding, not keyword matching: read the whole
   catalog against the goal and the local data shape, shortlist the 2–5 most
   promising cards. For a very large catalog you may narrow first with
   `search "<goal>"`, but the catalog is the source of truth.
   - If genuinely nothing fits: say so, stop, and log the gap so the
     platform learns — `feedback gap --query "<the goal>"`.

4. **Open their notes and judge.** For each shortlisted slug, `doc SLUG` —
   the card's full markdown: Steps with code, Inputs, Input example,
   `## AI Notes`, and a `## Community signals` section (votes, recent
   discussion verbatim — weigh caveats users raised). Narrow to the single
   best workflow, keeping one or two alternatives in mind.

5. **Introduce it, then CONFIRM — mandatory.** Present in plain language:
   the chosen card's title, summary and `card_url`; why it fits this goal
   and this data (cite its notes); what input it expects and what it
   produces (the estimand, the outputs); the alternatives, one sentence
   each. Ask: run it / use an alternative / cancel. Only after "run it":
   `feedback picked --slug <slug> --query "<the goal>"`.

6. **Run it, to the end.** Execute the card's Steps in order, adapting the
   code to the actual files and column names:
   - Map the user's columns to the inputs the method expects; ask only if a
     mapping is genuinely ambiguous.
   - Run each step in the folder (R / Python / whatever the card uses);
     install missing packages when you can. If a required runtime is
     missing, say exactly what to install and stop with whatever you have.
   - Use the function names and arguments from the document — never invent
     an API.
   - Save outputs (tables, figures, a short `statsotter-results.md`) into
     the folder as you go.
   - When finished: `feedback ran_ok|ran_fail --slug <slug> --query
     "<the goal>" --note "<one line>"`. The note describes only how the
     WORKFLOW behaved ("converged after mapping columns", "step 3 needs the
     did package") — never estimates, column names, or anything else derived
     from the user's data; the no-data-leaves-the-machine promise covers the
     note too.

7. **Report.** The key results (estimates, standard errors / intervals),
   files produced, the card link, and anything skipped or needing the
   user's attention — in the user's language.

---
name: enrich
description: Research a StatsOtter card's sources and turn its thin knowledge document into a deep one. Use when the user says a doc/card is thin, shallow, empty, "just a bunch of links" or "has no AI notes"; wants to enrich, deepen, expand or improve the docs, the AI notes or the knowledge base; wants the platform's AI (or its training corpus) to get smarter; asks to fill in the notes for one card, several, or all of theirs; or asks which docs need work (audit, quality score, thin docs). Any language.
---

# StatsOtter — enrich: make a card's knowledge document worth learning from

The card page is for humans. The **knowledge document** is for AI: it is the
corpus the platform's card-generation AI learns from today and the retrieval
brain of everything the product builds next. A doc that says "see
https://…" teaches a future AI nothing — and when the link rots it teaches
nothing at all, forever.

This skill closes that gap. It is a **research** job, not a writing job: you
read the sources a doc points at, verify what they actually say, and write
the knowledge into the doc so the doc stands alone.

> **The one rule that governs everything here.** A URL may only ever
> *accompany* knowledge, never *replace* it. And never invent an API, an
> argument, a default, a number or a citation — anything you could not verify
> from a real source is either left out or written down explicitly under
> `### Open questions` as unverified.

## The client

All server calls go through one stdlib script (never hand-write curl):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sotter.py" <command> …
```

(If `CLAUDE_PLUGIN_ROOT` is unset, the script lives at `scripts/sotter.py`
two directories above this SKILL.md. Config is `.statsotter.json` — if it is
missing, follow the first-run setup in the `manage` skill: ask for the user's
API key from **Settings → API keys** on https://statsotter.ai, then
`setup <key>`.)

| Command | Does |
|---|---|
| `audit [--all]` | the worklist: every card with quality score < 60, most recently updated first (`--all`: the whole platform — site admins) |
| `cards [--all]` | all cards with `doc_chars`, `ai_notes_chars`, `quality_score` |
| `doc SLUG --save [FILE]` | save the upload-ready markdown (default `./<slug>.md`) |
| `doc SLUG --versions` | list the doc's versions (number, date, source, author, chars) |
| `doc SLUG --version N [--save FILE]` | that version's stored content — for recovering knowledge an earlier edit dropped |
| `doc SLUG --with-signals` | the live render **plus** the read-only `## Community signals` block (reading only — that block does not validate) |
| `validate FILE` | server grammar check → `errors`, `warnings`, `quality` |
| `upload FILE --target SLUG` | overwrite the card and record a new immutable doc version |
| `card SLUG` / `edit SLUG --json FILE` | structured read / field-level patch (see the `manage` skill) |
| `lesson --instruction "…" [--slug S]` | teach the card-generation AI (site admins) |

Exit 0 = success; non-zero prints the server's JSON error body — read its
`errors` array and act on it. `--save` without a value writes `./<slug>.md`;
saved files are fetched raw, so they upload back as-is.

## Quality: the score you are moving

Every doc carries `quality = {doc_chars, ai_notes_chars, score, warnings}`.
The score is deterministic out of 100, so it is a target, not an opinion:

| Points | For |
|---|---|
| up to 40 | AI Notes volume (full marks at ~6000 characters) |
| up to 20 | recommended AI-Notes subsections present — assumptions · API/parameters · worked example · failure modes · provenance (4 each) |
| 10 | every Step has a `- Note:` |
| 10 | at least one fenced code block in Steps |
| 5 + 5 + 5 | Results / Inputs / Input example non-empty |
| 5 | Description ≥ 400 characters |

`warnings` **never block an upload** — they are your to-do list. Treat each
one as unfinished work:

| Code | What it is telling you to do |
|---|---|
| `ai_notes_missing` / `ai_notes_thin` | there is no distilled knowledge yet — this is the whole job |
| `ai_notes_sections_missing` | add the missing headings from the outline below (with real content, not stubs) |
| `url_without_substance` | the doc leans on links it never digested — go read them |
| `step_without_note` | say what the step does **and why it matters** |
| `no_code_example` | put runnable code in the Steps |
| `results_empty` · `inputs_empty` · `input_example_empty` | the card cannot be executed by anyone (or any AI) without these |
| `description_thin` | the human-facing framing is too shallow to place the method |

`errors` are different: they are grammar violations and they **do** block the
upload. Fix them and re-validate.

## The AI-Notes outline

Inside `## AI Notes`, use these `###` headings, in this order. All are
optional-but-expected; write the ones the source material actually supports
and leave out the ones you could not verify (naming a heading and putting
guesses under it is worse than omitting it).

| Heading | What belongs under it |
|---|---|
| `### Method identity` | what it is, lineage, key papers (authors, year, DOI/arXiv), canonical implementation + version |
| `### When to use / when not to use` | decision rules, competing designs |
| `### Assumptions` | each stated formally, **how to check it**, what breaks when it fails |
| `### Estimand and estimator` | formal notation, the estimating equation, what is identified and under what |
| `### API reference` | every user-facing function: signature, EVERY argument with type, default and meaning, the shape of the return object and its fields |
| `### Data requirements` | data shape, required columns and their semantics, sample-size / balance guidance, missing data |
| `### Worked example` | runnable end-to-end code on a named public dataset, plus the actual expected output and how to read it |
| `### Interpreting the output` | what each number means, plausible ranges, thresholds, common misreadings |
| `### Diagnostics` | the checks to run and what a failure looks like |
| `### Failure modes and fixes` | symptom → cause → fix, with error messages verbatim |
| `### Alternatives and comparisons` | sibling methods, when each wins, how estimates typically differ |
| `### Performance and scale` | complexity, memory, practical limits, parallelism |
| `### Provenance` | every source actually read: URL, what was taken from it, version/commit, access date |
| `### Open questions` | what remains unverified, contested, or unreachable |

Everything outside `## AI Notes` still obeys the strict document grammar —
see the `manage` skill's grammar reference
([`../manage/references/template.md`](../manage/references/template.md)).
The section list is closed, so all of this new knowledge goes **inside**
`## AI Notes` (or into the existing Description / Results / Inputs / Steps
bodies), never into a new `## Something` heading.

## Playbook

### 1. Scope

- **One card** the user named → resolve it by title against `cards`
  (case-insensitively, same as the `manage` skill: one match, proceed;
  several or zero, show candidates and ask).
- **"All my thin ones" / "improve our docs"** → `audit` (site admins asking
  about the whole platform: `audit --all`). Show the worklist as a compact
  table — title (slug), `doc_chars`, `ai_notes_chars`, score, top warning —
  and agree with the user how many to do in this session. The server returns
  it most-recently-updated first, so sort by `quality_score` yourself when the
  user asks to start with the worst.
- If the user has no thin docs, say so and stop; do not manufacture work.

### 2. Read what exists, and inventory the gaps

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sotter.py" doc <slug> --save
```

Read the whole file. Then write down, explicitly, before researching:

1. **Every URL it cites** — Metadata Source, Figures, step `- URL:` lines,
   links in prose. This is the research queue.
2. **Every outline heading missing** from `## AI Notes`.
3. **Every step without a `- Note:`**, and every step without code.
4. **Every claim with no source** — a stated default, a threshold, an
   assumption, a number. Each is either verified in step 3 or it goes.
5. **What the card is really about** — the method, the package, the paper.

Run `doc <slug> --versions`, and if an earlier version is markedly larger,
read it — `doc <slug> --version N --save <slug>-v<N>.md`, always with an
explicit filename, because a bare `--save` writes `./<slug>.md` and would
overwrite the working copy you just downloaded. Knowledge someone once wrote
and a later edit dropped is knowledge you should carry forward, not re-derive.

### 3. Research — this is the job

For each URL in the queue, and each gap in the inventory, **actually read the
source**. Never summarize a page from its title or from memory of the
library.

| Source | How to work it |
|---|---|
| Package repo / README | `WebFetch` the repo, the README, `NEWS`/changelog for the version, the source of the main function when the reference is vague |
| Function reference / man pages | fetch and copy the parameter table **verbatim**: name, type, default, meaning. This is what `### API reference` is made of |
| Vignettes / tutorials | the worked example, the dataset it uses, and the printed output |
| Papers (arXiv, journal, DOI) | the estimand, the assumptions, the identification result, the notation. Record authors + year + identifier |
| A local repo the card came from | read the **real code** on disk (Read/Grep) — signatures, defaults, error strings, tests. On-disk truth beats documentation |
| Anything you cannot find | `WebSearch` for the canonical docs, then fetch them. A search snippet is a pointer, never a citation |

While reading, extract: exact signatures and defaults; return-object field
names; real error strings (copy them character-for-character); the dataset
names in the examples; version numbers or commit hashes; the assumptions as
the authors state them.

**Budget and politeness.** Work one card at a time and a handful of sources
at a time — a card is usually well served by 5–15 well-chosen sources. Never
fire dozens of fetches blindly. If a source turns out to be a hub page, pick
the 2–3 pages behind it that carry the actual content rather than crawling
it. Tell the user what you are reading as you go.

**When a source is paywalled, dead, rate-limited or login-walled**: do not
guess and do not paraphrase from memory as if you had read it. Record it
under `### Provenance` as unavailable — URL, what you hoped to take from it,
the date and the reason — and put the resulting gap under
`### Open questions`. For a dead paper, an arXiv preprint or the package's
own documentation of the same result is a legitimate substitute; say which
one you actually used. An honest gap is worth more to a future AI than a
confident invention.

### 4. Synthesize

Rewrite the saved file:

- **Extend, never silently drop.** Every fact already in the doc survives,
  corrected if a source contradicts it (and say so in the before/after).
- Fill in the outline headings you have evidence for, in order.
- Fix the card-facing sections too when they are the thing that is thin —
  Description, Results, Inputs, Input example, and a `- Note:` on every step
  that lacks one.
- Keep every URL, but now each one sits **next to** the knowledge taken from
  it, not in place of it. A reader with no internet must still learn the
  method from this file.
- `### Provenance` gets one line per source actually read: URL — what was
  taken — version/commit — access date (today's date).
- Grammar still applies: no raw `##` inside bodies, `$…$` for math, real
  Unicode characters, at most one fenced block per step. Site content is
  English — the doc is English even when the conversation is not.

### 5. Validate, and work the warnings

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sotter.py" validate <slug>.md
```

Fix every `error` and re-validate (≤3 rounds; then show the errors verbatim
and stop). Then read `warnings` and `quality.score`: each remaining warning
is a piece of research you have not done yet. Go back to step 3 for it. Stop
when the warnings are gone or the only ones left are genuinely unsupported by
any source — and say which those are and why.

A useful bar: a doc that was 1–3 KB with empty AI Notes should come back with
several thousand characters of AI Notes and a score in the 80s. If it did
not, you probably summarized instead of researching.

### 6. Show, confirm, upload

Present a compact before → after — never upload unasked:

```
did-multiplegt · Multiple treatment timing (DiD)
  doc_chars       1,204  →  11,860
  ai_notes_chars      0  →   8,430
  score              22  →      88
  sections added  Method identity, Assumptions, API reference,
                  Worked example, Failure modes, Provenance (+6 more)
  sources read    9 (2 unreachable — recorded under Open questions)
  warnings left   none
```

On an explicit yes:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sotter.py" upload <slug>.md --target <slug>
```

Report the score the server returned and `card_url` / `doc_url`. The upload
response carries `quality` but **no version number** — never invent one; if
the user wants it, read it from `doc <slug> --versions` (top row, writes
nothing). Note that the card's public page is unchanged apart
from any card-facing sections you improved — the AI Notes are invisible to
readers. Offer to overwrite the local file with the response's canonical
`markdown` so local == server. A doc upload rebuilds steps as external steps:
if the card has platform-method links on its steps — check for a non-empty
`method` on any step in `card <slug>`, ideally back in step 2 — enrich AI Notes
with `edit <slug> --json <file>` (`ai_notes` replaces that section wholesale)
instead of a full doc upload.

### 7. Batch: repeat, one at a time

For a worklist, loop steps 2–6 per card and report progress after each
(`3/7 done — enriched did-honest, score 24 → 86`). Confirm each upload; do
not ask for one blanket approval and then push seven cards. If the user steps
away, stop at the current card rather than running ahead. Keep the saved
`.md` files so an interrupted session can resume.

### 8. Feed the lesson back (site admins only)

After a successful enrichment, teach the card-generation AI so future cards
start deep instead of thin — skip silently for non-admins, and never let a
failure here affect the upload:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sotter.py" lesson \
  --instruction "<the user's request, verbatim in their own words>" \
  --slug <slug> --context "<one line: what the enrichment added>"
```

## Errors

| Response | Meaning / action |
|---|---|
| 401 | key missing/expired → re-run the first-run setup from the `manage` skill |
| 403 | `audit --all` / editing another member's card is site-admin only — explain, don't retry |
| 404 on a card | not theirs or gone — refresh with `cards` and re-resolve |
| 400 on upload/validate | grammar errors — show each `errors[]` line verbatim, fix, retry |
| 409 on upload | you omitted `--target` — enrichment always targets an existing card |
| fetch fails / robots-blocked | record the source as unavailable in Provenance; never fill the gap from memory |
| network error | say the server is unreachable; check `base_url` in `.statsotter.json` |

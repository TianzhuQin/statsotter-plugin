# The StatsOtter knowledge document — grammar

A card's **knowledge document** (`statsotter.md`) is the AI-facing source of
truth: everything the card page shows PLUS an `## AI Notes` section with every
detail worth learning. The server parses it deterministically — the grammar
is strict and the server is the final validator (`sotter.py validate FILE`).

## Grammar (a document is valid iff ALL hold)

1. Exactly one H1 `# <title>` before any section. The title is the card title
   — specific, not clickbait, ideally "What the recipe does (PackageName)".
2. Only these H2 sections, each at most once (unknown `## X` = error):
   `Summary, Metadata, Description, Results, Inputs, Input example, Figures, Steps, AI Notes`
3. `## Summary` is required and non-empty: 1–3 plain sentences for the card.
4. `## Metadata` holds only these bullets (`-` for an empty value):
   - `- Source: <url or ->`
   - `- Tags: A, B, C`  (2–4 Title-Case tags naming the identification
     strategy, e.g. DiD, Event Study, Synthetic Control — not the software)
   - `- Cover: <image url or ->`
5. `## Figures`: lines `- https://… | one-sentence caption`, or `- none`.
   Only real, hot-linkable image URLs. The first figure becomes the cover
   when no Cover is set.
6. `## Steps` is required with 1–10 blocks. Each block starts
   `### N. <stage> — <name>` where `<stage>` is one of:
   `prep, diagnostic, estimation, inference, robustness, heterogeneity, reporting, other`
   Inside a block (all optional): `- URL: …`, `- Note: …` (1–2 sentences,
   what happens AND why it matters), `- Formula: <KaTeX, no $ delimiters>`,
   and at most one fenced code block in the tutorial's own language.
7. `## AI Notes`: free markdown, as long as useful. Never shown on the card.
8. Math in prose uses `$…$` / `$$…$$` (the site renders KaTeX). Write real
   Unicode characters (×, –, α) — never literal `\uXXXX` escapes.
9. Markdown bodies must not contain raw `##` headings (use `###`+ or bold);
   level-2 headings are reserved for the section grammar.
10. An empty section body may be written as `(none)`.

## Worked example

```markdown
# Honest sensitivity bounds for parallel trends (HonestDiD)

## Summary
One factual sentence (or a short paragraph) shown under the title.

## Metadata
- Source: https://github.com/asheshrambachan/HonestDiD
- Tags: DiD, Event Study
- Cover: https://docs.package.org/figure.png

## Description
> ⚠️ *Unofficial community showcase of [HonestDiD](https://…). All credit to the authors.*

The big picture, in markdown. Inline math $\tau$ and display math:
$$Y_{it}^{0} = \alpha_i + \xi_t + e_{it}$$

## Results
The estimand and the headline numbers: coefficients, standard errors,
confidence intervals — how to read the output.

## Inputs
What goes in: data shape, the question. Markdown.

## Input example
```text
id,t,y,d
1,2018,3.4,0
```

## Figures
- https://docs.package.org/fig1.png | Event-study estimates with honest CIs.

## Steps

### 1. prep — Load the panel
- URL: https://docs.package.org/reference/load.html
- Note: One or two sentences on what happens and why it matters.
- Formula: \hat\tau = \bar Y_1 - \bar Y_0

```r
df <- read.csv("panel.csv")
```

### 2. estimation — Event-study regression
- Note: Steps repeat this shape; URL / Formula / code are each optional.

## AI Notes
Everything else an AI should know — full parameter tables, defaults, edge
cases, benchmarks, design decisions, quotes from the docs. Never on the card.
```

## Semantics worth remembering

- `upload FILE` **without** `--target` always tries to CREATE a new card; a
  similar existing card returns 409 with `{duplicate: {title, slug, url,
  reason, is_yours}}` — recommend updating that card instead; `--force`
  creates a separate card only after explicit user confirmation.
- `upload FILE --target SLUG` overwrites THAT card and records a new
  knowledge-doc version (the author's, or any card for site admins).
- The success response's `markdown` field is the canonical regenerated
  document — offer to overwrite the local file so local == server.
- New cards are drafts. `sotter.py publish SLUG` puts them on the public
  feed; no website visit needed.

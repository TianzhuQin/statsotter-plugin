# The StatsOtter knowledge document — depth contract

[template.md](template.md) says what a document must *look like* for the
parser to accept it. This file says what a document must *contain* to be worth
keeping. A doc can be perfectly valid and still worthless; the grammar is the
floor, this is the bar.

## Why this file exists

The card page is for a human skimming a feed. The knowledge document is the
corpus. It is what the platform's card-generation AI reads today and what the
product's future AI is trained and retrieved against. Everything an AI will
ever know about a method, it knows because someone wrote it into a doc.

Measured over the first eleven cards on the site: every doc was 0.9–2.8 KB,
`## AI Notes` was **empty on all of them**, and each doc carried 5–8 bare URLs.
That is a corpus that teaches nothing. The links were doing all the work, and
links are not knowledge — they are a promise that knowledge exists somewhere
else, made to a reader who may have no way to follow them.

**The standing test for every doc:** if every URL it cites went dead tonight,
would a competent analyst still be able to understand the method, run it
correctly, and read the output? If no, the doc is not finished.

Write for a reader with no internet access.

## Where the depth goes

| Section | Audience | Length |
|---|---|---|
| `## Summary` | card feed | 1–3 sentences |
| `## Description` | card page | 400+ characters; the big picture, some math |
| `## Results` | card page | what the output is and the headline numbers |
| `## Inputs` / `## Input example` | card page | data shape + a real pasteable sample |
| `## Steps` | card page | 1–10 blocks, each with a `- Note:`, at least one with code |
| `## AI Notes` | **AI only** | the rest of this file — usually 80% of the doc |

Card-facing sections stay tight and human. `## AI Notes` is where the depth
lives; it never appears on the card, so there is no such thing as "too long"
there — only "not verified".

A serious doc is typically **8–20 KB**, dominated by AI Notes. Under 3 KB means
the knowledge is still sitting behind the links.

## The AI Notes outline

Use `###` headings inside `## AI Notes` (level-2 headings are reserved for the
section grammar — a raw `##` in a body is a parse error). All of these are
optional but expected; keep this order so docs stay diffable and comparable.
Drop a heading only when it genuinely does not apply, and prefer writing
"nothing to report, and here is why" over silence.

> The examples below illustrate **shape and depth**. They are not verified
> facts to copy into a card. Everything in a real doc must come from a source
> you actually read.

### Method identity

What it is in one paragraph, its lineage, the papers that define it (authors,
year, venue, DOI or arXiv id), and the canonical implementation with the exact
version you read.

Good:

~~~markdown
### Method identity
Group-time average treatment effects for staggered adoption: instead of one
regression coefficient, the estimator reports a separate ATT for each
treatment cohort g and calendar period t, then aggregates those cells with
explicit, non-negative weights.

- Defining paper: Callaway & Sant'Anna (2021), "Difference-in-Differences with
  Multiple Time Periods", Journal of Econometrics 225(2), 200-230,
  doi:10.1016/j.jeconom.2020.12.001.
- Motivating critique: Goodman-Bacon (2021) shows the two-way fixed-effects
  coefficient is a weighted average of all 2x2 comparisons, including
  already-treated-as-control ones that can carry negative weights.
- Canonical implementation: R package `did`, version 2.1.2 (CRAN), read
  2026-07-20. Python has no equivalent maintained port; see Alternatives.
~~~

Bad — the version we have today:

~~~markdown
### Method identity
Callaway-Sant'Anna DiD. See https://bcallaway11.github.io/did/.
~~~

### When to use / when not to use

Decision rules a reader can apply to their own dataset without judgement
calls, plus the competing designs and what makes this one lose.

Good:

~~~markdown
### When to use / when not to use
Use when: treatment switches on at different dates for different units; you
suspect effects vary by cohort or grow with exposure; you have at least one
never-treated or not-yet-treated group to serve as a control.

Do not use when: every unit is treated in the same period (this collapses to a
2x2 DiD and the machinery buys nothing); treatment turns on and off (the
estimator assumes absorbing treatment); the outcome is measured only once
after treatment for some cohorts (no event-time aggregation is possible);
selection into timing is driven by the outcome's own trajectory (no DiD
estimator saves you here - consider a design with an instrument).
~~~

Bad:

~~~markdown
### When to use / when not to use
Good for modern DiD designs with staggered treatment.
~~~

### Assumptions

Each assumption stated formally, then **how to check it**, then **what breaks
when it fails**. The middle item is the one docs always skip and the one a
reader most needs.

Good:

~~~markdown
### Assumptions
1. **Conditional parallel trends.**
   $E[Y_t(0) - Y_{t-1}(0) \mid G = g, X] = E[Y_t(0) - Y_{t-1}(0) \mid C = 1, X]$
   for all $t \ge g$.
   - Check: the estimated ATT(g,t) for t < g are placebo estimates; plot them
     and read the *simultaneous* band (`cband = TRUE`), not the pointwise one.
   - Breaks: a sloping pre-trend is absorbed into the post estimates with the
     same sign, so a violated assumption inflates rather than blurs the effect.
     Bound the damage with a sensitivity analysis rather than declaring the
     test "passed".
2. **Absorbing treatment (no reversal).** Once treated, always treated.
   - Check: `all(diff(treated_flag) >= 0)` within every unit.
   - Breaks: silently mislabels post-reversal periods as treated; the estimate
     becomes an uninterpretable mix of on and off periods.
~~~

Bad:

~~~markdown
### Assumptions
Parallel trends, no anticipation.
~~~

### Estimand and estimator

What quantity is being estimated, in notation; the estimating equation; what
is identified and under exactly which assumptions; how aggregation works.

Good:

~~~markdown
### Estimand and estimator
Target: $ATT(g,t) = E[Y_t(g) - Y_t(\infty) \mid G_g = 1]$ - the effect at
calendar time t on units first treated at g.

Estimator (doubly robust, `est_method = "dr"`): combines an outcome-regression
term and an inverse-propensity-weighted term, so it is consistent if *either*
the propensity model $p(X)$ or the outcome model is correctly specified.

Aggregation: `aggte(type = "dynamic")` maps the ATT(g,t) grid onto event time
e = t - g with weights proportional to cohort size, so the reported event-study
coefficient at e is a genuine average of cohort effects at that exposure - no
negative weights, unlike the TWFE event-study coefficient it resembles.
~~~

Bad:

~~~markdown
### Estimand and estimator
Estimates the ATT.
~~~

### API reference

Every user-facing function: the signature verbatim, **every** argument with
type, default and meaning, and the shape of the return object with its fields.
A table beats prose. This section is the single most valuable thing in the doc
for an AI that has to write working code — and the one that is most often
replaced by a link.

Good:

~~~markdown
### API reference

**`att_gt(yname, tname, idname, gname, xformla = NULL, data, ...)`** - returns
an `MP` object.

| Argument | Type | Default | Meaning |
|---|---|---|---|
| `yname` | character(1) | - | outcome column name |
| `tname` | character(1) | - | time period column; must be numeric |
| `idname` | character(1) | - | unit id column |
| `gname` | character(1) | - | period each unit is first treated; **0 for never-treated** |
| `xformla` | formula | `NULL` | covariates, e.g. `~ lpop`; `NULL` means unconditional |
| `control_group` | character(1) | `"nevertreated"` | or `"notyettreated"` |
| `anticipation` | integer | `0` | periods of anticipated effect to exclude |
| `est_method` | character(1) | `"dr"` | `"dr"`, `"ipw"` or `"reg"` |
| `bstrap` / `cband` | logical | `TRUE` / `TRUE` | multiplier bootstrap; simultaneous band |

Returned `MP` object fields: `$group` (cohort per estimate), `$t` (period),
`$att` (point estimates), `$se`, `$c` (critical value for the simultaneous
band), `$Wpval` (p-value of the pre-trend Wald test), `$DIDparams` (the call).

Downstream: `aggte(mp, type = c("simple", "dynamic", "group", "calendar"))`
returns an `AGGTEobj` with `$overall.att`, `$overall.se`, `$egt`, `$att.egt`.
~~~

Bad:

~~~markdown
### API reference
The main function is att_gt(). See the reference manual for the arguments.
~~~

### Data requirements

Data shape, required columns and their semantics, encoding conventions that
bite, sample-size and balance guidance, and how missing data is handled.

Good:

~~~markdown
### Data requirements
Long panel, one row per unit-period. Required columns: unit id, numeric time
period, outcome, and a first-treatment-period column coded 0 (not NA) for
never-treated units - NA there drops the row silently and quietly removes your
control group. Periods must be consecutive integers; gaps are treated as real
gaps, not missing data. Unbalanced panels need `allow_unbalanced_panel = TRUE`,
which switches the estimator to repeated cross-sections internally. Cohorts
with a handful of units produce estimable but unstable ATT(g,t) cells - inspect
cohort sizes before trusting the disaggregated grid.
~~~

Bad:

~~~markdown
### Data requirements
Panel data with a treatment indicator.
~~~

### Worked example

Runnable end-to-end code on a **named public dataset** (one shipped with the
package is ideal), plus the actual output it produced and how to read it. Run
it. Paste what came back. Never retype output from memory.

Good:

~~~markdown
### Worked example
Dataset: `mpdta`, shipped with the `did` package (county teen employment,
2003-2007, staggered minimum-wage adoption).

```r
library(did)
data(mpdta)
out <- att_gt(yname = "lemp", tname = "year", idname = "countyreal",
              gname = "first.treat", xformla = ~ lpop, data = mpdta)
summary(aggte(out, type = "dynamic"))
```

Output (verbatim, `did` 2.1.2, R 4.4.1):

```text
Overall summary of ATT's based on event-study/dynamic aggregation:
   ATT    Std. Error  [ 95%  Conf. Int.]
   …      …           …      …

Dynamic Effects:
 Event time Estimate Std. Error [95% Simult.  Conf. Band]
 …
```

Reading it: the "Overall" line averages the post-treatment event times only.
Rows with negative event time are placebo estimates; a simultaneous band that
covers zero across all of them is the passing case. Signif. codes marked on
the dynamic rows are pointwise and will disagree with the simultaneous band -
trust the band.
~~~

(In a real doc the `…` are the actual numbers from your run.)

Bad:

~~~markdown
### Worked example
See the package vignette for an example.
~~~

### Interpreting the output

What each number means, the units it is in, plausible ranges, thresholds, and
the misreadings you expect a reader to make.

Good:

~~~markdown
### Interpreting the output
`att` is in the units of the outcome as supplied - with a log outcome it is
approximately a proportional effect, so 0.05 means about +5%, and the
approximation degrades above roughly |0.2|.

Common misreadings:
- Treating the event-time-0 coefficient as "the" effect. It is the effect in
  the first treated period only, usually the smallest one.
- Reading pre-period estimates as evidence *for* parallel trends. Wide bands
  make them insignificant; insignificant is not equal to zero.
- Comparing `simple` and `dynamic` aggregations as if they should match. They
  weight cohorts differently and routinely differ.
~~~

Bad:

~~~markdown
### Interpreting the output
The ATT is the treatment effect. Check the confidence interval.
~~~

### Diagnostics

The checks to run before believing anything, and what a failure looks like on
screen.

Good:

~~~markdown
### Diagnostics
1. Pre-trend test: `out$Wpval`. A small p-value says the pre-treatment ATT(g,t)
   are jointly non-zero. Do not stop at the p-value - plot with `ggdid(out)`
   and look at the shape; a single noisy early cell is a different problem from
   a monotone slope.
2. Cohort sizes: `table(mpdta$first.treat)`. Any cohort in single digits makes
   its ATT(g,t) row decorative.
3. Control-group swap: rerun with `control_group = "notyettreated"`. Estimates
   that move materially indicate the never-treated group is not comparable.
4. Covariate sensitivity: rerun with `xformla = NULL`. A large change means the
   result rests on the propensity/outcome model, not on the design.
~~~

Bad:

~~~markdown
### Diagnostics
Check pre-trends.
~~~

### Failure modes and fixes

Symptom → cause → fix, with error messages **verbatim**. This is the section
that saves an AI from a debugging loop, and it can only be written by someone
who actually hit the errors.

Good:

~~~markdown
### Failure modes and fixes
- **`Error in att_gt(...) : object 'first.treat' not found`** - column names
  are passed as strings, not symbols. Fix: quote them (`gname = "first.treat"`).
- **All estimates NA for the earliest cohort** - that cohort has no
  pre-treatment period, so no baseline difference exists. Expected behaviour,
  not a bug; drop the cohort or start the panel earlier.
- **Standard errors much larger than a TWFE run on the same data** - usually
  correct: the multiplier bootstrap with a simultaneous band is wider than
  pointwise clustered errors by construction. Compare like with like before
  concluding something broke.
~~~

Bad:

~~~markdown
### Failure modes and fixes
If you get errors, check your data format.
~~~

### Alternatives and comparisons

Sibling methods, when each one wins, and how the estimates typically differ and
why. Direction and mechanism, not invented magnitudes.

Good:

~~~markdown
### Alternatives and comparisons
- **TWFE event study** - fine with a single adoption date; with staggered
  adoption its coefficients can be contaminated by already-treated controls.
- **Sun & Abraham (2021) interaction-weighted estimator** - same target, drops
  in as a regression, integrates with existing `fixest` pipelines; less
  flexible on covariates.
- **Synthetic control / synthetic DiD** - better with very few treated units
  and a long pre-period; not designed for many cohorts.
- **Sensitivity analysis (HonestDiD)** - complements rather than replaces this
  estimator: it takes these estimates as input and reports how large a
  parallel-trends violation would have to be to overturn the conclusion.
~~~

Bad:

~~~markdown
### Alternatives and comparisons
There are other DiD estimators available.
~~~

### Performance and scale

Complexity, memory, practical limits actually observed, and the parallelism
switches.

Good:

~~~markdown
### Performance and scale
Cost scales with the number of (g,t) cells times bootstrap iterations: roughly
G x T x `biters` 2x2 estimations. `biters = 1000` (the default) on a panel of a
few thousand units and five periods runs in seconds on a laptop; a long panel
with dozens of cohorts is where it becomes minutes. `pl = TRUE, cores = N`
parallelises the bootstrap. Memory is dominated by the influence-function
matrix (units x cells), not by the panel itself.
~~~

Bad:

~~~markdown
### Performance and scale
Runs quickly on normal datasets.
~~~

### Provenance

Every source you actually read, what you took from it, the version or commit
it described, and the date you read it. A URL appears here *with* its content,
never instead of it.

Good:

~~~markdown
### Provenance
- https://bcallaway11.github.io/did/articles/did-basics.html - the worked
  example and the reading of the dynamic aggregation output. Docs for `did`
  2.1.2, read 2026-07-20.
- CRAN reference manual for `did` 2.1.2 - the full `att_gt` argument table
  above, copied field by field. Read 2026-07-20.
- Callaway & Sant'Anna (2021), JoE 225(2) - estimand definition and the
  identification result. Read the published version.
- Source: `R/att_gt.R` at the CRAN 2.1.2 tarball - confirmed that `gname` uses
  0 (not NA) for never-treated, which the vignette does not state explicitly.
~~~

Bad:

~~~markdown
### Provenance
https://bcallaway11.github.io/did/
https://cran.r-project.org/package=did
~~~

### Open questions

What you could not verify, what is contested, what the next pass should pick
up. An honest gap is worth more than a confident guess, and it is what lets the
next author extend the doc instead of re-deriving it.

Good:

~~~markdown
### Open questions
- Unverified: whether `allow_unbalanced_panel = TRUE` changes the estimand or
  only the estimation path. The vignette is ambiguous; not traced through the
  source yet.
- Not run: the covariate-sensitivity diagnostic above is described from the
  documentation, not from an execution on `mpdta`.
- Contested in the literature: whether to report pointwise or simultaneous
  bands as the default in applied work. Both conventions appear in print.
~~~

Bad: the section is missing, so the next author cannot tell verified content
from plausible content and rewrites the whole doc.

## Hard rules

1. **A URL may accompany knowledge, never replace it.** "See the vignette" is
   not a sentence in a knowledge document. Read the page, write what it says,
   then cite it.
2. **Never invent an API, an argument, a default, a number or a citation.** If
   you did not read it in a real source or produce it in a real run, it does
   not go in. A doc that is 60% shorter and entirely true beats a complete-
   looking doc with one hallucinated default in it — the hallucinated default
   is what a future AI will confidently emit.
3. **Mark unverified claims explicitly**, in the sentence itself
   ("unverified:") and again under Open questions.
4. **Prefer the artifact over the paraphrase.** A verbatim parameter table, a
   real error string, the actual shape of a returned object, the console output
   from a run. Prose summaries of parameter lists lose exactly the details that
   make code run.
5. **Write for a reader with no internet access.** No "as described above in
   the linked paper", no "the standard reference explains this well".
6. **Keep the card human.** Depth belongs in AI Notes; the card-facing sections
   should not grow into essays because the doc got serious.
7. **English only**, everywhere in the document.

## What the server measures

`validate` and `upload` return a `quality` block plus non-blocking `warnings`.
Warnings never stop an upload — they tell you what a future AI will find
missing.

`quality = {doc_chars, ai_notes_chars, score, warnings}`, score 0–100:

| Points | Earned by |
|---|---|
| up to 40 | AI Notes volume: `min(40, round(40 * ai_notes_chars / 6000))` |
| up to 20 | recommended AI-Notes subsections present, 4 points each: assumptions / API-parameters-arguments / worked example / failure-troubleshooting-pitfalls / provenance-sources |
| 10 | every Step has a `- Note:` |
| 10 | at least one fenced code block in Steps |
| 5 + 5 + 5 | Results, Inputs, Input example each non-empty |
| 5 | Description ≥ 400 characters |

6,000 characters of AI Notes (roughly 900 words) is where the volume component
tops out. Treat that as the floor for a method worth a card, not the target —
the outline above, done properly, runs well past it.

Warning codes you may see:

| Code | Means |
|---|---|
| `ai_notes_missing` | there is no distilled knowledge in this doc at all |
| `ai_notes_thin` | AI Notes under 1,500 characters |
| `ai_notes_sections_missing` | the recommended subsections above are absent |
| `url_without_substance` | 3+ URLs while AI Notes is under 1,000 characters — the exact failure this contract exists to end |
| `step_without_note` | a step says what to run but not what it does or why |
| `no_code_example` | no runnable code anywhere in Steps |
| `results_empty` / `inputs_empty` / `input_example_empty` | a card-facing section is blank |
| `description_thin` | Description under 400 characters |

A score in the 80s with an honest Open questions section is a good doc. A score
of 100 achieved by padding AI Notes with restated card text is worse than a 60,
because it poisons the corpus instead of merely underfilling it.

## How docs compound

Docs are versioned and immutable server-side, so every pass is additive if you
let it be:

1. `audit` lists cards whose quality score is under 60 — the enrichment
   worklist, most recently updated first (sort by `quality_score` yourself if
   you want to start with the worst).
2. `doc SLUG --save` writes an upload-ready `<slug>.md` (raw, without the
   server's read-only community-signals block). `--versions` lists the history;
   `--version N` pulls an older one back.
3. Edit the file. **Extend, do not restart.** Provenance tells you which
   sources have already been read so you do not re-read them; Open questions
   tells you exactly where the previous pass ran out of road. Close what you
   can, and leave behind the questions you opened.
4. `validate FILE` — fix every error, read every warning, decide consciously
   about each one.
5. `upload FILE --target SLUG` — records a new version; nothing is lost, so an
   ambitious pass is always safe to attempt.

The discipline that makes this work is small: **every fact you add carries its
source, and every gap you leave is written down.** A doc maintained that way
gets better with each pass by a different author, human or AI. A doc without
provenance gets rewritten from scratch every time, and the corpus never grows.

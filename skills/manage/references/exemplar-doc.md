# Group-time average treatment effects for staggered adoption (did)

## Summary
Callaway and Sant'Anna's estimator for difference-in-differences with more than two periods and staggered treatment timing: instead of one two-way fixed effects coefficient, it reports a separate ATT(g,t) for every adoption cohort g in every period t, then aggregates those into event-study, cohort, calendar-time or overall summaries. The R package `did` implements it with doubly robust 2x2 building blocks and a multiplier bootstrap that gives simultaneous confidence bands.

## Metadata
- Source: https://bcallaway11.github.io/did/articles/did-basics.html
- Tags: DiD, Event Study, Staggered Adoption
- Cover: https://bcallaway11.github.io/did/articles/did-basics_files/figure-html/unnamed-chunk-14-1.png

## Description
<!-- REFERENCE EXEMPLAR. This file ships with the StatsOtter Claude Code plugin as
     the gold-standard example of a rich knowledge document. It is not a user card.
     Read it to calibrate depth, sourcing and the AI Notes outline before writing
     or editing a real card's document. -->

> *Reference exemplar shipped with the StatsOtter plugin — this is what a "rich" knowledge document looks like. Unofficial community showcase of [did](https://bcallaway11.github.io/did/) by Brantly Callaway and Pedro H. C. Sant'Anna. All credit to the authors.*

Textbook DiD compares two groups over two periods. Real policies do not arrive that way: states raise the minimum wage in different years, firms adopt a technology on their own schedule, hospitals roll out a protocol ward by ward. The reflex is to throw everything into a two-way fixed effects regression with leads and lags — and that reflex is wrong when treatment effects differ across cohorts or grow with exposure, because already-treated units end up serving as controls for later-treated units and enter the estimate with negative weights.

Callaway and Sant'Anna (2021) take the problem apart instead of averaging it away. Define a *group* $g$ as the period in which a unit is first treated, and estimate one parameter per cohort per period:

$$ATT(g,t) = \mathbb{E}\left[Y_t(g) - Y_t(0) \mid G = g\right]$$

Each $ATT(g,t)$ is a clean 2x2 comparison — cohort $g$ against a comparison group that is still untreated, from the base period $g-1$ to period $t$ — so no already-treated unit is ever used as a control. Under parallel trends and no anticipation these are identified by

$$ATT(g,t) = \mathbb{E}\left[Y_t - Y_{g-1} \mid G = g\right] - \mathbb{E}\left[Y_t - Y_{g-1} \mid C = 1\right]$$

with the never-treated group $C$, or with the not-yet-treated at $t$ in place of $C$. Because the building block is a two-period, two-group problem, each cell can be estimated with outcome regression, inverse probability weighting, or the locally efficient doubly robust estimator of Sant'Anna and Zhao (2020) — which is what `did` does by default — so parallel trends only has to hold conditional on covariates.

The disaggregated estimates are the honest object, but there can be dozens of them. The package therefore aggregates: by length of exposure $e = t - g$ (an event study that is valid under selective treatment timing), by cohort, by calendar period, or into a single overall ATT. Inference throughout uses a multiplier bootstrap on the influence functions, which yields simultaneous confidence bands rather than pointwise intervals — in the package's own simulated example the 95% uniform critical value is 2.7 rather than 1.96.

## Results
The estimand is $ATT(g,t)$ and its aggregations, all on the scale of the outcome. In the package's minimum-wage application the outcome is log county teen employment, so effects read as approximate proportional changes.

Estimating without covariates on `mpdta` gives 12 group-time effects across cohorts 2004, 2006 and 2007. Two are negative and outside the simultaneous band: $ATT(2004, 2006) = -0.1373$ (s.e. 0.0412) and $ATT(2004, 2007) = -0.1008$ (s.e. 0.0358). The Wald pre-test of parallel trends on the pre-treatment cells does not reject, $p = 0.16812$.

Aggregated by length of exposure, the overall event-study ATT is $-0.0772$ (s.e. 0.0203, 95% CI $[-0.1171, -0.0374]$), with effects near zero on impact ($e = 0$: $-0.0199$) and growing more negative with exposure ($e = 1$: $-0.0510$; $e = 2$: $-0.1373$; $e = 3$: $-0.1008$). Balancing the event-time sample with `balance_e = 1` — which keeps only cohorts observed for at least one post-period, dropping the 2007 cohort — shrinks the overall estimate to $-0.0288$ (s.e. 0.0135). That gap between $-0.0772$ and $-0.0288$ is the whole point of the balancing option: composition, not effect size, is doing part of the work in the unbalanced event study.

## Inputs
A long-format panel or repeated cross section with four required columns and optional covariates:

- **unit id** (`idname`) — numeric, time-invariant. Required for panel data; omit for genuine repeated cross sections.
- **time** (`tname`) — numeric period.
- **outcome** (`yname`) — numeric.
- **cohort** (`gname`) — numeric, the period in which the unit is *first* treated, and exactly `0` for never-treated units. Must not vary within a unit; negative values are rejected.
- **covariates** (`xformla`, e.g. `~ lpop`) — optional; needed only if parallel trends is conditional.

The design must be staggered and irreversible: once treated, always treated. Units already treated in the first period carry no information and are dropped with a warning.

## Input example
```text
year,countyreal,lpop,lemp,first.treat,treat
2003,8001,5.896761,8.461469,2007,1
2004,8001,5.896761,8.336870,2007,1
2005,8001,5.896761,8.340217,2007,1
2006,8001,5.896761,8.378161,2007,1
2007,8001,5.896761,8.487352,2007,1
2003,8019,2.232377,4.997212,2007,1
```

## Figures
- https://bcallaway11.github.io/did/articles/did-basics_files/figure-html/unnamed-chunk-13-1.png | Group-time ATT(g,t) for the minimum-wage example, one panel per adoption cohort, red for pre-treatment pseudo-effects and blue for post-treatment effects.
- https://bcallaway11.github.io/did/articles/did-basics_files/figure-html/unnamed-chunk-14-1.png | The same estimates aggregated by length of exposure into an event study with simultaneous bands.
- https://bcallaway11.github.io/did/articles/did-basics_files/figure-html/unnamed-chunk-15-1.png | The event study after balancing the sample with balance_e = 1, which drops the 2007 cohort.

## Steps

### 1. prep — Load the county panel
- URL: https://bcallaway11.github.io/did/articles/did-basics.html
- Note: `mpdta` is a balanced panel of 2,500 rows — 500 U.S. counties observed 2003-2007 — shipped with the package, so the whole example is reproducible with no external download.

```r
library(did)
data(mpdta)
head(mpdta)
nrow(mpdta)
```

### 2. prep — Encode the adoption cohort
- Note: `first.treat` holds the year a county's state first raised the minimum wage and is `0` for never-treated counties; this single column replaces the usual treatment dummy and defines every 2x2 comparison the estimator builds.
- Formula: G_i = \min\{t : D_{it} = 1\}, \quad G_i = 0 \text{ if never treated}

```r
table(mpdta$first.treat)
stopifnot(!any(mpdta$first.treat < 0))
```

### 3. estimation — Group-time average treatment effects
- URL: https://bcallaway11.github.io/did/reference/att_gt.html
- Note: `att_gt()` estimates one ATT for every (cohort, period) cell using a doubly robust 2x2 estimator, never using an already-treated unit as a control. `xformla = ~1` imposes unconditional parallel trends.
- Formula: ATT(g,t) = \mathbb{E}[Y_t - Y_{g-1} \mid G = g] - \mathbb{E}[Y_t - Y_{g-1} \mid C = 1]

```r
mw.attgt <- att_gt(yname = "lemp",
                   gname = "first.treat",
                   idname = "countyreal",
                   tname = "year",
                   xformla = ~1,
                   data = mpdta)
summary(mw.attgt)
```

### 4. diagnostic — Pre-test parallel trends
- URL: https://bcallaway11.github.io/did/articles/pre-testing.html
- Note: Cells with $t < g$ are pseudo-effects that should be zero if parallel trends held before treatment; `summary()` reports a Wald test over all of them ($p = 0.16812$ here). It is a pre-test, not a test of the assumption you actually need.

```r
mw.attgt$Wpval
```

### 5. inference — Simultaneous bands and clustering
- Note: `bstrap = TRUE, cband = TRUE` (both defaults) run a multiplier bootstrap and widen the critical value so the band covers *all* ATT(g,t) simultaneously; `clustervars` adds a second clustering dimension beyond the unit.
- Formula: \Pr\left(ATT(g,t) \in \left[\hat{ATT}(g,t) \pm \hat{c}_{1-\alpha}\,\hat{\sigma}(g,t)\right] \ \forall (g,t)\right) \to 1-\alpha

```r
mw.attgt.cl <- att_gt(yname = "lemp", gname = "first.treat",
                      idname = "countyreal", tname = "year",
                      xformla = ~1, data = mpdta,
                      clustervars = "countyreal", biters = 1000)
```

### 6. heterogeneity — Aggregate into an event study
- URL: https://bcallaway11.github.io/did/reference/aggte.html
- Note: `type = "dynamic"` averages ATT(g,t) across cohorts at each length of exposure $e = t - g$; unlike an event-study regression this stays valid when treatment effects differ across cohorts.
- Formula: \theta_D(e) = \sum_{g} \mathbf{1}\{g + e \le \mathcal{T}\}\, ATT(g, g+e)\, \Pr(G = g \mid G + e \le \mathcal{T})

```r
mw.dyn <- aggte(mw.attgt, type = "dynamic")
summary(mw.dyn)
```

### 7. robustness — Balance the exposure window
- Note: Without balancing, each event time averages a different set of cohorts, so the shape of the event study can be composition rather than dynamics; `balance_e = 1` keeps only cohorts observed at least one period post-treatment and moves the overall ATT from -0.0772 to -0.0288.

```r
mw.dyn.balance <- aggte(mw.attgt, type = "dynamic", balance_e = 1)
summary(mw.dyn.balance)

mw.nyt <- att_gt(yname = "lemp", gname = "first.treat",
                 idname = "countyreal", tname = "year",
                 xformla = ~1, data = mpdta,
                 control_group = "notyettreated")
```

### 8. reporting — Plot the estimates
- URL: https://bcallaway11.github.io/did/reference/ggdid.html
- Note: `ggdid()` renders an `MP` object as one panel per cohort and an `AGGTEobj` as an event-study, cohort or calendar plot; fixing `ylim` keeps the panels comparable.

```r
ggdid(mw.attgt, ylim = c(-.3, .3))
ggdid(mw.dyn, ylim = c(-.3, .3))
```

## AI Notes

### Method identity

**What it is.** The group-time average treatment effect framework of Callaway and Sant'Anna for difference-in-differences with (i) more than two periods, (ii) variation in treatment timing, and (iii) parallel trends that may hold only conditional on covariates. The primitive parameter is $ATT(g,t)$, the average effect in period $t$ for the cohort first treated in period $g$; everything else in the framework is an aggregation of those.

**Lineage.**
- Two-period, two-group DiD is the special case $T = 2$, one cohort.
- Semiparametric conditional DiD comes from Heckman, Ichimura and Todd (1998), *Review of Economic Studies* 65(2), 261-294, and Abadie (2005), "Semiparametric difference-in-differences estimators", *Review of Economic Studies* 72(1), 1-19 (both cited as background in the package's pre-testing vignette).
- The doubly robust 2x2 engine is Sant'Anna and Zhao (2020), "Doubly Robust Difference-in-Differences Estimators", *Journal of Econometrics* 219(1), 101-122, DOI 10.1016/j.jeconom.2020.06.003 — implemented in the `DRDID` package and called internally by `did` for every cell.
- The negative-weights critique of TWFE that motivates the whole literature: de Chaisemartin and D'Haultfœuille (2020), "Two-Way Fixed Effects Estimators with Heterogeneous Treatment Effects", *American Economic Review* 110(9), 2964-2996, DOI 10.1257/aer.20181169; and Sun and Abraham (2021), *Journal of Econometrics* 225(2), 175-199.

**Key paper.** Callaway, Brantly and Pedro H. C. Sant'Anna (2021), "Difference-in-Differences with multiple time periods", *Journal of Econometrics* 225(2), 200-230, DOI 10.1016/j.jeconom.2020.12.001; preprint arXiv:1803.09015 (v1 2018-03-23, v4 2020-12-01), DOI 10.48550/arXiv.1803.09015. The package prints this citation in the header of every `summary()`.

**Canonical implementation.** R package `did`, version 2.5.1, published on CRAN 2026-07-08. Authors Brantly Callaway (maintainer, brantly.callaway@uga.edu) and Pedro H. C. Sant'Anna. License GPL-3. Depends R (>= 4.1.0). Imports BMisc (>= 1.4.4), Matrix, pbapply, ggplot2, DRDID (>= 1.3.0), generics, methods, tidyr, fastglm, data.table (>= 1.15.4), dreamerr (>= 1.4.0). Sites: https://bcallaway11.github.io/did/ and https://github.com/bcallaway11/did/.

### When to use / when not to use

**Use it when all of these hold.**
- Treatment adoption is staggered *and* irreversible (absorbing). Once a unit is treated it stays treated.
- There are at least two periods, and for identification of any given cell, at least one period before cohort $g$ becomes treated.
- There exists a never-treated group, or at least a not-yet-treated group at each relevant period.
- You expect effect heterogeneity across cohorts or over exposure — this is exactly where TWFE breaks and this estimator does not.
- Parallel trends is plausible only after conditioning on covariates (then supply `xformla`).

**Do not use it when.**
- Treatment switches on and off. The package rejects this outright; use estimators built for switching designs (de Chaisemartin and D'Haultfœuille).
- Treatment is continuous or multi-valued in dose. `did` is binary-treatment only.
- Every unit is treated in the same period. Then there is nothing staggered and a plain two-period DiD is the right tool.
- No untreated comparison exists at all in any period. If there is merely no *never*-treated group, the package silently coerces the last-treated cohort into the control role and drops later periods, with a warning — prefer setting `control_group = "notyettreated"` deliberately.
- Cohorts are tiny. Effective sample size for a given $ATT(g,t)$ is the number of units in that cohort; the package documents that asymptotics are a poor approximation for small groups and recommends reading only the aggregated parameters in that case.

**Competing designs.** If parallel trends itself is the weak point rather than the aggregation, the complement is sensitivity analysis (Rambachan and Roth 2023) rather than a different DiD estimator. If units are few and the comparison group must be constructed, synthetic control is the alternative design.

### Assumptions

| Assumption | Formal statement | How to check | What breaks if it fails |
| --- | --- | --- | --- |
| Staggered adoption / irreversibility | $D_{it} = 1 \Rightarrow D_{it+1} = 1$ for $t = 1,\dots,T-1$ | The package checks it: `gname` must be constant within a unit. Cross-tabulate `id` by `first.treat` yourself first. | `att_gt()` errors. There is no fallback inside `did`. |
| No anticipation | $Y_{it} = Y_{it}(0)$ for all $t < g$ (optionally $t < g - \delta$) | Look at pre-treatment pseudo-ATTs immediately before $g$; a dip at $e = -1$ is the signature. Re-run with `anticipation = 1`. | The base period $g-1$ is already contaminated, biasing every post-treatment cell for that cohort in the opposite direction. |
| Parallel trends, never-treated variant | $\mathbb{E}[Y_t(0) - Y_{t-1}(0) \mid G = g] = \mathbb{E}[Y_t(0) - Y_{t-1}(0) \mid C = 1]$ | Wald pre-test in `summary()` (`MP$Wpval`); uniform bands on pre-treatment cells; `ggdid()` red points. | Every $ATT(g,t)$ is biased by the differential trend; the pre-test may or may not catch it. |
| Parallel trends, not-yet-treated variant | $\mathbb{E}[Y_t(0) - Y_{t-1}(0) \mid G = g] = \mathbb{E}[Y_t(0) - Y_{t-1}(0) \mid D_s = 0, G \neq g]$ for $s \ge t$ | Estimate both ways (`control_group = "nevertreated"` vs `"notyettreated"`) and compare. Divergence is evidence against one of them. | Same as above, plus the comparison group now changes with $t$, so the bias is period-specific. |
| Conditional parallel trends | The above holds conditional on $X$ | `conditional_did_pretest()` runs a Cramér-von Mises conditional-moment test that can detect violations invisible to the unconditional pre-test (e.g. opposite-signed violations for men and women that cancel). | Covariate-adjusted estimates are still biased; adding covariates does not save you. |
| Overlap / common support | $\Pr(G = g \mid X, \text{eligible}) < 1$ for the propensity score in each 2x2 cell | The package fits a per-cell logit and applies an overlap guard at a 0.999 cutoff; affected cells warn and return `NA` rather than a number. | Inverse probability weights explode; the doubly robust estimate becomes unstable or undefined. |
| Random sampling across units | $(Y_{i1},\dots,Y_{iT}, G_i, X_i)$ i.i.d. across $i$ | Not testable. Use `clustervars` when units are nested (at most one variable beyond `idname`). | Standard errors are too small; the bootstrap inherits the same problem. |
| Balanced panel (unless relaxed) | Every unit observed in every period | Default behavior drops offenders and warns with the count. | Nothing breaks statistically, but you may silently lose a large, non-random slice of the sample — always read the warning. |

### Estimand and estimator

**Primitive parameter.**
$$ATT(g,t) = \mathbb{E}\left[Y_t(g) - Y_t(0) \mid G = g\right]$$
identified for $t \ge g$ under the assumptions above. For $t < g$ the same formula produces a *pseudo* effect used only for pre-testing.

**Identification.**
$$ATT(g,t) = \mathbb{E}\left[Y_t - Y_{g-1} \mid G = g\right] - \mathbb{E}\left[Y_t - Y_{g-1} \mid C = 1\right]$$
with the never-treated group, and
$$ATT(g,t) = \mathbb{E}\left[Y_t - Y_{g-1} \mid G = g\right] - \mathbb{E}\left[Y_t - Y_{g-1} \mid D_t = 0, G \neq g\right]$$
with the not-yet-treated. Conditional versions replace the raw difference in trends by a covariate-adjusted contrast estimated by outcome regression, IPW, or the doubly robust combination.

**Base period.** `base_period = "varying"` (default) uses period $t-1$ as the base for pre-treatment cells and $g-1$ for post-treatment cells, so pre-treatment pseudo-ATTs are one-period-ahead placebo effects. `base_period = "universal"` normalizes to $g-1$ throughout, which is the convention most event-study regressions use and makes the $e = -1$ estimate exactly zero by construction. Post-treatment estimates are the same either way; only the pre-treatment display and the pre-test differ.

**Aggregations** (all computed by `aggte()`):
- Cohort: $\theta_S(g) = \frac{1}{T - g + 1} \sum_{t} \mathbf{1}\{g \le t\}\, ATT(g,t)$
- Overall from cohorts: $\theta_S^{O} = \sum_g \theta_S(g) \Pr(G = g)$
- Dynamic / event study: $\theta_D(e) = \sum_g \mathbf{1}\{g + e \le \mathcal{T}\}\, ATT(g, g+e)\, \Pr(G = g \mid G + e \le \mathcal{T})$
- Calendar: average across cohorts already treated in period $t$, then averaged over $t$.
- Simple: weighted average of all post-treatment $ATT(g,t)$ with weights proportional to group size. The package's own vignette warns that this overweights early-treated cohorts simply because more of their post-periods are observed, and recommends `type = "group"` as the leading overall summary.

**Inference.** Each $ATT(g,t)$ has an influence function; `MP$inffunc` is an $n \times k$ matrix with one row per cross-sectional unit and one column per cell. Standard errors come from a multiplier bootstrap over those influence functions (`bstrap = TRUE`, `biters = 1000`), and `cband = TRUE` inflates the critical value so the band covers all cells simultaneously. As of 2.5.0 the cluster-robust bootstrap follows Remark 10 of the paper — one multiplier per cluster, influence functions aggregated to cluster sums — and analytical cluster-robust standard errors are available with `bstrap = FALSE` plus `clustervars`.

### API reference

**`att_gt()`** — https://bcallaway11.github.io/did/reference/att_gt.html

```r
att_gt(yname, tname, idname = NULL, gname, xformla = NULL, data,
       panel = TRUE, allow_unbalanced_panel = FALSE,
       control_group = c("nevertreated", "notyettreated"),
       anticipation = 0, weightsname = NULL, fix_weights = NULL,
       alp = 0.05, bstrap = TRUE, cband = TRUE, biters = 1000,
       clustervars = NULL, est_method = "dr", base_period = "varying",
       faster_mode = TRUE, print_details = FALSE, pl = FALSE, cores = 1,
       compute_inffunc = TRUE, ...)
```

| Argument | Type | Default | Meaning |
| --- | --- | --- | --- |
| `yname` | character | required | Name of the outcome column. Must be numeric (logical is coerced). |
| `tname` | character | required | Name of the time-period column. Must be numeric. |
| `idname` | character | `NULL` | Cross-sectional unit id. Required when `panel = TRUE`; must be numeric. For genuine repeated cross sections, omit it — if supplied it is still validated (time-invariant `gname`, at most one row per unit-period). |
| `gname` | character | required | First period in which the unit is treated; positive for treated units, `0` for the untreated group. Defines the cohort. Must be numeric and non-negative. |
| `xformla` | formula | `NULL` | Covariates as `~ X1 + X2`; `NULL` is equivalent to `~1`. Since 2.5.0 may contain transformations and interactions (`~ I(X^2)`, `~ log(X)`, `~ poly(X, 2)`, `~ X1 * X2`) and factor variables. On balanced panels a time-varying covariate is taken from the base period; on repeated cross sections and unbalanced panels it is taken from each period. |
| `data` | data.frame | required | Long-format data: one row per unit per period. |
| `panel` | logical | `TRUE` | `FALSE` for repeated cross sections. |
| `allow_unbalanced_panel` | logical | `FALSE` | With `FALSE`, units not observed in every period are dropped to force balance. `TRUE` keeps them at higher computational cost. |
| `control_group` | character | `"nevertreated"` | Or `"notyettreated"`, which also includes eventually-treated units that are still untreated at $t$ and is weakly larger. |
| `anticipation` | integer | `0` | Number of periods before $g$ in which units may already respond; shifts the base period back accordingly. |
| `weightsname` | character | `NULL` | Sampling-weight column. Must be non-negative with a positive mean. |
| `fix_weights` | character | `NULL` | How time-varying weights are resolved per 2x2 cell: `NULL` (prior behavior), `"varying"`, `"base_period"` (fix at $g-1$), `"first_period"`. The last two are panel-only. |
| `alp` | numeric | `0.05` | Significance level. |
| `bstrap` | logical | `TRUE` | Multiplier-bootstrap standard errors. Setting `FALSE` gives analytical (and, with `clustervars`, analytically clustered) errors. |
| `cband` | logical | `TRUE` | Uniform confidence band covering all $ATT(g,t)$ with probability $1-\alpha$. Requires `bstrap = TRUE`. |
| `biters` | integer | `1000` | Bootstrap iterations; only used when `bstrap = TRUE`. |
| `clustervars` | character vector | `NULL` | At most two variables, one of which must equal `idname`; effectively one extra clustering dimension. Must be time-invariant. |
| `est_method` | character or function | `"dr"` | `"dr"` (doubly robust: linear outcome regression + logit propensity score), `"ipw"`, `"reg"`, or a user function with the DRDID signature. |
| `base_period` | character | `"varying"` | Or `"universal"`. |
| `faster_mode` | logical | `TRUE` | Optimized data management. Results are identical to `FALSE` up to numerical precision, but the row *order* of `inffunc` differs. |
| `print_details` | logical | `FALSE` | Progress/diagnostic printing. |
| `pl` | logical | `FALSE` | Parallel processing. |
| `cores` | integer | `1` | Cores when `pl = TRUE`. |
| `compute_inffunc` | logical | `TRUE` | `FALSE` returns point estimates only — no influence functions, no standard errors, no bands, no pre-test — and forces `bstrap = FALSE, cband = FALSE`. Much faster and far lighter on memory. The result cannot be passed to `aggte()`; doing so errors with a clear message. |
| `...` | | | Forwarded to a custom `est_method`; ignored for the built-in methods. |

**Return: `MP` object** — https://bcallaway11.github.io/did/reference/MP.html

| Field | Contents |
| --- | --- |
| `group` | Cohort (period first treated) for each estimate. |
| `t` | Time period for each estimate. |
| `att` | The $ATT(g,t)$ point estimates. |
| `V_analytical` | Analytical asymptotic variance-covariance matrix of the group-time effects. |
| `se` | Standard errors; bootstrap-based when `bstrap = TRUE`. |
| `c` | Simultaneous critical value when `cband = TRUE`, otherwise the pointwise normal critical value. |
| `inffunc` | Influence-function matrix: one column per $ATT(g,t)$, one row per cross-sectional unit. Since 2.5.0 rownames carry the unit ids (an internal observation index for repeated cross sections). **Align rows by rowname, never by position** — the order is `faster_mode`-dependent (`FALSE` sorts by id; `TRUE` uses an internal period/cohort/id ordering). |
| `n` | Number of unique cross-sectional units. |
| `W` | Wald statistic for the pre-test of parallel trends. |
| `Wpval` | p-value of that Wald statistic. |
| `aggte` | An aggregate treatment-effects object. |
| `alp` | Significance level used. |
| `DIDparams` | The options from the originating call. |

**`aggte()`** — https://bcallaway11.github.io/did/reference/aggte.html

```r
aggte(MP, type = "group", balance_e = NULL, min_e = -Inf, max_e = Inf,
      na.rm = FALSE, bstrap = NULL, biters = NULL, cband = NULL,
      alp = NULL, clustervars = NULL)
```

| Argument | Default | Meaning |
| --- | --- | --- |
| `MP` | required | Output of `att_gt()`. |
| `type` | `"group"` | `"simple"` (size-weighted average of all post-treatment cells), `"dynamic"` (event study by length of exposure), `"group"` (per cohort), `"calendar"` (per period). |
| `balance_e` | `NULL` | Restrict to cohorts exposed for at least this many post-periods, and report only those event times. `balance_e = 2` excludes cohorts not exposed for at least three periods. |
| `min_e` | `-Inf` | Smallest event time reported. |
| `max_e` | `Inf` | Largest event time reported. |
| `na.rm` | `FALSE` | Drop `NA` cells rather than propagating them. |
| `bstrap`, `biters`, `cband`, `alp` | `NULL` | Inherit from the `MP` object unless overridden. `cband` requires `bstrap = TRUE`. |
| `clustervars` | `NULL` | Defaults to what `att_gt()` clustered on. Since 2.5.0 a request the aggregation cannot honor warns and falls back to non-clustered errors instead of silently returning i.i.d. errors. |

**Return: `AGGTEobj`** — https://bcallaway11.github.io/did/reference/AGGTEobj.html — with fields `overall.att`, `overall.se`, `type`, `egt` (the exposure length, cohort, or period the row refers to), `att.egt`, `se.egt`, `crit.val.egt` (critical value for the uniform band), `inf.function`, `min_e`, `max_e`, `balance_e`, `call`, `DIDparams`.

**Other user-facing functions.**
- `ggdid(object, ...)` with methods `ggdid.MP()` and `ggdid.AGGTEobj()`; builds on ggplot2. `ylim = c(-.3, .3)` is the documented way to force a common y-scale across cohort panels.
- `conditional_did_pretest(yname, tname, idname, gname, xformla, data)` — Cramér-von Mises test of *conditional* parallel trends. Substantially slower than `att_gt()`.
- `mpdta` — the bundled example dataset.
- `reset.sim()` / `build_sim_dataset()` — simulation helpers used in the vignettes.
- S3 methods: `summary()`, `nobs()` (unique cross-sectional units), `tidy()` (since 2.5.0 includes `statistic` and `p.value` columns following broom conventions), `glance()`.

### Data requirements

- **Shape.** Long format, one row per unit per period. Wide data must be reshaped first; the vignette points to `tidyr::pivot_longer()`.
- **Types.** `tname`, `gname`, `idname`, `yname` all numeric. Non-numeric columns are rejected with explicit errors (see Failure modes).
- **Cohort coding.** `gname` = period of first treatment, `0` = never treated. Negative values are rejected outright; if your periods are non-positive, shift them so the earliest is $\ge 1$.
- **Uniqueness.** At most one row per (`idname`, `tname`). Duplicated unit-period rows are a common long-format mistake and are now rejected in both code paths (before 2.5.0, `faster_mode = FALSE` silently produced incorrect estimates).
- **Reserved names.** The package reserves the column name `.w` for internal use.
- **Balance.** Default behavior coerces to a balanced panel by dropping units with any missing period, reporting how many. `allow_unbalanced_panel = TRUE` keeps them at a computational cost.
- **Sample size.** The effective sample for a single $ATT(g,t)$ is the size of cohort $g$. The package warns when any group has fewer observations than the number of covariates plus five. When a cell cannot be estimated (singular covariate matrix, overlap violation, too few observations), `att_gt()` warns for that cell and returns `NA` for it rather than erroring — the exception being a too-small never-treated group, which stops with a suggestion to use `control_group = "notyettreated"`.
- **Missing data.** Rows with missing or non-finite values in any referenced variable are dropped with a warning giving the count; non-finite evaluated covariates (e.g. `log()` of a non-positive value) are dropped too.
- **Scale reference.** `mpdta`: 2,500 rows, 6 columns, 500 counties, 2003-2007, cohorts 2004 / 2006 / 2007 plus never-treated.

### Worked example

Public dataset: `mpdta`, bundled with the package (county-level teen employment, 2003-2007, from Callaway and Sant'Anna 2021). Runnable end to end after `install.packages("did")`.

```r
library(did)
data(mpdta)

head(mpdta)
#>     year countyreal     lpop     lemp first.treat treat
#> 866 2003       8001 5.896761 8.461469        2007     1
#> 841 2004       8001 5.896761 8.336870        2007     1
#> 842 2005       8001 5.896761 8.340217        2007     1
#> 819 2006       8001 5.896761 8.378161        2007     1
#> 827 2007       8001 5.896761 8.487352        2007     1
#> 937 2003       8019 2.232377 4.997212        2007     1

mw.attgt <- att_gt(yname = "lemp",
                   gname = "first.treat",
                   idname = "countyreal",
                   tname = "year",
                   xformla = ~1,
                   data = mpdta)

summary(mw.attgt)
#> Group-Time Average Treatment Effects:
#>  Group Time ATT(g,t) Std. Error [95% Simult.  Conf. Band]
#>   2004 2004  -0.0105     0.0243       -0.0753      0.0543
#>   2004 2005  -0.0704     0.0331       -0.1586      0.0178
#>   2004 2006  -0.1373     0.0412       -0.2470     -0.0275 *
#>   2004 2007  -0.1008     0.0358       -0.1963     -0.0054 *
#>   2006 2004   0.0065     0.0230       -0.0547      0.0677
#>   2006 2005  -0.0028     0.0210       -0.0588      0.0533
#>   2006 2006  -0.0046     0.0175       -0.0513      0.0421
#>   2006 2007  -0.0412     0.0196       -0.0936      0.0111
#>   2007 2004   0.0305     0.0147       -0.0087      0.0697
#>   2007 2005  -0.0027     0.0156       -0.0442      0.0387
#>   2007 2006  -0.0311     0.0179       -0.0789      0.0168
#>   2007 2007  -0.0261     0.0175       -0.0726      0.0205
#> ---
#> Signif. codes: `*' confidence band does not cover 0
#>
#> P-value for pre-test of parallel trends assumption:  0.16812
#> Control Group:  Never Treated,  Anticipation Periods:  0
#> Estimation Method:  Doubly Robust

mw.dyn <- aggte(mw.attgt, type = "dynamic")
summary(mw.dyn)
#> Overall summary of ATT's based on event-study/dynamic aggregation:
#>      ATT    Std. Error     [ 95%  Conf. Int.]
#>  -0.0772        0.0203    -0.1171     -0.0374 *
#>
#> Dynamic Effects:
#>  Event time Estimate Std. Error [95% Simult.  Conf. Band]
#>          -3   0.0305     0.0157       -0.0084      0.0694
#>          -2  -0.0006     0.0136       -0.0343      0.0332
#>          -1  -0.0245     0.0144       -0.0601      0.0112
#>           0  -0.0199     0.0124       -0.0507      0.0108
#>           1  -0.0510     0.0163       -0.0913     -0.0106 *
#>           2  -0.1373     0.0402       -0.2369     -0.0376 *
#>           3  -0.1008     0.0354       -0.1886     -0.0131 *

mw.dyn.balance <- aggte(mw.attgt, type = "dynamic", balance_e = 1)
summary(mw.dyn.balance)
#> Overall summary of ATT's based on event-study/dynamic aggregation:
#>      ATT    Std. Error     [ 95%  Conf. Int.]
#>  -0.0288        0.0135    -0.0552     -0.0023 *
#>
#> Dynamic Effects:
#>  Event time Estimate Std. Error [95% Simult.  Conf. Band]
#>          -2   0.0065     0.0237       -0.0515      0.0646
#>          -1  -0.0028     0.0207       -0.0534      0.0479
#>           0  -0.0066     0.0155       -0.0444      0.0313
#>           1  -0.0510     0.0171       -0.0927     -0.0092 *

mw.attgt.X <- att_gt(yname = "lemp", gname = "first.treat",
                     idname = "countyreal", tname = "year",
                     xformla = ~lpop, data = mpdta)
```

**How to read it.** Rows with `Time < Group` are pre-treatment pseudo-effects; only rows with `Time >= Group` are causal estimates. `*` means the *simultaneous* band excludes zero, which is a stricter bar than a pointwise interval. The 2004 cohort is the only one with a long post-treatment window, and it is where the significant negative effects appear.

**Companion simulated example** (same vignette, `build_sim_dataset()`, 15,916 observations, 4 periods, cohorts 2/3/4, true $ATT(g,t) = e + 1$). It is useful as a correctness check because the truth is known: the estimated event study returns 0.9929 at $e = 0$, 2.0231 at $e = 1$, 2.9552 at $e = 2$, with pre-treatment estimates 0.0023 at $e = -2$ and 0.0105 at $e = -1$ — i.e. it recovers $e + 1$ and a flat pre-trend. Cohort aggregation for that dataset gives an overall ATT of 1.488 (s.e. 0.0343) with cohort effects 1.9545 / 1.5835 / 0.9523 for groups 2 / 3 / 4; calendar aggregation gives 1.4808 (s.e. 0.0347) with period effects 0.9209 / 1.5491 / 1.9724; simple aggregation gives 1.6583 (s.e. 0.0333) — visibly larger than both, which is the overweighting of early cohorts the authors warn about.

### Interpreting the output

- **Scale.** $ATT(g,t)$ is in outcome units. With a log outcome, $-0.1373$ is $-13.7$ log points, roughly a 12.8% decline ($e^{-0.1373} - 1$). Report which convention you are using; the difference matters above about 0.1 in absolute value.
- **Event time.** $e = 0$ is the first treated period (an impact effect, not a lag). $e = -1$ is the base period under `base_period = "universal"` and is mechanically zero there; under the default `"varying"` it is a genuine one-period-ahead placebo, which is why it can be non-zero ($-0.0245$ above).
- **Which overall number to quote.** The package authors' recommendation is `type = "group"`: it averages cohort-specific effects across cohorts and has the same interpretation as the textbook two-period ATT. `type = "simple"` overweights early adopters. `type = "dynamic"`'s overall number averages across exposure lengths, so it depends on how far the panel runs.
- **Bands vs intervals.** The per-cell columns are *simultaneous* bands; the overall ATT line is a conventional pointwise 95% interval. Do not compare a starred cell against an unstarred one as if they were pointwise tests.
- **Plausible ranges.** None are universal — but a pre-treatment pseudo-effect of the same magnitude as your post-treatment effects is a red flag regardless of its p-value, and an $e = 0$ effect far larger than $e = 1$ in an absorbing-treatment design usually means anticipation or a mis-coded cohort.
- **Common misreadings.** (1) Treating the pre-test p-value as evidence *for* parallel trends — failing to reject is weak evidence, and the pre-test has low power in small samples. (2) Reading the unbalanced event study's shape as dynamics when it is composition (compare with `balance_e`). (3) Quoting `NA` cells as zeros; they are cells the estimator refused to compute.

### Diagnostics

1. **Wald pre-test.** `summary()` prints "P-value for pre-test of parallel trends assumption"; programmatically `MP$Wpval` and `MP$W`. It is a joint test over all pre-treatment cells.
2. **Visual pre-trends.** `ggdid(mw.attgt, ylim = c(-.3, .3))` — one panel per cohort, red pre-treatment points with simultaneous bands. Fixing `ylim` prevents the per-panel autoscaling that makes flat pre-trends look alarming.
3. **Conditional pre-test.** `conditional_did_pretest()` when `xformla` is non-trivial. The unconditional pre-test can miss violations that cancel across covariate strata (the vignette's example: violations of opposite sign for men and women). Note this function was silently broken under R >= 4.0 and spuriously rejected almost always when there was more than one pre-treatment cell; it was fixed in 2.5.0 — check your package version before trusting an old result.
4. **Control-group swap.** Re-run with `control_group = "notyettreated"`. Large movement means one of the two parallel-trends variants is failing.
5. **Base-period swap.** Re-run with `base_period = "universal"`. Post-treatment estimates should be unchanged; if they move, something is wrong with the cohort coding.
6. **Anticipation probe.** Re-run with `anticipation = 1`. If the estimates shift materially, the base period was contaminated.
7. **Composition check.** Compare `aggte(type = "dynamic")` with and without `balance_e`.
8. **Estimator swap.** `est_method = "reg"` vs `"ipw"` vs `"dr"`. Under correct specification of at least one nuisance model the doubly robust estimate should sit close to both; a large gap points at misspecification or overlap problems.
9. **Cell health.** Scan for `NA` in `MP$att` and read every warning — each one names the affected cell or group.

### Failure modes and fixes

Error and warning strings below are verbatim from `did`'s pre-processing (`R/pre_process_did.R`, master branch, read 2026-07-22); bracketed placeholders are filled with your variable names at runtime.

| Symptom (verbatim message) | Cause | Fix |
| --- | --- | --- |
| `The value of gname (treatment variable) must be the same across all periods for each particular unit. The treatment must be irreversible.` | Treatment switches off, or the cohort column was built from a per-period dummy. | Rebuild `gname` as $\min\{t : D_{it} = 1\}$ (0 if never). If treatment genuinely reverses, `did` is the wrong package. |
| `The value of idname must be unique (by tname). Some units are observed more than once in a period.` | Duplicated unit-period rows from a bad join or reshape. | De-duplicate before calling. Do not assume older versions caught this — `faster_mode = FALSE` used to produce wrong numbers silently. |
| `The group variable '[gname]' must be 0 (never-treated) or a positive treatment-timing value; negative values are not supported. If your time periods are non-positive, shift them so the earliest period is >= 1.` | Cohorts coded as event time, or calendar years centered on zero. | Shift periods so the first is $\ge 1$ and recode `gname` accordingly. |
| `The time variable '[tname]' must be numeric. Please convert it.` / `The group variable '[gname]' must be numeric...` / `The id variable '[idname]' must be numeric...` / `The outcome variable '[yname]' must be numeric...` | Factor or character columns, typically after `read.csv(stringsAsFactors = TRUE)` or a date column. | Convert explicitly; map dates to integer periods. |
| `The following column(s) are not found in the data: [list]. Please check the spelling of yname, tname, idname, gname, weightsname, and clustervars.` | Typo, or the column lives in a different data frame. | Check `names(data)`. |
| `The following variables are not in data: [list]` | A variable named in `xformla` is absent. | Add it, or drop it from the formula. |
| `control_group must be either 'nevertreated' or 'notyettreated'` / `base_period must be either 'universal' or 'varying'.` | Typo in an option string. | Use the exact literals. |
| `At most one cluster variable (beyond 'idname') is supported. Please reduce to one.` | Three-way clustering attempted. | Cluster on the coarsest single dimension. |
| `Time-varying cluster variables are not supported. Please provide a time-invariant cluster variable.` | Cluster id changes within a unit over time. | Collapse to a time-invariant assignment (e.g. first-period value). |
| `The weights variable '[weightsname]' must be non-negative with a positive mean.` | Negative or all-zero weights. | Fix the weights; before 2.5.0 this produced `NA`/`NaN` estimates silently. |
| ``Your data already contains a column named '.w', which is reserved for internal use by `did`. Please rename this column before calling att_gt().`` | Name collision with an internal column. | Rename your column. |
| ``The never-treated group is too small to serve as a reliable control. Try setting `control_group = 'notyettreated'` to include not-yet-treated units as controls.`` | Almost everyone is eventually treated. | Switch the control group, or accept that this design cannot be identified. |
| `All observations dropped while converting data to balanced panel. Consider setting panel = FALSE and/or revisiting 'idname'.` | The id is not actually a stable unit identifier (e.g. a row index), so no unit appears in every period. | Fix `idname`, or treat the data as repeated cross sections. |
| `All observations were dropped due to missing data. Check your outcome, group, time, and covariate variables for missing values.` | Missingness in a required column across the board. | Inspect `colSums(is.na(data))` first. |
| `No valid groups. The variable in 'gname' should be expressed as the time a unit is first treated (0 if never-treated).` | `gname` is a 0/1 dummy rather than a timing variable. | Recode. |
| Warning: `No never-treated group is available. The last treated cohort is being coerced as 'never-treated' units, and data from periods after that is being filtered out (no available comparison groups).` | Every unit is eventually treated. | Prefer setting `control_group = "notyettreated"` explicitly so the choice is deliberate. |
| Warning: `Dropped [n] units that were already treated in the first period[...].` | Always-treated units. | Expected; they carry no identifying information. |
| Warning: `[n] units are missing in some periods. Converting to balanced panel by dropping them.` / `dropped [n] rows from original data due to missing or non-finite data` | Unbalanced or missing data. | Read the count. If it is large, use `allow_unbalanced_panel = TRUE` or investigate the attrition. |
| Warning: `Some groups in your dataset have very few observations, which may cause estimation problems.\n  Check groups: [list].` | A cohort has fewer observations than covariates + 5. | Drop covariates, pool cohorts, or report only aggregated parameters. |
| Warning: `Time-varying weights detected. For balanced panel data, the default behavior uses the weight from the earlier of the two time periods in each 2x2 comparison (the base period for post-treatment cells). Use the 'fix_weights' argument to control this behavior. See ?att_gt for details.` | Sampling weights vary over time. | Choose `fix_weights` explicitly rather than accepting the default. |
| `contrasts can be applied only to factors with 2 or more levels` | Historic: a factor level absent from one 2x2 cell under `faster_mode = FALSE`. | Fixed in 2.5.0 (the design matrix is now built once with global levels). Upgrade. |
| `Error in get(gname): invalid first argument` from `aggte()` | The group column is literally named `gname` and `dreamerr >= 1.5.0` is installed. | Fixed in 2.5.0; otherwise rename the column. |
| `No valid att_gt() estimates found ...` from `aggte(type = "group", na.rm = TRUE, max_e = ...)` | A group's only non-missing cell lay past `max_e`. | Fixed in 2.5.0. |
| `aggte()` errors on an `MP` object | The `MP` came from `compute_inffunc = FALSE`, which has no influence functions to aggregate. | Re-run `att_gt()` with the default `compute_inffunc = TRUE`. |
| Cell reports `NA` with a warning | Singular covariate matrix, overlap violation, or too few observations in that cell. | Simplify `xformla`, use `control_group = "notyettreated"` to enlarge the comparison group, or accept the cell is not identified. |

### Alternatives and comparisons

| Method | When it wins | How estimates typically differ |
| --- | --- | --- |
| TWFE with a treatment dummy | Single adoption date, or genuinely homogeneous effects. | With staggered timing and heterogeneous effects the coefficient is a weighted average of 2x2 comparisons that can carry negative weights (de Chaisemartin and D'Haultfœuille 2020, AER 110(9), 2964-2996); it can have the wrong sign relative to every underlying $ATT(g,t)$. |
| Event-study regression with leads and lags | Common dynamics across cohorts and no selective timing. | Under selective treatment timing the lead coefficients are contaminated by post-treatment effects of other cohorts, so the pre-test rejects even when parallel trends holds. The package's pre-testing vignette shows exactly this: in a simulated design where parallel trends holds by construction, the event-study regression returns significant leads (`Dtmin3` 0.938, s.e. 0.072; `Dtmin2` 0.424, s.e. 0.051) while `att_gt()` on the same data returns pre-treatment cells of $-0.0276$ and $-0.0420$ with a pre-test p-value of 0.79239. |
| Sun and Abraham (2021), *JoE* 225(2), 175-199 | You want an interaction-weighted event study inside a regression framework, e.g. alongside other regression machinery. | Same spirit as `did` — cohort-by-relative-time effects, then explicit aggregation. Estimates are usually close; the main practical difference is the choice of comparison group and covariate handling. |
| de Chaisemartin and D'Haultfœuille estimators | Treatment switches on *and* off, or is non-binary. | `did` cannot be used at all in those designs. |
| Rambachan and Roth (2023), *ReStud* 90(5), 2555-2591, DOI 10.1093/restud/rdad018 (HonestDiD) | Parallel trends is doubtful and you want a breakdown value rather than a point estimate. | Complementary, not competing: it takes an event study as input and reports how large a violation would have to be to overturn the conclusion. |
| Synthetic control | Very few treated units, long pre-period, no credible parallel-trends comparison group. | Different design entirely; not an aggregation choice. |

Within `did` itself, the meaningful choices are: never-treated vs not-yet-treated control (the latter is weakly larger and period-varying); `dr` vs `ipw` vs `reg` (the doubly robust default is consistent if *either* the outcome model or the propensity model is correct); and which aggregation to headline.

### Performance and scale

- **Cell count.** The estimator computes one 2x2 comparison per (cohort, period) cell — on the order of (number of cohorts) x (number of periods). Cost grows with distinct adoption dates, not just with $N$.
- **Fast path.** `faster_mode = TRUE` is the default since the 2.5.0 line and is documented as roughly 2.5-3x faster than `faster_mode = FALSE` on common problems, with results identical to numerical precision. Additional per-cell guard optimizations (closed forms for intercept-only designs; caching the overlap/feasibility guards per group rather than per cell for panel data with never-treated controls) make a default no-covariate run about 10-15% faster again. `options(did.disable_check_cache = TRUE)` and `options(did.disable_precompute = TRUE)` restore the older per-cell behavior as debugging escape hatches.
- **Memory.** The influence-function matrix is $n \times k$ (units by cells) and is the dominant allocation. `compute_inffunc = FALSE` skips it entirely for a point-estimates-only run — much faster and much lighter, at the cost of all inference and the pre-test.
- **Bootstrap.** `biters = 1000` multiplier draws by default. Cost is linear in `biters` and in the size of the influence matrix.
- **Unbalanced panels.** `allow_unbalanced_panel = TRUE` is materially more expensive; 2.5.0 introduced a sparse unit-aggregation operator built once per call that the changelog reports as about 2x faster end to end on large unbalanced panels.
- **Conditional pre-test.** `conditional_did_pretest()` was the memory hot spot: its multiplier bootstrap previously allocated an $O(n^2 k)$ transient per draw (over 1 GB per draw at a few thousand units) and is now a single tiled matrix contraction, reported as 100x+ faster on that step. Even so, budget far more time for it than for `att_gt()`.
- **Parallelism.** `pl = TRUE` with `cores = k`. The changelog's headline speedups are single-threaded, so measure before assuming parallelism helps.
- **Practical limits.** No hard cap is documented. The binding constraints in practice are the number of distinct cohorts (cells) and the influence-matrix memory, not the row count.

### Provenance

All sources below were fetched and read on **2026-07-22**. Nothing in this document is asserted from memory.

| URL | What was taken from it |
| --- | --- |
| https://bcallaway11.github.io/did/reference/att_gt.html | Full `att_gt()` signature with every argument and default; per-argument semantics (`gname` coding, `xformla` covariate timing, `allow_unbalanced_panel`, `anticipation`, `bstrap`/`cband`/`biters`, `clustervars` two-variable limit, `est_method`, `base_period`, `faster_mode`, `compute_inffunc`); the `inffunc` rowname contract. |
| https://bcallaway11.github.io/did/reference/aggte.html | `aggte()` signature and defaults; the four `type` values and their meanings; `balance_e`, `min_e`, `max_e`, `na.rm`, inherited inference options. |
| https://bcallaway11.github.io/did/reference/MP.html | Every field of the `MP` return object. |
| https://bcallaway11.github.io/did/reference/AGGTEobj.html | Every field of the `AGGTEobj` return object. |
| https://bcallaway11.github.io/did/reference/mpdta.html | Dataset shape (2,500 rows, 6 variables, 500 counties, 2003-2007) and each variable's meaning. |
| https://bcallaway11.github.io/did/reference/ggdid.html | `ggdid()` generic and its `MP` / `AGGTEobj` methods. |
| https://bcallaway11.github.io/did/articles/did-basics.html (vignette build date 2026-06-13) | The complete worked example: `head(mpdta)`, the 12-row group-time table, pre-test p-value 0.16812, dynamic and `balance_e = 1` aggregations, the simulated-data simple/group/calendar outputs, the data-requirements list, the small-group behavior (`NA` + warning), the uniform critical value 2.7 vs 1.96, and the figure URLs used in the Figures section. |
| https://bcallaway11.github.io/did/articles/multi-period-did.html | Definition of $ATT(g,t)$; the staggered-adoption, no-anticipation and both parallel-trends statements; the never-treated and not-yet-treated identification formulas; the cohort, overall and dynamic aggregation formulas. |
| https://bcallaway11.github.io/did/articles/pre-testing.html (vignette build date 2026-06-13) | The event-study-regression pitfall under selective treatment timing, with the contrasting `plm` lead coefficients (0.938, 0.424) and `att_gt()` pre-treatment cells and p-value 0.79239; the motivation and call signature for `conditional_did_pretest()`; the Abadie (2005), Heckman-Ichimura-Todd (1998) and Sun-Abraham (2021) citations. |
| https://bcallaway11.github.io/did/news/index.html | The 2.5.0 changelog: dependency floors, `compute_inffunc`, `fix_weights`, transformation and factor covariates, `inffunc` rownames and ordering caveat, the performance numbers (2.5-3x, 10-15%, 2x unbalanced, 100x+ pre-test step), clustered-inference changes, and the bug fixes quoted under Failure modes. |
| https://raw.githubusercontent.com/bcallaway11/did/master/R/pre_process_did.R | Every verbatim error and warning string in the Failure modes table, with its triggering condition. |
| https://cran.r-project.org/web/packages/did/index.html | Version 2.5.1, published 2026-07-08; Depends/Imports with version floors; authors, maintainer, GPL-3 licence, package URLs. |
| https://arxiv.org/abs/1803.09015 | Preprint identifier, v1 2018-03-23 / v4 2020-12-01, arXiv DOI 10.48550/arXiv.1803.09015, and the abstract's framing of the identification result. |
| https://ideas.repec.org/a/eee/econom/v225y2021i2p200-230.html (via search) | Journal of Econometrics 225(2), 200-230, 2021, DOI 10.1016/j.jeconom.2020.12.001 — corroborated by the citation the package prints in every `summary()`. |
| https://psantanna.com/DRDID/reference/drdid_panel.html | The doubly robust 2x2 engine: logit propensity score + linear outcome regression, and the Sant'Anna and Zhao (2020) *JoE* 219(1), 101-122, DOI 10.1016/j.jeconom.2020.06.003 citation. |
| https://www.aeaweb.org/articles?id=10.1257/aer.20181169 (via search) | de Chaisemartin and D'Haultfœuille (2020), AER 110(9), 2964-2996, DOI 10.1257/aer.20181169. |
| https://academic.oup.com/restud/article-abstract/90/5/2555/7039335 (via search) | Rambachan and Roth (2023), *Review of Economic Studies* 90(5), 2555-2591, DOI 10.1093/restud/rdad018. |

Sources that were attempted and are *not* the basis of anything here: the ScienceDirect landing page for the Callaway-Sant'Anna article returned HTTP 403, so the journal metadata above comes from the package's own printed citation plus the RePEc record rather than from the publisher page.

### Open questions

- **Package version behind the printed output.** The vignette pages carry a build date of 2026-06-13 while CRAN's current release is 2.5.1 (2026-07-08). The pkgdown site is built from the development source, so the exact version that produced the console numbers quoted above is not stated on the page. Treat the digits as reproducible-in-spirit, not as a regression fixture, and re-run before citing them.
- **`aggte()` default `type`.** The reference page shows `type = "group"` in the signature and labels `"group"` as the default. This has changed across the package's history; verify against your installed version with `args(aggte)` before relying on the default.
- **`ggdid.MP()` / `ggdid.AGGTEobj()` argument lists.** The generic's page defers to `help(ggdid.MP)` and `help(ggdid.AGGTEobj)`; only `ylim` is confirmed here from vignette usage. The remaining plotting arguments were not verified.
- **`conditional_did_pretest()` full signature and return object.** Only the call form shown in the pre-testing vignette was verified; its arguments beyond `yname, tname, idname, gname, xformla, data` and its return fields were not.
- **Custom `est_method` contract.** The documentation says a user function must match the DRDID signature and warns this is advanced usage; the exact required signature and return shape were not verified here.
- **Effect sizes.** The minimum-wage numbers are illustrative. The vignette states plainly that a real evaluation of minimum-wage effects on teen employment would need more care along several dimensions; do not quote $-0.0772$ as a substantive finding.
- **Not verified in this pass, deliberately omitted from the comparison table:** the Goodman-Bacon decomposition, Borusyak-Jaravel-Spiess imputation, and Wooldridge's extended TWFE. All three are relevant siblings, but no citation details were checked, so none are asserted above. A future revision should verify and add them.
- **Stata and Python ports.** Implementations exist outside R (`csdid` and others). None were read here, so no claim is made about their argument names, defaults, or numerical agreement with the R package.
